import json
import os
from typing import Dict, Any, List
from datetime import datetime
import logging

class LoggingService:
    """Handles detection logging to file."""
    
    def __init__(self, log_file: str = "detection_logs.json"):
        self.log_file = log_file
        self.logger = logging.getLogger(__name__)
    
    def log_detection(self, model_used: str, detections: List[Dict], timestamp: str | None = None) -> bool:
        """
        Log detection results to file.
        
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
            
            # Read existing logs
            logs = []
            if os.path.exists(self.log_file):
                try:
                    with open(self.log_file, "r") as f:
                        logs = json.load(f)
                except (json.JSONDecodeError, IOError) as e:
                    self.logger.warning(f"Could not read existing log file: {e}")
            
            # Append new entry
            logs.append(log_entry)
            
            # Write back to file
            with open(self.log_file, "w") as f:
                json.dump(logs, f, indent=2)
                
            return True
        except Exception as e:
            self.logger.error(f"Error logging detection: {e}")
            return False
    
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
                # Return most recent entries
                return logs[-limit:] if len(logs) > limit else logs
            return []
        except Exception as e:
            self.logger.error(f"Error reading detection logs: {e}")
            return []