"""
Preprocessing Module
Handles data normalization, noise reduction, atmospheric correction, cloud detection, and PCA for spectral data.
"""

import numpy as np
from sklearn.decomposition import PCA
from sklearn.preprocessing import MinMaxScaler
from typing import Tuple, Optional
import cv2

# Import cloud detection module
try:
    from src.cloud_detection import CloudDetector
    CLOUD_DETECTION_AVAILABLE = True
except ImportError:
    CLOUD_DETECTION_AVAILABLE = False
    print("Warning: Cloud detection module not available")

class SpectralPreprocessor:
    """Preprocesses spectral data for anomaly detection."""
    
    def __init__(self, n_components: int = 10, apply_noise_reduction: bool = True,
                 detect_clouds: bool = True, cloud_method: str = 'threshold'):
        """
        Initialize the preprocessor.
        
        Args:
            n_components: Number of PCA components to keep
            apply_noise_reduction: Whether to apply Gaussian noise reduction
            detect_clouds: Whether to detect and mask clouds
            cloud_method: Cloud detection method ('threshold', 'ml', 'fmask')
        """
        self.n_components = n_components
        self.apply_noise_reduction = apply_noise_reduction
        self.detect_clouds = detect_clouds
        self.cloud_method = cloud_method
        self.scaler = MinMaxScaler()
        self.pca = PCA(n_components=n_components)
        self.original_shape = None
        
        # Initialize cloud detector
        if CLOUD_DETECTION_AVAILABLE and detect_clouds:
            self.cloud_detector = CloudDetector(method=cloud_method)
        else:
            self.cloud_detector = None
    
    def normalize(self, data: np.ndarray) -> np.ndarray:
        """
        Normalize spectral data to [0, 1] range.
        
        Args:
            data: Input spectral data of shape (H, W, Bands)
            
        Returns:
            Normalized data
        """
        # Reshape to 2D for scaling
        original_shape = data.shape
        data_2d = data.reshape(-1, data.shape[-1])
        
        # Normalize
        data_normalized = self.scaler.fit_transform(data_2d)
        
        # Reshape back
        data_normalized = data_normalized.reshape(original_shape)
        
        return data_normalized
    
    def reduce_noise(self, data: np.ndarray, kernel_size: int = 3) -> np.ndarray:
        """
        Apply Gaussian noise reduction to each spectral band.
        
        Args:
            data: Input spectral data of shape (H, W, Bands)
            kernel_size: Size of Gaussian kernel
            
        Returns:
            Denoised data
        """
        if not self.apply_noise_reduction:
            return data
        
        denoised = np.zeros_like(data)
        
        for band in range(data.shape[-1]):
            # Apply Gaussian filter to each band
            denoised[:, :, band] = cv2.GaussianBlur(
                data[:, :, band], 
                (kernel_size, kernel_size), 
                0
            )
        
        return denoised
    
    def reshape_to_pixels(self, data: np.ndarray) -> np.ndarray:
        """
        Reshape data from (H, W, Bands) to (Pixels, Bands).
        
        Args:
            data: Input spectral data of shape (H, W, Bands)
            
        Returns:
            Reshaped data of shape (H*W, Bands)
        """
        self.original_shape = data.shape
        pixels, bands = data.shape[0] * data.shape[1], data.shape[-1]
        return data.reshape(pixels, bands)
    
    def reshape_to_image(self, data: np.ndarray) -> np.ndarray:
        """
        Reshape data from (Pixels, Bands) back to (H, W, Bands).
        
        Args:
            data: Input data of shape (Pixels, Bands)
            
        Returns:
            Reshaped data of shape (H, W, Bands)
        """
        if self.original_shape is None:
            raise ValueError("Original shape not saved. Call reshape_to_pixels first.")
        
        return data.reshape(self.original_shape)
    
    def apply_pca(self, data: np.ndarray, fit: bool = True) -> np.ndarray:
        """
        Apply PCA dimensionality reduction.
        
        Args:
            data: Input data of shape (Pixels, Bands)
            fit: Whether to fit the PCA model (True for training, False for inference)
            
        Returns:
            PCA-transformed data of shape (Pixels, n_components)
        """
        if fit:
            data_pca = self.pca.fit_transform(data)
            print(f"PCA explained variance ratio: {self.pca.explained_variance_ratio_.sum():.4f}")
            print(f"PCA components: {self.n_components}")
        else:
            # Check if PCA has been fitted, if not, fit it first
            if not hasattr(self.pca, 'components_'):
                print("PCA not fitted, fitting now...")
                data_pca = self.pca.fit_transform(data)
                print(f"PCA explained variance ratio: {self.pca.explained_variance_ratio_.sum():.4f}")
            else:
                data_pca = self.pca.transform(data)
        
        return data_pca
    
    def apply_spatial_smoothing(self, data: np.ndarray, 
                                original_shape: Tuple[int, int, int],
                                kernel_size: int = 3) -> np.ndarray:
        """
        Apply spatial smoothing to feature maps.
        
        Args:
            data: Feature data of shape (Pixels, Features)
            original_shape: Original image shape (H, W, Bands)
            kernel_size: Size of smoothing kernel
            
        Returns:
            Smoothed feature data
        """
        h, w = original_shape[0], original_shape[1]
        n_features = data.shape[-1]
        
        # Reshape to image format
        data_image = data.reshape(h, w, n_features)
        
        # Apply smoothing to each feature
        smoothed = np.zeros_like(data_image)
        for feat in range(n_features):
            smoothed[:, :, feat] = cv2.GaussianBlur(
                data_image[:, :, feat],
                (kernel_size, kernel_size),
                0
            )
        
        # Reshape back to pixel format
        return smoothed.reshape(-1, n_features)
    
    def dark_object_subtraction(self, data: np.ndarray) -> np.ndarray:
        """
        Apply Dark Object Subtraction (DOS) atmospheric correction.
        Simple but effective method for atmospheric haze removal.
        
        Args:
            data: Input spectral data of shape (H, W, Bands)
            
        Returns:
            Atmospherically corrected data
        """
        corrected = np.zeros_like(data)
        
        for band in range(data.shape[-1]):
            # Find the minimum value in each band (dark object)
            dark_value = np.percentile(data[:, :, band], 1)  # Use 1st percentile to avoid outliers
            
            # Subtract dark value from the band
            corrected[:, :, band] = data[:, :, band] - dark_value
            
            # Clip to valid range
            corrected[:, :, band] = np.clip(corrected[:, :, band], 0, None)
        
        return corrected
    
    def empirical_line_correction(self, data: np.ndarray, 
                                  reference_spectra: np.ndarray) -> np.ndarray:
        """
        Apply Empirical Line Correction (ELC) using reference spectra.
        Requires ground truth or known reference spectra.
        
        Args:
            data: Input spectral data of shape (H, W, Bands)
            reference_spectra: Reference spectra of shape (N, Bands)
            
        Returns:
            Atmospherically corrected data
        """
        if reference_spectra is None or len(reference_spectra) == 0:
            print("No reference spectra provided, skipping ELC")
            return data
        
        corrected = np.zeros_like(data)
        
        for band in range(data.shape[-1]):
            # Calculate gain and offset from reference
            ref_mean = reference_spectra[:, band].mean()
            data_mean = data[:, :, band].mean()
            
            # Simple linear correction
            gain = ref_mean / (data_mean + 1e-8)
            offset = ref_mean - gain * data_mean
            
            corrected[:, :, band] = data[:, :, band] * gain + offset
        
        return corrected
    
    def apply_atmospheric_correction(self, data: np.ndarray, 
                                    method: str = 'dos',
                                    reference_spectra: Optional[np.ndarray] = None) -> np.ndarray:
        """
        Apply atmospheric correction to spectral data.
        
        Args:
            data: Input spectral data of shape (H, W, Bands)
            method: Correction method ('dos' for Dark Object Subtraction, 'elc' for Empirical Line)
            reference_spectra: Reference spectra for ELC method
            
        Returns:
            Atmospherically corrected data
        """
        print(f"Applying atmospheric correction using method: {method}")
        
        if method == 'dos':
            return self.dark_object_subtraction(data)
        elif method == 'elc':
            return self.empirical_line_correction(data, reference_spectra)
        else:
            print(f"Unknown atmospheric correction method: {method}, skipping")
            return data
    
    def preprocess(self, data: np.ndarray, fit_pca: bool = False, skip_pca: bool = False,
                   apply_atmospheric_correction: bool = True,
                   atmospheric_method: str = 'dos',
                   remove_clouds: bool = True) -> Tuple[np.ndarray, np.ndarray]:
        """
        Preprocess spectral data for anomaly detection.
        
        Args:
            data: Input spectral data of shape (H, W, Bands)
            fit_pca: Whether to fit the PCA model (True for training, False for inference)
            skip_pca: Whether to skip PCA entirely (for RGB-only data to save time)
            apply_atmospheric_correction: Whether to apply atmospheric correction
            atmospheric_method: Atmospheric correction method ('dos' or 'elc')
            remove_clouds: Whether to detect and remove clouds
            
        Returns:
            Tuple of (processed_features, rgb_composite)
        """
        print(f"Input data shape: {data.shape}")
        
        # Step 0: Cloud detection and removal (before other processing)
        if remove_clouds and self.cloud_detector is not None and data.shape[-1] >= 3:
            print("Step 0: Detecting and removing clouds...")
            cloud_mask = self.cloud_detector.detect_clouds(data)
            cloud_coverage = self.cloud_detector.get_cloud_coverage(cloud_mask)
            print(f"Cloud coverage: {cloud_coverage:.2f}%")
            
            if cloud_coverage > 0:
                data = self.cloud_detector.remove_clouds(data, cloud_mask, method='interpolation')
                print("Clouds removed using interpolation")
        
        # Step 1: Atmospheric correction (before normalization)
        if apply_atmospheric_correction and data.shape[-1] > 3:
            print("Step 1: Applying atmospheric correction...")
            data = self.apply_atmospheric_correction(data, method=atmospheric_method)
        
        # Step 2: Normalize
        print("Step 2: Normalizing data...")
        data_normalized = self.normalize(data)
        
        # Step 3: Noise reduction
        print("Step 3: Reducing noise...")
        data_denoised = self.reduce_noise(data_normalized)
        
        # Step 4: Extract RGB for visualization
        print("Step 4: Extracting RGB composite...")
        if data_denoised.shape[-1] >= 3:
            rgb = data_denoised[:, :, :3].copy()
        else:
            rgb = np.stack([data_denoised[:, :, 0]] * 3, axis=-1)
        
        # Step 5: Reshape to pixels
        print("Step 5: Reshaping to pixel vectors...")
        data_pixels = self.reshape_to_pixels(data_denoised)
        print(f"Pixel vectors shape: {data_pixels.shape}")
        
        # Step 6: Apply PCA (skip if requested for speed)
        if skip_pca:
            print("Step 6: Skipping PCA for speed...")
            data_pca = data_pixels
        else:
            print("Step 6: Applying PCA...")
            data_pca = self.apply_pca(data_pixels, fit=fit_pca)
            print(f"PCA-transformed shape: {data_pca.shape}")
        
        return data_pca, rgb
    
    def get_pca_components(self) -> np.ndarray:
        """
        Get PCA components for visualization.
        
        Returns:
            PCA components matrix
        """
        return self.pca.components_
    
    def get_explained_variance(self) -> np.ndarray:
        """
        Get explained variance ratio for each component.
        
        Returns:
            Array of explained variance ratios
        """
        return self.pca.explained_variance_ratio_


def main():
    """Test the preprocessor."""
    from src.data_loader import SatelliteDataLoader
    
    print("=== Testing Spectral Preprocessor ===\n")
    
    # Load test data
    loader = SatelliteDataLoader()
    data, source = loader.load_data(use_gee=False)
    print(f"Loaded data from: {source}")
    
    # Initialize preprocessor
    preprocessor = SpectralPreprocessor(n_components=10)
    
    # Preprocess
    features, rgb = preprocessor.preprocess(data, fit_pca=True)
    
    print(f"\nPreprocessing complete!")
    print(f"Features shape: {features.shape}")
    print(f"RGB shape: {rgb.shape}")
    print(f"Explained variance: {preprocessor.get_explained_variance().sum():.4f}")


if __name__ == "__main__":
    main()
