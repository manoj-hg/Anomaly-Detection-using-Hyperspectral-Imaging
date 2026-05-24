"""
Model Explainability Module
Provides SHAP values, Grad-CAM, and other explanation methods
"""

import numpy as np
import torch
import torch.nn.functional as F
from typing import Dict, Tuple, Optional, Any
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False
    print("Warning: shap not installed. Install with: pip install shap")


class ModelExplainer:
    """
    Unified model explainability interface
    """
    
    def __init__(self, model, device: str = 'cpu'):
        self.model = model
        self.device = device
        self.explainer = None
        
    def compute_shap_values(
        self, 
        data: np.ndarray, 
        background_samples: int = 100,
        nsamples: int = 100
    ) -> Dict[str, np.ndarray]:
        """
        Compute SHAP values for model explanations
        
        Args:
            data: Input data (N, C)
            background_samples: Number of background samples
            nsamples: Number of SHAP samples
            
        Returns:
            dict with SHAP values and base values
        """
        if not SHAP_AVAILABLE:
            print("SHAP not available, skipping explainability")
            return None
        
        # Create background data
        background = data[np.random.choice(len(data), min(background_samples, len(data)), replace=False)]
        
        # Create explainer
        def model_wrapper(x):
            x_tensor = torch.FloatTensor(x).to(self.device)
            with torch.no_grad():
                output = self.model(x_tensor)
                if isinstance(output, dict):
                    return output.get('anomaly_scores', output.get('reconstruction_error', np.zeros(len(x))))
                return output.cpu().numpy()
        
        self.explainer = shap.KernelExplainer(model_wrapper, background)
        
        # Compute SHAP values
        shap_values = self.explainer.shap_values(data, nsamples=nsamples)
        
        return {
            'shap_values': shap_values,
            'base_values': self.explainer.expected_value
        }
    
    def compute_grad_cam(
        self,
        data: torch.Tensor,
        target_layer: Optional[torch.nn.Module] = None,
        class_idx: int = 0
    ) -> np.ndarray:
        """
        Compute Grad-CAM heatmap for CNN/Transformer models
        
        Args:
            data: Input tensor (B, C, H, W)
            target_layer: Target layer for Grad-CAM
            class_idx: Target class index
            
        Returns:
            Grad-CAM heatmap (H, W)
        """
        self.model.eval()
        data = data.requires_grad_(True).to(self.device)
        
        # Forward pass
        output = self.model(data)
        if isinstance(output, dict):
            scores = output.get('patch_scores', output.get('anomaly_scores'))
        else:
            scores = output
        
        # Get target score
        if len(scores.shape) > 2:
            target = scores[:, class_idx].mean()
        else:
            target = scores.mean()
        
        # Backward pass
        self.model.zero_grad()
        target.backward()
        
        # Get gradients
        gradients = data.grad
        
        # Compute Grad-CAM
        weights = gradients.mean(dim=(2, 3), keepdim=True)
        cam = (gradients * weights).sum(dim=1, keepdim=True)
        cam = F.relu(cam)
        
        # Normalize
        cam = cam.squeeze().cpu().numpy()
        cam = (cam - cam.min()) / (cam.max() - cam.min() + 1e-8)
        
        return cam
    
    def compute_feature_importance(
        self,
        data: np.ndarray,
        method: str = 'permutation'
    ) -> Dict[str, np.ndarray]:
        """
        Compute feature importance
        
        Args:
            data: Input data (N, C)
            method: 'permutation' or 'variance'
            
        Returns:
            dict with feature importance scores
        """
        if method == 'permutation':
            # Permutation importance
            original_pred = self._predict(data)
            importance = np.zeros(data.shape[1])
            
            for i in range(data.shape[1]):
                data_permuted = data.copy()
                np.random.shuffle(data_permuted[:, i])
                permuted_pred = self._predict(data_permuted)
                importance[i] = np.mean(np.abs(original_pred - permuted_pred))
            
            return {'feature_importance': importance}
        
        elif method == 'variance':
            # Variance-based importance
            return {'feature_importance': np.var(data, axis=0)}
        
        else:
            raise ValueError(f"Unknown method: {method}")
    
    def _predict(self, data: np.ndarray) -> np.ndarray:
        """Helper function for predictions"""
        data_tensor = torch.FloatTensor(data).to(self.device)
        with torch.no_grad():
            output = self.model(data_tensor)
            if isinstance(output, dict):
                output = output.get('anomaly_scores', output.get('reconstruction_error'))
            return output.cpu().numpy()
    
    def generate_explanation_report(
        self,
        data: np.ndarray,
        original_shape: Tuple[int, int]
    ) -> Dict[str, Any]:
        """
        Generate comprehensive explanation report
        
        Args:
            data: Input data
            original_shape: Original image shape
            
        Returns:
            dict with all explanations
        """
        report = {
            'shap': self.compute_shap_values(data),
            'feature_importance': self.compute_feature_importance(data),
            'summary': {
                'num_features': data.shape[1],
                'num_samples': data.shape[0],
                'shape': original_shape
            }
        }
        
        return report


class AttentionVisualizer:
    """
    Visualize attention maps from transformer models
    """
    
    def __init__(self, model, device: str = 'cpu'):
        self.model = model
        self.device = device
    
    def extract_attention_maps(
        self,
        data: torch.Tensor,
        layer_idx: int = -1
    ) -> np.ndarray:
        """
        Extract attention maps from transformer
        
        Args:
            data: Input tensor (B, C, H, W)
            layer_idx: Which layer to extract from
            
        Returns:
            Attention maps (B, heads, H, W)
        """
        self.model.eval()
        
        # Hook to capture attention
        attention_maps = []
        
        def hook_fn(module, input, output):
            if hasattr(output, 'attn_weights'):
                attention_maps.append(output.attn_weights.detach())
        
        # Register hook
        if hasattr(self.model, 'transformer'):
            target_layer = self.model.transformer.layers[layer_idx]
            handle = target_layer.register_forward_hook(hook_fn)
        
        # Forward pass
        with torch.no_grad():
            _ = self.model(data)
        
        # Remove hook
        if 'handle' in locals():
            handle.remove()
        
        if attention_maps:
            return attention_maps[0].cpu().numpy()
        else:
            # Fallback: use feature maps
            with torch.no_grad():
                output = self.model(data, return_features=True)
                features = output.get('features')
                if features is not None:
                    return features.mean(dim=-1).cpu().numpy()
        
        return np.zeros((1, 1, data.shape[2], data.shape[3]))
    
    def visualize_attention(
        self,
        attention_map: np.ndarray,
        original_shape: Tuple[int, int]
    ) -> np.ndarray:
        """
        Upsample and normalize attention map for visualization
        
        Args:
            attention_map: Attention map (H', W')
            original_shape: Target shape (H, W)
            
        Returns:
            Visualized attention map (H, W)
        """
        import cv2
        
        # Normalize
        attention_map = (attention_map - attention_map.min()) / (attention_map.max() - attention_map.min() + 1e-8)
        
        # Upsample
        if attention_map.shape != original_shape:
            attention_map = cv2.resize(
                attention_map, 
                (original_shape[1], original_shape[0]),
                interpolation=cv2.INTER_LINEAR
            )
        
        # Apply colormap
        attention_map = (attention_map * 255).astype(np.uint8)
        attention_map = cv2.applyColorMap(attention_map, cv2.COLORMAP_JET)
        
        return attention_map


if __name__ == "__main__":
    print("Testing Model Explainability Module...")
    
    # Create dummy model
    class DummyModel(torch.nn.Module):
        def __init__(self):
            super().__init__()
            self.fc = torch.nn.Linear(10, 1)
        
        def forward(self, x):
            return self.fc(x)
    
    model = DummyModel()
    explainer = ModelExplainer(model)
    
    # Test data
    data = np.random.randn(100, 10)
    
    # Test feature importance
    importance = explainer.compute_feature_importance(data, method='variance')
    print(f"Feature importance shape: {importance['feature_importance'].shape}")
    
    print("Explainability module test complete!")
