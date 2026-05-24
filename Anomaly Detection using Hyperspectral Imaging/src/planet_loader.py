"""
Planet Labs Loader Module
Fetches high-resolution multispectral imagery from Planet Labs API
"""

import numpy as np
import requests
import os
from typing import Optional, Tuple, Dict
import rasterio
from PIL import Image
import tempfile
import io
import json
from datetime import datetime, timedelta


class PlanetLabsLoader:
    """
    Load high-resolution multispectral imagery from Planet Labs
    Requires Planet Labs API key
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Planet Labs loader
        
        Args:
            api_key: Planet Labs API key (required for production)
        """
        self.api_key = api_key or os.environ.get('PLANET_API_KEY')
        self.base_url = "https://api.planet.com/data/v1"
        
        # PlanetScope bands for anomaly detection
        self.bands = ['Blue', 'Green', 'Red', 'NIR', 'NIR2']
        self.band_names = {
            'Blue': 'Blue (490nm)',
            'Green': 'Green (560nm)',
            'Red': 'Red (665nm)',
            'NIR': 'NIR (842nm)',
            'NIR2': 'Red Edge (740nm)'
        }
    
    def fetch_planetscope_imagery(
        self,
        lat: float,
        lon: float,
        radius: int = 1000,
        days_back: int = 7,
        cloud_cover: float = 0.1
    ) -> Optional[np.ndarray]:
        """
        Fetch PlanetScope imagery from Planet Labs
        
        Args:
            lat: Latitude
            lon: Longitude
            radius: Radius in meters
            days_back: Look back this many days
            cloud_cover: Maximum cloud cover (0-1)
            
        Returns:
            Spectral data array (H, W, 5) with 5 bands
        """
        if not self.api_key:
            print("Planet Labs API key not provided. Skipping Planet Labs.")
            return None
        
        try:
            # Calculate bounding box
            delta = radius / 111000
            min_lon = lon - delta
            max_lon = lon + delta
            min_lat = lat - delta
            max_lat = lat + delta
            
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)
            
            # Search for available imagery
            search_url = f"{self.base_url}/quick-search"
            
            headers = {
                'Authorization': f'api-key {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            search_payload = {
                "item_types": ["PSScene"],
                "filter": {
                    "type": "AndFilter",
                    "config": [
                        {
                            "type": "GeometryFilter",
                            "field_name": "geometry",
                            "config": {
                                "type": "Polygon",
                                "coordinates": [[
                                    [min_lon, min_lat],
                                    [max_lon, min_lat],
                                    [max_lon, max_lat],
                                    [min_lon, max_lat],
                                    [min_lon, min_lat]
                                ]]
                            }
                        },
                        {
                            "type": "RangeFilter",
                            "field_name": "acquired",
                            "config": {
                                "gte": start_date.isoformat(),
                                "lte": end_date.isoformat()
                            }
                        },
                        {
                            "type": "RangeFilter",
                            "field_name": "cloud_cover",
                            "config": {
                                "lte": cloud_cover
                            }
                        },
                        {
                            "type": "PermissionFilter",
                            "config": [
                                "assets:download"
                            ]
                        }
                    ]
                }
            }
            
            print(f"Searching Planet Labs for imagery near lat={lat}, lon={lon}")
            
            response = requests.post(search_url, json=search_payload, headers=headers, timeout=30)
            
            if response.status_code != 200:
                print(f"Planet Labs search failed: {response.status_code}")
                return None
            
            search_results = response.json()
            
            if not search_results.get('features'):
                print("No Planet Labs imagery found for the specified location and time")
                return None
            
            # Get the most recent image
            image_item = search_results['features'][0]
            image_id = image_item['id']
            
            print(f"Found Planet Labs image: {image_id}")
            
            # Get asset activation
            assets_url = f"{self.base_url}/item-types/PSScene/items/{image_id}/assets"
            assets_response = requests.get(assets_url, headers=headers, timeout=30)
            
            if assets_response.status_code != 200:
                print(f"Failed to get assets: {assets_response.status_code}")
                return None
            
            assets = assets_response.json()
            
            # Activate analytic asset (multispectral)
            analytic_asset = assets.get('analytic')
            if not analytic_asset:
                print("Analytic asset not available")
                return None
            
            # Activate if not already active
            if analytic_asset['status'] != 'active':
                activate_url = analytic_asset['_links']['activate']
                activate_response = requests.post(activate_url, headers=headers, timeout=30)
                print(f"Asset activation status: {activate_response.status_code}")
                
                # Wait for activation (simplified - in production, use polling)
                import time
                time.sleep(5)
            
            # Download the imagery
            download_url = analytic_asset['_links']['location']
            
            print(f"Downloading Planet Labs imagery...")
            download_response = requests.get(download_url, headers=headers, timeout=120)
            
            if download_response.status_code != 200:
                print(f"Download failed: {download_response.status_code}")
                return None
            
            # Parse the downloaded data (GeoTIFF)
            # For simplicity, we'll use rasterio if available, otherwise PIL
            try:
                import rasterio
                from rasterio.transform import from_bounds
                
                # Save to temp file and read with rasterio
                with tempfile.NamedTemporaryFile(suffix='.tif', delete=False) as tmp:
                    tmp.write(download_response.content)
                    tmp_path = tmp.name
                
                with rasterio.open(tmp_path) as src:
                    # Read all bands
                    data = src.read()
                    # Convert to (H, W, C)
                    data = np.moveaxis(data, 0, -1)
                    
                    # Select relevant bands (Blue, Green, Red, NIR)
                    # PlanetScope analytic has 4 bands: Blue, Green, Red, NIR
                    if data.shape[-1] >= 4:
                        data = data[:, :, :4]
                        # Note: Red Edge band not available in PlanetScope, using 4 bands only
                    
                    print(f"Successfully loaded Planet Labs data with shape: {data.shape}")
                    
                    # Clean up temp file
                    os.unlink(tmp_path)
                    
                    return data
                    
            except ImportError:
                print("rasterio not available, using PIL fallback")
                # Fallback to PIL (limited functionality)
                img = Image.open(io.BytesIO(download_response.content))
                data = np.array(img)
                
                if len(data.shape) == 2:
                    data = np.stack([data] * 5, axis=-1)
                elif data.shape[-1] == 3:
                    # RGB only, estimate NIR and Red Edge
                    nir = data[:, :, 1] * 1.2  # Estimate from green
                    red_edge = (data[:, :, 2] + nir) / 2
                    data = np.dstack([data, nir, red_edge])
                elif data.shape[-1] == 4:
                    # RGBA or BGRA, estimate Red Edge
                    red_edge = (data[:, :, 2] + data[:, :, 3]) / 2
                    data = np.dstack([data[:, :, :4], red_edge])
                
                print(f"Successfully loaded Planet Labs data (PIL fallback) with shape: {data.shape}")
                return data
                
        except Exception as e:
            print(f"Error fetching Planet Labs imagery: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def get_metadata(self, lat: float, lon: float) -> Dict:
        """
        Get metadata about Planet Labs imagery
        
        Args:
            lat: Latitude
            lon: Longitude
            
        Returns:
            Dictionary with metadata
        """
        return {
            'source': 'Planet Labs',
            'satellite': 'PlanetScope',
            'bands': self.bands,
            'band_descriptions': self.band_names,
            'resolution': '3m (high resolution)',
            'revisit_time': '1-3 days (daily at equator)',
            'api_required': True
        }


def main():
    """Test the Planet Labs loader"""
    # Note: This requires a valid Planet Labs API key
    api_key = os.environ.get('PLANET_API_KEY')
    
    if not api_key:
        print("Planet Labs API key not found. Set PLANET_API_KEY environment variable to test.")
        return
    
    loader = PlanetLabsLoader(api_key=api_key)
    
    # Test with a known location
    lat, lon = 40.7128, -74.0060  # New York
    
    print("Testing Planet Labs Loader...")
    data = loader.fetch_planetscope_imagery(lat, lon)
    
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
    import os
    import tempfile
    main()
