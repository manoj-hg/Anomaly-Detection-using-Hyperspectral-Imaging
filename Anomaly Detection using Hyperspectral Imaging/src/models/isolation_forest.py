"""
Isolation Forest Model
Beginner-friendly anomaly detection using PCA + Isolation Forest.
"""

import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import MinMaxScaler
from typing import Tuple, Optional
import joblib
import os


class IsolationForestAnomalyDetector:
    """Anomaly detection using Isolation Forest algorithm."""
    
    def __init__(self, contamination: float = 0.1, 
                 n_estimators: int = 100,
                 random_state: int = 42):
        """
        Initialize the Isolation Forest detector.
        
        Args:
            contamination: Expected proportion of outliers in the dataset
            n_estimators: Number of base estimators in the ensemble
            random_state: Random seed for reproducibility
        """
        self.contamination = contamination
        self.n_estimators = n_estimators
        self.random_state = random_state
        self.model = IsolationForest(
            contamination=contamination,
            n_estimators=n_estimators,
            random_state=random_state,
            n_jobs=-1
        )
        self.scaler = MinMaxScaler()
        self.is_fitted = False
        self.original_shape = None
    
    def fit(self, features: np.ndarray, original_shape: Optional[Tuple] = None):
        """
        Fit the Isolation Forest model on the features.
        
        Args:
            features: Feature array of shape (Pixels, Features)
            original_shape: Original image shape (H, W) for reshaping scores
        """
        print("Training Isolation Forest model...")
        self.original_shape = original_shape
        
        # Fit the model
        self.model.fit(features)
        self.is_fitted = True
        
        print("Isolation Forest training complete.")
    
    def predict(self, features: np.ndarray) -> np.ndarray:
        """
        Predict anomaly scores.
        
        Args:
            features: Feature array of shape (Pixels, Features)
            
        Returns:
            Anomaly scores (lower = more anomalous)
        """
        if not self.is_fitted:
            raise ValueError("Model must be fitted before prediction.")
        
        # Get anomaly scores (negative scores indicate anomalies)
        scores = self.model.score_samples(features)
        
        # Convert to positive scores (higher = more anomalous)
        scores = -scores
        
        # Normalize to [0, 1]
        scores = self.scaler.fit_transform(scores.reshape(-1, 1)).flatten()
        
        return scores
    
    def predict_reshaped(self, features: np.ndarray) -> np.ndarray:
        """
        Predict and reshape scores back to image format.
        
        Args:
            features: Feature array of shape (Pixels, Features)
            
        Returns:
            Anomaly score map of shape (H, W)
        """
        scores = self.predict(features)
        
        if self.original_shape is not None:
            h, w = self.original_shape
            score_map = scores.reshape(h, w)
        else:
            # Assume square if shape not provided
            n_pixels = len(scores)
            side = int(np.sqrt(n_pixels))
            score_map = scores.reshape(side, side)
        
        return score_map
    
    def get_binary_mask(self, scores: np.ndarray, 
                       threshold: Optional[float] = None) -> np.ndarray:
        """
        Convert anomaly scores to binary mask.
        
        Args:
            scores: Anomaly scores (can be 1D or 2D)
            threshold: Threshold for binary classification (auto if None)
            
        Returns:
            Binary mask (1 = anomaly, 0 = normal)
        """
        if threshold is None:
            # Use adaptive threshold: mean + std
            threshold = scores.mean() + scores.std()
        
        binary_mask = (scores > threshold).astype(int)
        return binary_mask
    
    def save_model(self, path: str = "data/isolation_forest_model.pkl"):
        """
        Save the trained model.
        
        Args:
            path: Path to save the model
        """
        if not self.is_fitted:
            raise ValueError("Model must be fitted before saving.")
        
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        model_data = {
            'model': self.model,
            'scaler': self.scaler,
            'contamination': self.contamination,
            'n_estimators': self.n_estimators,
            'random_state': self.random_state,
            'original_shape': self.original_shape
        }
        
        joblib.dump(model_data, path)
        print(f"Model saved to {path}")
    
    def load_model(self, path: str = "data/isolation_forest_model.pkl"):
        """
        Load a trained model.
        
        Args:
            path: Path to load the model from
        """
        if not os.path.exists(path):
            raise FileNotFoundError(f"Model file not found: {path}")
        
        model_data = joblib.load(path)
        
        self.model = model_data['model']
        self.scaler = model_data['scaler']
        self.contamination = model_data['contamination']
        self.n_estimators = model_data['n_estimators']
        self.random_state = model_data['random_state']
        self.original_shape = model_data['original_shape']
        self.is_fitted = True
        
        print(f"Model loaded from {path}")
    
    def detect_anomalies(self, features: np.ndarray, 
                        original_shape: Optional[Tuple] = None) -> Tuple[np.ndarray, np.ndarray, float]:
        """
        Complete anomaly detection pipeline.
        
        Args:
            features: Feature array of shape (Pixels, Features)
            original_shape: Original image shape (H, W)
            
        Returns:
            Tuple of (score_map, binary_mask, threshold)
        """
        if not self.is_fitted:
            self.fit(features, original_shape)
        
        # Get score map
        score_map = self.predict_reshaped(features)
        
        # Get binary mask with adaptive threshold
        threshold = score_map.mean() + score_map.std()
        binary_mask = self.get_binary_mask(score_map, threshold)
        
        return score_map, binary_mask, threshold


def main():
    """Test the Isolation Forest detector."""
    from src.data_loader import SatelliteDataLoader
    from src.preprocess import SpectralPreprocessor
    
    print("=== Testing Isolation Forest Anomaly Detector ===\n")
    
    # Load and preprocess data
    loader = SatelliteDataLoader()
    data, source = loader.load_data(use_gee=False)
    print(f"Loaded data from: {source}")
    
    preprocessor = SpectralPreprocessor(n_components=10)
    features, rgb = preprocessor.preprocess(data, fit_pca=True)
    
    # Initialize detector
    detector = IsolationForestAnomalyDetector(contamination=0.1)
    
    # Detect anomalies
    original_shape = data.shape[:2]
    score_map, binary_mask, threshold = detector.detect_anomalies(features, original_shape)
    
    print(f"\nAnomaly detection complete!")
    print(f"Score map shape: {score_map.shape}")
    print(f"Binary mask shape: {binary_mask.shape}")
    print(f"Threshold: {threshold:.4f}")
    print(f"Anomalies detected: {binary_mask.sum()} pixels ({binary_mask.sum()/binary_mask.size*100:.2f}%)")


if __name__ == "__main__":
    main()
