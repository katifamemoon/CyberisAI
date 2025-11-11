import cv2
import numpy as np
import os
from ultralytics import YOLO
from typing import List, Dict, Any, Optional, Tuple
import base64
import logging

class DetectionService:
    """Handles object detection using YOLO models."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.confidence_threshold = float(os.getenv("CONFIDENCE_THRESHOLD", "0.5"))
    
    def detect_objects(self, model: YOLO, image: np.ndarray) -> Dict[str, Any]:
        """
        Run object detection on an image.
        
        Args:
            model: YOLO model to use for detection
            image: Input image as numpy array
            
        Returns:
            Dictionary containing detections and processed image
        """
        try:
            # Run object detection
            results = model(image)
            
            # Process results
            detections = []
            for r in results:
                boxes = r.boxes
                for box in boxes:
                    confidence = float(box.conf)
                    if confidence < self.confidence_threshold:
                        continue
                        
                    b = box.xyxy[0].tolist()  # get box coordinates
                    c = box.cls
                    class_name = model.names[int(c)]
                    
                    detections.append({
                        "class": class_name,
                        "confidence": confidence,
                        "box": {
                            "x1": int(b[0]),
                            "y1": int(b[1]),
                            "x2": int(b[2]),
                            "y2": int(b[3])
                        }
                    })
            
            return {
                "detections": detections,
                "success": True
            }
        except Exception as e:
            self.logger.error(f"Error in object detection: {e}")
            return {
                "detections": [],
                "success": False,
                "error": str(e)
            }
    
    def draw_detections(self, image: np.ndarray, detections: List[Dict], color: Tuple[int, int, int] = (0, 255, 0)) -> np.ndarray:
        """
        Draw bounding boxes on image.
        
        Args:
            image: Input image
            detections: List of detection results
            color: BGR color tuple for bounding boxes
            
        Returns:
            Image with drawn bounding boxes
        """
        try:
            image_copy = image.copy()
            
            for detection in detections:
                box = detection["box"]
                class_name = detection["class"]
                confidence = detection["confidence"]
                
                # Draw bounding box
                cv2.rectangle(
                    image_copy, 
                    (box["x1"], box["y1"]), 
                    (box["x2"], box["y2"]), 
                    color, 
                    2
                )
                
                # Draw label
                label = f"{class_name} {confidence:.2f}"
                cv2.putText(
                    image_copy, 
                    label, 
                    (box["x1"], box["y1"] - 10), 
                    cv2.FONT_HERSHEY_SIMPLEX, 
                    0.9, 
                    color, 
                    2
                )
            
            return image_copy
        except Exception as e:
            self.logger.error(f"Error drawing detections: {e}")
            return image
    
    def process_frame_with_dual_models(self, weapon_model: YOLO, fire_smoke_model: YOLO, image: np.ndarray) -> Dict[str, Any]:
        """
        Process frame with both models.
        
        Args:
            weapon_model: Weapon detection model
            fire_smoke_model: Fire/smoke detection model
            image: Input image
            
        Returns:
            Dictionary containing detections from both models
        """
        try:
            # Run detection with both models
            weapon_results = self.detect_objects(weapon_model, image)
            fire_smoke_results = self.detect_objects(fire_smoke_model, image)
            
            return {
                "weapon_detections": weapon_results["detections"],
                "fire_smoke_detections": fire_smoke_results["detections"],
                "success": True
            }
        except Exception as e:
            self.logger.error(f"Error in dual model detection: {e}")
            return {
                "weapon_detections": [],
                "fire_smoke_detections": [],
                "success": False,
                "error": str(e)
            }