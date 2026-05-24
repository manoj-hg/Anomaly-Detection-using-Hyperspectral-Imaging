"""
Score Fusion Module
Combines anomaly scores from multiple models with optimization.
"""

import numpy as np
import cv2
from sklearn.preprocessing import MinMaxScaler
from typing import Tuple, Optional


class ScoreFusion:
    """Fuses anomaly scores from multiple models with optimization."""
    
    def __init__(self, isolation_weight: float = 0.5, 
                 autoencoder_weight: float = 0.5,
                 vit_weight: float = 0.0):
        """
        Initialize the score fusion module.
        
        Args:
            isolation_weight: Weight for Isolation Forest scores
            autoencoder_weight: Weight for Autoencoder scores
            vit_weight: Weight for Vision Transformer scores
        """
        self.isolation_weight = isolation_weight
        self.autoencoder_weight = autoencoder_weight
        self.vit_weight = vit_weight
        self.scaler = MinMaxScaler()
    
    def normalize_scores(self, scores: np.ndarray) -> np.ndarray:
        """
        Normalize scores to [0, 1] range.
        
        Args:
            scores: Input scores (1D or 2D)
            
        Returns:
            Normalized scores
        """
        scores_flat = scores.flatten()
        scores_normalized = self.scaler.fit_transform(scores_flat.reshape(-1, 1)).flatten()
        return scores_normalized.reshape(scores.shape)
    
    def weighted_sum(self, score_map1: np.ndarray, 
                    score_map2: np.ndarray,
                    score_map3: Optional[np.ndarray] = None) -> np.ndarray:
        """
        Combine two or three score maps using weighted sum.
        
        Args:
            score_map1: First score map (e.g., Isolation Forest)
            score_map2: Second score map (e.g., Autoencoder)
            score_map3: Optional third score map (e.g., Vision Transformer)
            
        Returns:
            Fused score map
        """
        # Normalize both score maps
        score_map1_norm = self.normalize_scores(score_map1)
        score_map2_norm = self.normalize_scores(score_map2)
        
        if score_map3 is not None and self.vit_weight > 0:
            score_map3_norm = self.normalize_scores(score_map3)
            # Three-way weighted sum
            fused = (self.isolation_weight * score_map1_norm + 
                    self.autoencoder_weight * score_map2_norm +
                    self.vit_weight * score_map3_norm)
        else:
            # Two-way weighted sum
            fused = (self.isolation_weight * score_map1_norm + 
                    self.autoencoder_weight * score_map2_norm)
        
        return fused
    
    def adaptive_threshold(self, scores: np.ndarray, 
                          multiplier: float = 1.0) -> float:
        """
        Compute adaptive threshold using mean + std * multiplier.
        
        Args:
            scores: Anomaly scores
            multiplier: Multiplier for standard deviation
            
        Returns:
            Threshold value
        """
        threshold = scores.mean() + multiplier * scores.std()
        return threshold
    
    def median_filter(self, scores: np.ndarray, 
                     kernel_size: int = 3) -> np.ndarray:
        """
        Apply median filtering to reduce noise in score maps.
        
        Args:
            scores: Anomaly score map
            kernel_size: Size of median filter kernel
            
        Returns:
            Filtered score map
        """
        # Ensure odd kernel size
        if kernel_size % 2 == 0:
            kernel_size += 1
        
        # Convert to uint8 for OpenCV
        scores_uint8 = (scores * 255).astype(np.uint8)
        
        # Apply median filter
        filtered = cv2.medianBlur(scores_uint8, kernel_size)
        
        # Convert back to float
        filtered = filtered.astype(np.float32) / 255.0
        
        return filtered
    
    def reduce_false_positives(self, scores: np.ndarray,
                              min_cluster_size: int = 5) -> np.ndarray:
        """
        Reduce false positives by removing small isolated clusters.
        
        Args:
            scores: Anomaly score map
            min_cluster_size: Minimum cluster size to keep
            
        Returns:
            Processed score map
        """
        # Create binary mask
        threshold = self.adaptive_threshold(scores)
        binary = (scores > threshold).astype(np.uint8)
        
        # Find connected components
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(
            binary, connectivity=8
        )
        
        # Remove small components
        filtered = binary.copy()
        for i in range(1, num_labels):  # Skip background (label 0)
            if stats[i, cv2.CC_STAT_AREA] < min_cluster_size:
                filtered[labels == i] = 0
        
        # Convert back to scores
        filtered_scores = scores * filtered
        
        return filtered_scores
    
    def fuse_and_optimize(self, isolation_scores: np.ndarray,
                         autoencoder_scores: np.ndarray,
                         vit_scores: Optional[np.ndarray] = None,
                         apply_filtering: bool = True,
                         apply_fp_reduction: bool = True) -> Tuple[np.ndarray, np.ndarray, float]:
        """
        Complete fusion and optimization pipeline.
        
        Args:
            isolation_scores: Isolation Forest anomaly scores
            autoencoder_scores: Autoencoder anomaly scores
            vit_scores: Optional Vision Transformer anomaly scores
            apply_filtering: Whether to apply median filtering
            apply_fp_reduction: Whether to apply false positive reduction
            
        Returns:
            Tuple of (fused_score_map, binary_mask, threshold)
        """
        print("Fusing anomaly scores...")
        
        # Step 1: Weighted sum fusion
        fused = self.weighted_sum(isolation_scores, autoencoder_scores, vit_scores)
        
        # Step 2: Median filtering
        if apply_filtering:
            print("Applying median filtering...")
            fused = self.median_filter(fused, kernel_size=3)
        
        # Step 3: False positive reduction
        if apply_fp_reduction:
            print("Reducing false positives...")
            fused = self.reduce_false_positives(fused, min_cluster_size=5)
        
        # Step 4: Adaptive thresholding
        threshold = self.adaptive_threshold(fused, multiplier=1.0)
        binary_mask = (fused > threshold).astype(int)
        
        print(f"Fusion complete. Threshold: {threshold:.4f}")
        print(f"Anomalies detected: {binary_mask.sum()} pixels")
        
        return fused, binary_mask, threshold
    
    def create_overlay(self, rgb_image: np.ndarray,
                      binary_mask: np.ndarray,
                      alpha: float = 0.5,
                      color: Tuple[int, int, int] = (255, 0, 0)) -> np.ndarray:
        """
        Create overlay of anomalies on RGB image.
        
        Args:
            rgb_image: RGB image of shape (H, W, 3)
            binary_mask: Binary anomaly mask of shape (H, W)
            alpha: Transparency of overlay (0-1)
            color: Color for anomaly overlay (B, G, R)
            
        Returns:
            Overlay image
        """
        # Ensure RGB is in correct range
        if rgb_image.max() <= 1.0:
            rgb_image = (rgb_image * 255).astype(np.uint8)
        
        # Create overlay
        overlay = rgb_image.copy()
        overlay[binary_mask == 1] = color
        
        # Blend
        result = cv2.addWeighted(rgb_image, 1 - alpha, overlay, alpha, 0)
        
        return result
    
    def create_heatmap(self, scores: np.ndarray,
                      colormap: int = cv2.COLORMAP_JET) -> np.ndarray:
        """
        Create heatmap visualization of anomaly scores.
        
        Args:
            scores: Anomaly score map
            colormap: OpenCV colormap to use
            
        Returns:
            Heatmap image
        """
        # Normalize to 0-255
        scores_normalized = self.normalize_scores(scores)
        scores_uint8 = (scores_normalized * 255).astype(np.uint8)
        
        # Apply colormap
        heatmap = cv2.applyColorMap(scores_uint8, colormap)
        
        return heatmap


def main():
    """Test the score fusion."""
    print("=== Testing Score Fusion ===\n")
    
    # Create synthetic score maps
    np.random.seed(42)
    h, w = 100, 100
    
    # Isolation Forest scores
    isolation_scores = np.random.rand(h, w) * 0.3
    isolation_scores[40:60, 40:60] = 0.8  # Add anomaly region
    
    # Autoencoder scores
    autoencoder_scores = np.random.rand(h, w) * 0.3
    autoencoder_scores[45:55, 45:55] = 0.9  # Add anomaly region
    
    # Initialize fusion
    fusion = ScoreFusion(isolation_weight=0.5, autoencoder_weight=0.5)
    
    # Fuse and optimize
    fused, binary_mask, threshold = fusion.fuse_and_optimize(
        isolation_scores, autoencoder_scores
    )
    
    print(f"\nFusion complete!")
    print(f"Fused score map shape: {fused.shape}")
    print(f"Binary mask shape: {binary_mask.shape}")
    print(f"Threshold: {threshold:.4f}")
    print(f"Anomalies detected: {binary_mask.sum()} pixels")


if __name__ == "__main__":
    main()
