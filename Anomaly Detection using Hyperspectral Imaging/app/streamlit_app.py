"""
Streamlit Application
Web UI for AI-Powered Geospatial Anomaly Detection.
"""

import streamlit as st
import numpy as np
import cv2
from PIL import Image
import os
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data_loader import SatelliteDataLoader
from src.preprocess import SpectralPreprocessor
from src.models.isolation_forest import IsolationForestAnomalyDetector
from src.models.autoencoder import AutoencoderAnomalyDetector
from src.fusion import ScoreFusion
from src.utils import Visualizer


# Page configuration
st.set_page_config(
    page_title="AI-Powered Geospatial Anomaly Detection",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .sub-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #2c3e50;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    .info-box {
        background-color: #e8f4f8;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .success-box {
        background-color: #d4edda;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)


def run_detection(lat, lon, use_gee, n_components, encoding_dim):
    """
    Run the complete anomaly detection pipeline.
    
    Args:
        lat: Latitude
        lon: Longitude
        use_gee: Whether to use Google Earth Engine
        n_components: Number of PCA components
        encoding_dim: Autoencoder encoding dimension
        
    Returns:
        Dictionary containing results
    """
    # Initialize components
    loader = SatelliteDataLoader()
    preprocessor = SpectralPreprocessor(n_components=n_components)
    iso_detector = IsolationForestAnomalyDetector(contamination=0.1)
    fusion = ScoreFusion(isolation_weight=0.5, autoencoder_weight=0.5)
    viz = Visualizer()
    
    # Load data
    if use_gee:
        data, source = loader.load_data(lat=lat, lon=lon, use_gee=True)
    else:
        data, source = loader.load_data(use_gee=False)
    
    # Preprocess
    features, rgb = preprocessor.preprocess(data, fit_pca=False)
    original_shape = data.shape[:2]
    
    # Isolation Forest
    iso_detector.fit(features, original_shape)
    iso_scores, iso_binary, iso_threshold = iso_detector.detect_anomalies(
        features, original_shape
    )
    
    # Autoencoder
    input_dim = features.shape[1]
    ae_detector = AutoencoderAnomalyDetector(
        input_dim=input_dim,
        encoding_dim=encoding_dim,
        epochs=50,
        batch_size=32
    )
    
    # Try to load pre-trained model
    ae_path = "data/autoencoder_model.pth"
    if os.path.exists(ae_path):
        try:
            ae_detector.load_model(ae_path)
            ae_scores, ae_binary, ae_threshold = ae_detector.detect_anomalies(
                features, original_shape, train=False
            )
        except:
            ae_detector.train(features, original_shape=original_shape, verbose=False)
            ae_scores, ae_binary, ae_threshold = ae_detector.detect_anomalies(
                features, original_shape, train=False
            )
    else:
        ae_detector.train(features, original_shape=original_shape, verbose=False)
        ae_scores, ae_binary, ae_threshold = ae_detector.detect_anomalies(
            features, original_shape, train=False
        )
    
    # Fuse scores
    fused_scores, fused_binary, fused_threshold = fusion.fuse_and_optimize(
        iso_scores, ae_scores
    )
    
    # Create overlay
    overlay = fusion.create_overlay(rgb, fused_binary, alpha=0.5, color=(0, 0, 255))
    
    # Create heatmap
    heatmap = fusion.create_heatmap(fused_scores)
    
    return {
        'data_source': source,
        'rgb': rgb,
        'iso_scores': iso_scores,
        'ae_scores': ae_scores,
        'fused_scores': fused_scores,
        'binary_mask': fused_binary,
        'overlay': overlay,
        'heatmap': heatmap,
        'threshold': fused_threshold,
        'iso_threshold': iso_threshold,
        'ae_threshold': ae_threshold
    }


def main():
    """Main Streamlit application."""
    
    # Header
    st.markdown('<div class="main-header">🛰️ AI-Powered Geospatial Anomaly Detection</div>', 
                unsafe_allow_html=True)
    
    st.markdown("""
    <div class="info-box">
    <b>System Overview:</b> This system uses multi-spectral satellite data to detect camouflaged objects 
    through anomaly detection. We approximate hyperspectral analysis using Sentinel-2 multispectral data 
    based on user-provided coordinates.
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    st.sidebar.header("Configuration")
    
    # Input coordinates
    st.sidebar.subheader("Location")
    lat = st.sidebar.number_input("Latitude", value=40.7128, min_value=-90.0, max_value=90.0, 
                                   format="%.6f", help="Enter latitude (-90 to 90)")
    lon = st.sidebar.number_input("Longitude", value=-74.0060, min_value=-180.0, max_value=180.0, 
                                   format="%.6f", help="Enter longitude (-180 to 180)")
    
    # Model parameters
    st.sidebar.subheader("Model Parameters")
    use_gee = st.sidebar.checkbox("Use Google Earth Engine", value=True, 
                                  help="Uncheck to use fallback dataset")
    n_components = st.sidebar.slider("PCA Components", min_value=5, max_value=20, value=10, 
                                      help="Number of PCA components for dimensionality reduction")
    encoding_dim = st.sidebar.slider("Autoencoder Encoding Dim", min_value=4, max_value=16, value=8, 
                                      help="Dimension of autoencoder latent space")
    
    # Run button
    run_button = st.sidebar.button("🚀 Run Detection", type="primary")
    
    # Information section
    st.sidebar.markdown("---")
    st.sidebar.subheader("About")
    st.sidebar.info("""
    **Beginner Model:** PCA + Isolation Forest
    
    **Advanced Model:** PyTorch Autoencoder
    
    **Fusion:** Weighted sum with adaptive thresholding
    """)
    
    # Main content
    if run_button:
        st.markdown('<div class="sub-header">Detection Results</div>', unsafe_allow_html=True)
        
        # Progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # Step 1: Loading data
            status_text.text("Loading spectral data...")
            progress_bar.progress(20)
            
            # Step 2: Preprocessing
            status_text.text("Preprocessing data...")
            progress_bar.progress(40)
            
            # Step 3: Running models
            status_text.text("Running anomaly detection models...")
            progress_bar.progress(60)
            
            # Step 4: Fusion
            status_text.text("Fusing anomaly scores...")
            progress_bar.progress(80)
            
            # Run detection
            results = run_detection(lat, lon, use_gee, n_components, encoding_dim)
            
            progress_bar.progress(100)
            status_text.text("Complete!")
            
            # Display results
            st.markdown('<div class="success-box">✅ Anomaly detection completed successfully!</div>', 
                       unsafe_allow_html=True)
            
            # Data source info
            st.info(f"**Data Source:** {results['data_source']}")
            
            # Statistics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Isolation Forest Anomalies", 
                         f"{results['iso_scores'][results['binary_mask'] == 1].sum():.2f}",
                         f"Threshold: {results['iso_threshold']:.4f}")
            with col2:
                st.metric("Autoencoder Anomalies", 
                         f"{results['ae_scores'][results['binary_mask'] == 1].sum():.2f}",
                         f"Threshold: {results['ae_threshold']:.4f}")
            with col3:
                st.metric("Fused Anomalies", 
                         f"{results['fused_scores'][results['binary_mask'] == 1].sum():.2f}",
                         f"Threshold: {results['threshold']:.4f}")
            
            # Visualizations
            st.markdown('<div class="sub-header">Visualizations</div>', unsafe_allow_html=True)
            
            # Row 1: RGB and Heatmap
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("RGB Composite")
                st.image(results['rgb'], use_column_width=True, caption="Satellite RGB Composite")
            
            with col2:
                st.subheader("Anomaly Heatmap")
                st.image(results['heatmap'], use_column_width=True, 
                        caption="Anomaly Score Heatmap")
            
            # Row 2: Individual model scores
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Isolation Forest Scores")
                iso_heatmap = cv2.applyColorMap(
                    ((results['iso_scores'] - results['iso_scores'].min()) / 
                     (results['iso_scores'].max() - results['iso_scores'].min() + 1e-8) * 255).astype(np.uint8),
                    cv2.COLORMAP_JET
                )
                st.image(iso_heatmap, use_column_width=True, 
                        caption="Isolation Forest Anomaly Scores")
            
            with col2:
                st.subheader("Autoencoder Scores")
                ae_heatmap = cv2.applyColorMap(
                    ((results['ae_scores'] - results['ae_scores'].min()) / 
                     (results['ae_scores'].max() - results['ae_scores'].min() + 1e-8) * 255).astype(np.uint8),
                    cv2.COLORMAP_JET
                )
                st.image(ae_heatmap, use_column_width=True, 
                        caption="Autoencoder Anomaly Scores")
            
            # Row 3: Binary mask and overlay
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Binary Anomaly Mask")
                st.image(results['binary_mask'], use_column_width=True, 
                        caption="Binary Anomaly Mask (White = Anomaly)")
            
            with col2:
                st.subheader("Anomaly Overlay")
                st.image(results['overlay'], use_column_width=True, 
                        caption="Anomalies Overlaid on RGB Image")
            
            # Download buttons
            st.markdown('<div class="sub-header">Download Results</div>', unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # Convert overlay to PIL Image
                overlay_pil = Image.fromarray(cv2.cvtColor(results['overlay'], cv2.COLOR_BGR2RGB))
                st.download_button(
                    label="Download Overlay",
                    data=overlay_pil.tobytes(),
                    file_name="anomaly_overlay.png",
                    mime="image/png"
                )
            
            with col2:
                # Convert heatmap to PIL Image
                heatmap_pil = Image.fromarray(cv2.cvtColor(results['heatmap'], cv2.COLOR_BGR2RGB))
                st.download_button(
                    label="Download Heatmap",
                    data=heatmap_pil.tobytes(),
                    file_name="anomaly_heatmap.png",
                    mime="image/png"
                )
            
            with col3:
                # Convert binary mask to PIL Image
                binary_pil = Image.fromarray((results['binary_mask'] * 255).astype(np.uint8))
                st.download_button(
                    label="Download Binary Mask",
                    data=binary_pil.tobytes(),
                    file_name="binary_mask.png",
                    mime="image/png"
                )
            
        except Exception as e:
            st.error(f"Error during detection: {str(e)}")
            st.markdown("""
            <div class="info-box">
            <b>Troubleshooting:</b>
            - If Google Earth Engine fails, try unchecking "Use Google Earth Engine"
            - Ensure you have authenticated with GEE using: earthengine authenticate
            - Check your internet connection
            </div>
            """, unsafe_allow_html=True)
    
    else:
        # Default state - show instructions
        st.markdown('<div class="sub-header">Getting Started</div>', unsafe_allow_html=True)
        
        st.markdown("""
        ### How to Use
        
        1. **Enter Coordinates**: Input the latitude and longitude of your area of interest in the sidebar.
        
        2. **Configure Parameters**: Adjust model parameters as needed:
           - Use Google Earth Engine: Toggle to use real satellite data or fallback dataset
           - PCA Components: Number of principal components for dimensionality reduction
           - Autoencoder Encoding Dim: Latent space dimension for the autoencoder
        
        3. **Run Detection**: Click the "Run Detection" button to start the analysis.
        
        4. **View Results**: The system will display:
           - RGB composite image
           - Anomaly heatmap
           - Individual model scores
           - Binary anomaly mask
           - Anomaly overlay on the satellite image
        
        5. **Download Results**: Download any of the visualizations for further analysis.
        
        ### Technical Details
        
        **Data Pipeline:**
        - Fetches Sentinel-2 multispectral data from Google Earth Engine
        - Selects bands: B2 (Blue), B3 (Green), B4 (Red), B8 (NIR), B11 (SWIR1), B12 (SWIR2)
        - Falls back to synthetic hyperspectral dataset if GEE is unavailable
        
        **Preprocessing:**
        - Min-max normalization
        - Gaussian noise reduction
        - PCA dimensionality reduction
        
        **Models:**
        - **Beginner**: PCA + Isolation Forest (fast, interpretable)
        - **Advanced**: PyTorch Autoencoder (deep learning approach)
        
        **Fusion:**
        - Weighted sum of both model outputs
        - Adaptive thresholding (mean + std)
        - Median filtering for noise reduction
        - False positive reduction using connected components
        """)
        
        # Example coordinates
        st.markdown("""
        ### Example Coordinates
        
        Try these interesting locations:
        - New York City: 40.7128, -74.0060
        - San Francisco: 37.7749, -122.4194
        - London: 51.5074, -0.1278
        - Tokyo: 35.6762, 139.6503
        - Sydney: -33.8688, 151.2093
        """)


if __name__ == "__main__":
    main()
