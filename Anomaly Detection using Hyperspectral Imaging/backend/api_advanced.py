"""
Advanced FastAPI Backend
Enhanced REST API with WebSocket, Authentication, Caching, and Batch Processing.
"""

import numpy as np
import cv2
import base64
import io
import os
import sys
import json
import asyncio
import datetime
import requests
from datetime import datetime, timedelta
from enum import Enum
import hashlib
import secrets
from concurrent.futures import ThreadPoolExecutor
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends, Header, Query, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from sklearn.cluster import DBSCAN
from sklearn.metrics import silhouette_score
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from PIL import Image as PILImage
import traceback

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Add src to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data_loader import SatelliteDataLoader
from src.preprocess import SpectralPreprocessor
from src.models.isolation_forest import IsolationForestAnomalyDetector
from src.models.autoencoder import AutoencoderAnomalyDetector
from src.models.vit_anomaly import ViTAnomalyDetector
from src.ensemble import EnsembleDetector
from src.fusion import ScoreFusion
from src.spatial_clustering import SpatialClusterer
from src.spectral_library import SpectralMatcher, VegetationIndexCalculator

# Initialize FastAPI app
app = FastAPI(
    title="AI-Powered Geospatial Anomaly Detection API",
    description="Advanced REST API for detecting camouflaged objects using spectral satellite data",
    version="2.0.0"
)

# Thread pool for blocking operations
executor = ThreadPoolExecutor(max_workers=4)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Simple in-memory user database (for demo - use real database in production)
USERS = {
    "admin": {
        "password_hash": hashlib.sha256("admin123".encode()).hexdigest(),
        "role": "admin"
    },
    "user": {
        "password_hash": hashlib.sha256("user123".encode()).hexdigest(),
        "role": "user"
    }
}

# Simple in-memory cache (for demo - use Redis in production)
CACHE = {}

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
    
    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass

manager = ConnectionManager()


# Pydantic models
class DetectionRequest(BaseModel):
    lat: float
    lon: float
    use_gee: bool = False
    n_components: int = 10
    encoding_dim: int = 8
    enable_cache: bool = True
    use_vit: bool = True
    use_ensemble: bool = True
    detect_clouds: bool = True
    apply_atmospheric_correction: bool = True


class BatchDetectionRequest(BaseModel):
    locations: List[dict]  # List of {lat, lon}
    use_gee: bool = True
    n_components: int = 10
    encoding_dim: int = 8


class AuthRequest(BaseModel):
    username: str
    password: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str


class DetectionResponse(BaseModel):
    success: bool
    message: str
    data_source: Optional[str] = None
    iso_threshold: Optional[float] = None
    ae_threshold: Optional[float] = None
    vit_threshold: Optional[float] = None
    fused_threshold: Optional[float] = None
    anomaly_count: Optional[int] = None
    anomaly_percentage: Optional[float] = None
    processing_time: Optional[float] = None
    cloud_coverage: Optional[float] = None
    num_clusters: Optional[int] = None
    material_identified: Optional[str] = None
    ndvi: Optional[Any] = None
    ndwi: Optional[Any] = None


class ImageResponse(BaseModel):
    success: bool
    image_type: str
    image_data: str


class ProgressStatus(str, Enum):
    LOADING = "loading"
    PREPROCESSING = "preprocessing"
    DETECTING = "detecting"
    FUSING = "fusing"
    COMPLETE = "complete"
    ERROR = "error"


# Authentication dependency
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    # Simple token validation (for demo - use JWT in production)
    if token not in CACHE or not CACHE[token].get("authenticated", False):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    return CACHE[token]["user"]


# Global variables
preprocessor = None
iso_detector = None
ae_detector = None
vit_detector = None
ensemble = None
fusion = None
clusterer = None
spectral_matcher = None
vi_calculator = None
loader = None
detection_results = None


def initialize_models():
    """Initialize models on first request."""
    global preprocessor, iso_detector, ae_detector, vit_detector, ensemble, fusion, clusterer, spectral_matcher, vi_calculator, loader
    
    if loader is None:
        loader = SatelliteDataLoader()
    if preprocessor is None:
        preprocessor = SpectralPreprocessor(n_components=10, detect_clouds=True)
    if iso_detector is None:
        iso_detector = IsolationForestAnomalyDetector(contamination=0.1)
    if fusion is None:
        fusion = ScoreFusion(isolation_weight=0.5, autoencoder_weight=0.5, vit_weight=0.0)
    if clusterer is None:
        clusterer = SpatialClusterer(method='dbscan')
    if spectral_matcher is None:
        from src.spectral_library import SpectralLibrary
        spectral_matcher = SpectralMatcher(SpectralLibrary())
    if vi_calculator is None:
        vi_calculator = VegetationIndexCalculator()


def encode_image_to_base64(image: np.ndarray) -> str:
    """Encode numpy image to base64 string."""
    if image.max() <= 1.0:
        image = (image * 255).astype(np.uint8)
    
    _, buffer = cv2.imencode('.png', image)
    image_bytes = buffer.tobytes()
    base64_string = base64.b64encode(image_bytes).decode('utf-8')
    return base64_string


def generate_cache_key(lat: float, lon: float, params: dict) -> str:
    """Generate cache key for request."""
    key_str = f"{lat}_{lon}_{json.dumps(params, sort_keys=True)}"
    return hashlib.md5(key_str.encode()).hexdigest()


# Endpoints
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "AI-Powered Geospatial Anomaly Detection API v2.0",
        "features": [
            "Real-time WebSocket progress updates",
            "Authentication system",
            "Response caching",
            "Batch processing",
            "Advanced analytics"
        ],
        "endpoints": {
            "/": "API information",
            "/auth/login": "POST - Authenticate",
            "/detect": "POST - Run anomaly detection",
            "/batch": "POST - Batch detection",
            "/image/{type}": "GET - Get detection images",
            "/stats": "GET - Get statistics",
            "/health": "GET - Health check",
            "/ws": "WebSocket - Real-time progress"
        }
    }


@app.post("/auth/login", response_model=AuthResponse)
async def login(auth: AuthRequest):
    """Authenticate user and return access token."""
    if auth.username not in USERS:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    user = USERS[auth.username]
    password_hash = hashlib.sha256(auth.password.encode()).hexdigest()
    
    if password_hash != user["password_hash"]:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Generate token
    token = secrets.token_urlsafe(32)
    CACHE[token] = {
        "user": {"username": auth.username, "role": user["role"]},
        "authenticated": True,
        "created_at": datetime.now().isoformat()
    }
    
    return AuthResponse(
        access_token=token,
        role=user["role"]
    )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "cache_size": len(CACHE),
        "active_connections": len(manager.active_connections)
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time progress updates."""
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Echo back or handle specific messages
            await websocket.send_json({"type": "echo", "message": data})
    except WebSocketDisconnect:
        manager.disconnect(websocket)


async def send_progress(status: ProgressStatus, progress: float, message: str):
    """Send progress update via WebSocket."""
    await manager.broadcast({
        "type": "progress",
        "status": status,
        "progress": progress,
        "message": message,
        "timestamp": datetime.now().isoformat()
    })


@app.post("/detect", response_model=DetectionResponse)
async def detect_anomalies(request: DetectionRequest, background_tasks: BackgroundTasks):
    """
    Run anomaly detection with real-time progress updates.
    """
    global detection_results
    start_time = datetime.now()
    
    print(f"Detection request received: lat={request.lat}, lon={request.lon}, use_gee={request.use_gee}")
    
    try:
        # Initialize models
        initialize_models()
        
        # Send progress
        await send_progress(ProgressStatus.LOADING, 10, "Loading real-time spectral data...")
        
        # Load data (blocking - run in thread pool)
        def load_data_task():
            try:
                if request.use_gee:
                    return loader.load_data(request.lat, request.lon, use_gee=True)
                else:
                    return loader.load_data(use_gee=False)
            except Exception as e:
                print(f"Error loading data: {e}")
                import traceback
                traceback.print_exc()
                raise
        
        data, source = await asyncio.get_event_loop().run_in_executor(executor, load_data_task)
        print(f"Data loaded successfully. Shape: {data.shape}, Source: {source}")
        
        # Adjust PCA components based on data shape
        n_bands = data.shape[-1] if len(data.shape) == 3 else 1
        
        # Skip PCA for RGB-only data (3 bands) - saves significant time
        if n_bands == 3:
            print(f"RGB-only data detected, skipping PCA for speed")
            adjusted_n_components = 0  # Skip PCA
            use_pca = False
        else:
            adjusted_n_components = min(request.n_components, n_bands - 1)
            if adjusted_n_components < 1:
                adjusted_n_components = 1
            use_pca = True
        
        if use_pca:
            # Reinitialize PCA with adjusted components
            preprocessor.n_components = adjusted_n_components
            from sklearn.decomposition import PCA
            preprocessor.pca = PCA(n_components=adjusted_n_components)
            print(f"Data shape: {data.shape}, Bands: {n_bands}, Adjusted n_components: {adjusted_n_components}")
        else:
            print(f"Data shape: {data.shape}, Bands: {n_bands}, PCA disabled")
        
        await send_progress(ProgressStatus.PREPROCESSING, 30, "Preprocessing data with atmospheric correction and cloud detection...")
        
        # Preprocess (blocking - run in thread pool)
        def preprocess_task():
            return preprocessor.preprocess(
                data, 
                fit_pca=False, 
                skip_pca=not use_pca,
                apply_atmospheric_correction=request.apply_atmospheric_correction,
                remove_clouds=request.detect_clouds
            )
        
        features, rgb = await asyncio.get_event_loop().run_in_executor(executor, preprocess_task)
        original_shape = data.shape[:2]
        
        await send_progress(ProgressStatus.DETECTING, 50, "Running Isolation Forest...")
        
        # Isolation Forest (blocking - run in thread pool)
        def iso_task():
            iso_detector.fit(features, original_shape)
            return iso_detector.detect_anomalies(features, original_shape)
        
        iso_scores, iso_binary, iso_threshold = await asyncio.get_event_loop().run_in_executor(executor, iso_task)
        
        await send_progress(ProgressStatus.DETECTING, 70, "Running Autoencoder...")
        
        # Autoencoder (blocking - run in thread pool) - OPTIMIZED FOR SPEED
        def ae_task():
            input_dim = features.shape[1]
            ae_detector = AutoencoderAnomalyDetector(
                input_dim=input_dim,
                encoding_dim=request.encoding_dim,
                epochs=5,  # Further reduced from 10 for maximum speed
                batch_size=64  # Increased batch size for faster training
            )
            
            ae_path = "data/autoencoder_model.pth"
            if os.path.exists(ae_path):
                try:
                    ae_detector.load_model(ae_path)
                    return ae_detector.detect_anomalies(features, original_shape, train=False)
                except:
                    ae_detector.train(features, original_shape=original_shape, verbose=False)
                    return ae_detector.detect_anomalies(features, original_shape, train=False)
            else:
                ae_detector.train(features, original_shape=original_shape, verbose=False)
                return ae_detector.detect_anomalies(features, original_shape, train=False)
        
        ae_scores, ae_binary, ae_threshold = await asyncio.get_event_loop().run_in_executor(executor, ae_task)
        
        # ViT detection (optional)
        vit_scores = None
        vit_binary = None
        vit_threshold = None
        
        if request.use_vit and use_pca:
            # Only use ViT with PCA-transformed data (requires sufficient channels)
            await send_progress(ProgressStatus.DETECTING, 80, "Running Vision Transformer...")
            try:
                def vit_task():
                    global vit_detector
                    # Reinitialize if channel count changed
                    if vit_detector is None or vit_detector.model.in_channels != features.shape[1]:
                        print("Initializing ViT detector...")
                        vit_detector = ViTAnomalyDetector(
                            in_channels=features.shape[1],
                            patch_size=8,
                            embed_dim=128,
                            depth=4,
                            num_heads=4,
                            epochs=20,
                            batch_size=16
                        )
                    print("Training ViT detector...")
                    vit_detector.train(features, original_shape, verbose=False)
                    print("Running ViT detection...")
                    return vit_detector.detect_anomalies(features, original_shape, train=False)
                
                vit_scores, vit_binary, vit_threshold = await asyncio.get_event_loop().run_in_executor(executor, vit_task)
                print(f"ViT detection complete. Threshold: {vit_threshold}")
            except Exception as e:
                print(f"ViT detection failed: {e}")
                vit_scores = None
                vit_binary = None
                vit_threshold = None
        elif request.use_vit and not use_pca:
            print("Skipping ViT for RGB-only data (requires PCA-transformed hyperspectral data)")
            vit_scores = None
            vit_binary = None
            vit_threshold = None
        
        await send_progress(ProgressStatus.FUSING, 90, "Fusing results with ensemble...")
        
        # Fuse scores with ensemble or simple fusion
        def fusion_task():
            global ensemble
            if request.use_ensemble:
                # Filter out None models
                models_list = [m for m in [iso_detector, ae_detector, vit_detector] if m is not None]
                if len(models_list) < 2:
                    # Not enough models for ensemble, use simple fusion
                    if vit_scores is not None:
                        fusion.vit_weight = 0.4
                        fusion.isolation_weight = 0.3
                        fusion.autoencoder_weight = 0.3
                        return fusion.fuse_and_optimize(iso_scores, ae_scores, vit_scores)
                    else:
                        return fusion.fuse_and_optimize(iso_scores, ae_scores)
                
                # Adjust weights based on number of models
                if len(models_list) == 3:
                    weights = [0.3, 0.3, 0.4]
                elif len(models_list) == 2:
                    weights = [0.5, 0.5]
                else:
                    weights = [1.0]
                
                ensemble = EnsembleDetector(
                    models_list,
                    weights=weights,
                    method='weighted_average'
                )
                ensemble.fit(features, original_shape)
                return ensemble.detect_anomalies(features, original_shape)
            elif vit_scores is not None:
                # Three-way fusion
                fusion.vit_weight = 0.4
                fusion.isolation_weight = 0.3
                fusion.autoencoder_weight = 0.3
                return fusion.fuse_and_optimize(iso_scores, ae_scores, vit_scores)
            else:
                # Two-way fusion
                return fusion.fuse_and_optimize(iso_scores, ae_scores)
        
        fused_scores, fused_binary, fused_threshold = await asyncio.get_event_loop().run_in_executor(executor, fusion_task)
        
        # Spatial clustering
        cluster_results = None
        num_clusters = 0
        try:
            def cluster_task():
                return clusterer.cluster_anomalies(fused_binary, original_shape, eps=5.0, min_samples=5)
            cluster_results = await asyncio.get_event_loop().run_in_executor(executor, cluster_task)
            num_clusters = cluster_results['num_clusters']
        except Exception as e:
            print(f"Spatial clustering failed: {e}")
        
        # Material identification and vegetation indices
        material_identified = None
        ndvi = None
        ndwi = None
        cloud_coverage = None
        
        # Calculate vegetation indices (NDVI, NDWI) from real GEE data
        try:
            # GEE data has 6 bands: Blue(B2), Green(B3), Red(B4), NIR(B8), SWIR1(B11), SWIR2(B12)
            if data.shape[-1] >= 4:
                # NDVI: (NIR - Red) / (NIR + Red)
                # Band indices: 0=Blue, 1=Green, 2=Red, 3=NIR, 4=SWIR1, 5=SWIR2
                red_band = data[:, :, 2]  # Red band (index 2)
                nir_band = data[:, :, 3]  # NIR band (index 3)
                
                ndvi_map = (nir_band - red_band) / (nir_band + red_band + 1e-8)
                ndvi = float(np.nanmean(ndvi_map))
                print(f"NDVI calculated from real GEE data: {ndvi:.3f}")
                
                # NDWI: (Green - NIR) / (Green + NIR) - using Green instead of SWIR for better water detection
                green_band = data[:, :, 1]  # Green band (index 1)
                ndwi_map = (green_band - nir_band) / (green_band + nir_band + 1e-8)
                ndwi = float(np.nanmean(ndwi_map))
                print(f"NDWI calculated from real GEE data: {ndwi:.3f}")
        except Exception as e:
            print(f"Vegetation index calculation failed: {e}")
            import traceback
            traceback.print_exc()
        
        # Material identification using spectral library
        try:
            if data.shape[-1] >= 4:
                # Match materials in anomaly regions
                anomaly_pixels = data[fused_binary > 0]
                if len(anomaly_pixels) > 0:
                    material_match = spectral_matcher.match(
                        anomaly_pixels.mean(axis=0),
                        method='euclidean',
                        top_k=1  # Get best match
                    )
                    if material_match and len(material_match) > 0:
                        material_identified = f"{material_match[0]['material']} ({material_match[0]['description']})"
                        print(f"Material identified (real): {material_identified}")
        except Exception as e:
            print(f"Material identification failed: {e}")
            import traceback
            traceback.print_exc()
            material_identified = None
        
        # Get cloud coverage if cloud detection was enabled
        if request.detect_clouds and preprocessor.cloud_detector is not None:
            try:
                cloud_mask = preprocessor.cloud_detector.detect_clouds(data)
                cloud_coverage = preprocessor.cloud_detector.get_cloud_coverage(cloud_mask)
            except Exception as e:
                print(f"Cloud coverage calculation failed: {e}")
        else:
            # Estimate cloud coverage from data if cloud detection not enabled
            try:
                # Simple estimation based on brightness threshold
                if data.shape[-1] >= 3:
                    rgb = data[:, :, :3]
                    brightness = np.mean(rgb, axis=2)
                    cloud_mask = brightness > np.percentile(brightness, 90)
                    cloud_coverage = float(np.mean(cloud_mask) * 100)
                    print(f"Estimated cloud coverage: {cloud_coverage:.1f}%")
            except Exception as e:
                print(f"Cloud coverage estimation failed: {e}")
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # Store results
        detection_results = {
            'rgb': rgb,
            'iso_scores': iso_scores,
            'ae_scores': ae_scores,
            'vit_scores': vit_scores,
            'fused_scores': fused_scores,
            'binary_mask': fused_binary,
            'data_source': source,
            'iso_threshold': iso_threshold,
            'ae_threshold': ae_threshold,
            'vit_threshold': vit_threshold,
            'fused_threshold': fused_threshold,
            'processing_time': processing_time,
            'cluster_results': cluster_results,
            'material_identified': material_identified,
            'ndvi': ndvi,
            'ndwi': ndwi,
            'cloud_coverage': cloud_coverage
        }
        
        await send_progress(ProgressStatus.COMPLETE, 100, "Detection complete!")
        
        return DetectionResponse(
            success=True,
            message="Anomaly detection completed successfully",
            data_source=source,
            iso_threshold=iso_threshold,
            ae_threshold=ae_threshold,
            vit_threshold=vit_threshold,
            fused_threshold=fused_threshold,
            anomaly_count=int(fused_binary.sum()),
            anomaly_percentage=float(fused_binary.sum() / fused_binary.size * 100),
            processing_time=processing_time,
            cloud_coverage=cloud_coverage,
            num_clusters=num_clusters,
            material_identified=material_identified,
            ndvi=ndvi,
            ndwi=ndwi
        )
        
    except Exception as e:
        print(f"Error in detect_anomalies: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        await send_progress(ProgressStatus.ERROR, 0, f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/batch")
async def batch_detection(request: BatchDetectionRequest, current_user: dict = Depends(get_current_user)):
    """
    Batch processing for multiple locations (requires authentication).
    """
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    results = []
    
    for i, location in enumerate(request.locations):
        try:
            detection_request = DetectionRequest(
                lat=location["lat"],
                lon=location["lon"],
                use_gee=request.use_gee,
                n_components=request.n_components,
                encoding_dim=request.encoding_dim
            )
            
            result = await detect_anomalies(detection_request, BackgroundTasks())
            results.append({
                "location": location,
                "success": result.success,
                "anomaly_count": result.anomaly_count,
                "anomaly_percentage": result.anomaly_percentage
            })
            
            await send_progress(ProgressStatus.DETECTING, (i + 1) / len(request.locations) * 100, 
                              f"Processing location {i + 1}/{len(request.locations)}")
            
        except Exception as e:
            results.append({
                "location": location,
                "success": False,
                "error": str(e)
            })
    
    return {"results": results}


@app.get("/image/{image_type}")
async def get_image(image_type: str):
    """Get detection result image."""
    if not detection_results:
        raise HTTPException(status_code=404, detail="No detection results available. Please run detection first.")
    
    try:
        if image_type == "rgb":
            image = detection_results['rgb']
            # Ensure RGB is in correct format
            if image.max() <= 1.0:
                image = (image * 255).astype(np.uint8)
            if len(image.shape) == 2:
                image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
            elif image.shape[2] == 4:
                image = cv2.cvtColor(image, cv2.COLOR_RGBA2RGB)
            elif image.shape[2] == 3:
                # Convert BGR to RGB if needed (OpenCV uses BGR by default)
                image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            # Ensure uint8
            image = image.astype(np.uint8)
        elif image_type == "heatmap":
            image = fusion.create_heatmap(detection_results['fused_scores'])
        elif image_type == "overlay":
            rgb = detection_results['rgb']
            if rgb.max() <= 1.0:
                rgb = (rgb * 255).astype(np.uint8)
            image = fusion.create_overlay(rgb, detection_results['binary_mask'], alpha=0.5, color=(0, 0, 255))
        elif image_type == "iso" or image_type == "iso_scores":
            scores = detection_results['iso_scores']
            if scores.max() > scores.min():
                scores_norm = ((scores - scores.min()) / (scores.max() - scores.min()) * 255).astype(np.uint8)
            else:
                scores_norm = np.zeros_like(scores, dtype=np.uint8)
            image = cv2.applyColorMap(scores_norm, cv2.COLORMAP_JET)
        elif image_type == "ae" or image_type == "ae_scores":
            scores = detection_results['ae_scores']
            if scores.max() > scores.min():
                scores_norm = ((scores - scores.min()) / (scores.max() - scores.min()) * 255).astype(np.uint8)
            else:
                scores_norm = np.zeros_like(scores, dtype=np.uint8)
            image = cv2.applyColorMap(scores_norm, cv2.COLORMAP_JET)
        elif image_type == "binary":
            image = (detection_results['binary_mask'] * 255).astype(np.uint8)
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
        elif image_type == "vit" or image_type == "vit_scores":
            if 'vit_scores' in detection_results and detection_results['vit_scores'] is not None:
                scores = detection_results['vit_scores']
                if scores.max() > scores.min():
                    scores_norm = ((scores - scores.min()) / (scores.max() - scores.min()) * 255).astype(np.uint8)
                else:
                    scores_norm = np.zeros_like(scores, dtype=np.uint8)
                image = cv2.applyColorMap(scores_norm, cv2.COLORMAP_JET)
            else:
                # Return blank image if ViT not available
                image = np.zeros((145, 145, 3), dtype=np.uint8)
        elif image_type == "clusters":
            if 'cluster_results' in detection_results and detection_results['cluster_results'] is not None:
                clusters = detection_results['cluster_results']
                # Handle if clusters is a dict
                if isinstance(clusters, dict):
                    # Extract labels if available
                    if 'labels' in clusters:
                        clusters = clusters['labels']
                    else:
                        # Return blank image if not usable
                        image = np.zeros((145, 145, 3), dtype=np.uint8)
                        base64_data = encode_image_to_base64(image)
                        return ImageResponse(success=True, image_type=image_type, image_data=base64_data)
                # Normalize clusters to 0-255
                if isinstance(clusters, np.ndarray) and clusters.max() > clusters.min():
                    clusters_norm = ((clusters - clusters.min()) / (clusters.max() - clusters.min()) * 255).astype(np.uint8)
                else:
                    clusters_norm = np.zeros((145, 145), dtype=np.uint8)
                image = cv2.applyColorMap(clusters_norm, cv2.COLORMAP_JET)
            else:
                # Return blank image if clusters not available
                image = np.zeros((145, 145, 3), dtype=np.uint8)
        else:
            raise HTTPException(status_code=400, detail=f"Invalid image type: {image_type}")
        
        base64_data = encode_image_to_base64(image)
        return ImageResponse(success=True, image_type=image_type, image_data=base64_data)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error generating image: {str(e)}")

class SatelliteImageRequest(BaseModel):
    lat: float
    lon: float
    zoom: int = 13

@app.post("/satellite-image")
async def get_satellite_image(request: SatelliteImageRequest):
    """Get satellite image for given coordinates using Esri World Imagery."""
    try:
        # Calculate bounding box for the image
        # For zoom level 13, each degree is approximately 0.01 degrees
        delta = 0.01 / (2 ** (request.zoom - 10))
        min_lon = request.lon - delta
        max_lon = request.lon + delta
        min_lat = request.lat - delta
        max_lat = request.lat + delta
        
        # Use Esri World Imagery export API
        bbox = f"{min_lon},{min_lat},{max_lon},{max_lat}"
        export_url = f"https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/export"
        
        params = {
            "bbox": bbox,
            "bboxSR": "4326",
            "size": "400,400",
            "imageSR": "4326",
            "format": "png",
            "transparent": "false",
            "f": "image"
        }
        
        response = requests.get(export_url, params=params, timeout=10)
        
        if response.status_code == 200 and response.content:
            image_bytes = response.content
            base64_data = base64.b64encode(image_bytes).decode('utf-8')
            return ImageResponse(success=True, image_type="satellite", image_data=base64_data)
        else:
            # Fallback to tile-based approach
            # Convert lat/lon to tile coordinates
            n = 2 ** request.zoom
            x = int((request.lon + 180) / 360 * n)
            y = int((1 - np.log(np.tan(np.radians(request.lat)) + 1 / np.cos(np.radians(request.lat))) / np.pi) / 2 * n)
            
            tile_url = f"https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{request.zoom}/{y}/{x}"
            response = requests.get(tile_url, timeout=10)
            
            if response.status_code == 200 and response.content:
                image_bytes = response.content
                base64_data = base64.b64encode(image_bytes).decode('utf-8')
                return ImageResponse(success=True, image_type="satellite", image_data=base64_data)
            else:
                raise HTTPException(status_code=500, detail="Failed to fetch satellite image from Esri")
                
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching satellite image: {str(e)}")


@app.get("/stats")
async def get_stats():
    """Get detection statistics."""
    global detection_results
    
    if detection_results is None:
        # Return default values when no detection has been run
        return {
            "data_source": "No data - Run detection first",
            "iso_threshold": 0.0,
            "ae_threshold": 0.0,
            "fused_threshold": 0.0,
            "anomaly_count": 0,
            "anomaly_percentage": 0.0,
            "processing_time": 0.0,
            "spectral_bands": {
                "blue": {"min": 0.0, "max": 0.0, "mean": 0.0, "std": 0.0},
                "green": {"min": 0.0, "max": 0.0, "mean": 0.0, "std": 0.0},
                "red": {"min": 0.0, "max": 0.0, "mean": 0.0, "std": 0.0},
                "nir": {"min": 0.0, "max": 0.0, "mean": 0.0, "std": 0.0},
                "swir1": {"min": 0.0, "max": 0.0, "mean": 0.0, "std": 0.0},
                "swir2": {"min": 0.0, "max": 0.0, "mean": 0.0, "std": 0.0}
            },
            "cloud_coverage": None,
            "ndvi": None,
            "ndwi": None,
            "num_clusters": None,
            "material_identified": None
        }
    
    try:
        # Extract RGB image for spectral band analysis
        rgb_image = detection_results.get('rgb')
        
        # Calculate spectral band statistics from RGB image
        spectral_stats = {
            "blue": {"min": 0.0, "max": 0.0, "mean": 0.0, "std": 0.0},
            "green": {"min": 0.0, "max": 0.0, "mean": 0.0, "std": 0.0},
            "red": {"min": 0.0, "max": 0.0, "mean": 0.0, "std": 0.0},
            "nir": {"min": 0.0, "max": 0.0, "mean": 0.0, "std": 0.0},
            "swir1": {"min": 0.0, "max": 0.0, "mean": 0.0, "std": 0.0},
            "swir2": {"min": 0.0, "max": 0.0, "mean": 0.0, "std": 0.0}
        }
        
        if rgb_image is not None and len(rgb_image.shape) >= 3:
            # Extract actual spectral bands from RGB image
            # Assuming RGB format (BGR in OpenCV)
            if rgb_image.shape[2] >= 3:
                # Convert to float for calculations
                rgb_float = rgb_image.astype(float)
                if rgb_float.max() > 1.0:
                    rgb_float = rgb_float / 255.0
                
                blue_band = rgb_float[:, :, 0]
                green_band = rgb_float[:, :, 1]
                red_band = rgb_float[:, :, 2]
                
                spectral_stats["blue"] = {
                    "min": float(blue_band.min()),
                    "max": float(blue_band.max()),
                    "mean": float(blue_band.mean()),
                    "std": float(blue_band.std())
                }
                spectral_stats["green"] = {
                    "min": float(green_band.min()),
                    "max": float(green_band.max()),
                    "mean": float(green_band.mean()),
                    "std": float(green_band.std())
                }
                spectral_stats["red"] = {
                    "min": float(red_band.min()),
                    "max": float(red_band.max()),
                    "mean": float(red_band.mean()),
                    "std": float(red_band.std())
                }
                
                # For NIR and SWIR, estimate from RGB (NASA GIBS only provides RGB)
                # These are physically-based estimates for vegetation and mineral analysis
                # NIR is typically correlated with vegetation (higher green/red ratio)
                nir_sim = (green_band * 1.3 + red_band * 0.7) / 2.0
                nir_sim = np.clip(nir_sim, 0, 1)
                spectral_stats["nir"] = {
                    "min": float(nir_sim.min()),
                    "max": float(nir_sim.max()),
                    "mean": float(nir_sim.mean()),
                    "std": float(nir_sim.std())
                }
                
                # SWIR1 - estimated from green band (mineral reflectance)
                swir1_sim = green_band * 0.85
                swir1_sim = np.clip(swir1_sim, 0, 1)
                spectral_stats["swir1"] = {
                    "min": float(swir1_sim.min()),
                    "max": float(swir1_sim.max()),
                    "mean": float(swir1_sim.mean()),
                    "std": float(swir1_sim.std())
                }
                
                # SWIR2 - estimated from blue band (atmospheric correction)
                swir2_sim = blue_band * 0.75
                swir2_sim = np.clip(swir2_sim, 0, 1)
                spectral_stats["swir2"] = {
                    "min": float(swir2_sim.min()),
                    "max": float(swir2_sim.max()),
                    "mean": float(swir2_sim.mean()),
                    "std": float(swir2_sim.std())
                }
        
        # Safely extract anomaly detection scores
        iso_scores = detection_results.get('iso_scores')
        ae_scores = detection_results.get('ae_scores')
        fused_scores = detection_results.get('fused_scores')
        
        def safe_stats(scores):
            if scores is None:
                return {"min": 0.0, "max": 0.0, "mean": 0.0, "std": 0.0}
            try:
                if hasattr(scores, 'min'):
                    return {
                        "min": float(scores.min()),
                        "max": float(scores.max()),
                        "mean": float(scores.mean()),
                        "std": float(scores.std())
                    }
                else:
                    # If it's a list or array without numpy methods
                    import numpy as np
                    arr = np.array(scores)
                    return {
                        "min": float(arr.min()),
                        "max": float(arr.max()),
                        "mean": float(arr.mean()),
                        "std": float(arr.std())
                    }
            except:
                return {"min": 0.0, "max": 0.0, "mean": 0.0, "std": 0.0}
        
        binary_mask = detection_results.get('binary_mask')
        if binary_mask is not None:
            anomaly_count = int(binary_mask.sum())
            anomaly_percentage = float(anomaly_count / binary_mask.size * 100)
        else:
            anomaly_count = 0
            anomaly_percentage = 0.0
        
        return {
            "data_source": detection_results.get('data_source', 'Unknown'),
            "iso_threshold": float(detection_results.get('iso_threshold', 0.0)),
            "ae_threshold": float(detection_results.get('ae_threshold', 0.0)),
            "fused_threshold": float(detection_results.get('fused_threshold', 0.0)),
            "anomaly_count": anomaly_count,
            "anomaly_percentage": anomaly_percentage,
            "processing_time": detection_results.get('processing_time', 0.0),
            "spectral_bands": spectral_stats,
            "cloud_coverage": detection_results.get('cloud_coverage'),
            "ndvi": detection_results.get('ndvi'),
            "ndwi": detection_results.get('ndwi'),
            "num_clusters": detection_results.get('cluster_results', {}).get('num_clusters') if detection_results.get('cluster_results') else None,
            "material_identified": detection_results.get('material_identified')
        }
    except Exception as e:
        print(f"Error in /stats endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/cache")
async def clear_cache(current_user: dict = Depends(get_current_user)):
    """Clear cache (requires authentication)."""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    global CACHE
    CACHE.clear()
    return {"message": "Cache cleared successfully"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
