import cv2
import numpy as np
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from ultralytics import YOLO
import os
from dotenv import load_dotenv
import json
from datetime import datetime
import base64
import logging

# Import our services
from services.model_manager import ModelManager
from services.detection_service import DetectionService
from services.logging_service import LoggingService

# ===== NEW: Import database =====
from database import get_db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

app = FastAPI(title="YOLO Object Detection API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
model_manager = ModelManager()
detection_service = DetectionService()
logging_service = LoggingService()

# ===== NEW: Initialize database =====
db = None

# Global variable for current model
current_model = "weapon"

# Load models on startup
@app.on_event("startup")
async def load_models():
    global db
    
    # Load ML models
    result = model_manager.load_models()
    if not result.get("weapon_loaded") and not result.get("fire_smoke_loaded"):
        logger.error("No models loaded successfully")
    else:
        logger.info("Models loaded successfully")
        global current_model
        current_model = model_manager.current_model
    
    # ===== NEW: Initialize database =====
    try:
        db = get_db()
        logger.info("✓ Database connected successfully")
    except Exception as e:
        logger.error(f"✗ Database connection failed: {e}")
        logger.warning("⚠️ Running without database - detections won't be saved")

# ===== NEW: Shutdown event =====
@app.on_event("shutdown")
async def shutdown_event():
    if db:
        db.close_all_connections()
        logger.info("✓ Database connections closed")

# Health check endpoint
@app.get("/")
async def root():
    db_status = "connected" if db else "disconnected"
    return {
        "message": "YOLO Object Detection API is running",
        "database": db_status
    }

# Get available models
@app.get("/models")
async def get_models():
    return {
        "models": model_manager.get_available_models(),
        "current_model": model_manager.current_model
    }

# Switch between models
@app.post("/models/switch")
async def switch_model(model_name: str = Form(...)):
    if model_manager.switch_model(model_name):
        return {"message": f"Switched to {model_name} model", "current_model": model_name}
    else:
        return {"error": "Invalid model name. Use 'weapon' or 'fire_smoke'"}

# Detect objects in an image
@app.post("/detect")
async def detect_objects(
    file: UploadFile = File(...),
    camera_id: str = Form("default")  # NEW: Optional camera ID
):
    global current_model
    
    # Select model based on current selection
    model = model_manager.get_current_model()
    if model is None:
        return {"error": "Model not loaded"}
    
    # Read image file
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    # Check if image was decoded successfully
    if img is None:
        return {"error": "Invalid image file. Please upload a valid image file (JPEG, PNG, etc.)."}
    
    # Run object detection using detection service
    detection_result = detection_service.detect_objects(model, img)
    
    if not detection_result["success"]:
        return {"error": "Detection failed", "details": detection_result.get("error")}
    
    detections = detection_result["detections"]
    
    # ===== NEW: Save detections to database =====
    saved_detections = []
    if db and detections:
        for detection in detections:
            try:
                # Determine detection type based on class name
                class_name = detection['class'].lower()
                
                # Map class names to detection types
                if 'weapon' in class_name or 'gun' in class_name or 'knife' in class_name:
                    detection_type = 'weapon'
                elif 'fire' in class_name:
                    detection_type = 'fire'
                elif 'smoke' in class_name:
                    detection_type = 'smoke'
                else:
                    detection_type = detection['class']
                
                detection_id = db.insert_detection(
                    detection_type=detection_type,
                    confidence=detection['confidence'],
                    camera_id=camera_id,
                    model_name=f"YOLOv8-{model_manager.current_model}",
                    bbox_coordinates=detection['box']
                )
                
                if detection_id:
                    saved_detections.append(detection_id)
                    logger.info(f"✓ Saved {detection_type} detection (ID: {detection_id})")
                    
            except Exception as e:
                logger.error(f"✗ Failed to save detection to database: {e}")
    
    # Draw bounding boxes using detection service
    processed_img = detection_service.draw_detections(img, detections)
    
    # Log detections
    logging_service.log_detection(model_manager.current_model, detections)
    
    # Convert image back to bytes
    _, buffer = cv2.imencode('.jpg', processed_img)
    img_bytes = buffer.tobytes()
    
    return {
        "detections": detections,
        "image": base64.b64encode(img_bytes).decode('utf-8'),
        "model_used": model_manager.current_model,
        "saved_to_db": len(saved_detections),  # NEW
        "detection_ids": saved_detections  # NEW
    }

# Detect with both models
@app.post("/detect/both")
async def detect_both_models(
    file: UploadFile = File(...),
    camera_id: str = Form("default")  # NEW: Optional camera ID
):
    if not model_manager.models_loaded():
        return {"error": "One or both models not loaded"}
    
    # Read image file
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    # Check if image was decoded successfully
    if img is None:
        return {"error": "Invalid image file. Please upload a valid image file (JPEG, PNG, etc.)."}
    
    # Create copies for each model
    img_weapon = img.copy()
    img_fire_smoke = img.copy()
    
    # ===== NEW: Lists to store DB IDs =====
    weapon_db_ids = []
    fire_smoke_db_ids = []
    
    # Run object detection with weapon model
    weapon_model = model_manager.get_model("weapon")
    if weapon_model is None:
        return {"error": "Weapon model not loaded"}
    weapon_results = weapon_model(img_weapon)
    weapon_detections = []
    
    for r in weapon_results:
        boxes = r.boxes
        for box in boxes:
            b = box.xyxy[0].tolist()
            c = box.cls
            conf = box.conf
            class_name = weapon_model.names[int(c)]
            
            detection_data = {
                "class": class_name,
                "confidence": float(conf),
                "box": {
                    "x1": int(b[0]),
                    "y1": int(b[1]),
                    "x2": int(b[2]),
                    "y2": int(b[3])
                }
            }
            weapon_detections.append(detection_data)
            
            # ===== NEW: Save to database =====
            if db:
                try:
                    detection_id = db.insert_detection(
                        detection_type='weapon',
                        confidence=float(conf),
                        camera_id=camera_id,
                        model_name="YOLOv8-weapon",
                        bbox_coordinates=detection_data['box']
                    )
                    if detection_id:
                        weapon_db_ids.append(detection_id)
                except Exception as e:
                    logger.error(f"Failed to save weapon detection: {e}")
            
            # Draw bounding box (red for weapon)
            cv2.rectangle(img_weapon, (int(b[0]), int(b[1])), (int(b[2]), int(b[3])), (0, 0, 255), 2)
            cv2.putText(img_weapon, f"{class_name} {float(conf):.2f}", 
                       (int(b[0]), int(b[1]) - 10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)
    
    # Run object detection with fire/smoke model
    fire_smoke_model = model_manager.get_model("fire_smoke")
    if fire_smoke_model is None:
        return {"error": "Fire/Smoke model not loaded"}
    fire_smoke_results = fire_smoke_model(img_fire_smoke)
    fire_smoke_detections = []
    
    for r in fire_smoke_results:
        boxes = r.boxes
        for box in boxes:
            b = box.xyxy[0].tolist()
            c = box.cls
            conf = box.conf
            class_name = fire_smoke_model.names[int(c)]
            
            detection_data = {
                "class": class_name,
                "confidence": float(conf),
                "box": {
                    "x1": int(b[0]),
                    "y1": int(b[1]),
                    "x2": int(b[2]),
                    "y2": int(b[3])
                }
            }
            fire_smoke_detections.append(detection_data)
            
            # ===== NEW: Save to database =====
            if db:
                try:
                    # Determine if it's fire or smoke
                    detection_type = 'fire' if 'fire' in class_name.lower() else 'smoke'
                    detection_id = db.insert_detection(
                        detection_type=detection_type,
                        confidence=float(conf),
                        camera_id=camera_id,
                        model_name="YOLOv8-fire_smoke",
                        bbox_coordinates=detection_data['box']
                    )
                    if detection_id:
                        fire_smoke_db_ids.append(detection_id)
                except Exception as e:
                    logger.error(f"Failed to save fire/smoke detection: {e}")
            
            # Draw bounding box (blue for fire/smoke)
            cv2.rectangle(img_fire_smoke, (int(b[0]), int(b[1])), (int(b[2]), int(b[3])), (255, 0, 0), 2)
            cv2.putText(img_fire_smoke, f"{class_name} {float(conf):.2f}", 
                       (int(b[0]), int(b[1]) - 10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 0, 0), 2)
    
    # Convert images back to bytes
    _, buffer_weapon = cv2.imencode('.jpg', img_weapon)
    img_bytes_weapon = buffer_weapon.tobytes()
    
    _, buffer_fire_smoke = cv2.imencode('.jpg', img_fire_smoke)
    img_bytes_fire_smoke = buffer_fire_smoke.tobytes()
    
    return {
        "weapon_detections": weapon_detections,
        "fire_smoke_detections": fire_smoke_detections,
        "weapon_image": base64.b64encode(img_bytes_weapon).decode('utf-8'),
        "fire_smoke_image": base64.b64encode(img_bytes_fire_smoke).decode('utf-8'),
        "weapon_db_ids": weapon_db_ids,  # NEW
        "fire_smoke_db_ids": fire_smoke_db_ids  # NEW
    }

# ===== NEW: Database endpoints =====

@app.get("/detections/recent")
async def get_recent_detections(
    limit: int = 10,
    detection_type: str = None,
    hours: int = 24
):
    """Get recent detections from database"""
    if not db:
        return {"error": "Database not available"}
    
    try:
        detections = db.get_recent_detections(
            limit=limit,
            detection_type=detection_type,
            hours=hours
        )
        
        result = []
        for det in detections:
            result.append({
                "id": det[0],
                "type": det[1],
                "confidence": det[2],
                "timestamp": det[3].isoformat(),
                "camera_id": det[4],
                "image_path": det[5],
                "status": det[6]
            })
        
        return {
            "detections": result,
            "count": len(result),
            "period_hours": hours
        }
    except Exception as e:
        logger.error(f"Error fetching detections: {e}")
        return {"error": str(e)}

@app.get("/statistics")
async def get_statistics(hours: int = 24):
    """Get detection statistics"""
    if not db:
        return {"error": "Database not available"}
    
    try:
        stats = db.get_statistics(hours=hours)
        return {
            "statistics": stats,
            "period_hours": hours
        }
    except Exception as e:
        logger.error(f"Error fetching statistics: {e}")
        return {"error": str(e)}

@app.put("/detections/{detection_id}/status")
async def update_detection_status(
    detection_id: int,
    status: str = Form(...),
    notes: str = Form(None)
):
    """Update detection status (e.g., resolved, false_alarm)"""
    if not db:
        return {"error": "Database not available"}
    
    try:
        success = db.update_detection_status(detection_id, status, notes)
        if success:
            return {
                "success": True,
                "detection_id": detection_id,
                "new_status": status
            }
        else:
            return {"error": "Update failed"}
    except Exception as e:
        logger.error(f"Error updating detection: {e}")
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=os.getenv("HOST", "localhost"), port=int(os.getenv("PORT", 8000)))