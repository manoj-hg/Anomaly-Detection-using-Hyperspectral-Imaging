# Lovable Frontend UI Prompt - AI-Powered Geospatial Anomaly Detection

## Project Overview
Create a modern, responsive frontend for an AI-powered geospatial anomaly detection system that identifies camouflaged objects in satellite imagery. The system uses machine learning models (Isolation Forest, Autoencoder) to detect anomalies in spectral satellite data.

## Tech Stack
- **Framework**: React (Next.js preferred)
- **Styling**: Tailwind CSS with shadcn/ui components
- **Icons**: Lucide React
- **Charts**: Chart.js or Recharts
- **Maps**: Leaflet for 2D maps
- **3D Globe**: Globe.gl or Cesium (optional)
- **API**: REST API integration with FastAPI backend running on port 8000

## Page Structure
The application should have 4 main pages with a navigation bar:

### 1. Dashboard Page (Overview)
- **3D Globe Visualization**: Interactive 3D globe showing detection locations
- **Data Source Info**: Display current data source (NASA GIBS, Google Earth Engine, etc.)
- **Quick Stats**: 
  - Total Detections count
  - Average Processing Time
  - Success Rate percentage
- **Score Distribution Chart**: Line chart showing anomaly score distribution (Min, 25%, 50%, 75%, Max percentiles)

### 2. Detection Page
- **Detection Parameters Form**:
  - Latitude input (number, range -90 to 90)
  - Longitude input (number, range -180 to 180)
  - PCA Components slider (1-50)
  - Encoding Dimension slider (1-32)
  - Use Google Earth Engine checkbox
  - Enable Cache checkbox
  - Quick Location buttons (NYC, London, Tokyo, Sydney, etc.)
- **Progress Section**:
  - Progress bar with percentage
  - Real-time log container showing detection steps
- **Run Detection Button**: Primary action button

### 3. Analysis Page
- **Image Analysis Section**:
  - Image view tabs: RGB, Heatmap, Isolation Forest, Autoencoder, Binary, Overlay
  - Image display area with placeholder when no data
  - Download image button
  - Fullscreen button
- **Spectral Band Analysis**:
  - 6 spectral band charts: Blue, Green, Red, NIR, SWIR1, SWIR2
  - Each band shows as a mini chart with placeholder when no data

### 4. Reports Page
- **Score Distribution Chart**: Detailed line chart with multiple datasets
- **Model Comparison Chart**: Bar chart comparing Isolation Forest, Autoencoder, and Fused thresholds
- **Detection History**: List showing recent detections with:
  - Date/Time
  - Location (lat, lon)
  - Anomaly count

## Design Requirements

### Color Scheme
- **Primary Gradient**: Purple to Blue (#667eea to #764ba2)
- **Light Mode**: White cards, light gray backgrounds, dark text
- **Dark Mode**: Dark gray cards, black backgrounds, light text
- **Accent Colors**: Success (green), Error (red), Warning (yellow)

### Layout
- **Grid-based layout**: CSS Grid with responsive columns
- **Cards/Frames**: Rounded corners (16px), subtle shadows, glassmorphism effects
- **Spacing**: Consistent padding (20px default), gaps (20px default)

### Navigation
- **Top navigation bar**: Horizontal scrolling on mobile
- **Navigation buttons**: 4 buttons (Dashboard, Detection, Analysis, Reports)
- **Active state**: Gradient background with shadow
- **Hover effect**: Lift animation

### Responsive Design
- **Desktop (>1600px)**: 4-column grid
- **Large Desktop (1400px)**: 3-column grid
- **Tablet (1024px)**: 2-column grid
- **Mobile (768px)**: 1-column stack
- **Small Mobile (480px)**: Optimized for phones with smaller elements

### Animations
- **Page transitions**: Fade-in with slide-up effect
- **Hover effects**: Card lift, button scale
- **Loading states**: Skeleton loaders or spinners
- **Custom cursor**: Optional animated cursor with trail effect

## API Integration

### Base URL
`http://localhost:8000`

### Endpoints

#### POST /detect
Run anomaly detection
```json
Request: {
  "lat": 40.7128,
  "lon": -74.0060,
  "use_gee": false,
  "n_components": 10,
  "encoding_dim": 8,
  "enable_cache": true
}
Response: {
  "success": true,
  "message": "Detection completed",
  "data_source": "NASA GIBS",
  "iso_threshold": 0.35,
  "ae_threshold": 0.17,
  "fused_threshold": 0.16,
  "anomaly_count": 6648,
  "anomaly_percentage": 10.14,
  "processing_time": 15.5
}
```

#### GET /stats
Get detection statistics
```json
Response: {
  "data_source": "NASA GIBS",
  "iso_threshold": 0.35,
  "ae_threshold": 0.17,
  "fused_threshold": 0.16,
  "anomaly_count": 6648,
  "anomaly_percentage": 10.14,
  "processing_time": 15.5,
  "spectral_bands": {
    "iso_scores": {"min": 0.0, "max": 1.0, "mean": 0.18, "std": 0.17},
    "ae_scores": {"min": 0.0, "max": 1.0, "mean": 0.08, "std": 0.09},
    "fused_scores": {"min": 0.0, "max": 0.92, "mean": 0.04, "std": 0.12}
  }
}
```

#### GET /image/{image_type}
Get detection result image
- Types: rgb, heatmap, iso, ae, binary, overlay
- Response: Base64 encoded image data

#### WebSocket /ws
Real-time progress updates
```json
{
  "type": "progress",
  "status": "loading",
  "progress": 50,
  "message": "Running Isolation Forest...",
  "timestamp": "2024-04-24T10:00:00"
}
```

## Component Requirements

### Theme Toggle
- Button to switch between light/dark mode
- Persist preference in localStorage

### Toast Notifications
- Success, error, info, warning types
- Auto-dismiss after 3 seconds
- Slide-in animation

### Loading Overlay
- Full-screen overlay with spinner
- Progress text display
- Transparent backdrop

### Forms
- Input validation (latitude: -90 to 90, longitude: -180 to 180)
- Error messages for invalid inputs
- Submit button with loading state

### Charts
- Responsive charts that resize with container
- Tooltips on hover
- Legend display
- Custom colors matching theme

## Additional Features

### Custom Cursor (Optional)
- Animated cursor with gradient border
- Trail effect following mouse
- Hover state enlargement on interactive elements
- Only on desktop (mouse devices)

### Quick Locations
- Pre-defined location buttons for testing
- NYC: 40.7128, -74.0060
- London: 51.5074, -0.1278
- Tokyo: 35.6762, 139.6503
- Sydney: -33.8688, 151.2093
- Paris: 48.8566, 2.3522

### Placeholder States
- Show placeholder messages when no data available
- Icons and text indicating "Run detection to view data"
- Graceful degradation for missing data

## Performance Requirements
- Fast initial load (<2 seconds)
- Smooth animations (60fps)
- Efficient re-renders (React optimization)
- Lazy loading for charts and maps
- Debounced input handling

## Accessibility
- Semantic HTML
- ARIA labels for interactive elements
- Keyboard navigation support
- Screen reader compatible
- Focus indicators
- Color contrast compliance (WCAG AA)

## Deployment
- Build for production
- Optimize assets
- Environment variables for API URL
- Static site hosting compatible

## Notes
- The backend is already running on port 8000
- Use the existing API endpoints
- Maintain the multi-page navigation structure
- Keep the frame/card-based layout concept
- Ensure all charts and visualizations are responsive
- Support both light and dark themes
