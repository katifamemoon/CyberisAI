import json
import os
from typing import Dict, Any, List
from datetime import datetime
import logging

# ADD THIS IMPORT
from database import get_db

class LoggingService:
    """Handles detection logging to file AND database."""
    
    def __init__(self, log_file: str = "detection_logs.json", camera_id: str = "CAM_001", save_to_db: bool = True):
        self.log_file = log_file
        self.logger = logging.getLogger(__name__)
        
        # NEW: Database integration
        self.save_to_db = save_to_db
        self.camera_id = camera_id
        
        if self.save_to_db:
            try:
                self.db = get_db(enable_logging=True)
                self.logger.info("✓ Database connection established")
            except Exception as e:
                self.logger.error(f"✗ Database connection failed: {e}")
                self.save_to_db = False
    
    def log_detection(self, model_used: str, detections: List[Dict], timestamp: str | None = None) -> bool:
        """
        Log detection results to file AND database.
        
        Args:
            model_used: Name of the model used
            detections: List of detection results
            timestamp: Optional timestamp (defaults to current time)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if timestamp is None:
                timestamp = datetime.now().isoformat()
            
            log_entry = {
                "timestamp": timestamp,
                "model": model_used,
                "detections": detections
            }
            
            # EXISTING: Save to JSON file
            logs = []
            if os.path.exists(self.log_file):
                try:
                    with open(self.log_file, "r") as f:
                        logs = json.load(f)
                except (json.JSONDecodeError, IOError) as e:
                    self.logger.warning(f"Could not read existing log file: {e}")
            
            logs.append(log_entry)
            
            with open(self.log_file, "w") as f:
                json.dump(logs, f, indent=2)
            
            # NEW: Save to database
            if self.save_to_db:
                self._save_to_database(log_entry)
                
            return True
        except Exception as e:
            self.logger.error(f"Error logging detection: {e}")
            return False
    
    def _save_to_database(self, log_entry: Dict) -> None:
        """
        Save detection to database (NEW METHOD)
        
        Args:
            log_entry: Detection log entry with timestamp, model, and detections
        """
        try:
            timestamp = log_entry['timestamp']
            model_name = log_entry['model']
            detections = log_entry['detections']
            
            # Parse timestamp
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            
            # If no detections, optionally save as "no_detection"
            if len(detections) == 0:
                # Uncomment if you want to save empty frames
                # self.db.save_detection(
                #     camera_id=self.camera_id,
                #     object_label="no_detection",
                #     confidence=1.0,
                #     image_path=f"frame_{dt.strftime('%Y%m%d_%H%M%S')}.jpg",
                #     bbox_coordinates={},
                #     model_name=model_name,
                #     timestamp=dt
                # )
                return
            
            # Save each detection to database
            for det in detections:
                class_label = det.get('class', 'unknown')
                confidence = det.get('confidence', 0.0)
                bbox = det.get('box', {})
                
                # Save detection
                detection_id = self.db.save_detection(
                    camera_id=self.camera_id,
                    object_label=class_label,
                    confidence=confidence,
                    image_path=f"frame_{dt.strftime('%Y%m%d_%H%M%S')}_{class_label}.jpg",
                    bbox_coordinates=bbox,
                    model_name=model_name,
                    timestamp=dt
                )
                
                self.logger.info(f"✓ Saved {class_label} to database (ID: {detection_id})")
                
                # Create alert for high-risk detections
                self._create_alert_if_needed(detection_id, class_label, confidence)
                
        except Exception as e:
            self.logger.error(f"Error saving to database: {e}")
    
    def _create_alert_if_needed(self, detection_id: int, class_label: str, confidence: float) -> None:
        """
        Create alert for high-risk detections (NEW METHOD)
        
        Args:
            detection_id: ID of the detection
            class_label: Type of detection (weapon/fire/smoke)
            confidence: Confidence score
        """
        try:
            alert_level = None
            
            # Determine alert level
            if class_label == 'weapon' and confidence > 0.5:
                alert_level = 'critical'
            elif class_label == 'fire' and confidence > 0.5:
                alert_level = 'critical'
            elif class_label == 'smoke' and confidence > 0.4:
                alert_level = 'high'
            
            # Create alert if needed
            if alert_level:
                connection = self.db.get_connection()
                cursor = connection.cursor()
                try:
                    cursor.execute("""
                        INSERT INTO alerts (behavior_id, alert_level, status)
                        VALUES (NULL, %s, 'pending')
                        RETURNING id;
                    """, (alert_level,))
                    alert_id = cursor.fetchone()[0]
                    connection.commit()
                    self.logger.warning(f"🚨 ALERT created: {alert_level.upper()} (ID: {alert_id})")
                except Exception as e:
                    connection.rollback()
                    self.logger.error(f"Error creating alert: {e}")
                finally:
                    cursor.close()
                    self.db.return_connection(connection)
                    
        except Exception as e:
            self.logger.error(f"Error in alert creation: {e}")
    
    def get_recent_detections(self, limit: int = 50) -> List[Dict]:
        """
        Get recent detection logs.
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of recent detection logs
        """
        try:
            if os.path.exists(self.log_file):
                with open(self.log_file, "r") as f:
                    logs = json.load(f)
                return logs[-limit:] if len(logs) > limit else logs
            return []
        except Exception as e:
            self.logger.error(f"Error reading detection logs: {e}")
            return []
    
    def get_detections_from_database(self, limit: int = 100) -> List[Dict]:
        """
        Get recent detections from database (NEW METHOD)
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            List of recent detections from database
        """
        if not self.save_to_db:
            self.logger.warning("Database is not enabled")
            return []
        
        try:
            return self.db.get_detections(camera_id=self.camera_id, limit=limit)
        except Exception as e:
            self.logger.error(f"Error getting detections from database: {e}")
            return []
    
    def cleanup(self):
        """Close database connections (NEW METHOD)"""
        if self.save_to_db and hasattr(self, 'db'):
            self.db.close_all_connections()
            self.logger.info("✓ Database connections closed")


# ============================================================
# USAGE EXAMPLE
# ============================================================

if __name__ == "__main__":
    # Initialize logging service with database
    logging_service = LoggingService(
        log_file="detection_logs.json",
        camera_id="CAM_001",
        save_to_db=True  # Set to False to disable database saving
    )
    
    # Example 1: Log weapon detection
    weapon_detections = [
        {
            "class": "weapon",
            "confidence": 0.87,
            "box": {"x1": 100, "y1": 150, "x2": 200, "y2": 300}
        }
    ]
    logging_service.log_detection("weapon", weapon_detections)
    
    # Example 2: Log fire detection
    fire_detections = [
        {
            "class": "fire",
            "confidence": 0.92,
            "box": {"x1": 300, "y1": 200, "x2": 450, "y2": 400}
        },
        {
            "class": "smoke",
            "confidence": 0.65,
            "box": {"x1": 250, "y1": 100, "x2": 350, "y2": 250}
        }
    ]
    logging_service.log_detection("fire_smoke", fire_detections)
    
    # Example 3: Get recent detections from database
    recent = logging_service.get_detections_from_database(limit=10)
    print(f"\n📊 Recent detections from database: {len(recent)}")
    
    # Cleanup
    logging_service.cleanup()
    
    print("\n✅ Test complete! Check your database.")