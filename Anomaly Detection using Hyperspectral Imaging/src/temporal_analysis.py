"""
Temporal Change Detection Module
Detects changes over time in satellite imagery
"""

import numpy as np
from typing import Tuple, List, Dict, Optional
from datetime import datetime, timedelta
import cv2
from sklearn.cluster import DBSCAN
from scipy import stats
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TemporalChangeDetector:
    """
    Detects changes in satellite imagery over time
    """
    
    def __init__(self, threshold: float = 0.3, method: str = 'diff'):
        self.threshold = threshold
        self.method = method
        self.history = []
        
    def add_observation(
        self,
        data: np.ndarray,
        timestamp: datetime,
        metadata: Optional[Dict] = None
    ):
        """
        Add a new observation to the temporal history
        
        Args:
            data: (H, W, C) - Spectral data
            timestamp: Observation timestamp
            metadata: Optional metadata (satellite, cloud cover, etc.)
        """
        self.history.append({
            'data': data,
            'timestamp': timestamp,
            'metadata': metadata or {}
        })
        
        # Sort by timestamp
        self.history.sort(key=lambda x: x['timestamp'])
    
    def detect_changes(
        self,
        time_window: Optional[timedelta] = None,
        method: str = 'diff'
    ) -> Dict[str, np.ndarray]:
        """
        Detect changes between observations
        
        Args:
            time_window: Only compare observations within this window
            method: 'diff', 'ratio', or 'statistical'
            
        Returns:
            dict with change maps and statistics
        """
        if len(self.history) < 2:
            return {'error': 'Need at least 2 observations'}
        
        # Filter by time window
        if time_window:
            recent = [obs for obs in self.history 
                     if (self.history[-1]['timestamp'] - obs['timestamp']) <= time_window]
        else:
            recent = self.history
        
        if len(recent) < 2:
            return {'error': 'Not enough observations in time window'}
        
        # Compare consecutive observations
        changes = []
        for i in range(len(recent) - 1):
            change = self._compare_observations(
                recent[i]['data'],
                recent[i + 1]['data'],
                method
            )
            changes.append(change)
        
        # Aggregate changes
        aggregated = self._aggregate_changes(changes)
        
        return {
            'change_map': aggregated,
            'num_observations': len(recent),
            'time_span': (recent[-1]['timestamp'] - recent[0]['timestamp']).days
        }
    
    def _compare_observations(
        self,
        data1: np.ndarray,
        data2: np.ndarray,
        method: str
    ) -> np.ndarray:
        """Compare two observations"""
        if method == 'diff':
            # Simple difference
            change = np.abs(data1 - data2)
            change = change.mean(axis=-1)  # Average across bands
            
        elif method == 'ratio':
            # Ratio-based change
            ratio = data2 / (data1 + 1e-8)
            change = np.abs(ratio - 1).mean(axis=-1)
            
        elif method == 'statistical':
            # Statistical test (t-test per pixel)
            change = np.zeros(data1.shape[:2])
            for i in range(data1.shape[0]):
                for j in range(data1.shape[1]):
                    _, p_value = stats.ttest_ind(
                        data1[i, j, :],
                        data2[i, j, :]
                    )
                    change[i, j] = -np.log10(p_value + 1e-10)
            
        else:
            raise ValueError(f"Unknown method: {method}")
        
        # Normalize
        change = (change - change.min()) / (change.max() - change.min() + 1e-8)
        
        return change
    
    def _aggregate_changes(self, changes: List[np.ndarray]) -> np.ndarray:
        """Aggregate multiple change maps"""
        if not changes:
            return np.zeros((100, 100))
        
        # Stack and take maximum
        stacked = np.stack(changes, axis=0)
        aggregated = stacked.max(axis=0)
        
        return aggregated
    
    def detect_trends(self, window_size: int = 3) -> Dict[str, np.ndarray]:
        """
        Detect temporal trends (gradual changes)
        
        Args:
            window_size: Size of sliding window for trend detection
            
        Returns:
            dict with trend maps
        """
        if len(self.history) < window_size:
            return {'error': f'Need at least {window_size} observations'}
        
        # Extract time series per pixel
        H, W, C = self.history[0]['data'].shape
        time_series = np.zeros((len(self.history), H, W, C))
        
        for i, obs in enumerate(self.history):
            time_series[i] = obs['data']
        
        # Compute linear trend per pixel
        trend_map = np.zeros((H, W))
        for i in range(H):
            for j in range(W):
                for c in range(C):
                    pixels = time_series[:, i, j, c]
                    if len(pixels) > 1:
                        slope, _, _, _, _ = stats.linregress(
                            range(len(pixels)),
                            pixels
                        )
                        trend_map[i, j] += abs(slope)
        
        trend_map /= C  # Average across bands
        
        return {
            'trend_map': trend_map,
            'trend_magnitude': trend_map.mean()
        }
    
    def detect_seasonal_patterns(self) -> Dict[str, np.ndarray]:
        """
        Detect seasonal patterns in the data
        """
        if len(self.history) < 12:  # Need at least a year
            return {'error': 'Need at least 12 observations for seasonal analysis'}
        
        # Extract day of year for each observation
        doy_values = [obs['timestamp'].timetuple().tm_yday for obs in self.history]
        
        # Group by day of year
        seasonal_data = {}
        for obs, doy in zip(self.history, doy_values):
            if doy not in seasonal_data:
                seasonal_data[doy] = []
            seasonal_data[doy].append(obs['data'])
        
        # Compute average per day of year
        seasonal_mean = {}
        for doy, data_list in seasonal_data.items():
            seasonal_mean[doy] = np.mean(data_list, axis=0)
        
        return {
            'seasonal_patterns': seasonal_mean,
            'num_years': len(self.history) // 365
        }


class AnomalyEventDetector:
    """
    Detects anomalous events in time series
    """
    
    def __init__(self, window_size: int = 7, threshold: float = 3.0):
        self.window_size = window_size
        self.threshold = threshold  # Standard deviations
        
    def detect_events(
        self,
        time_series: np.ndarray,
        timestamps: List[datetime]
    ) -> List[Dict]:
        """
        Detect anomalous events in time series
        
        Args:
            time_series: (T,) - Time series values
            timestamps: List of timestamps
            
        Returns:
            List of detected events
        """
        events = []
        
        # Compute rolling statistics
        rolling_mean = np.convolve(
            time_series,
            np.ones(self.window_size) / self.window_size,
            mode='valid'
        )
        rolling_std = np.convolve(
            time_series,
            np.ones(self.window_size) / self.window_size,
            mode='valid'
        )
        
        # Detect anomalies
        for i in range(len(rolling_mean)):
            if i + self.window_size < len(time_series):
                value = time_series[i + self.window_size]
                z_score = abs(value - rolling_mean[i]) / (rolling_std[i] + 1e-8)
                
                if z_score > self.threshold:
                    events.append({
                        'timestamp': timestamps[i + self.window_size],
                        'value': value,
                        'z_score': z_score,
                        'type': 'spike' if value > rolling_mean[i] else 'drop'
                    })
        
        return events
    
    def detect_breakpoints(self, time_series: np.ndarray) -> List[int]:
        """
        Detect structural breakpoints in time series
        """
        breakpoints = []
        
        # Simple change point detection using cumulative sum
        mean = np.mean(time_series)
        cumulative_sum = np.cumsum(time_series - mean)
        
        # Find maximum deviation
        max_dev = np.argmax(np.abs(cumulative_sum))
        if max_dev > 0:
            breakpoints.append(max_dev)
        
        return breakpoints


class TimeSeriesForecaster:
    """
    Forecast future values using simple methods
    """
    
    def __init__(self, method: str = 'linear'):
        self.method = method
        
    def forecast(
        self,
        time_series: np.ndarray,
        steps: int = 5
    ) -> np.ndarray:
        """
        Forecast future values
        
        Args:
            time_series: (T,) - Historical values
            steps: Number of steps to forecast
            
        Returns:
            Forecasted values
        """
        if self.method == 'linear':
            # Linear regression
            x = np.arange(len(time_series))
            slope, intercept, _, _, _ = stats.linregress(x, time_series)
            forecast = slope * (len(time_series) + np.arange(steps)) + intercept
            
        elif self.method == 'mean':
            # Mean forecast
            forecast = np.full(steps, np.mean(time_series))
            
        elif self.method == 'last':
            # Last value forecast
            forecast = np.full(steps, time_series[-1])
            
        else:
            raise ValueError(f"Unknown method: {self.method}")
        
        return forecast


if __name__ == "__main__":
    print("Testing Temporal Change Detection...")
    
    # Create dummy time series
    detector = TemporalChangeDetector()
    
    # Add observations
    for i in range(10):
        data = np.random.randn(50, 50, 10)
        timestamp = datetime(2024, 1, 1) + timedelta(days=i * 10)
        detector.add_observation(data, timestamp)
    
    # Detect changes
    changes = detector.detect_changes()
    print(f"Change map shape: {changes.get('change_map', np.array()).shape}")
    
    # Detect trends
    trends = detector.detect_trends()
    print(f"Trend map shape: {trends.get('trend_map', np.array()).shape}")
    
    # Test event detection
    event_detector = AnomalyEventDetector()
    time_series = np.random.randn(100)
    time_series[50] = 10.0  # Anomaly
    timestamps = [datetime(2024, 1, 1) + timedelta(days=i) for i in range(100)]
    events = event_detector.detect_events(time_series, timestamps)
    print(f"Detected {len(events)} events")
    
    print("Temporal analysis test complete!")
