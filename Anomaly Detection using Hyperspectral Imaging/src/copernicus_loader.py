"""
Copernicus Open Access Hub Loader
Real Sentinel-2 data without Google Earth Engine authentication
"""

import numpy as np
import requests
import os
from typing import Tuple, Optional, Dict, List
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET
from PIL import Image
import io
import zipfile
import tempfile


class CopernicusHubLoader:
    """
    Load real Sentinel-2 data from Copernicus Open Access Hub
    No GEE authentication required - uses Sentinel Hub Open Access
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Copernicus Hub loader
        
        Args:
            api_key: Optional Sentinel Hub API key (for higher rate limits)
        """
        import os
        # Use environment variable if api_key not provided
        if api_key is None:
            api_key = os.environ.get('SENTINEL_HUB_API_KEY', '')
        self.api_key = api_key
        self.base_url = "https://services.sentinel-hub.com"
        self.processing_url = "https://services.sentinel-hub.com/api/v1/process"
        
        # Sentinel-2 bands for anomaly detection
        self.bands = ['B02', 'B03', 'B04', 'B08', 'B11', 'B12']
        self.band_names = {
            'B02': 'Blue (490nm)',
            'B03': 'Green (560nm)',
            'B04': 'Red (665nm)',
            'B08': 'NIR (842nm)',
            'B11': 'SWIR1 (1610nm)',
            'B12': 'SWIR2 (2190nm)'
        }
    
    def fetch_sentinel2_imagery(
        self,
        lat: float,
        lon: float,
        radius: int = 1000,
        days_back: int = 30,
        max_cloud_cover: float = 20.0
    ) -> Optional[np.ndarray]:
        """
        Fetch real Sentinel-2 imagery from Sentinel Hub
        
        Args:
            lat: Latitude
            lon: Longitude
            radius: Radius in meters
            days_back: Look back this many days for imagery
            max_cloud_cover: Maximum cloud cover percentage
            
        Returns:
            Spectral data array (H, W, 6) with 6 bands
        """
        try:
            # Calculate bounding box
            delta = radius / 111000  # Approximate meters to degrees
            min_lon = lon - delta
            max_lon = lon + delta
            min_lat = lat - delta
            max_lat = lat + delta
            
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)
            
            # Build Sentinel Hub request
            evalscript = """
            //VERSION=3
            function setup() {
                return {
                    input: [{
                        bands: ["B02", "B03", "B04", "B08", "B11", "B12"]
                    }],
                    output: {
                        bands: 6,
                        sampleType: "FLOAT32"
                    }
                };
            }
            
            function evaluatePixel(sample) {
                return [sample.B02, sample.B03, sample.B04, sample.B08, sample.B11, sample.B12];
            }
            """
            
            payload = {
                "input": {
                    "bounds": {
                        "bbox": [min_lon, min_lat, max_lon, max_lat],
                        "properties": {
                            "crs": "EPSG:4326"
                        }
                    },
                    "data": [{
                        "type": "sentinel-2-l2a",
                        "dataFilter": {
                            "timeRange": {
                                "from": start_date.strftime("%Y-%m-%dT00:00:00Z"),
                                "to": end_date.strftime("%Y-%m-%dT23:59:59Z")
                            },
                            "maxCloudCoverage": max_cloud_cover
                        }
                    }]
                },
                "output": {
                    "width": 256,
                    "height": 256,
                    "responses": [{
                        "identifier": "default",
                        "format": {
                            "type": "image/tiff"
                        }
                    }]
                },
                "evalscript": evalscript
            }
            
            headers = {
                "Content-Type": "application/json"
            }
            
            if self.api_key:
                # Try multiple authentication methods for Sentinel Hub
                headers["Authorization"] = f"Bearer {self.api_key}"
                # Also try x-api-key header as fallback
                headers["x-api-key"] = self.api_key
            
            print(f"Fetching Sentinel-2 data from Copernicus Hub for lat={lat}, lon={lon}")
            
            # Try Sentinel Hub first
            try:
                response = requests.post(
                    self.processing_url,
                    json=payload,
                    headers=headers,
                    timeout=60
                )
                
                if response.status_code == 200:
                    # Parse TIFF response
                    image = Image.open(io.BytesIO(response.content))
                    data = np.array(image)
                    
                    # Handle single band or multi-band
                    if len(data.shape) == 2:
                        data = np.stack([data] * 6, axis=-1)
                    elif data.shape[-1] != 6:
                        # Pad or truncate to 6 bands
                        if data.shape[-1] < 6:
                            padding = np.zeros((data.shape[0], data.shape[1], 6 - data.shape[-1]))
                            data = np.concatenate([data, padding], axis=-1)
                        else:
                            data = data[:, :, :6]
                    
                    print(f"Successfully fetched Sentinel-2 data with shape: {data.shape}")
                    return data
                elif response.status_code == 401:
                    print("Sentinel Hub authentication failed - API key required")
                    print("Skipping Copernicus Hub and using fallback data sources")
                else:
                    print(f"Sentinel Hub returned status {response.status_code}")
                    
            except Exception as e:
                print(f"Sentinel Hub request failed: {e}")
            
            # Fallback to USGS Earth Explorer (Landsat 8/9)
            return self._fetch_landsat_fallback(lat, lon, min_lat, max_lat, min_lon, max_lon)
            
        except Exception as e:
            print(f"Error fetching Copernicus data: {e}")
            return None
    
    def _fetch_landsat_fallback(
        self,
        lat: float,
        lon: float,
        min_lat: float,
        max_lat: float,
        min_lon: float,
        max_lon: float
    ) -> Optional[np.ndarray]:
        """
        Fallback to USGS Earth Explorer for Landsat 8/9 data
        
        Args:
            lat, lon: Center coordinates
            min_lat, max_lat, min_lon, max_lon: Bounding box
            
        Returns:
            Spectral data array (H, W, 6)
        """
        try:
            print("Falling back to USGS Earth Explorer for Landsat data...")
            
            # USGS M2M API endpoint
            usgs_url = "https://m2m.cr.usgs.gov/api/api/json/stable/"
            
            # This would require USGS API credentials
            # For now, we'll use a different approach - NASA GIBS with proper bands
            
            return self._fetch_nasa_gibs_multispectral(lat, lon)
            
        except Exception as e:
            print(f"USGS fallback failed: {e}")
            return None
    
    def _fetch_nasa_gibs_multispectral(
        self,
        lat: float,
        lon: float,
        width: int = 400,
        height: int = 400
    ) -> Optional[np.ndarray]:
        """
        Fetch multispectral data from NASA GIBS (MODIS/VIIRS)
        
        Args:
            lat: Latitude
            lon: Longitude
            width: Image width
            height: Image height
            
        Returns:
            Spectral data array (H, W, 6)
        """
        try:
            print("Fetching multispectral data from NASA GIBS...")
            
            # Use MODIS bands (has NIR and SWIR)
            # MODIS bands: 1 (Red), 2 (NIR), 6 (SWIR)
            delta = 0.05
            min_lon = lon - delta
            max_lon = lon + delta
            min_lat = lat - delta
            max_lat = lat + delta
            
            # Fetch multiple bands
            bands_data = []
            band_configs = [
                ('MODIS_Terra_CorrectedReflectance_TrueColor', 'rgb'),  # RGB
                ('MODIS_Terra_CorrectedReflectance_EVI', 'evi'),  # Vegetation
                ('MODIS_Terra_CorrectedReflectance_Bands721', 'swir')  # SWIR
            ]
            
            for product, band_type in band_configs:
                url = f"https://gibs.earthdata.nasa.gov/wmts/epsg4326/best/{product}/default/{datetime.now().strftime('%Y-%m-%d')}/250m/{width}/{height}/{int((lon + 180) * 100)}/{int((90 - lat) * 100)}.png"
                
                try:
                    response = requests.get(url, timeout=30)
                    if response.status_code == 200:
                        img = Image.open(io.BytesIO(response.content))
                        img_array = np.array(img)
                        bands_data.append(img_array)
                except:
                    continue
            
            if len(bands_data) >= 1:
                # Use available bands - only RGB from NASA GIBS
                base_img = bands_data[0]
                h, w = base_img.shape[:2]
                
                # Return only RGB data (3 bands) - no synthetic estimation
                if len(base_img.shape) == 3:
                    spectral_data = base_img[:, :, 0:3] / 255.0
                    print(f"Successfully fetched NASA GIBS RGB data with shape: {spectral_data.shape}")
                    return spectral_data
                else:
                    # Convert grayscale to RGB
                    spectral_data = np.stack([base_img] * 3, axis=-1) / 255.0
                    print(f"Successfully fetched NASA GIBS grayscale data, converted to RGB: {spectral_data.shape}")
                    return spectral_data
            
        except Exception as e:
            print(f"NASA GIBS fallback failed: {e}")
        
        return None
    
    def get_metadata(self, lat: float, lon: float) -> Dict:
        """
        Get metadata about available imagery
        
        Args:
            lat: Latitude
            lon: Longitude
            
        Returns:
            Dictionary with metadata
        """
        return {
            'source': 'Copernicus Open Access Hub',
            'satellite': 'Sentinel-2',
            'bands': self.bands,
            'band_descriptions': self.band_names,
            'resolution': '10m (visible/NIR), 20m (SWIR)',
            'revisit_time': '5 days'
        }


def main():
    """Test the Copernicus Hub loader"""
    loader = CopernicusHubLoader()
    
    # Test with a known location
    lat, lon = 40.7128, -74.0060  # New York
    
    print("Testing Copernicus Hub Loader...")
    data = loader.fetch_sentinel2_imagery(lat, lon)
    
    if data is not None:
        print(f"Success! Data shape: {data.shape}")
        print(f"Data range: [{data.min():.4f}, {data.max():.4f}]")
        print(f"Data type: {data.dtype}")
    else:
        print("Failed to fetch data")
    
    # Test metadata
    metadata = loader.get_metadata(lat, lon)
    print(f"\nMetadata: {metadata}")


if __name__ == "__main__":
    main()
