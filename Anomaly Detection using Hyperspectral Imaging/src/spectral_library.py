"""
Spectral Library Matching Module
Matches spectral signatures to material libraries for material identification
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from scipy.spatial.distance import euclidean, cosine
from scipy.signal import correlate
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class SpectralLibrary:
    """
    Manages spectral signature library for material identification
    """
    
    def __init__(self):
        # Common spectral signatures (simplified)
        # In production, load from USGS, ECOSTRESS, or other libraries
        self.library = {
            # Agriculture signatures
            'healthy_vegetation': {
                'signature': np.array([0.05, 0.1, 0.4, 0.8, 0.6, 0.3, 0.2, 0.1]),
                'description': 'Healthy vegetation (Agriculture)',
                'category': 'agriculture',
                'bands': ['B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B11']
            },
            'stressed_vegetation': {
                'signature': np.array([0.15, 0.25, 0.35, 0.45, 0.4, 0.35, 0.3, 0.25]),
                'description': 'Stressed/diseased crops (Agriculture)',
                'category': 'agriculture',
                'bands': ['B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B11']
            },
            'dry_soil': {
                'signature': np.array([0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7]),
                'description': 'Dry agricultural soil (Agriculture)',
                'category': 'agriculture',
                'bands': ['B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B11']
            },
            
            # Defense/Military signatures
            'camouflage_net': {
                'signature': np.array([0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5]),
                'description': 'Camouflage netting (Defense)',
                'category': 'defense',
                'bands': ['B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B11']
            },
            'military_vehicle': {
                'signature': np.array([0.25, 0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6]),
                'description': 'Military vehicle (Defense)',
                'category': 'defense',
                'bands': ['B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B11']
            },
            'concrete_structure': {
                'signature': np.array([0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7, 0.75]),
                'description': 'Concrete bunker/structure (Defense)',
                'category': 'defense',
                'bands': ['B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B11']
            },
            
            # Geological signatures
            'granite': {
                'signature': np.array([0.5, 0.52, 0.55, 0.58, 0.6, 0.62, 0.65, 0.68]),
                'description': 'Granite rock formation (Geological)',
                'category': 'geological',
                'bands': ['B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B11']
            },
            'limestone': {
                'signature': np.array([0.55, 0.58, 0.6, 0.62, 0.64, 0.66, 0.68, 0.7]),
                'description': 'Limestone deposit (Geological)',
                'category': 'geological',
                'bands': ['B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B11']
            },
            'iron_ore': {
                'signature': np.array([0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65]),
                'description': 'Iron ore deposit (Geological)',
                'category': 'geological',
                'bands': ['B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B11']
            },
            'mineral_deposit': {
                'signature': np.array([0.4, 0.42, 0.45, 0.48, 0.5, 0.52, 0.55, 0.58]),
                'description': 'General mineral deposit (Geological)',
                'category': 'geological',
                'bands': ['B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B11']
            },
            
            # General signatures
            'water': {
                'signature': np.array([0.1, 0.05, 0.02, 0.01, 0.0, 0.0, 0.0, 0.0]),
                'description': 'Water bodies',
                'category': 'general',
                'bands': ['B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B11']
            },
            'urban': {
                'signature': np.array([0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7, 0.75]),
                'description': 'Urban/Man-made',
                'category': 'general',
                'bands': ['B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B11']
            },
            'snow': {
                'signature': np.array([0.95, 0.95, 0.95, 0.9, 0.8, 0.7, 0.6, 0.5]),
                'description': 'Snow/Ice',
                'category': 'general',
                'bands': ['B2', 'B3', 'B4', 'B5', 'B6', 'B7', 'B8', 'B11']
            }
        }
        
    def add_signature(
        self,
        name: str,
        signature: np.ndarray,
        description: str,
        bands: List[str]
    ):
        """Add a new spectral signature to the library"""
        self.library[name] = {
            'signature': signature,
            'description': description,
            'bands': bands
        }
    
    def get_signature(self, name: str) -> Optional[Dict]:
        """Get a spectral signature by name"""
        return self.library.get(name)
    
    def list_signatures(self) -> List[str]:
        """List all available signatures"""
        return list(self.library.keys())


class SpectralMatcher:
    """
    Matches unknown spectra to library signatures
    """
    
    def __init__(self, library: SpectralLibrary):
        self.library = library
        self.methods = ['euclidean', 'cosine', 'correlation', 'sam']
        
    def match(
        self,
        spectrum: np.ndarray,
        method: str = 'euclidean',
        top_k: int = 3
    ) -> List[Dict]:
        """
        Match spectrum to library signatures
        
        Args:
            spectrum: (C,) - Unknown spectral signature
            method: Matching method ('euclidean', 'cosine', 'correlation', 'sam')
            top_k: Return top k matches
            
        Returns:
            List of matches with scores
        """
        matches = []
        
        for name, sig_data in self.library.library.items():
            reference = sig_data['signature']
            
            # Ensure same length
            if len(spectrum) != len(reference):
                # Interpolate to match length
                spectrum_interp = np.interp(
                    np.linspace(0, 1, len(reference)),
                    np.linspace(0, 1, len(spectrum)),
                    spectrum
                )
            else:
                spectrum_interp = spectrum
            
            # Compute similarity score
            if method == 'euclidean':
                score = 1.0 / (1.0 + euclidean(spectrum_interp, reference))
            elif method == 'cosine':
                score = 1.0 - cosine(spectrum_interp, reference)
            elif method == 'correlation':
                score = np.corrcoef(spectrum_interp, reference)[0, 1]
            elif method == 'sam':
                # Spectral Angle Mapper
                score = self._compute_sam(spectrum_interp, reference)
            else:
                raise ValueError(f"Unknown method: {method}")
            
            matches.append({
                'material': name,
                'description': sig_data['description'],
                'score': float(score),
                'method': method
            })
        
        # Sort by score (descending)
        matches.sort(key=lambda x: x['score'], reverse=True)
        
        return matches[:top_k]
    
    def _compute_sam(self, spectrum1: np.ndarray, spectrum2: np.ndarray) -> float:
        """
        Compute Spectral Angle Mapper (SAM) similarity
        
        Args:
            spectrum1: First spectrum
            spectrum2: Second spectrum
            
        Returns:
            SAM similarity score (1 = identical, 0 = orthogonal)
        """
        dot_product = np.dot(spectrum1, spectrum2)
        norm1 = np.linalg.norm(spectrum1)
        norm2 = np.linalg.norm(spectrum2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        cos_angle = dot_product / (norm1 * norm2)
        cos_angle = np.clip(cos_angle, -1.0, 1.0)
        
        return cos_angle
    
    def match_image(
        self,
        data: np.ndarray,
        method: str = 'euclidean'
    ) -> Dict[str, np.ndarray]:
        """
        Match each pixel in an image to library materials
        
        Args:
            data: (H, W, C) - Hyperspectral image
            method: Matching method
            
        Returns:
            Dictionary of material probability maps
        """
        H, W, C = data.shape
        
        # Initialize material maps
        material_maps = {}
        for material_name in self.library.list_signatures():
            material_maps[material_name] = np.zeros((H, W))
        
        # Match each pixel
        for i in range(H):
            for j in range(W):
                spectrum = data[i, j, :]
                matches = self.match(spectrum, method=method, top_k=1)
                
                if matches:
                    best_match = matches[0]
                    material_maps[best_match['material']][i, j] = best_match['score']
        
        return material_maps
    
    def unmix(
        self,
        spectrum: np.ndarray,
        endmembers: Optional[np.ndarray] = None
    ) -> Dict[str, float]:
        """
        Perform linear spectral unmixing
        
        Args:
            spectrum: (C,) - Mixed spectrum
            endmembers: (N, C) - Endmember spectra (optional, uses library if None)
            
        Returns:
            Dictionary of material abundances
        """
        if endmembers is None:
            # Use library as endmembers
            endmembers = np.array([sig['signature'] for sig in self.library.library.values()])
            material_names = list(self.library.library.keys())
        else:
            material_names = [f'material_{i}' for i in range(endmembers.shape[0])]
        
        # Ensure same length
        if len(spectrum) != endmembers.shape[1]:
            spectrum_interp = np.interp(
                np.linspace(0, 1, endmembers.shape[1]),
                np.linspace(0, 1, len(spectrum)),
                spectrum
            )
        else:
            spectrum_interp = spectrum
        
        # Solve linear unmixing (least squares with non-negativity constraint)
        from scipy.optimize import nnls
        
        abundances, _ = nnls(endmembers.T, spectrum_interp)
        
        # Normalize to sum to 1
        if abundances.sum() > 0:
            abundances = abundances / abundances.sum()
        
        return dict(zip(material_names, abundances))


class VegetationIndexCalculator:
    """
    Calculate vegetation indices from spectral data
    """
    
    def __init__(self):
        pass
    
    def calculate_ndvi(
        self,
        nir: np.ndarray,
        red: np.ndarray
    ) -> np.ndarray:
        """
        Calculate Normalized Difference Vegetation Index
        
        Args:
            nir: Near-infrared band
            red: Red band
            
        Returns:
            NDVI values
        """
        ndvi = (nir - red) / (nir + red + 1e-8)
        return np.clip(ndvi, -1, 1)
    
    def calculate_evi(
        self,
        nir: np.ndarray,
        red: np.ndarray,
        blue: np.ndarray
    ) -> np.ndarray:
        """
        Calculate Enhanced Vegetation Index
        
        Args:
            nir: Near-infrared band
            red: Red band
            blue: Blue band
            
        Returns:
            EVI values
        """
        L = 1.0  # Canopy background adjustment
        C1 = 6.0  # Aerosol resistance coefficient
        C2 = 7.5  # Aerosol resistance coefficient
        G = 2.5  # Gain factor
        
        evi = G * (nir - red) / (nir + C1 * red - C2 * blue + L + 1e-8)
        return np.clip(evi, -1, 1)
    
    def calculate_savi(
        self,
        nir: np.ndarray,
        red: np.ndarray,
        L: float = 0.5
    ) -> np.ndarray:
        """
        Calculate Soil Adjusted Vegetation Index
        
        Args:
            nir: Near-infrared band
            red: Red band
            L: Soil brightness correction factor
            
        Returns:
            SAVI values
        """
        savi = (nir - red) / (nir + red + L) * (1 + L)
        return np.clip(savi, -1, 1)
    
    def calculate_ndwi(
        self,
        nir: np.ndarray,
        swir: np.ndarray
    ) -> np.ndarray:
        """
        Calculate Normalized Difference Water Index
        
        Args:
            nir: Near-infrared band
            swir: Short-wave infrared band
            
        Returns:
            NDWI values
        """
        ndwi = (nir - swir) / (nir + swir + 1e-8)
        return np.clip(ndwi, -1, 1)
    
    def calculate_all_indices(
        self,
        data: np.ndarray,
        band_mapping: Dict[str, int]
    ) -> Dict[str, np.ndarray]:
        """
        Calculate all vegetation indices
        
        Args:
            data: (H, W, C) - Spectral data
            band_mapping: Dictionary mapping band names to indices
            
        Returns:
            Dictionary of index maps
        """
        indices = {}
        
        if 'nir' in band_mapping and 'red' in band_mapping:
            nir = data[:, :, band_mapping['nir']]
            red = data[:, :, band_mapping['red']]
            indices['ndvi'] = self.calculate_ndvi(nir, red)
        
        if 'nir' in band_mapping and 'red' in band_mapping and 'blue' in band_mapping:
            nir = data[:, :, band_mapping['nir']]
            red = data[:, :, band_mapping['red']]
            blue = data[:, :, band_mapping['blue']]
            indices['evi'] = self.calculate_evi(nir, red, blue)
        
        if 'nir' in band_mapping and 'red' in band_mapping:
            nir = data[:, :, band_mapping['nir']]
            red = data[:, :, band_mapping['red']]
            indices['savi'] = self.calculate_savi(nir, red)
        
        if 'nir' in band_mapping and ('swir' in band_mapping or 'swir1' in band_mapping):
            nir = data[:, :, band_mapping['nir']]
            swir_idx = band_mapping.get('swir', band_mapping.get('swir1'))
            if swir_idx is not None:
                swir = data[:, :, swir_idx]
                indices['ndwi'] = self.calculate_ndwi(nir, swir)
        
        return indices


if __name__ == "__main__":
    print("Testing Spectral Library Matching...")
    
    # Create library
    library = SpectralLibrary()
    matcher = SpectralMatcher(library)
    
    # Test matching
    test_spectrum = np.array([0.1, 0.15, 0.45, 0.85, 0.65, 0.35, 0.25, 0.15])
    matches = matcher.match(test_spectrum, method='euclidean')
    
    print("Top matches:")
    for match in matches:
        print(f"  {match['material']}: {match['score']:.4f} - {match['description']}")
    
    # Test vegetation indices
    vi_calc = VegetationIndexCalculator()
    
    # Create dummy data
    H, W = 100, 100
    nir = np.random.rand(H, W) * 0.8 + 0.1
    red = np.random.rand(H, W) * 0.4 + 0.05
    blue = np.random.rand(H, W) * 0.3 + 0.05
    swir = np.random.rand(H, W) * 0.2 + 0.05
    
    ndvi = vi_calc.calculate_ndvi(nir, red)
    evi = vi_calc.calculate_evi(nir, red, blue)
    savi = vi_calc.calculate_savi(nir, red)
    ndwi = vi_calc.calculate_ndwi(nir, swir)
    
    print(f"NDVI range: [{ndvi.min():.4f}, {ndvi.max():.4f}]")
    print(f"EVI range: [{evi.min():.4f}, {evi.max():.4f}]")
    print(f"SAVI range: [{savi.min():.4f}, {savi.max():.4f}]")
    print(f"NDWI range: [{ndwi.min():.4f}, {ndwi.max():.4f}]")
    
    print("Spectral library matching test complete!")
