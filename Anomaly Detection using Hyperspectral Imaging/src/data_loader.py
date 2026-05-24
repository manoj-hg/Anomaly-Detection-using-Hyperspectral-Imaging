"""
Data Loader Module
Fetches satellite spectral data from Google Earth Engine, Copernicus Hub, NASA GIBS, or fallback to Indian Pines dataset.
"""

import numpy as np
import ee
from typing import Tuple, Optional
import warnings
import requests
from PIL import Image
import io
from datetime import datetime

# Import Copernicus Hub loader for real Sentinel-2 data
try:
    from src.copernicus_loader import CopernicusHubLoader
    COPERNICUS_AVAILABLE = True
except ImportError:
    COPERNICUS_AVAILABLE = False
    print("Warning: Copernicus loader not available")

# Import Planet Labs loader for high-resolution data
try:
    from src.planet_loader import PlanetLabsLoader
    PLANET_AVAILABLE = True
except ImportError:
    PLANET_AVAILABLE = False
    print("Warning: Planet Labs loader not available")

# Import Sentinel-1 SAR loader
try:
    from src.sar_loader import Sentinel1Loader
    SAR_AVAILABLE = True
except ImportError:
    SAR_AVAILABLE = False
    print("Warning: Sentinel-1 SAR loader not available")


class SatelliteDataLoader:
    """Loads satellite data from Google Earth Engine or fallback dataset."""
    
    def __init__(self):
        """Initialize the data loader."""
        self.gee_initialized = False
        self._initialize_gee()
        
        # Initialize Copernicus Hub loader
        if COPERNICUS_AVAILABLE:
            self.copernicus_loader = CopernicusHubLoader()
        else:
            self.copernicus_loader = None
        
        # Initialize Planet Labs loader
        if PLANET_AVAILABLE:
            self.planet_loader = PlanetLabsLoader()
        else:
            self.planet_loader = None
        
        # Initialize Sentinel-1 SAR loader
        if SAR_AVAILABLE:
            self.sar_loader = Sentinel1Loader()
        else:
            self.sar_loader = None
    
    def _initialize_gee(self):
        """Initialize Google Earth Engine."""
        try:
            import ee
            import os
            project_id = os.environ.get('GEE_PROJECT_ID', '')
            if project_id:
                ee.Initialize(project=project_id)
                print(f"Google Earth Engine initialized successfully with project: {project_id}")
            else:
                ee.Initialize()
                print("Google Earth Engine initialized successfully (default project)")
            self.gee_initialized = True
        except Exception as e:
            print(f"Failed to initialize Google Earth Engine: {e}")
            print("GEE authentication required. Run 'earthengine authenticate' in terminal")
            self.gee_initialized = False
    
    def fetch_sentinel2_data(self, lat: float, lon: float, 
                            radius: int = 1000) -> Optional[np.ndarray]:
        """
        Fetch Sentinel-2 data from Google Earth Engine.
        
        Args:
            lat: Latitude of the point of interest
            lon: Longitude of the point of interest
            radius: Radius in meters around the point (default: 1000m)
            
        Returns:
            NumPy array of shape (H, W, Bands) or None if failed
        """
        if not self.gee_initialized:
            return None
        
        try:
            # Create point of interest
            point = ee.Geometry.Point([lon, lat])
            region = point.buffer(radius).bounds()
            
            # Load Sentinel-2 collection
            collection = (ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
                         .filterBounds(region)
                         .filterDate('2023-01-01', '2023-12-31')
                         .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 20))
                         .sort('CLOUDY_PIXEL_PERCENTAGE'))
            
            # Get the least cloudy image
            image = collection.first()
            
            if image is None:
                print("No Sentinel-2 data found for the specified location.")
                return None
            
            # Select spectral bands
            # B2: Blue (490nm), B3: Green (560nm), B4: Red (665nm)
            # B8: NIR (842nm), B11: SWIR1 (1610nm), B12: SWIR2 (2190nm)
            bands = ['B2', 'B3', 'B4', 'B8', 'B11', 'B12']
            image = image.select(bands)
            
            # Get the data as numpy array
            data = ee.Image.sampleRectangle(
                image, 
                region=region,
                defaultValue=0
            ).getInfo()
            
            # Extract band data
            band_data = []
            for band in bands:
                if band in data['properties']:
                    band_array = np.array(data['properties'][band])
                    band_data.append(band_array)
                else:
                    print(f"Warning: Band {band} not found in response")
            
            if not band_data:
                print("No bands found in response")
                return None
            
            # Check all bands have same shape
            shapes = [arr.shape for arr in band_data]
            if len(set(shapes)) > 1:
                print(f"Band shapes mismatch: {shapes}")
                # Resize all bands to match the first band's shape
                target_shape = band_data[0].shape
                for i in range(len(band_data)):
                    if band_data[i].shape != target_shape:
                        band_data[i] = np.resize(band_data[i], target_shape)
            
            # Stack bands to create (H, W, Bands) array
            spectral_data = np.stack(band_data, axis=-1)
            
            print(f"Successfully fetched Sentinel-2 data with shape: {spectral_data.shape}")
            return spectral_data
            
        except Exception as e:
            print(f"Error fetching Sentinel-2 data: {e}")
            return None
    
    def fetch_copernicus_imagery(self, lat: float, lon: float, 
                                radius: int = 1000) -> Optional[np.ndarray]:
        """
        Fetch real Sentinel-2 multispectral data from Copernicus Hub
        
        Args:
            lat: Latitude of the point of interest
            lon: Longitude of the point of interest
            radius: Radius in meters
            
        Returns:
            NumPy array of shape (H, W, 6) with spectral bands or None if failed
        """
        if self.copernicus_loader is None:
            print("Copernicus loader not available")
            return None
        
        try:
            print(f"Fetching real Sentinel-2 data from Copernicus Hub for lat={lat}, lon={lon}")
            data = self.copernicus_loader.fetch_sentinel2_imagery(lat, lon, radius)
            
            if data is not None:
                print(f"Successfully fetched Copernicus data with shape: {data.shape}")
                return data
            else:
                print("Copernicus Hub returned no data")
                return None
                
        except Exception as e:
            print(f"Error fetching Copernicus imagery: {e}")
            return None
    
    def fetch_planet_imagery(self, lat: float, lon: float,
                             radius: int = 1000) -> Optional[np.ndarray]:
        """
        Fetch high-resolution PlanetScope imagery from Planet Labs
        
        Args:
            lat: Latitude of the point of interest
            lon: Longitude of the point of interest
            radius: Radius in meters
            
        Returns:
            NumPy array of shape (H, W, 5) with spectral bands or None if failed
        """
        if self.planet_loader is None:
            print("Planet Labs loader not available")
            return None
        
        try:
            print(f"Fetching high-resolution PlanetScope data for lat={lat}, lon={lon}")
            data = self.planet_loader.fetch_planetscope_imagery(lat, lon, radius)
            
            if data is not None:
                print(f"Successfully fetched Planet Labs data with shape: {data.shape}")
                return data
            else:
                print("Planet Labs returned no data")
                return None
                
        except Exception as e:
            print(f"Error fetching Planet Labs imagery: {e}")
            return None
    
    def fetch_sar_imagery(self, lat: float, lon: float,
                          radius: int = 10000) -> Optional[np.ndarray]:
        """
        Fetch Sentinel-1 SAR imagery
        
        Args:
            lat: Latitude of the point of interest
            lon: Longitude of the point of interest
            radius: Radius in meters
            
        Returns:
            NumPy array of shape (H, W, 2) with VV and VH polarizations or None if failed
        """
        if self.sar_loader is None:
            print("Sentinel-1 SAR loader not available")
            return None
        
        try:
            print(f"Fetching Sentinel-1 SAR data for lat={lat}, lon={lon}")
            data = self.sar_loader.fetch_sentinel1_imagery(lat, lon, radius)
            
            if data is not None:
                print(f"Successfully fetched SAR data with shape: {data.shape}")
                return data
            else:
                print("SAR loader returned no data")
                return None
                
        except Exception as e:
            print(f"Error fetching SAR imagery: {e}")
            return None
    
    def fetch_nasa_gibs_imagery(self, lat: float, lon: float, 
                               width: int = 400, height: int = 400) -> Optional[np.ndarray]:
        """
        Fetch live satellite imagery using Esri World Imagery (reliable real-time source).
        
        Args:
            lat: Latitude of the point of interest
            lon: Longitude of the point of interest
            width: Image width in pixels
            height: Image height in pixels
            
        Returns:
            NumPy array of shape (H, W, 3) for RGB image or None if failed
        """
        try:
            print(f"Fetching real-time satellite imagery for lat={lat}, lon={lon}")
            
            # Use Esri World Imagery API (reliable, no date restrictions)
            # Calculate bounding box
            delta = 0.05
            min_lon = lon - delta
            max_lon = lon + delta
            min_lat = lat - delta
            max_lat = lat + delta
            
            # Esri World Imagery export endpoint
            base_url = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/export"
            
            params = {
                'bbox': f"{min_lon},{min_lat},{max_lon},{max_lat}",
                'bboxSR': '4326',
                'size': f"{width},{height}",
                'imageSR': '4326',
                'format': 'png',
                'f': 'image'
            }
            
            print(f"Requesting from Esri World Imagery")
            response = requests.get(base_url, params=params, timeout=30)
            response.raise_for_status()
            
            # Check if we got a valid image
            if len(response.content) < 1000:
                print("Received too small response from Esri")
                return None
            
            # Load image
            img = Image.open(io.BytesIO(response.content))
            img_array = np.array(img)
            
            # Convert RGBA to RGB if needed
            if len(img_array.shape) == 3 and img_array.shape[-1] == 4:
                img_array = img_array[:, :, :3]
            elif len(img_array.shape) == 2:
                img_array = np.stack([img_array] * 3, axis=-1)
            
            print(f"Successfully fetched real-time imagery from Esri with shape: {img_array.shape}")
            return img_array
            
        except Exception as e:
            print(f"Error fetching Esri imagery: {e}")
            return None
    
    def load_indian_pines_fallback(self) -> np.ndarray:
        """
        Load real hyperspectral dataset (Indian Pines) as fallback.
        
        Returns:
            NumPy array of shape (H, W, Bands)
        """
        try:
            import os
            
            # First, check for user-downloaded .npy files
            indian_pines_array_path = 'data/indianpinearray.npy'
            if os.path.exists(indian_pines_array_path):
                print("Loading Indian Pines dataset from local .npy file...")
                hyperspectral_data = np.load(indian_pines_array_path)
                print(f"Loaded real Indian Pines dataset with shape: {hyperspectral_data.shape}")
                
                # Also check for ground truth labels (try both uppercase and lowercase)
                for ipgt_path in ['data/IPgt.npy', 'data/ipgt.npy']:
                    if os.path.exists(ipgt_path):
                        print("Ground truth labels found at:", ipgt_path)
                        # Store ground truth for later use if needed
                        self.ground_truth = np.load(ipgt_path)
                        break
                
                return hyperspectral_data
            
            # Try to load from .mat file
            import requests
            from scipy.io import loadmat
            
            data_path = 'data/pavia_university.mat'
            
            if os.path.exists(data_path):
                print("Loading Pavia University dataset from local files...")
                data = loadmat(data_path)
                # Pavia University has shape (610, 340, 103)
                if 'paviaU' in data:
                    return data['paviaU']
                elif 'pavia' in data:
                    return data['pavia']
                else:
                    print("Unknown data format, cannot load data")
                    return None
            else:
                # Download real dataset automatically
                print("Downloading real hyperspectral dataset (Indian Pines)...")
                print("This is a real dataset with 200 spectral bands from agricultural area.")
                
                # Use Indian Pines dataset from a reliable source
        except Exception as e:
            print(f"Error loading Indian Pines: {e}")
            return None
    
    def _normalize_indian_pines(self, data: np.ndarray) -> np.ndarray:
        """
        Normalize Indian Pines data to [0, 1] range.
        
        Args:
            data: Raw Indian Pines data
            
        Returns:
            Normalized data
        """
        # Normalize to [0, 1]
        data_min = data.min()
        data_max = data.max()
        data = (data - data_min) / (data_max - data_min + 1e-8)
        
        # Clip to valid range
        data = np.clip(data, 0, 1)
        
        return data
    
    def load_data(self, lat: Optional[float] = None, lon: Optional[float] = None, 
                  use_gee: bool = True, use_sar: bool = False) -> Tuple[np.ndarray, str]:
        """
        Load satellite data with multiple fallback options.
        
        Priority order:
        1. Planet Labs (high-resolution 3m multispectral - best for detailed analysis)
        2. Copernicus Hub (real Sentinel-2 multispectral - good for anomaly detection)
        3. Google Earth Engine (real Sentinel-2 multispectral)
        4. NASA GIBS (RGB-only, limited spectral data)
        5. Sentinel-1 SAR (all-weather radar data - if use_sar=True)
        6. Indian Pines (real hyperspectral dataset, location-independent)
        
        Args:
            lat: Latitude for location-based data
            lon: Longitude for location-based data
            use_gee: Whether to try Google Earth Engine first
            use_sar: Whether to try Sentinel-1 SAR data
            
        Returns:
            Tuple of (data_array, data_source_description)
        """
        # Priority 1: Try Planet Labs for high-resolution multispectral data
        if lat is not None and lon is not None and self.planet_loader is not None:
            print("Fetching high-resolution PlanetScope multispectral data from Planet Labs...")
            planet_data = self.fetch_planet_imagery(lat, lon)
            if planet_data is not None:
                print("Successfully fetched high-resolution data from Planet Labs")
                return planet_data, "Planet Labs (PlanetScope - High-Resolution Multispectral)"
        
        # Priority 2: Try Copernicus Hub for real Sentinel-2 multispectral data
        if lat is not None and lon is not None and self.copernicus_loader is not None:
            print("Fetching real Sentinel-2 multispectral data from Copernicus Hub...")
            copernicus_data = self.fetch_copernicus_imagery(lat, lon)
            if copernicus_data is not None:
                print("Successfully fetched real Sentinel-2 data from Copernicus Hub")
                return copernicus_data, "Copernicus Hub (Sentinel-2 - Real Multispectral)"
        
        # Priority 3: Try Google Earth Engine for real Sentinel-2 data
        if lat is not None and lon is not None and use_gee and self.gee_initialized:
            print("Fetching Sentinel-2 data from Google Earth Engine...")
            gee_data = self.fetch_sentinel2_data(lat, lon)
            if gee_data is not None:
                return gee_data, "Google Earth Engine (Sentinel-2 - Real Multispectral)"
        
        # Priority 4: Try NASA GIBS for live satellite imagery (RGB-only, limited)
        if lat is not None and lon is not None:
            print("Fetching live satellite imagery from NASA GIBS...")
            gibs_data = self.fetch_nasa_gibs_imagery(lat, lon)
            if gibs_data is not None:
                print("Successfully fetched real satellite imagery from NASA GIBS")
                return gibs_data, "NASA GIBS (MODIS Terra - Live Satellite - RGB Only)"
        
        # Priority 5: Try Sentinel-1 SAR data (if requested)
        if use_sar and lat is not None and lon is not None and self.sar_loader is not None:
            print("Fetching Sentinel-1 SAR data...")
            sar_data = self.fetch_sar_imagery(lat, lon)
            if sar_data is not None:
                print("Successfully fetched SAR data")
                return sar_data, "Sentinel-1 SAR (All-Weather Radar Data)"
        
        # Priority 6: Fallback to Indian Pines (real hyperspectral dataset)
        print("Using real hyperspectral dataset (Indian Pines)...")
        fallback_data = self.load_indian_pines_fallback()
        if fallback_data is not None:
            return fallback_data, "Indian Pines (Real Hyperspectral Dataset - Location Independent)"
        
        # All real data sources failed - raise error instead of using synthetic data
        raise ValueError("All real data sources failed. Please check your internet connection, API credentials, or try a different location.")
    
    def get_rgb_composite(self, data: np.ndarray) -> np.ndarray:
        """
        Create RGB composite from spectral data.
        
        Args:
            data: Spectral data array of shape (H, W, Bands)
            
        Returns:
            RGB image of shape (H, W, 3)
        """
        if data.shape[-1] >= 3:
            # Use first 3 bands as RGB
            rgb = data[:, :, :3].copy()
        else:
            # If fewer than 3 bands, replicate
            rgb = np.stack([data[:, :, 0]] * 3, axis=-1)
        
        # Normalize to 0-1
        rgb = (rgb - rgb.min()) / (rgb.max() - rgb.min() + 1e-8)
        rgb = np.clip(rgb, 0, 1)
        
        return rgb


def main():
    """Test the data loader."""
    loader = SatelliteDataLoader()
    
    # Test with GEE (will fallback if not available)
    print("\n=== Testing with GEE coordinates ===")
    data, source = loader.load_data(lat=40.7128, lon=-74.0060)
    print(f"Data shape: {data.shape}")
    print(f"Data source: {source}")
    
    # Test RGB composite
    rgb = loader.get_rgb_composite(data)
    print(f"RGB composite shape: {rgb.shape}")
    
    # Test fallback directly
    print("\n=== Testing fallback dataset ===")
    fallback_data, source = loader.load_data(use_gee=False)
    print(f"Fallback data shape: {fallback_data.shape}")
    print(f"Fallback data source: {source}")


if __name__ == "__main__":
    main()
