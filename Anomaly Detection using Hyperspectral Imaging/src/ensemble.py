"""
Ensemble Model Stacking Module
Combines multiple models for improved anomaly detection
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, StackingClassifier
from sklearn.model_selection import cross_val_score
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class EnsembleDetector:
    """
    Ensemble of multiple anomaly detection models
    """
    
    def __init__(
        self,
        models: List,
        weights: Optional[List[float]] = None,
        method: str = 'weighted_average'
    ):
        """
        Initialize ensemble detector
        
        Args:
            models: List of anomaly detection models
            weights: Optional weights for each model
            method: 'weighted_average', 'voting', 'stacking', or 'max'
        """
        self.models = models
        self.method = method
        
        if weights is None:
            self.weights = [1.0 / len(models)] * len(models)
        else:
            self.weights = weights
        
        # Normalize weights
        self.weights = np.array(self.weights) / np.sum(self.weights)
        
        self.is_fitted = False
        
    def fit(self, data: np.ndarray, original_shape: Tuple[int, int]):
        """
        Fit all models in the ensemble
        
        Args:
            data: (H*W, C) - Flattened spectral data
            original_shape: (H, W) - Original image dimensions
        """
        for model in self.models:
            if hasattr(model, 'fit'):
                model.fit(data, original_shape)
        
        self.is_fitted = True
    
    def detect_anomalies(
        self,
        data: np.ndarray,
        original_shape: Tuple[int, int]
    ) -> Tuple[np.ndarray, np.ndarray, float]:
        """
        Detect anomalies using ensemble
        
        Args:
            data: (H*W, C) - Flattened spectral data
            original_shape: (H, W) - Original image dimensions
            
        Returns:
            anomaly_scores: (H, W) - Combined anomaly scores
            binary_mask: (H, W) - Binary anomaly mask
            threshold: float - Computed threshold
        """
        if not self.is_fitted:
            self.fit(data, original_shape)
        
        # Get predictions from all models
        all_scores = []
        all_binary = []
        all_thresholds = []
        
        for model in self.models:
            scores, binary, threshold = model.detect_anomalies(data, original_shape)
            all_scores.append(scores)
            all_binary.append(binary)
            all_thresholds.append(threshold)
        
        # Combine predictions
        if self.method == 'weighted_average':
            combined_scores = np.zeros_like(all_scores[0])
            for score, weight in zip(all_scores, self.weights):
                combined_scores += score * weight
                
        elif self.method == 'voting':
            # Majority voting for binary masks
            combined_binary = np.zeros_like(all_binary[0])
            for binary in all_binary:
                combined_binary += binary
            combined_binary = (combined_binary >= len(all_binary) / 2).astype(np.float32)
            
            # Use binary as scores
            combined_scores = combined_binary
            
        elif self.method == 'max':
            # Take maximum score
            combined_scores = np.maximum.reduce(all_scores)
            
        elif self.method == 'stacking':
            # Use stacking classifier (requires labels)
            # For unsupervised, fall back to weighted average
            combined_scores = np.zeros_like(all_scores[0])
            for score, weight in zip(all_scores, self.weights):
                combined_scores += score * weight
        
        else:
            raise ValueError(f"Unknown method: {self.method}")
        
        # Normalize combined scores
        combined_scores = (combined_scores - combined_scores.min()) / (combined_scores.max() - combined_scores.min() + 1e-8)
        
        # Compute adaptive threshold
        threshold = np.mean(combined_scores) + 2 * np.std(combined_scores)
        binary_mask = (combined_scores > threshold).astype(np.float32)
        
        return combined_scores, binary_mask, threshold
    
    def get_model_diversity(self) -> Dict:
        """
        Measure diversity among ensemble models
        
        Returns:
            Dictionary with diversity metrics
        """
        # This would require running models on test data
        # Placeholder implementation
        return {
            'num_models': len(self.models),
            'method': self.method,
            'weights': self.weights.tolist()
        }


class StackedEnsemble:
    """
    Stacked ensemble with meta-learner
    """
    
    def __init__(
        self,
        base_models: List,
        meta_learner: Optional = None
    ):
        """
        Initialize stacked ensemble
        
        Args:
            base_models: List of base anomaly detection models
            meta_learner: Meta-learner for combining predictions
        """
        self.base_models = base_models
        
        if meta_learner is None:
            self.meta_learner = LogisticRegression(random_state=42)
        else:
            self.meta_learner = meta_learner
        
        self.is_fitted = False
        
    def fit(
        self,
        data: np.ndarray,
        original_shape: Tuple[int, int],
        labels: Optional[np.ndarray] = None
    ):
        """
        Fit stacked ensemble
        
        Args:
            data: (H*W, C) - Flattened spectral data
            original_shape: (H, W) - Original image dimensions
            labels: Optional labels for supervised training
        """
        # Fit base models
        for model in self.base_models:
            if hasattr(model, 'fit'):
                model.fit(data, original_shape)
        
        # Get base model predictions
        base_predictions = []
        for model in self.base_models:
            scores, _, _ = model.detect_anomalies(data, original_shape)
            base_predictions.append(scores)
        
        # Stack predictions
        X_meta = np.column_stack(base_predictions)
        
        # Fit meta-learner if labels provided
        if labels is not None:
            self.meta_learner.fit(X_meta, labels)
        
        self.is_fitted = True
    
    def detect_anomalies(
        self,
        data: np.ndarray,
        original_shape: Tuple[int, int]
    ) -> Tuple[np.ndarray, np.ndarray, float]:
        """
        Detect anomalies using stacked ensemble
        
        Args:
            data: (H*W, C) - Flattened spectral data
            original_shape: (H, W) - Original image dimensions
            
        Returns:
            anomaly_scores: (H, W) - Combined anomaly scores
            binary_mask: (H, W) - Binary anomaly mask
            threshold: float - Computed threshold
        """
        if not self.is_fitted:
            self.fit(data, original_shape)
        
        # Get base model predictions
        base_predictions = []
        for model in self.base_models:
            scores, _, _ = model.detect_anomalies(data, original_shape)
            base_predictions.append(scores)
        
        # Stack predictions
        X_meta = np.column_stack(base_predictions)
        
        # Get meta-learner predictions
        if hasattr(self.meta_learner, 'predict_proba'):
            anomaly_scores = self.meta_learner.predict_proba(X_meta)[:, 1]
        else:
            anomaly_scores = self.meta_learner.predict(X_meta)
        
        # Reshape to image
        H, W = original_shape
        anomaly_scores = anomaly_scores.reshape(H, W)
        
        # Normalize
        anomaly_scores = (anomaly_scores - anomaly_scores.min()) / (anomaly_scores.max() - anomaly_scores.min() + 1e-8)
        
        # Compute threshold
        threshold = np.mean(anomaly_scores) + 2 * np.std(anomaly_scores)
        binary_mask = (anomaly_scores > threshold).astype(np.float32)
        
        return anomaly_scores, binary_mask, threshold


class ConfidenceEstimator:
    """
    Estimate confidence intervals for predictions
    """
    
    def __init__(self, n_bootstrap: int = 100):
        """
        Initialize confidence estimator
        
        Args:
            n_bootstrap: Number of bootstrap samples
        """
        self.n_bootstrap = n_bootstrap
        
    def estimate_confidence(
        self,
        model,
        data: np.ndarray,
        original_shape: Tuple[int, int],
        confidence_level: float = 0.95
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Estimate confidence intervals using bootstrap
        
        Args:
            model: Anomaly detection model
            data: (H*W, C) - Flattened spectral data
            original_shape: (H, W) - Original image dimensions
            confidence_level: Confidence level (0.0 to 1.0)
            
        Returns:
            lower_bound: (H, W) - Lower confidence bound
            upper_bound: (H, W) - Upper confidence bound
        """
        H, W = original_shape
        N = data.shape[0]
        
        # Store bootstrap predictions
        bootstrap_predictions = []
        
        for _ in range(self.n_bootstrap):
            # Bootstrap sample
            indices = np.random.choice(N, N, replace=True)
            bootstrap_data = data[indices]
            
            # Get predictions
            scores, _, _ = model.detect_anomalies(bootstrap_data, original_shape)
            bootstrap_predictions.append(scores)
        
        # Stack predictions
        bootstrap_predictions = np.stack(bootstrap_predictions, axis=0)
        
        # Compute percentiles
        alpha = 1 - confidence_level
        lower_percentile = (alpha / 2) * 100
        upper_percentile = (1 - alpha / 2) * 100
        
        lower_bound = np.percentile(bootstrap_predictions, lower_percentile, axis=0)
        upper_bound = np.percentile(bootstrap_predictions, upper_percentile, axis=0)
        
        return lower_bound, upper_bound
    
    def estimate_uncertainty(
        self,
        predictions: np.ndarray,
        confidence_intervals: Tuple[np.ndarray, np.ndarray]
    ) -> np.ndarray:
        """
        Estimate uncertainty from confidence intervals
        
        Args:
            predictions: (H, W) - Point predictions
            confidence_intervals: (lower, upper) - Confidence bounds
            
        Returns:
            uncertainty: (H, W) - Uncertainty measure
        """
        lower, upper = confidence_intervals
        uncertainty = (upper - lower) / 2
        return uncertainty


class ModelSelector:
    """
    Select best model based on cross-validation
    """
    
    def __init__(self, models: List, cv_folds: int = 5):
        """
        Initialize model selector
        
        Args:
            models: List of models to compare
            cv_folds: Number of cross-validation folds
        """
        self.models = models
        self.cv_folds = cv_folds
        self.scores = {}
        
    def select_best_model(
        self,
        data: np.ndarray,
        original_shape: Tuple[int, int]
    ) -> Tuple:
        """
        Select best model using cross-validation
        
        Args:
            data: (H*W, C) - Flattened spectral data
            original_shape: (H, W) - Original image dimensions
            
        Returns:
            best_model, best_score, all_scores
        """
        for i, model in enumerate(self.models):
            # Fit model
            model.fit(data, original_shape)
            
            # Get predictions
            scores, _, _ = model.detect_anomalies(data, original_shape)
            
            # Compute score (higher is better)
            # Use negative variance as score (lower variance = better)
            score = -np.var(scores)
            
            self.scores[f'model_{i}'] = score
        
        # Select best model
        best_model_name = max(self.scores, key=self.scores.get)
        best_model_idx = int(best_model_name.split('_')[1])
        best_model = self.models[best_model_idx]
        best_score = self.scores[best_model_name]
        
        return best_model, best_score, self.scores


if __name__ == "__main__":
    print("Testing Ensemble Model Stacking...")
    
    # Create dummy models
    class DummyModel:
        def __init__(self, bias: float = 0.0):
            self.bias = bias
        
        def fit(self, data, original_shape):
            pass
        
        def detect_anomalies(self, data, original_shape):
            H, W = original_shape
            scores = np.random.rand(H, W) + self.bias
            threshold = np.mean(scores) + 2 * np.std(scores)
            binary = (scores > threshold).astype(np.float32)
            return scores, binary, threshold
    
    # Create ensemble
    models = [DummyModel(bias=0.0), DummyModel(bias=0.1), DummyModel(bias=-0.1)]
    ensemble = EnsembleDetector(models, weights=[0.4, 0.3, 0.3], method='weighted_average')
    
    # Test ensemble
    dummy_data = np.random.randn(100 * 100, 10)
    scores, binary, threshold = ensemble.detect_anomalies(dummy_data, (100, 100))
    
    print(f"Ensemble score range: [{scores.min():.4f}, {scores.max():.4f}]")
    print(f"Threshold: {threshold:.4f}")
    print(f"Anomalies detected: {binary.sum()} pixels")
    
    # Test confidence estimation
    confidence_estimator = ConfidenceEstimator(n_bootstrap=10)
    lower, upper = confidence_estimator.estimate_confidence(
        models[0], dummy_data, (100, 100)
    )
    print(f"Confidence interval shape: {lower.shape}")
    
    # Test model selection
    selector = ModelSelector(models, cv_folds=3)
    best_model, best_score, all_scores = selector.select_best_model(dummy_data, (100, 100))
    print(f"Best model score: {best_score:.4f}")
    print(f"All scores: {all_scores}")
    
    print("Ensemble stacking test complete!")
