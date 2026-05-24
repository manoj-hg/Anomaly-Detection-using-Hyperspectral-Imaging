"""
Visualization Utilities
Helper functions for visualizing spectral data and anomaly detection results.
"""

import numpy as np
import matplotlib.pyplot as plt
import cv2
from typing import Tuple, Optional, List
import os


class Visualizer:
    """Visualization utilities for spectral anomaly detection."""
    
    def __init__(self, figsize: Tuple[int, int] = (15, 10)):
        """
        Initialize the visualizer.
        
        Args:
            figsize: Default figure size for plots
        """
        self.figsize = figsize
        plt.style.use('seaborn-v0_8-darkgrid')
    
    def plot_rgb_composite(self, rgb: np.ndarray, title: str = "RGB Composite"):
        """
        Plot RGB composite image.
        
        Args:
            rgb: RGB image of shape (H, W, 3)
            title: Plot title
        """
        plt.figure(figsize=(8, 8))
        plt.imshow(rgb)
        plt.title(title)
        plt.axis('off')
        plt.tight_layout()
        plt.show()
    
    def plot_pca_components(self, pca_data: np.ndarray, 
                           n_components: int = 4):
        """
        Plot PCA component visualization.
        
        Args:
            pca_data: PCA-transformed data of shape (H, W, Components)
            n_components: Number of components to display
        """
        n_to_plot = min(n_components, pca_data.shape[-1])
        fig, axes = plt.subplots(2, 2, figsize=(12, 12))
        axes = axes.flatten()
        
        for i in range(n_to_plot):
            im = axes[i].imshow(pca_data[:, :, i], cmap='viridis')
            axes[i].set_title(f'PCA Component {i+1}')
            axes[i].axis('off')
            plt.colorbar(im, ax=axes[i], fraction=0.046)
        
        plt.suptitle('PCA Components Visualization', fontsize=16)
        plt.tight_layout()
        plt.show()
    
    def plot_anomaly_score_map(self, score_map: np.ndarray,
                               title: str = "Anomaly Score Map",
                               cmap: str = 'hot'):
        """
        Plot anomaly score map.
        
        Args:
            score_map: Anomaly score map of shape (H, W)
            title: Plot title
            cmap: Colormap to use
        """
        plt.figure(figsize=(8, 8))
        im = plt.imshow(score_map, cmap=cmap)
        plt.title(title)
        plt.axis('off')
        plt.colorbar(im, fraction=0.046)
        plt.tight_layout()
        plt.show()
    
    def plot_binary_mask(self, binary_mask: np.ndarray,
                        title: str = "Binary Anomaly Mask"):
        """
        Plot binary anomaly mask.
        
        Args:
            binary_mask: Binary mask of shape (H, W)
            title: Plot title
        """
        plt.figure(figsize=(8, 8))
        plt.imshow(binary_mask, cmap='gray')
        plt.title(title)
        plt.axis('off')
        plt.tight_layout()
        plt.show()
    
    def plot_overlay(self, rgb: np.ndarray, 
                    binary_mask: np.ndarray,
                    title: str = "Anomaly Overlay"):
        """
        Plot anomaly overlay on RGB image.
        
        Args:
            rgb: RGB image of shape (H, W, 3)
            binary_mask: Binary mask of shape (H, W)
            title: Plot title
        """
        # Ensure RGB is in correct range
        if rgb.max() <= 1.0:
            rgb_display = rgb.copy()
        else:
            rgb_display = rgb / 255.0
        
        # Create overlay
        overlay = rgb_display.copy()
        overlay[binary_mask == 1] = [1, 0, 0]  # Red for anomalies
        
        plt.figure(figsize=(8, 8))
        plt.imshow(overlay)
        plt.title(title)
        plt.axis('off')
        plt.tight_layout()
        plt.show()
    
    def plot_comparison(self, rgb: np.ndarray,
                       isolation_scores: np.ndarray,
                       autoencoder_scores: np.ndarray,
                       fused_scores: np.ndarray,
                       binary_mask: np.ndarray):
        """
        Plot comprehensive comparison of all results.
        
        Args:
            rgb: RGB image
            isolation_scores: Isolation Forest scores
            autoencoder_scores: Autoencoder scores
            fused_scores: Fused scores
            binary_mask: Binary mask
        """
        fig, axes = plt.subplots(2, 3, figsize=(18, 12))
        
        # RGB composite
        axes[0, 0].imshow(rgb)
        axes[0, 0].set_title('RGB Composite')
        axes[0, 0].axis('off')
        
        # Isolation Forest
        im1 = axes[0, 1].imshow(isolation_scores, cmap='hot')
        axes[0, 1].set_title('Isolation Forest Scores')
        axes[0, 1].axis('off')
        plt.colorbar(im1, ax=axes[0, 1], fraction=0.046)
        
        # Autoencoder
        im2 = axes[0, 2].imshow(autoencoder_scores, cmap='hot')
        axes[0, 2].set_title('Autoencoder Scores')
        axes[0, 2].axis('off')
        plt.colorbar(im2, ax=axes[0, 2], fraction=0.046)
        
        # Fused scores
        im3 = axes[1, 0].imshow(fused_scores, cmap='hot')
        axes[1, 0].set_title('Fused Anomaly Scores')
        axes[1, 0].axis('off')
        plt.colorbar(im3, ax=axes[1, 0], fraction=0.046)
        
        # Binary mask
        axes[1, 1].imshow(binary_mask, cmap='gray')
        axes[1, 1].set_title('Binary Anomaly Mask')
        axes[1, 1].axis('off')
        
        # Overlay
        overlay = rgb.copy()
        if overlay.max() <= 1.0:
            overlay = overlay.copy()
        else:
            overlay = overlay / 255.0
        overlay[binary_mask == 1] = [1, 0, 0]
        axes[1, 2].imshow(overlay)
        axes[1, 2].set_title('Anomaly Overlay')
        axes[1, 2].axis('off')
        
        plt.suptitle('Anomaly Detection Results', fontsize=16)
        plt.tight_layout()
        plt.show()
    
    def save_figure(self, path: str, dpi: int = 300):
        """
        Save the current figure.
        
        Args:
            path: Path to save the figure
            dpi: Resolution in dots per inch
        """
        os.makedirs(os.path.dirname(path), exist_ok=True)
        plt.savefig(path, dpi=dpi, bbox_inches='tight')
        print(f"Figure saved to {path}")
    
    def plot_training_history(self, history: dict, title: str = "Training History"):
        """
        Plot training history (loss curves).
        
        Args:
            history: Dictionary containing training history
            title: Plot title
        """
        plt.figure(figsize=(10, 6))
        
        if 'loss' in history:
            plt.plot(history['loss'], label='Training Loss')
            plt.xlabel('Epoch')
            plt.ylabel('Loss')
            plt.title(title)
            plt.legend()
            plt.grid(True)
            plt.tight_layout()
            plt.show()
    
    def create_summary_image(self, rgb: np.ndarray,
                            isolation_scores: np.ndarray,
                            autoencoder_scores: np.ndarray,
                            fused_scores: np.ndarray,
                            binary_mask: np.ndarray) -> np.ndarray:
        """
        Create a single summary image with all visualizations.
        
        Args:
            rgb: RGB image
            isolation_scores: Isolation Forest scores
            autoencoder_scores: Autoencoder scores
            fused_scores: Fused scores
            binary_mask: Binary mask
            
        Returns:
            Summary image as numpy array
        """
        # Ensure RGB is uint8
        if rgb.max() <= 1.0:
            rgb_uint8 = (rgb * 255).astype(np.uint8)
        else:
            rgb_uint8 = rgb.astype(np.uint8)
        
        # Normalize score maps to 0-255
        isolation_norm = ((isolation_scores - isolation_scores.min()) / 
                         (isolation_scores.max() - isolation_scores.min() + 1e-8) * 255).astype(np.uint8)
        autoencoder_norm = ((autoencoder_scores - autoencoder_scores.min()) / 
                           (autoencoder_scores.max() - autoencoder_scores.min() + 1e-8) * 255).astype(np.uint8)
        fused_norm = ((fused_scores - fused_scores.min()) / 
                     (fused_scores.max() - fused_scores.min() + 1e-8) * 255).astype(np.uint8)
        
        # Convert to RGB using colormap
        isolation_rgb = cv2.applyColorMap(isolation_norm, cv2.COLORMAP_JET)
        autoencoder_rgb = cv2.applyColorMap(autoencoder_norm, cv2.COLORMAP_JET)
        fused_rgb = cv2.applyColorMap(fused_norm, cv2.COLORMAP_JET)
        
        # Binary mask as grayscale
        binary_rgb = cv2.cvtColor((binary_mask * 255).astype(np.uint8), cv2.COLOR_GRAY2RGB)
        
        # Overlay
        overlay = rgb_uint8.copy()
        overlay[binary_mask == 1] = [0, 0, 255]  # Red in BGR
        
        # Arrange in grid
        h, w = rgb.shape[:2]
        top_row = np.hstack([rgb_uint8, isolation_rgb, autoencoder_rgb])
        bottom_row = np.hstack([fused_rgb, binary_rgb, overlay])
        summary = np.vstack([top_row, bottom_row])
        
        return summary


def main():
    """Test the visualizer."""
    print("=== Testing Visualizer ===\n")
    
    # Create synthetic data
    np.random.seed(42)
    h, w = 100, 100
    
    rgb = np.random.rand(h, w, 3)
    isolation_scores = np.random.rand(h, w)
    autoencoder_scores = np.random.rand(h, w)
    fused_scores = np.random.rand(h, w)
    binary_mask = (fused_scores > 0.7).astype(int)
    
    # Initialize visualizer
    viz = Visualizer()
    
    # Test individual plots
    print("Testing individual plots...")
    viz.plot_rgb_composite(rgb)
    viz.plot_anomaly_score_map(isolation_scores, "Isolation Forest")
    viz.plot_binary_mask(binary_mask)
    
    # Test comparison
    print("Testing comparison plot...")
    viz.plot_comparison(rgb, isolation_scores, autoencoder_scores, fused_scores, binary_mask)
    
    # Test summary image
    print("Testing summary image...")
    summary = viz.create_summary_image(rgb, isolation_scores, autoencoder_scores, 
                                      fused_scores, binary_mask)
    print(f"Summary image shape: {summary.shape}")


if __name__ == "__main__":
    main()
