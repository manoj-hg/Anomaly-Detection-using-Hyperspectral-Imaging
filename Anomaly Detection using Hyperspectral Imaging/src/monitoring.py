"""
Continuous Monitoring System with Celery
Handles scheduled anomaly detection tasks and background processing
"""

import os
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import json

try:
    from celery import Celery
    from celery.schedules import crontab
    CELERY_AVAILABLE = True
except ImportError:
    CELERY_AVAILABLE = False
    print("Warning: Celery not available. Install with: pip install celery redis")


class AnomalyMonitoringSystem:
    """
    Continuous monitoring system for automated anomaly detection
    Uses Celery for distributed task scheduling
    """
    
    def __init__(self, broker_url: Optional[str] = None, 
                 result_backend: Optional[str] = None):
        """
        Initialize monitoring system
        
        Args:
            broker_url: Celery broker URL (e.g., redis://localhost:6379/0)
            result_backend: Celery result backend URL
        """
        self.broker_url = broker_url or os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
        self.result_backend = result_backend or os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
        
        if CELERY_AVAILABLE:
            self.celery_app = Celery(
                'anomaly_monitoring',
                broker=self.broker_url,
                backend=self.result_backend
            )
            self._configure_tasks()
        else:
            self.celery_app = None
            print("Celery not available, monitoring will run synchronously")
    
    def _configure_tasks(self):
        """Configure Celery tasks and schedules"""
        if not self.celery_app:
            return
        
        # Configure periodic tasks
        self.celery_app.conf.beat_schedule = {
            'monitor-high-priority-locations': {
                'task': 'tasks.monitor_location',
                'schedule': crontab(minute='*/30'),  # Every 30 minutes
                'args': (40.7128, -74.0060, 'high-priority'),
            },
            'monitor-all-locations': {
                'task': 'tasks.monitor_multiple_locations',
                'schedule': crontab(hour='*/6'),  # Every 6 hours
            },
            'cleanup-old-data': {
                'task': 'tasks.cleanup_old_detections',
                'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
            },
        }
        
        self.celery_app.conf.timezone = 'UTC'
    
    def add_monitoring_location(self, lat: float, lon: float, 
                               priority: str = 'normal',
                               interval_minutes: int = 60):
        """
        Add a location to continuous monitoring
        
        Args:
            lat: Latitude
            lon: Longitude
            priority: Priority level ('high', 'normal', 'low')
            interval_minutes: Monitoring interval in minutes
        """
        location = {
            'lat': lat,
            'lon': lon,
            'priority': priority,
            'interval_minutes': interval_minutes,
            'added_at': datetime.now().isoformat()
        }
        
        # In production, store in database
        print(f"Added monitoring location: {lat}, {lon} (priority: {priority})")
        return location
    
    def run_detection_task(self, lat: float, lon: float, 
                         task_id: Optional[str] = None) -> Dict:
        """
        Run a single anomaly detection task
        
        Args:
            lat: Latitude
            lon: Longitude
            task_id: Optional task identifier
            
        Returns:
            Detection results
        """
        print(f"Running detection task for location: {lat}, {lon}")
        
        # Import detection modules
        try:
            from src.data_loader import SatelliteDataLoader
            from src.preprocess import SpectralPreprocessor
            from src.models.isolation_forest import IsolationForestAnomalyDetector
            from src.models.autoencoder import AutoencoderAnomalyDetector
            from src.fusion import ScoreFusion
            
            # Run detection
            loader = SatelliteDataLoader()
            data, source = loader.load_data(lat=lat, lon=lon, use_gee=False)
            
            preprocessor = SpectralPreprocessor(n_components=10, detect_clouds=True)
            features, rgb = preprocessor.preprocess(data, fit_pca=False, remove_clouds=True)
            
            original_shape = data.shape[:2]
            
            iso_detector = IsolationForestAnomalyDetector(contamination=0.1)
            iso_detector.fit(features, original_shape)
            iso_scores, iso_binary, iso_threshold = iso_detector.detect_anomalies(features, original_shape)
            
            ae_detector = AutoencoderAnomalyDetector(
                input_dim=features.shape[1],
                encoding_dim=8,
                epochs=5,
                batch_size=32
            )
            ae_detector.train(features, original_shape=original_shape, verbose=False)
            ae_scores, ae_binary, ae_threshold = ae_detector.detect_anomalies(features, original_shape, train=False)
            
            fusion = ScoreFusion(isolation_weight=0.5, autoencoder_weight=0.5)
            fused_scores, fused_binary, fused_threshold = fusion.fuse_and_optimize(iso_scores, ae_scores)
            
            result = {
                'task_id': task_id,
                'timestamp': datetime.now().isoformat(),
                'lat': lat,
                'lon': lon,
                'data_source': source,
                'anomaly_count': int(fused_binary.sum()),
                'anomaly_percentage': float(fused_binary.sum() / fused_binary.size * 100),
                'iso_threshold': float(iso_threshold),
                'ae_threshold': float(ae_threshold),
                'fused_threshold': float(fused_threshold),
                'status': 'completed'
            }
            
            return result
            
        except Exception as e:
            return {
                'task_id': task_id,
                'timestamp': datetime.now().isoformat(),
                'lat': lat,
                'lon': lon,
                'status': 'failed',
                'error': str(e)
            }
    
    def schedule_detection(self, lat: float, lon: float, 
                         eta: Optional[datetime] = None) -> str:
        """
        Schedule a detection task for future execution
        
        Args:
            lat: Latitude
            lon: Longitude
            eta: Estimated time of arrival (when to run)
            
        Returns:
            Task ID
        """
        if not self.celery_app:
            # Run synchronously
            result = self.run_detection_task(lat, lon)
            return f"sync-task-{datetime.now().timestamp()}"
        
        # Schedule with Celery
        from src.tasks import monitor_location
        task = monitor_location.apply_async(args=[lat, lon], eta=eta)
        return task.id
    
    def get_task_status(self, task_id: str) -> Dict:
        """
        Get status of a scheduled task
        
        Args:
            task_id: Task identifier
            
        Returns:
            Task status information
        """
        if not self.celery_app:
            return {'status': 'unknown', 'message': 'Celery not available'}
        
        try:
            result = self.celery_app.AsyncResult(task_id)
            return {
                'task_id': task_id,
                'status': result.status,
                'result': result.result if result.ready() else None
            }
        except Exception as e:
            return {'status': 'error', 'message': str(e)}


class AlertSystem:
    """
    Alert system for anomaly notifications
    Supports webhook, email, and SMS alerts
    """
    
    def __init__(self):
        """Initialize alert system"""
        self.webhook_urls = os.environ.get('ALERT_WEBHOOK_URLS', '').split(',')
        self.email_enabled = os.environ.get('EMAIL_ENABLED', 'false').lower() == 'true'
        self.sms_enabled = os.environ.get('SMS_ENABLED', 'false').lower() == 'true'
    
    def send_alert(self, detection_result: Dict, alert_type: str = 'anomaly') -> bool:
        """
        Send alert based on detection result
        
        Args:
            detection_result: Detection result dictionary
            alert_type: Type of alert ('anomaly', 'system', 'info')
            
        Returns:
            True if alert sent successfully
        """
        print(f"Sending {alert_type} alert for detection at {detection_result.get('lat')}, {detection_result.get('lon')}")
        
        # Send webhook alerts
        webhook_success = self._send_webhook_alert(detection_result, alert_type)
        
        # Send email alerts (if enabled)
        email_success = True
        if self.email_enabled:
            email_success = self._send_email_alert(detection_result, alert_type)
        
        # Send SMS alerts (if enabled)
        sms_success = True
        if self.sms_enabled:
            sms_success = self._send_sms_alert(detection_result, alert_type)
        
        return webhook_success and email_success and sms_success
    
    def _send_webhook_alert(self, detection_result: Dict, alert_type: str) -> bool:
        """Send webhook alert"""
        import requests
        
        payload = {
            'alert_type': alert_type,
            'timestamp': datetime.now().isoformat(),
            'detection': detection_result
        }
        
        success_count = 0
        for url in self.webhook_urls:
            if not url.strip():
                continue
            try:
                response = requests.post(url, json=payload, timeout=10)
                if response.status_code == 200:
                    success_count += 1
            except Exception as e:
                print(f"Webhook alert failed for {url}: {e}")
        
        return success_count > 0
    
    def _send_email_alert(self, detection_result: Dict, alert_type: str) -> bool:
        """Send email alert"""
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            smtp_server = os.environ.get('SMTP_SERVER')
            smtp_port = int(os.environ.get('SMTP_PORT', 587))
            smtp_username = os.environ.get('SMTP_USERNAME')
            smtp_password = os.environ.get('SMTP_PASSWORD')
            recipient = os.environ.get('ALERT_EMAIL_RECIPIENT')
            
            if not all([smtp_server, smtp_username, smtp_password, recipient]):
                print("Email configuration incomplete, skipping email alert")
                return False
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = smtp_username
            msg['To'] = recipient
            msg['Subject'] = f"Anomaly Detection Alert: {alert_type.upper()}"
            
            body = f"""
            Anomaly Detection Alert
            
            Type: {alert_type}
            Timestamp: {datetime.now().isoformat()}
            Location: {detection_result.get('lat')}, {detection_result.get('lon')}
            Data Source: {detection_result.get('data_source')}
            Anomaly Count: {detection_result.get('anomaly_count')}
            Anomaly Percentage: {detection_result.get('anomaly_percentage')}%
            
            Full Result:
            {json.dumps(detection_result, indent=2)}
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(smtp_username, smtp_password)
                server.send_message(msg)
            
            print("Email alert sent successfully")
            return True
            
        except Exception as e:
            print(f"Email alert failed: {e}")
            return False
    
    def _send_sms_alert(self, detection_result: Dict, alert_type: str) -> bool:
        """Send SMS alert"""
        try:
            # Placeholder for SMS integration
            # In production, integrate with Twilio, AWS SNS, or similar service
            print(f"SMS alert would be sent: {alert_type} at {detection_result.get('lat')}, {detection_result.get('lon')}")
            return True
        except Exception as e:
            print(f"SMS alert failed: {e}")
            return False


def main():
    """Test monitoring and alert systems"""
    print("Testing Monitoring and Alert Systems...")
    
    # Test monitoring system
    monitoring = AnomalyMonitoringSystem()
    monitoring.add_monitoring_location(40.7128, -74.0060, priority='high')
    
    # Run a detection task
    result = monitoring.run_detection_task(40.7128, -74.0060, task_id='test-task-1')
    print(f"Detection task result: {result.get('status')}")
    
    # Test alert system
    alert_system = AlertSystem()
    if result.get('status') == 'completed':
        alert_system.send_alert(result, alert_type='anomaly')
    
    print("Monitoring and alert systems test complete!")


if __name__ == "__main__":
    main()
