"""
Autoencoder Model
Advanced anomaly detection using PyTorch Autoencoder with reconstruction error.
"""

import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
from torch.utils.data import DataLoader, TensorDataset
from typing import Tuple, Optional
import os


class Autoencoder(nn.Module):
    """Autoencoder neural network for anomaly detection."""
    
    def __init__(self, input_dim: int, encoding_dim: int = 8):
        """
        Initialize the Autoencoder.
        
        Args:
            input_dim: Number of input features
            encoding_dim: Dimension of the compressed representation
        """
        super(Autoencoder, self).__init__()
        
        # Encoder
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, 64),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(32, encoding_dim),
            nn.ReLU()
        )
        
        # Decoder
        self.decoder = nn.Sequential(
            nn.Linear(encoding_dim, 32),
            nn.ReLU(),
            nn.Linear(32, 64),
            nn.ReLU(),
            nn.Linear(64, input_dim),
            nn.Sigmoid()  # Output in [0, 1] range
        )
    
    def forward(self, x):
        """Forward pass through the autoencoder."""
        encoded = self.encoder(x)
        decoded = self.decoder(encoded)
        return decoded
    
    def encode(self, x):
        """Encode input to latent space."""
        return self.encoder(x)


class AutoencoderAnomalyDetector:
    """Anomaly detection using Autoencoder reconstruction error."""
    
    def __init__(self, input_dim: int, encoding_dim: int = 8,
                 learning_rate: float = 0.001,
                 batch_size: int = 32,
                 epochs: int = 100,
                 device: Optional[str] = None):
        """
        Initialize the Autoencoder detector.
        
        Args:
            input_dim: Number of input features
            encoding_dim: Dimension of the compressed representation
            learning_rate: Learning rate for optimizer
            batch_size: Batch size for training
            epochs: Number of training epochs
            device: Device to use ('cuda', 'cpu', or None for auto)
        """
        self.input_dim = input_dim
        self.encoding_dim = encoding_dim
        self.learning_rate = learning_rate
        self.batch_size = batch_size
        self.epochs = epochs
        
        # Set device
        if device is None:
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        else:
            self.device = torch.device(device)
        
        print(f"Using device: {self.device}")
        
        # Initialize model
        self.model = Autoencoder(input_dim, encoding_dim).to(self.device)
        self.criterion = nn.MSELoss()
        self.optimizer = optim.Adam(self.model.parameters(), lr=learning_rate)
        
        self.is_trained = False
        self.original_shape = None
        self.reconstruction_errors = None
    
    def train(self, features: np.ndarray, 
              original_shape: Optional[Tuple] = None,
              verbose: bool = True) -> dict:
        """
        Train the autoencoder.
        
        Args:
            features: Feature array of shape (Pixels, Features)
            original_shape: Original image shape (H, W) for reshaping
            verbose: Whether to print training progress
            
        Returns:
            Training history dictionary
        """
        self.original_shape = original_shape
        
        # Convert to torch tensors
        features_tensor = torch.FloatTensor(features).to(self.device)
        
        # Create dataset and dataloader
        dataset = TensorDataset(features_tensor)
        dataloader = DataLoader(dataset, batch_size=self.batch_size, shuffle=True)
        
        # Training history
        history = {'loss': []}
        
        # Training loop
        self.model.train()
        for epoch in range(self.epochs):
            epoch_loss = 0.0
            for batch in dataloader:
                x_batch = batch[0]
                
                # Forward pass
                self.optimizer.zero_grad()
                reconstructed = self.model(x_batch)
                loss = self.criterion(reconstructed, x_batch)
                
                # Backward pass
                loss.backward()
                self.optimizer.step()
                
                epoch_loss += loss.item()
            
            avg_loss = epoch_loss / len(dataloader)
            history['loss'].append(avg_loss)
            
            if verbose and (epoch + 1) % 10 == 0:
                print(f"Epoch [{epoch+1}/{self.epochs}], Loss: {avg_loss:.6f}")
        
        self.is_trained = True
        print("Autoencoder training complete.")
        
        return history
    
    def compute_reconstruction_error(self, features: np.ndarray) -> np.ndarray:
        """
        Compute reconstruction error for each sample.
        
        Args:
            features: Feature array of shape (Pixels, Features)
            
        Returns:
            Reconstruction error array of shape (Pixels,)
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before computing errors.")
        
        self.model.eval()
        
        with torch.no_grad():
            features_tensor = torch.FloatTensor(features).to(self.device)
            reconstructed = self.model(features_tensor)
            
            # Compute MSE for each sample
            errors = torch.mean((features_tensor - reconstructed) ** 2, dim=1)
            errors = errors.cpu().numpy()
        
        self.reconstruction_errors = errors
        return errors
    
    def predict(self, features: np.ndarray) -> np.ndarray:
        """
        Predict anomaly scores based on reconstruction error.
        
        Args:
            features: Feature array of shape (Pixels, Features)
            
        Returns:
            Normalized anomaly scores
        """
        errors = self.compute_reconstruction_error(features)
        
        # Normalize to [0, 1]
        errors_normalized = (errors - errors.min()) / (errors.max() - errors.min() + 1e-8)
        
        return errors_normalized
    
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
    
    def save_model(self, path: str = "data/autoencoder_model.pth"):
        """
        Save the trained model.
        
        Args:
            path: Path to save the model
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before saving.")
        
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        model_data = {
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'input_dim': self.input_dim,
            'encoding_dim': self.encoding_dim,
            'learning_rate': self.learning_rate,
            'batch_size': self.batch_size,
            'epochs': self.epochs,
            'original_shape': self.original_shape
        }
        
        torch.save(model_data, path)
        print(f"Model saved to {path}")
    
    def load_model(self, path: str = "data/autoencoder_model.pth"):
        """
        Load a trained model.
        
        Args:
            path: Path to load the model from
        """
        if not os.path.exists(path):
            raise FileNotFoundError(f"Model file not found: {path}")
        
        model_data = torch.load(path, map_location=self.device)
        
        self.model.load_state_dict(model_data['model_state_dict'])
        self.optimizer.load_state_dict(model_data['optimizer_state_dict'])
        self.input_dim = model_data['input_dim']
        self.encoding_dim = model_data['encoding_dim']
        self.learning_rate = model_data['learning_rate']
        self.batch_size = model_data['batch_size']
        self.epochs = model_data['epochs']
        self.original_shape = model_data['original_shape']
        self.is_trained = True
        
        print(f"Model loaded from {path}")
    
    def detect_anomalies(self, features: np.ndarray,
                        original_shape: Optional[Tuple] = None,
                        train: bool = True) -> Tuple[np.ndarray, np.ndarray, float]:
        """
        Complete anomaly detection pipeline.
        
        Args:
            features: Feature array of shape (Pixels, Features)
            original_shape: Original image shape (H, W)
            train: Whether to train the model first
            
        Returns:
            Tuple of (score_map, binary_mask, threshold)
        """
        if train and not self.is_trained:
            self.train(features, original_shape)
        
        # Get score map
        score_map = self.predict_reshaped(features)
        
        # Get binary mask with adaptive threshold
        threshold = score_map.mean() + score_map.std()
        binary_mask = self.get_binary_mask(score_map, threshold)
        
        return score_map, binary_mask, threshold


def main():
    """Test the Autoencoder detector."""
    from src.data_loader import SatelliteDataLoader
    from src.preprocess import SpectralPreprocessor
    
    print("=== Testing Autoencoder Anomaly Detector ===\n")
    
    # Load and preprocess data
    loader = SatelliteDataLoader()
    data, source = loader.load_data(use_gee=False)
    print(f"Loaded data from: {source}")
    
    preprocessor = SpectralPreprocessor(n_components=10)
    features, rgb = preprocessor.preprocess(data, fit_pca=True)
    
    # Initialize detector
    input_dim = features.shape[1]
    detector = AutoencoderAnomalyDetector(
        input_dim=input_dim,
        encoding_dim=8,
        epochs=50,
        batch_size=32
    )
    
    # Detect anomalies
    original_shape = data.shape[:2]
    score_map, binary_mask, threshold = detector.detect_anomalies(
        features, original_shape, train=True
    )
    
    print(f"\nAnomaly detection complete!")
    print(f"Score map shape: {score_map.shape}")
    print(f"Binary mask shape: {binary_mask.shape}")
    print(f"Threshold: {threshold:.4f}")
    print(f"Anomalies detected: {binary_mask.sum()} pixels ({binary_mask.sum()/binary_mask.size*100:.2f}%)")


if __name__ == "__main__":
    main()
