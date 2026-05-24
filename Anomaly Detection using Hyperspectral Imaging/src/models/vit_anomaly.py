"""
Vision Transformer (ViT) for Spatial-Spectral Anomaly Detection
State-of-the-art transformer model for hyperspectral image analysis
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from typing import Tuple, Optional
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

try:
    import timm
    TIMM_AVAILABLE = True
except ImportError:
    TIMM_AVAILABLE = False
    print("Warning: timm not installed. Install with: pip install timm")


class PatchEmbedding(nn.Module):
    """Convert hyperspectral image into patches and embed them."""
    
    def __init__(self, in_channels: int, patch_size: int = 16, embed_dim: int = 768):
        super().__init__()
        self.patch_size = patch_size
        self.proj = nn.Conv2d(
            in_channels, embed_dim,
            kernel_size=patch_size,
            stride=patch_size
        )
    
    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, Tuple[int, int]]:
        """
        Args:
            x: (B, C, H, W) - Batch of hyperspectral images
        Returns:
            patches: (B, N, D) - Flattened patches
            grid_size: (H//patch_size, W//patch_size)
        """
        B, C, H, W = x.shape
        patches = self.proj(x)  # (B, D, H//P, W//P)
        patches = patches.flatten(2).transpose(1, 2)  # (B, N, D)
        grid_size = (H // self.patch_size, W // self.patch_size)
        return patches, grid_size


class MultiSpectralViT(nn.Module):
    """
    Vision Transformer for Multi-Spectral/Hyperspectral Anomaly Detection
    """
    
    def __init__(
        self,
        in_channels: int = 10,  # PCA components
        patch_size: int = 8,
        embed_dim: int = 256,
        depth: int = 6,
        num_heads: int = 8,
        mlp_ratio: float = 4.0,
        dropout: float = 0.1,
        num_classes: int = 1  # Binary anomaly detection
    ):
        super().__init__()
        
        self.in_channels = in_channels
        self.patch_size = patch_size
        self.embed_dim = embed_dim
        
        self.patch_embed = PatchEmbedding(in_channels, patch_size, embed_dim)
        
        # Positional encoding - dynamic based on max patches
        self.pos_embed = nn.Parameter(torch.zeros(1, 1024, embed_dim))  # Max 32x32 patches
        self.pos_drop = nn.Dropout(dropout)
        
        # Transformer blocks
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=embed_dim,
            nhead=num_heads,
            dim_feedforward=int(embed_dim * mlp_ratio),
            dropout=dropout,
            batch_first=True
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, depth)
        
        # Classification head
        self.norm = nn.LayerNorm(embed_dim)
        self.head = nn.Linear(embed_dim, num_classes)
        
        # Reconstruction head for anomaly detection
        self.decoder = nn.Sequential(
            nn.Linear(embed_dim, embed_dim * 4),
            nn.GELU(),
            nn.Linear(embed_dim * 4, in_channels * patch_size * patch_size)
        )
        
    def forward(self, x: torch.Tensor, return_features: bool = False) -> dict:
        """
        Args:
            x: (B, C, H, W) - Input hyperspectral image
            return_features: Whether to return intermediate features
        Returns:
            dict with anomaly scores, reconstructions, and features
        """
        B, C, H, W = x.shape
        
        # Patch embedding
        patches, grid_size = self.patch_embed(x)  # (B, N, D)
        N = patches.shape[1]
        
        # Add positional encoding - handle dynamic patch count
        if N <= self.pos_embed.shape[1]:
            pos_embed = self.pos_embed[:, :N, :]
        else:
            # If more patches than expected, use learned interpolation
            pos_embed = F.interpolate(
                self.pos_embed.permute(0, 2, 1).reshape(1, self.embed_dim, 32, 32),
                size=(int((H/self.patch_size)), int((W/self.patch_size))),
                mode='bilinear',
                align_corners=False
            )
            pos_embed = pos_embed.reshape(1, self.embed_dim, -1).permute(0, 2, 1)
        
        patches = patches + pos_embed
        patches = self.pos_drop(patches)
        
        # Transformer encoding
        features = self.transformer(patches)  # (B, N, D)
        features_norm = self.norm(features)
        
        # Classification (anomaly score per patch)
        patch_scores = self.head(features_norm).squeeze(-1)  # (B, N)
        
        # Reconstruction
        reconstruction = self.decoder(features_norm)  # (B, N, C*P*P)
        reconstruction = reconstruction.view(B, N, C, self.patch_size, self.patch_size)
        
        # Reshape back to image
        H_patches, W_patches = grid_size
        reconstruction = reconstruction.permute(0, 2, 1, 3, 4)  # (B, C, N, P, P)
        reconstruction = reconstruction.reshape(B, C, H_patches * self.patch_size, W_patches * self.patch_size)
        
        # Crop/pad to match original size
        if reconstruction.shape[2] != H or reconstruction.shape[3] != W:
            reconstruction = F.interpolate(reconstruction, size=(H, W), mode='bilinear', align_corners=False)
        
        result = {
            'patch_scores': patch_scores,
            'reconstruction': reconstruction,
            'features': features_norm if return_features else None
        }
        
        return result


class ViTAnomalyDetector:
    """
    Wrapper class for ViT-based anomaly detection
    """
    
    def __init__(
        self,
        in_channels: int = 10,
        patch_size: int = 8,
        embed_dim: int = 256,
        depth: int = 6,
        num_heads: int = 8,
        device: str = 'cuda' if torch.cuda.is_available() else 'cpu',
        epochs: int = 50,
        batch_size: int = 32,
        learning_rate: float = 1e-4
    ):
        self.device = device
        self.epochs = epochs
        self.batch_size = batch_size
        self.learning_rate = learning_rate
        
        # Initialize model
        self.model = MultiSpectralViT(
            in_channels=in_channels,
            patch_size=patch_size,
            embed_dim=embed_dim,
            depth=depth,
            num_heads=num_heads
        ).to(device)
        
        self.optimizer = torch.optim.AdamW(self.model.parameters(), lr=learning_rate)
        self.scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(self.optimizer, T_max=epochs)
        
        self.is_trained = False
        
    def train(self, data: np.ndarray, original_shape: Tuple[int, int], verbose: bool = True):
        """
        Train ViT on normal data (unsupervised)
        
        Args:
            data: (H*W, C) - Flattened spectral data
            original_shape: (H, W) - Original image dimensions
            verbose: Print training progress
        """
        H, W = original_shape
        C = data.shape[1]
        
        # Reshape to image format
        data_img = data.reshape(H, W, C).transpose(2, 0, 1)  # (C, H, W)
        data_tensor = torch.FloatTensor(data_img).unsqueeze(0).to(self.device)  # (1, C, H, W)
        
        self.model.train()
        
        for epoch in range(self.epochs):
            # Reconstruction loss
            output = self.model(data_tensor)
            reconstruction = output['reconstruction']
            
            # MSE loss between input and reconstruction
            loss = F.mse_loss(reconstruction, data_tensor)
            
            self.optimizer.zero_grad()
            loss.backward()
            self.optimizer.step()
            self.scheduler.step()
            
            if verbose and (epoch + 1) % 10 == 0:
                print(f"Epoch [{epoch+1}/{self.epochs}], Loss: {loss.item():.6f}")
        
        self.is_trained = True
        if verbose:
            print("ViT training complete.")
    
    def detect_anomalies(
        self, 
        data: np.ndarray, 
        original_shape: Tuple[int, int],
        train: bool = False
    ) -> Tuple[np.ndarray, np.ndarray, float]:
        """
        Detect anomalies using reconstruction error
        
        Args:
            data: (H*W, C) - Flattened spectral data
            original_shape: (H, W) - Original image dimensions
            train: Whether to train before detection
            
        Returns:
            anomaly_scores: (H, W) - Anomaly scores per pixel
            binary_mask: (H, W) - Binary anomaly mask
            threshold: float - Computed threshold
        """
        if train:
            self.train(data, original_shape)
        
        H, W = original_shape
        C = data.shape[1]
        
        # Reshape to image format
        data_img = data.reshape(H, W, C).transpose(2, 0, 1)  # (C, H, W)
        data_tensor = torch.FloatTensor(data_img).unsqueeze(0).to(self.device)  # (1, C, H, W)
        
        self.model.eval()
        with torch.no_grad():
            output = self.model(data_tensor, return_features=True)
            reconstruction = output['reconstruction']
            patch_scores = output['patch_scores']
        
        # Compute reconstruction error per pixel
        reconstruction_error = torch.mean((data_tensor - reconstruction) ** 2, dim=1)  # (1, H, W)
        anomaly_scores = reconstruction_error.squeeze(0).cpu().numpy()  # (H, W)
        
        # Normalize scores
        anomaly_scores = (anomaly_scores - anomaly_scores.min()) / (anomaly_scores.max() - anomaly_scores.min() + 1e-8)
        
        # Adaptive threshold
        threshold = np.mean(anomaly_scores) + 2 * np.std(anomaly_scores)
        binary_mask = (anomaly_scores > threshold).astype(np.float32)
        
        return anomaly_scores, binary_mask, threshold
    
    def get_explanations(self, data: np.ndarray, original_shape: Tuple[int, int]) -> dict:
        """
        Get model explanations (attention maps, feature importance)
        
        Args:
            data: (H*W, C) - Flattened spectral data
            original_shape: (H, W) - Original image dimensions
            
        Returns:
            dict with attention maps and feature importance
        """
        H, W = original_shape
        C = data.shape[1]
        
        data_img = data.reshape(H, W, C).transpose(2, 0, 1)
        data_tensor = torch.FloatTensor(data_img).unsqueeze(0).to(self.device)
        
        self.model.eval()
        with torch.no_grad():
            output = self.model(data_tensor, return_features=True)
            features = output['features']  # (1, N, D)
        
        # Reshape features to spatial grid
        patch_size = self.model.patch_size
        H_patches = H // patch_size
        W_patches = W // patch_size
        
        # Compute feature importance (mean across dimensions)
        feature_importance = features.mean(dim=-1).squeeze(0).cpu().numpy()  # (N,)
        feature_importance = feature_importance.reshape(H_patches, W_patches)
        
        # Upsample to original size
        feature_importance = torch.FloatTensor(feature_importance).unsqueeze(0).unsqueeze(0)
        feature_importance = F.interpolate(feature_importance, size=(H, W), mode='bilinear', align_corners=False)
        feature_importance = feature_importance.squeeze().numpy()
        
        return {
            'attention_map': feature_importance,
            'patch_scores': output['patch_scores'].squeeze(0).cpu().numpy()
        }
    
    def save_model(self, path: str):
        """Save model weights."""
        torch.save({
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'is_trained': self.is_trained
        }, path)
    
    def load_model(self, path: str):
        """Load model weights."""
        checkpoint = torch.load(path, map_location=self.device)
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        self.is_trained = checkpoint.get('is_trained', False)


if __name__ == "__main__":
    # Test the ViT model
    print("Testing Vision Transformer for Anomaly Detection...")
    
    # Create dummy data
    H, W, C = 64, 64, 10
    dummy_data = np.random.randn(H * W, C).astype(np.float32)
    
    # Initialize detector
    detector = ViTAnomalyDetector(
        in_channels=C,
        patch_size=8,
        embed_dim=128,
        depth=4,
        num_heads=4,
        epochs=5,  # Quick test
        batch_size=16
    )
    
    # Train
    print("Training...")
    detector.train(dummy_data, (H, W), verbose=True)
    
    # Detect
    print("Detecting anomalies...")
    scores, mask, threshold = detector.detect_anomalies(dummy_data, (H, W))
    
    print(f"Anomaly score range: [{scores.min():.4f}, {scores.max():.4f}]")
    print(f"Threshold: {threshold:.4f}")
    print(f"Anomalies detected: {mask.sum()} pixels ({mask.sum()/mask.size*100:.2f}%)")
    
    # Get explanations
    print("Getting explanations...")
    explanations = detector.get_explanations(dummy_data, (H, W))
    print(f"Attention map shape: {explanations['attention_map'].shape}")
    
    print("Test complete!")
