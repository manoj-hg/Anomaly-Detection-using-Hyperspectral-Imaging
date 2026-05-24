"""
PostgreSQL + PostGIS Database Module
Handles geospatial data storage and retrieval
"""

import os
from typing import Optional, List, Dict, Any
from datetime import datetime
import json

try:
    import psycopg2
    from psycopg2 import sql
    from psycopg2.extras import RealDictCursor
    POSTGIS_AVAILABLE = True
except ImportError:
    POSTGIS_AVAILABLE = False
    print("Warning: psycopg2 not available. Install with: pip install psycopg2-binary")


class GeospatialDatabase:
    """
    Manages PostgreSQL + PostGIS database for geospatial anomaly detection data
    """
    
    def __init__(self, db_url: Optional[str] = None):
        """
        Initialize database connection
        
        Args:
            db_url: PostgreSQL connection URL (postgresql://user:password@host:port/dbname)
                     If None, uses environment variable DATABASE_URL
        """
        self.db_url = db_url or os.environ.get('DATABASE_URL')
        self.connection = None
        self.cursor = None
        self.in_memory_storage = []  # Always initialize fallback storage
        
        if POSTGIS_AVAILABLE and self.db_url:
            self.connect()
    
    def connect(self):
        """Establish database connection"""
        if not POSTGIS_AVAILABLE:
            print("PostgreSQL not available, using in-memory storage")
            self.in_memory_storage = []
            return
        
        try:
            self.connection = psycopg2.connect(self.db_url)
            self.cursor = self.connection.cursor(cursor_factory=RealDictCursor)
            print("Successfully connected to PostgreSQL database")
            self._initialize_tables()
        except Exception as e:
            print(f"Failed to connect to database: {e}")
            print("Falling back to in-memory storage")
            self.in_memory_storage = []
    
    def _initialize_tables(self):
        """Initialize database tables with PostGIS extension"""
        if not self.connection:
            return
        
        try:
            # Enable PostGIS extension
            self.cursor.execute("CREATE EXTENSION IF NOT EXISTS postgis")
            
            # Create anomaly detections table
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS anomaly_detections (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    latitude FLOAT NOT NULL,
                    longitude FLOAT NOT NULL,
                    location GEOMETRY(POINT, 4326),
                    data_source VARCHAR(255),
                    anomaly_count INTEGER,
                    anomaly_percentage FLOAT,
                    iso_threshold FLOAT,
                    ae_threshold FLOAT,
                    vit_threshold FLOAT,
                    fused_threshold FLOAT,
                    cloud_coverage FLOAT,
                    num_clusters INTEGER,
                    material_identified VARCHAR(100),
                    ndvi FLOAT,
                    ndwi FLOAT,
                    processing_time FLOAT,
                    detection_data JSONB
                )
            """)
            
            # Create spatial index
            self.cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_anomaly_detections_location 
                ON anomaly_detections USING GIST(location)
            """)
            
            # Create index on timestamp
            self.cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_anomaly_detections_timestamp 
                ON anomaly_detections(timestamp)
            """)
            
            self.connection.commit()
            print("Database tables initialized successfully")
            
        except Exception as e:
            print(f"Error initializing tables: {e}")
            self.connection.rollback()
    
    def save_detection(self, detection_data: Dict[str, Any]) -> Optional[int]:
        """
        Save anomaly detection result to database
        
        Args:
            detection_data: Dictionary containing detection results
            
        Returns:
            ID of inserted record or None
        """
        if not self.connection:
            # In-memory fallback
            detection_data['id'] = len(self.in_memory_storage) + 1
            detection_data['timestamp'] = datetime.now().isoformat()
            self.in_memory_storage.append(detection_data)
            return detection_data['id']
        
        try:
            query = sql.SQL("""
                INSERT INTO anomaly_detections 
                (latitude, longitude, location, data_source, anomaly_count, anomaly_percentage,
                 iso_threshold, ae_threshold, vit_threshold, fused_threshold,
                 cloud_coverage, num_clusters, material_identified, ndvi, ndwi,
                 processing_time, detection_data)
                VALUES (%s, %s, ST_SetSRID(ST_MakePoint(%s, %s), 4326), %s, %s, %s,
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """)
            
            self.cursor.execute(query, (
                detection_data.get('lat'),
                detection_data.get('lon'),
                detection_data.get('lon'),
                detection_data.get('lat'),
                detection_data.get('data_source'),
                detection_data.get('anomaly_count'),
                detection_data.get('anomaly_percentage'),
                detection_data.get('iso_threshold'),
                detection_data.get('ae_threshold'),
                detection_data.get('vit_threshold'),
                detection_data.get('fused_threshold'),
                detection_data.get('cloud_coverage'),
                detection_data.get('num_clusters'),
                detection_data.get('material_identified'),
                detection_data.get('ndvi'),
                detection_data.get('ndwi'),
                detection_data.get('processing_time'),
                json.dumps(detection_data)
            ))
            
            self.connection.commit()
            result = self.cursor.fetchone()
            return result['id'] if result else None
            
        except Exception as e:
            print(f"Error saving detection: {e}")
            self.connection.rollback()
            return None
    
    def get_detections_by_location(self, lat: float, lon: float, 
                                  radius_km: float = 10) -> List[Dict]:
        """
        Get detections within a radius of a location
        
        Args:
            lat: Latitude
            lon: Longitude
            radius_km: Search radius in kilometers
            
        Returns:
            List of detection records
        """
        if not self.connection:
            # In-memory fallback
            return [d for d in self.in_memory_storage 
                    if self._distance(d.get('lat', 0), d.get('lon', 0), lat, lon) <= radius_km]
        
        try:
            query = sql.SQL("""
                SELECT * FROM anomaly_detections
                WHERE ST_DWithin(
                    location,
                    ST_SetSRID(ST_MakePoint(%s, %s), 4326),
                    %s
                )
                ORDER BY timestamp DESC
                LIMIT 100
            """)
            
            self.cursor.execute(query, (lon, lat, radius_km / 111.32))  # Approximate km to degrees
            return self.cursor.fetchall()
            
        except Exception as e:
            print(f"Error querying detections: {e}")
            return []
    
    def get_detections_by_time_range(self, start_time: datetime, 
                                     end_time: datetime) -> List[Dict]:
        """
        Get detections within a time range
        
        Args:
            start_time: Start timestamp
            end_time: End timestamp
            
        Returns:
            List of detection records
        """
        if not self.connection:
            # In-memory fallback
            return [d for d in self.in_memory_storage 
                    if start_time <= datetime.fromisoformat(d.get('timestamp', '')) <= end_time]
        
        try:
            query = sql.SQL("""
                SELECT * FROM anomaly_detections
                WHERE timestamp BETWEEN %s AND %s
                ORDER BY timestamp DESC
            """)
            
            self.cursor.execute(query, (start_time, end_time))
            return self.cursor.fetchall()
            
        except Exception as e:
            print(f"Error querying detections by time: {e}")
            return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get overall statistics from database
        
        Returns:
            Dictionary of statistics
        """
        if not self.connection:
            # In-memory fallback
            if not self.in_memory_storage:
                return {'total_detections': 0}
            
            total = len(self.in_memory_storage)
            avg_anomalies = sum(d.get('anomaly_count', 0) for d in self.in_memory_storage) / total
            return {
                'total_detections': total,
                'avg_anomaly_count': avg_anomalies
            }
        
        try:
            query = sql.SQL("""
                SELECT 
                    COUNT(*) as total_detections,
                    AVG(anomaly_count) as avg_anomaly_count,
                    AVG(anomaly_percentage) as avg_anomaly_percentage,
                    AVG(processing_time) as avg_processing_time
                FROM anomaly_detections
            """)
            
            self.cursor.execute(query)
            result = self.cursor.fetchone()
            return dict(result) if result else {}
            
        except Exception as e:
            print(f"Error getting statistics: {e}")
            return {}
    
    def _distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate approximate distance between two points in km"""
        from math import radians, cos, sin, asin, sqrt
        dlat = radians(lat2 - lat1)
        dlon = radians(lon2 - lon1)
        a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        r = 6371  # Earth's radius in km
        return c * r
    
    def close(self):
        """Close database connection"""
        if self.connection:
            self.cursor.close()
            self.connection.close()
            print("Database connection closed")


def main():
    """Test database module"""
    print("Testing Geospatial Database...")
    
    # Test with in-memory storage (no actual database required)
    db = GeospatialDatabase(db_url=None)
    
    # Save a detection
    test_detection = {
        'lat': 40.7128,
        'lon': -74.0060,
        'data_source': 'Test',
        'anomaly_count': 150,
        'anomaly_percentage': 2.5,
        'iso_threshold': 0.5,
        'ae_threshold': 0.6,
        'fused_threshold': 0.55,
        'processing_time': 3.2
    }
    
    detection_id = db.save_detection(test_detection)
    print(f"Saved detection with ID: {detection_id}")
    
    # Query detections
    detections = db.get_detections_by_location(40.7128, -74.0060, radius_km=10)
    print(f"Found {len(detections)} detections near location")
    
    # Get statistics
    stats = db.get_statistics()
    print(f"Statistics: {stats}")
    
    db.close()
    print("Database test complete!")


if __name__ == "__main__":
    main()
