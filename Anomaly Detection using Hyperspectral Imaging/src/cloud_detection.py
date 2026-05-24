"""
Cloud Detection and Masking Module
Implements multiple methods for cloud detection in satellite imagery
"""

import numpy as np
from typing import Tuple, Optional
import cv2


class CloudDetector:
    """
    Detect clouds in satellite imagery using multiple methods
    """
    
    def __init__(self, method: str = 'threshold'):
        """
        Initialize cloud detector
        
        Args:
            method: Detection method ('threshold', 'ml', 'fmask')
        """
        self.method = method
    
    def detect_clouds_threshold(self, data: np.ndarray) -> np.ndarray:
        """
        Simple threshold-based cloud detection
        Uses brightness and spectral indices
        
        Args:
            data: Spectral data of shape (H, W, Bands)
            
        Returns:
            Binary cloud mask (1 = cloud, 0 = clear)
        """
        h, w, bands = data.shape
        
        # Need at least Blue, Green, Red, NIR bands
        if bands < 3:
            print("Insufficient bands for cloud detection, returning empty mask")
            return np.zeros((h, w), dtype=np.uint8)
        
        # Extract bands (assuming standard ordering: Blue, Green, Red, NIR, ...)
        blue = data[:, :, 0] if bands > 0 else data[:, :, 2]  # Blue or use Red as fallback
        green = data[:, :, 1] if bands > 1 else data[:, :, 1]
        red = data[:, :, 2] if bands > 2 else data[:, :, 0]
        
        # Calculate brightness
        if bands >= 3:
            brightness = (blue + green + red) / 3
        else:
            brightness = data.mean(axis=-1)
        
        # Calculate NDVI (if NIR available)
        if bands >= 4:
            nir = data[:, :, 3]
            ndvi = (nir - red) / (nir + red + 1e-8)
        else:
            ndvi = np.zeros_like(brightness)
        
        # Cloud detection rules
        # Rule 1: High brightness
        cloud_mask_1 = brightness > 0.6
        
        # Rule 2: Low NDVI (clouds have low vegetation index)
        cloud_mask_2 = ndvi < 0.1
        
        # Rule 3: Blue band ratio (clouds reflect more blue)
        if bands >= 3:
            blue_ratio = blue / (red + 1e-8)
            cloud_mask_3 = blue_ratio > 1.0
        else:
            cloud_mask_3 = np.zeros_like(brightness)
        
        # Combine rules
        cloud_mask = cloud_mask_1 & cloud_mask_2
        if bands >= 3:
            cloud_mask = cloud_mask | cloud_mask_3
        
        return cloud_mask.astype(np.uint8)
    
    def detect_clouds_ml(self, data: np.ndarray) -> np.ndarray:
        """
        Machine learning-based cloud detection
        Uses simple clustering to identify cloud pixels
        
        Args:
            data: Spectral data of shape (H, W, Bands)
            
        Returns:
            Binary cloud mask (1 = cloud, 0 = clear)
        """
        try:
            from sklearn.cluster import KMeans
        except ImportError:
            print("sklearn not available, falling back to threshold method")
            return self.detect_clouds_threshold(data)
        
        h, w, bands = data.shape
        
        # Reshape to pixel vectors
        pixels = data.reshape(-1, bands)
        
        # Use K-means to cluster into 2 groups (cloud vs non-cloud)
        kmeans = KMeans(n_clusters=2, random_state=42, n_init=10)
        labels = kmeans.fit_predict(pixels)
        
        # Determine which cluster is clouds (higher brightness)
        cluster_means = kmeans.cluster_centers_.mean(axis=1)
        cloud_cluster = np.argmax(cluster_means)
        
        # Create mask
        cloud_mask = (labels == cloud_cluster).reshape(h, w)
        
        return cloud_mask.astype(np.uint8)
    
    def detect_clouds_fmask(self, data: np.ndarray) -> np.ndarray:
        """
        FMask-like cloud detection algorithm
        Simplified implementation of the FMask algorithm
        
        Args:
            data: Spectral data of shape (H, W, Bands)
            
        Returns:
            Binary cloud mask (1 = cloud, 0 = clear)
        """
        h, w, bands = data.shape
        
        if bands < 4:
            print("FMask requires at least 4 bands (Blue, Green, Red, NIR), falling back to threshold")
            return self.detect_clouds_threshold(data)
        
        # Extract bands
        blue = data[:, :, 0]
        green = data[:, :, 1]
        red = data[:, :, 2]
        nir = data[:, :, 3]
        
        # Calculate indices
        ndvi = (nir - red) / (nir + red + 1e-8)
        ndsi = (green - nir) / (green + nir + 1e-8)  # Normalized Difference Snow Index
        
        # Brightness
        brightness = (blue + green + red + nir) / 4
        
        # FMask rules (simplified)
        # Rule 1: Low NDVI (not vegetation)
        mask1 = ndvi < 0.2
        
        # Rule 2: High brightness
        mask2 = brightness > 0.4
        
        # Rule 3: Not snow (snow has high NDSI)
        mask3 = ndsi < 0.4
        
        # Rule 4: Blue band threshold
        mask4 = blue > 0.3
        
        # Combine rules
        cloud_mask = mask1 & mask2 & mask3 & mask4
        
        return cloud_mask.astype(np.uint8)
    
    def detect_clouds(self, data: np.ndarray) -> np.ndarray:
        """
        Detect clouds using the specified method
        
        Args:
            data: Spectral data of shape (H, W, Bands)
            
        Returns:
            Binary cloud mask (1 = cloud, 0 = clear)
        """
        print(f"Detecting clouds using method: {self.method}")
        
        if self.method == 'threshold':
            return self.detect_clouds_threshold(data)
        elif self.method == 'ml':
            return self.detect_clouds_ml(data)
        elif self.method == 'fmask':
            return self.detect_clouds_fmask(data)
        else:
            print(f"Unknown cloud detection method: {self.method}, using threshold")
            return self.detect_clouds_threshold(data)
    
    def remove_clouds(self, data: np.ndarray, cloud_mask: np.ndarray, 
                     method: str = 'interpolation') -> np.ndarray:
        """
        Remove clouds from spectral data
        
        Args:
            data: Spectral data of shape (H, W, Bands)
            cloud_mask: Binary cloud mask (1 = cloud, 0 = clear)
            method: Removal method ('interpolation', 'temporal', 'median')
            
        Returns:
            Cloud-corrected data
        """
        h, w, bands = data.shape
        corrected = data.copy()
        
        if method == 'interpolation':
            # Simple interpolation using neighboring pixels
            for band in range(bands):
                band_data = corrected[:, :, band]
                
                # Use inpainting to fill cloud pixels
                mask = (cloud_mask > 0).astype(np.uint8) * 255
                corrected[:, :, band] = cv2.inpaint(
                    (band_data * 255).astype(np.uint8),
                    mask,
                    3,
                    cv2.INPAINT_TELEA
                ).astype(np.float32) / 255.0
        
        elif method == 'median':
            # Replace cloud pixels with median of surrounding area
            for band in range(bands):
                band_data = corrected[:, :, band]
                
                # Apply median filter only to cloud areas
                median_filtered = cv2.medianBlur(
                    (band_data * 255).astype(np.uint8),
                    5
                ).astype(np.float32) / 255.0
                
                # Replace cloud pixels
                corrected[cloud_mask > 0, band] = median_filtered[cloud_mask > 0]
        
        elif method == 'temporal':
            # Would use temporal data (placeholder)
            print("Temporal cloud removal requires historical data, using interpolation")
            return self.remove_clouds(data, cloud_mask, method='interpolation')
        
        return corrected
    
    def get_cloud_coverage(self, cloud_mask: np.ndarray) -> float:
        """
        Calculate cloud coverage percentage
        
        Args:
            cloud_mask: Binary cloud mask
            
        Returns:
            Cloud coverage percentage (0-100)
        """
        total_pixels = cloud_mask.size
        cloud_pixels = np.sum(cloud_mask)
        coverage = (cloud_pixels / total_pixels) * 100
        return coverage


def main():
    """Test cloud detection"""
    print("Testing Cloud Detection...")
    
    # Create test data
    h, w, bands = 100, 100, 4
    data = np.random.rand(h, w, bands) * 0.5
    
    # Add some "clouds" (bright pixels)
    data[20:30, 20:30, :] = 0.8
    data[50:60, 50:60, :] = 0.9
    
    # Test threshold method
    detector = CloudDetector(method='threshold')
    cloud_mask = detector.detect_clouds(data)
    
    print(f"Cloud mask shape: {cloud_mask.shape}")
    print(f"Cloud coverage: {detector.get_cloud_coverage(cloud_mask):.2f}%")
    
    # Test cloud removal
    corrected = detector.remove_clouds(data, cloud_mask, method='interpolation')
    print(f"Corrected data shape: {corrected.shape}")
    
    print("Cloud detection test complete!")


if __name__ == "__main__":
    main()
