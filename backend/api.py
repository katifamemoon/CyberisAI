# Add this to your FastAPI main.py file

from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import time
from collections import deque

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory log storage (use Redis or database in production)
database_logs = deque(maxlen=500)  # Keep last 500 logs

class DatabaseLogger:
    """Logger for database operations"""
    
    @staticmethod
    def log_operation(operation_type, table, action, data, status='success', duration=0):
        """Log a database operation"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'type': operation_type,
            'table': table,
            'action': action,
            'data': data,
            'status': status,
            'duration': round(duration, 2)
        }
        database_logs.append(log_entry)
        return log_entry

# Database logging endpoints
@app.get("/api/database/logs")
async def get_database_logs(limit: int = 50):
    """Get recent database logs"""
    logs = list(database_logs)[-limit:]
    return {
        "logs": logs,
        "count": len(logs)
    }

@app.post("/api/database/logs/clear")
async def clear_database_logs():
    """Clear all database logs"""
    database_logs.clear()
    return {"message": "Database logs cleared successfully"}

# Modified detection endpoint with database logging
@app.post("/detect")
async def detect_objects(file: UploadFile = File(...)):
    """Detect objects and log database operations"""
    start_time = time.time()
    
    try:
        # Your existing detection logic here
        # ...
        
        # Example: Log detection save to database
        detection_data = {
            'camera_id': 'CAM_001',
            'object_label': 'person',
            'confidence': 0.95,
            'timestamp': datetime.now().isoformat()
        }
        
        # Simulate database save time
        db_start = time.time()
        
        # Here you would call your actual database save
        # detection_id = db.save_detection(...)
        
        db_duration = (time.time() - db_start) * 1000  # Convert to ms
        
        # Log the database operation
        DatabaseLogger.log_operation(
            operation_type='INSERT',
            table='detections',
            action=f'INSERT INTO detections (camera_id, object_label, confidence)',
            data=detection_data,
            status='success',
            duration=db_duration
        )
        
        # Return your detection results
        return {
            "detections": [],
            "image": None,
            "processing_time": time.time() - start_time
        }
        
    except Exception as e:
        # Log database error
        DatabaseLogger.log_operation(
            operation_type='INSERT',
            table='detections',
            action='INSERT INTO detections',
            data={'error': str(e)},
            status='error',
            duration=(time.time() - start_time) * 1000
        )
        raise

# Example: Add logging to your existing database class methods
from database import get_db

# Wrap your database methods with logging
original_save_detection = None

def save_detection_with_logging(camera_id, object_label, confidence, image_path, 
                               bbox_coordinates, model_name, timestamp=None):
    """Save detection with logging"""
    start_time = time.time()
    
    try:
        db = get_db()
        detection_id = db.save_detection(
            camera_id, object_label, confidence, image_path,
            bbox_coordinates, model_name, timestamp
        )
        
        duration = (time.time() - start_time) * 1000
        
        # Log successful operation
        DatabaseLogger.log_operation(
            operation_type='INSERT',
            table='detections',
            action=f'INSERT INTO detections VALUES (...)',
            data={
                'detection_id': detection_id,
                'camera_id': camera_id,
                'object_label': object_label,
                'confidence': confidence
            },
            status='success',
            duration=duration
        )
        
        return detection_id
        
    except Exception as e:
        duration = (time.time() - start_time) * 1000
        
        # Log failed operation
        DatabaseLogger.log_operation(
            operation_type='INSERT',
            table='detections',
            action=f'INSERT INTO detections VALUES (...)',
            data={'error': str(e)},
            status='error',
            duration=duration
        )
        raise

# Example endpoint to test database logging
@app.post("/test/save-detection")
async def test_save_detection():
    """Test endpoint to demonstrate database logging"""
    
    # Simulate saving a detection
    save_detection_with_logging(
        camera_id='CAM_TEST',
        object_label='person',
        confidence=0.92,
        image_path='/images/test.jpg',
        bbox_coordinates={'x': 100, 'y': 150, 'width': 200, 'height': 400},
        model_name='YOLOv8'
    )
    
    return {"message": "Detection saved and logged"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)