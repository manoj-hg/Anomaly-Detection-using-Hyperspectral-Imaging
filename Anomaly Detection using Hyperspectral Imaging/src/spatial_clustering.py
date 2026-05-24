"""
Spatial Clustering Module
Implements DBSCAN, HDBSCAN, and other clustering algorithms for anomaly grouping
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from sklearn.cluster import DBSCAN, AgglomerativeClustering
from sklearn.preprocessing import StandardScaler
import cv2
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import hdbscan
    HDBSCAN_AVAILABLE = True
except ImportError:
    HDBSCAN_AVAILABLE = False
    print("Warning: hdbscan not installed. Install with: pip install hdbscan")


class SpatialClusterer:
    """
    Clusters anomalies in spatial domain
    """
    
    def __init__(self, method: str = 'dbscan'):
        self.method = method
        self.scaler = StandardScaler()
        
    def cluster_anomalies(
        self,
        anomaly_map: np.ndarray,
        original_shape: Tuple[int, int],
        eps: float = 5.0,
        min_samples: int = 5
    ) -> Dict:
        """
        Cluster anomalies spatially
        
        Args:
            anomaly_map: (H, W) - Binary anomaly mask
            original_shape: (H, W) - Original image dimensions
            eps: DBSCAN epsilon parameter
            min_samples: Minimum samples for cluster formation
            
        Returns:
            Dictionary with clustering results
        """
        # Get anomaly coordinates
        anomaly_coords = np.argwhere(anomaly_map > 0.5)
        
        if len(anomaly_coords) == 0:
            return {
                'num_clusters': 0,
                'cluster_labels': np.array([]),
                'cluster_sizes': [],
                'anomaly_coords': anomaly_coords
            }
        
        # Scale coordinates
        coords_scaled = self.scaler.fit_transform(anomaly_coords)
        
        # Apply clustering
        if self.method == 'dbscan':
            clustering = DBSCAN(eps=eps, min_samples=min_samples)
            labels = clustering.fit_predict(coords_scaled)
        elif self.method == 'hdbscan' and HDBSCAN_AVAILABLE:
            clustering = hdbscan.HDBSCAN(min_cluster_size=min_samples)
            labels = clustering.fit_predict(coords_scaled)
        elif self.method == 'agglomerative':
            clustering = AgglomerativeClustering(n_clusters=None, distance_threshold=eps)
            labels = clustering.fit_predict(coords_scaled)
        else:
            # Fallback to DBSCAN
            clustering = DBSCAN(eps=eps, min_samples=min_samples)
            labels = clustering.fit_predict(coords_scaled)
        
        # Count clusters (excluding noise labeled as -1)
        unique_labels = set(labels)
        n_clusters = len(unique_labels) - (1 if -1 in unique_labels else 0)
        
        # Cluster sizes
        cluster_sizes = []
        for label in unique_labels:
            if label != -1:
                cluster_sizes.append((labels == label).sum())
        
        return {
            'num_clusters': n_clusters,
            'cluster_labels': labels,
            'cluster_sizes': cluster_sizes,
            'anomaly_coords': anomaly_coords,
            'method': self.method
        }
    
    def visualize_clusters(
        self,
        anomaly_map: np.ndarray,
        cluster_labels: np.ndarray,
        anomaly_coords: np.ndarray
    ) -> np.ndarray:
        """
        Create visualization of clustered anomalies
        
        Args:
            anomaly_map: (H, W) - Binary anomaly mask
            cluster_labels: Cluster labels for each anomaly pixel
            anomaly_coords: Coordinates of anomaly pixels
            
        Returns:
            (H, W, 3) RGB visualization
        """
        H, W = anomaly_map.shape
        visualization = np.zeros((H, W, 3), dtype=np.uint8)
        
        # Generate colors for clusters
        unique_labels = np.unique(cluster_labels)
        colors = {}
        for i, label in enumerate(unique_labels):
            if label == -1:
                colors[label] = [128, 128, 128]  # Gray for noise
            else:
                # Generate distinct colors
                hue = (i * 137.508) % 360  # Golden angle approximation
                color = cv2.cvtColor(np.array([[[hue, 255, 255]]], dtype=np.uint8), cv2.COLOR_HSV2BGR)[0][0]
                colors[label] = color
        
        # Fill visualization
        for coord, label in zip(anomaly_coords, cluster_labels):
            y, x = coord
            visualization[y, x] = colors.get(label, [255, 255, 255])
        
        return visualization
    
    def get_cluster_statistics(
        self,
        cluster_labels: np.ndarray,
        anomaly_coords: np.ndarray
    ) -> List[Dict]:
        """
        Get statistics for each cluster
        
        Args:
            cluster_labels: Cluster labels
            anomaly_coords: Anomaly coordinates
            
        Returns:
            List of cluster statistics
        """
        unique_labels = np.unique(cluster_labels)
        stats = []
        
        for label in unique_labels:
            if label == -1:
                continue  # Skip noise
            
            mask = cluster_labels == label
            cluster_coords = anomaly_coords[mask]
            
            # Compute centroid
            centroid = cluster_coords.mean(axis=0)
            
            # Compute bounding box
            min_y, min_x = cluster_coords.min(axis=0)
            max_y, max_x = cluster_coords.max(axis=0)
            
            # Compute area
            area = len(cluster_coords)
            
            # Compute density
            bbox_area = (max_y - min_y + 1) * (max_x - min_x + 1)
            density = area / bbox_area if bbox_area > 0 else 0
            
            stats.append({
                'cluster_id': int(label),
                'size': int(area),
                'centroid': centroid.tolist(),
                'bbox': [int(min_y), int(min_x), int(max_y), int(max_x)],
                'density': float(density)
            })
        
        return stats


class AnomalyGroupAnalyzer:
    """
    Analyzes groups of anomalies for patterns
    """
    
    def __init__(self):
        pass
    
    def analyze_shape(
        self,
        cluster_coords: np.ndarray
    ) -> Dict:
        """
        Analyze shape of anomaly cluster
        
        Args:
            cluster_coords: (N, 2) - Coordinates of cluster pixels
            
        Returns:
            Shape analysis results
        """
        if len(cluster_coords) < 3:
            return {'shape': 'point', 'aspect_ratio': 1.0}
        
        # Compute bounding box
        min_y, min_x = cluster_coords.min(axis=0)
        max_y, max_x = cluster_coords.max(axis=0)
        
        height = max_y - min_y + 1
        width = max_x - min_x + 1
        
        aspect_ratio = width / height if height > 0 else 1.0
        
        # Classify shape
        if aspect_ratio < 0.5:
            shape = 'vertical_line'
        elif aspect_ratio > 2.0:
            shape = 'horizontal_line'
        elif 0.8 <= aspect_ratio <= 1.2:
            shape = 'circular'
        else:
            shape = 'irregular'
        
        return {
            'shape': shape,
            'aspect_ratio': aspect_ratio,
            'height': int(height),
            'width': int(width),
            'area': len(cluster_coords)
        }
    
    def detect_linear_patterns(
        self,
        cluster_coords: np.ndarray,
        threshold: float = 0.9
    ) -> Dict:
        """
        Detect if anomalies form linear patterns
        
        Args:
            cluster_coords: (N, 2) - Coordinates
            threshold: Correlation threshold for linearity
            
        Returns:
            Linearity analysis
        """
        if len(cluster_coords) < 3:
            return {'is_linear': False, 'correlation': 0.0}
        
        # Compute correlation between x and y coordinates
        x = cluster_coords[:, 1]
        y = cluster_coords[:, 0]
        
        correlation = np.corrcoef(x, y)[0, 1]
        
        return {
            'is_linear': abs(correlation) > threshold,
            'correlation': float(correlation),
            'slope': float(np.polyfit(x, y, 1)[0]) if len(x) > 1 else 0.0
        }
    
    def compute_spatial_distribution(
        self,
        cluster_coords: np.ndarray,
        image_shape: Tuple[int, int]
    ) -> Dict:
        """
        Compute spatial distribution statistics
        
        Args:
            cluster_coords: (N, 2) - Coordinates
            image_shape: (H, W) - Image dimensions
            
        Returns:
            Spatial distribution statistics
        """
        H, W = image_shape
        
        # Compute centroid
        centroid = cluster_coords.mean(axis=0)
        
        # Compute distance from image center
        image_center = np.array([H / 2, W / 2])
        distance_from_center = np.linalg.norm(centroid - image_center)
        
        # Compute quadrant
        if centroid[0] < H / 2 and centroid[1] < W / 2:
            quadrant = 'top_left'
        elif centroid[0] < H / 2 and centroid[1] >= W / 2:
            quadrant = 'top_right'
        elif centroid[0] >= H / 2 and centroid[1] < W / 2:
            quadrant = 'bottom_left'
        else:
            quadrant = 'bottom_right'
        
        return {
            'centroid': centroid.tolist(),
            'distance_from_center': float(distance_from_center),
            'quadrant': quadrant,
            'relative_position': {
                'x': float(centroid[1] / W),
                'y': float(centroid[0] / H)
            }
        }


if __name__ == "__main__":
    print("Testing Spatial Clustering...")
    
    # Create dummy anomaly map
    H, W = 100, 100
    anomaly_map = np.zeros((H, W))
    
    # Add some clustered anomalies
    anomaly_map[20:30, 20:30] = 1
    anomaly_map[50:60, 50:60] = 1
    anomaly_map[70:80, 30:40] = 1
    
    # Cluster anomalies
    clusterer = SpatialClusterer(method='dbscan')
    results = clusterer.cluster_anomalies(anomaly_map, (H, W))
    
    print(f"Number of clusters: {results['num_clusters']}")
    print(f"Cluster sizes: {results['cluster_sizes']}")
    
    # Visualize clusters
    if len(results['anomaly_coords']) > 0:
        visualization = clusterer.visualize_clusters(
            anomaly_map,
            results['cluster_labels'],
            results['anomaly_coords']
        )
        print(f"Visualization shape: {visualization.shape}")
    
    # Get cluster statistics
    stats = clusterer.get_cluster_statistics(
        results['cluster_labels'],
        results['anomaly_coords']
    )
    print(f"Cluster statistics: {stats}")
    
    # Test shape analysis
    analyzer = AnomalyGroupAnalyzer()
    for coord_set in [results['anomaly_coords'][results['cluster_labels'] == i] 
                      for i in np.unique(results['cluster_labels']) if i != -1]:
        if len(coord_set) > 0:
            shape = analyzer.analyze_shape(coord_set)
            print(f"Shape analysis: {shape}")
    
    print("Spatial clustering test complete!")
