# AI-Powered Geospatial Anomaly Detection using Spectral Data for Camouflaged Object Detection

## � World-Class Features

This project now includes **cutting-edge features** making it one of the most comprehensive anomaly detection platforms:

### 🤖 Advanced AI/ML Models
- **Vision Transformer (ViT)** - State-of-the-art spatial-spectral analysis
- **Isolation Forest** - Fast, interpretable baseline model
- **Autoencoder** - Deep learning reconstruction-based detection
- **Ensemble Stacking** - Combines multiple models for improved accuracy
- **Confidence Intervals** - Bootstrap-based uncertainty estimation

### 🔍 Model Explainability
- **SHAP Values** - Feature importance analysis
- **Grad-CAM** - Visual attention maps
- **Attention Visualization** - Transformer attention analysis
- **Feature Importance** - Permutation-based importance

### 📡 Multi-Satellite Support
- **Sentinel-2** - Optical multispectral data
- **Sentinel-1** - SAR radar data
- **Landsat 8/9** - Additional spectral bands
- **MODIS** - Daily temporal data
- **Data Fusion** - Combine multiple satellite sources
- **Cloud Masking** - Automatic cloud detection and removal
- **Atmospheric Correction** - Dark object subtraction

### ⏱️ Temporal Analysis
- **Change Detection** - Detect changes over time
- **Trend Analysis** - Identify gradual changes
- **Seasonal Patterns** - Detect seasonal variations
- **Event Detection** - Identify sudden anomalies
- **Time-Series Forecasting** - Predict future values

### 🗺️ Advanced Visualization
- **3D Interactive Globe** - Click to select coordinates
- **3D Terrain View** - CesiumJS immersive 3D maps
- **Spectral Curve Plotting** - Interactive spectral signatures
- **Heatmap Animations** - Time-lapse visualizations
- **Custom ROI Drawing** - Draw regions of interest

### 🎯 Material Identification
- **Spectral Library Matching** - Match signatures to materials
- **Vegetation Indices** - NDVI, EVI, SAVI, NDWI
- **Spectral Unmixing** - Linear unmixing for material abundance
- **Material Classification** - Identify surface materials

### 📊 Spatial Analysis
- **DBSCAN Clustering** - Group anomalies spatially
- **HDBSCAN Clustering** - Hierarchical density-based clustering
- **Shape Analysis** - Analyze cluster shapes
- **Linear Pattern Detection** - Identify linear arrangements
- **Spatial Distribution** - Analyze anomaly distribution

### 📄 Reporting & Export
- **Automated PDF Reports** - Comprehensive analysis reports
- **CSV Export** - Tabular data export
- **JSON Export** - Structured data export
- **GeoTIFF Export** - Geospatial data export

### ⚡ Performance
- **GPU Acceleration** - CUDA support for faster inference
- **Batch Processing** - Process multiple locations
- **Model Quantization** - INT8 quantization for deployment
- **TorchScript Compilation** - Optimized model serving

### 🏗️ Infrastructure
- **Docker Support** - Containerized deployment
- **Kubernetes** - Cloud-native orchestration
- **PostgreSQL** - Persistent database storage
- **Redis** - Caching layer
- **Celery** - Async task processing
- **Flower** - Task monitoring

### 🔐 Enterprise Features
- **Authentication** - Token-based auth
- **Role-Based Access** - Admin, user, viewer roles
- **Audit Logging** - Track all actions
- **API Rate Limiting** - Protect against abuse
- **Webhook Notifications** - Event-driven alerts
- **Scheduled Analysis** - Automated periodic analysis

### 🌐 Frontend
- **Real-time WebSocket** - Live progress updates
- **Dark/Light Mode** - Theme switching
- **PWA Support** - Install as mobile app
- **Responsive Design** - Mobile-friendly
- **Glassmorphism UI** - Modern design
- **Advanced Animations** - Smooth transitions

## � Problem Explanation

### Why RGB Imaging Fails for Camouflaged Detection

RGB imaging captures only three spectral bands (Red, Green, Blue) in the visible spectrum (400-700 nm). Camouflaged objects are specifically designed to match the visual appearance of their surroundings in the visible spectrum. This makes them nearly indistinguishable from the background in RGB images, as camouflage patterns exploit the limitations of human vision and standard RGB sensors.

### What Are Spectral Signatures?

Spectral signatures are the unique patterns of reflectance, absorption, and emission of electromagnetic radiation across different wavelengths for specific materials. Every material (soil, vegetation, metal, fabric, etc.) has a distinct spectral signature that acts like a fingerprint. Even if two materials look similar in RGB, they often have different spectral responses in non-visible wavelengths (near-infrared, short-wave infrared, etc.).

### Hyperspectral vs Multispectral

**Multispectral Imaging:**
- Captures data in 3-15 discrete spectral bands
- Wider bandwidth per band
- Examples: Sentinel-2 (13 bands), Landsat (11 bands)
- Lower spatial and spectral resolution
- More common and accessible

**Hyperspectral Imaging:**
- Captures data in hundreds of contiguous narrow spectral bands
- Narrow bandwidth (typically 5-10 nm)
- Provides detailed spectral information
- Higher data volume and complexity
- Less common, more expensive

### Why Anomaly Detection is Needed (Unsupervised)

Anomaly detection is crucial because:
1. **No labeled data**: Real-world camouflaged objects are rare and difficult to collect
2. **Unknown patterns**: Camouflage techniques evolve constantly
3. **Scalability**: Unsupervised methods can detect novel anomalies without retraining
4. **Generalization**: Works across different terrains and environments

## 🔷 Project Positioning

**We approximate hyperspectral analysis using multispectral satellite data (Sentinel-2) based on user-provided coordinates.**

While true hyperspectral sensors capture hundreds of bands, Sentinel-2 provides 13 carefully selected bands spanning visible, near-infrared, and short-wave infrared spectra. This allows us to extract meaningful spectral features for anomaly detection, effectively simulating hyperspectral analysis with freely available satellite data.

## 🔷 Project Structure

```
project/
│
├── data/                          # Data storage
│
├── src/                           # Source code
│   ├── data_loader.py            # GEE data fetching + fallback
│   ├── preprocess.py             # Normalization, PCA, noise reduction
│   ├── models/
│   │   ├── isolation_forest.py   # Beginner model (PCA + Isolation Forest)
│   │   ├── autoencoder.py        # Advanced model (PyTorch Autoencoder)
│   │   └── vit_anomaly.py        # Vision Transformer for spatial-spectral analysis
│   ├── fusion.py                 # Score fusion and optimization
│   ├── explainability.py        # SHAP, Grad-CAM, model explanations
│   ├── temporal_analysis.py      # Time-series change detection
│   ├── multi_satellite.py        # Multi-satellite data fusion
│   ├── spectral_library.py      # Material identification & vegetation indices
│   ├── report_generator.py       # PDF reports & data export
│   ├── gpu_accelerator.py        # GPU acceleration support
│   ├── spatial_clustering.py     # DBSCAN, HDBSCAN clustering
│   ├── ensemble.py               # Ensemble model stacking
│   └── utils.py                  # Visualization helpers
│
├── app/
│   └── streamlit_app.py          # Streamlit UI
│
├── backend/
│   ├── api.py                    # FastAPI REST API backend (basic)
│   ├── api_advanced.py           # Advanced API with WebSocket, Auth, Caching
│   └── database.py              # PostgreSQL database integration
│
├── frontend/
│   ├── index.html                # Basic HTML frontend
│   ├── styles.css                # Basic CSS styles
│   ├── app.js                    # Basic JavaScript logic
│   ├── index_advanced.html       # Advanced HTML frontend
│   ├── styles_advanced.css       # Advanced CSS with dark mode
│   ├── app_advanced.js           # Advanced JS with 3D globe, WebSocket, Cesium
│   └── manifest.json             # PWA manifest for mobile app
│
├── train.py                       # Autoencoder training script
├── infer.py                       # Inference pipeline
├── requirements.txt               # Python dependencies
├── Dockerfile                     # Docker containerization
├── docker-compose.yml             # Docker Compose orchestration
├── k8s-deployment.yaml           # Kubernetes deployment configs
└── README.md                      # This file
```

## 🔷 Installation

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Authenticate Google Earth Engine

```bash
earthengine authenticate
```

Follow the instructions to authenticate with your Google account.

**Note**: If you don't have GEE access, the system will automatically fall back to the Indian Pines hyperspectral dataset.

## 🔷 Usage

### Training the Autoencoder

```bash
python train.py
```

This will:
- Load training data (either from GEE or fallback dataset)
- Train the autoencoder model
- Save the trained model to `data/autoencoder_model.pth`

### Running Inference

```bash
python infer.py --lat 40.7128 --lon -74.0060
```

Replace the latitude and longitude with your desired location.

### Running the Streamlit App

```bash
streamlit run app/streamlit_app.py
```

This will launch the web interface where you can:
- Enter latitude and longitude
- Click "Run Detection"
- View satellite image, heatmap, and final overlay

### Running the FastAPI Backend + Frontend

**Option 1: Run Backend Only (for API access)**

```bash
python backend/api.py
```

The API will be available at `http://localhost:8000`
- Interactive API documentation: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health`

**Option 2: Run Backend + Frontend (Full Web Application)**

Terminal 1 - Start the backend:
```bash
python backend/api.py
```

Terminal 2 - Serve the frontend:
```bash
# Using Python's built-in server
cd frontend
python -m http.server 3000
```

Then open your browser to: `http://localhost:3000`

**API Endpoints:**
- `POST /detect` - Run anomaly detection
- `GET /image/{type}` - Get detection result images (rgb, heatmap, overlay, iso_scores, ae_scores, binary)
- `GET /stats` - Get detection statistics
- `GET /health` - Health check

### Running the Advanced Interface (Premium Features)

The advanced interface includes cutting-edge features:
- **3D Interactive Globe** - Click to select coordinates on a 3D Earth
- **Real-time WebSocket Updates** - Live progress tracking
- **Dark/Light Mode** - Smooth theme transitions
- **Advanced Analytics** - Charts and statistical visualizations
- **Image Comparison Slider** - Before/after comparison
- **Authentication System** - Role-based access control
- **Response Caching** - Faster repeated queries
- **Batch Processing** - Process multiple locations
- **PWA Support** - Install as mobile app

**Terminal 1 - Start Advanced Backend:**
```bash
python backend/api_advanced.py
```

**Terminal 2 - Serve Advanced Frontend:**
```bash
cd frontend
python -m http.server 3000
```

Then open your browser to: `http://localhost:3000/index_advanced.html`

**Advanced API Endpoints:**
- `POST /auth/login` - Authenticate (demo: admin/admin123 or user/user123)
- `POST /detect` - Run detection with real-time progress
- `POST /batch` - Batch processing (admin only)
- `GET /image/{type}` - Get detection images
- `GET /stats` - Get detailed statistics with spectral analysis
- `DELETE /cache` - Clear cache (admin only)
- `WS /ws` - WebSocket for real-time updates

## 🔷 Technical Details

### Data Pipeline

1. **Input**: Latitude, longitude coordinates
2. **Fetch**: Sentinel-2 data via Google Earth Engine
3. **Bands**: B2 (Blue), B3 (Green), B4 (Red), B8 (NIR), B11 (SWIR1), B12 (SWIR2)
4. **Fallback**: Indian Pines hyperspectral dataset if GEE fails

### Preprocessing

- Min-max normalization
- Gaussian noise reduction (OpenCV)
- Reshape: (H, W, Bands) → (Pixels × Bands)
- PCA: Reduce to 5-15 components

### Models

**Beginner Model (PCA + Isolation Forest):**
- Fast, interpretable
- No training required
- Good baseline

**Advanced Model (Autoencoder):**
- Deep learning approach
- Learns compressed representation
- Reconstruction error as anomaly score

### Score Fusion

- Normalize both model outputs
- Weighted sum combination
- Adaptive thresholding (mean + std)
- Median filtering for noise reduction

## 🔷 Output Visualizations

1. RGB composite from spectral bands
2. PCA visualization
3. Isolation Forest anomaly map
4. Autoencoder reconstruction error map
5. Final fused anomaly map with overlay

## 🔷 Hackathon Optimization

- **Fast execution**: Optimized for quick inference
- **Robust fallback**: Works even if GEE fails
- **Modular design**: Easy to modify and extend
- **Beginner-friendly**: Clear code structure with comments
- **Error handling**: Graceful degradation on failures

## 🔷 Dependencies

- Python 3.8+
- PyTorch
- NumPy
- OpenCV
- scikit-learn
- matplotlib
- streamlit
- geemap
- earthengine-api
- tensorflow (for Indian Pines dataset)
- FastAPI (for REST API backend)
- uvicorn (for FastAPI server)

## 🔷 License

MIT License - Feel free to use and modify for your projects.

## 🔷 Acknowledgments

- Google Earth Engine for satellite data access
- Sentinel-2 mission by ESA
- Indian Pines dataset from Purdue University
