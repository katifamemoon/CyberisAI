import psycopg2
from psycopg2 import pool
from datetime import datetime
import os
from dotenv import load_dotenv
import json
import time
import requests

load_dotenv()

class CyberisAIDatabaseWithLogging:
    def __init__(self, enable_api_logging=True, api_url='http://localhost:8000'):
        """Initialize database connection pool with logging"""
        self.enable_api_logging = enable_api_logging
        self.api_url = api_url
        
        try:
            self.connection_pool = psycopg2.pool.SimpleConnectionPool(
                1, 10,
                host=os.getenv('DB_HOST', 'localhost'),
                port=os.getenv('DB_PORT', '5432'),
                database=os.getenv('DB_NAME', 'cyberisai'),
                user=os.getenv('DB_USER', 'postgres'),
                password=os.getenv('DB_PASSWORD', '')
            )
            
            if self.connection_pool:
                print("✓ Database connection pool created successfully")
                self.create_tables()
        except Exception as e:
            print(f"✗ Error creating connection pool: {e}")
            raise
    
    def _log_to_api(self, operation_type, table, action, data, status='success', duration=0):
        """Send log to FastAPI backend"""
        if not self.enable_api_logging:
            return
            
        try:
            log_data = {
                'timestamp': datetime.now().isoformat(),
                'type': operation_type,
                'table': table,
                'action': action,
                'data': data,
                'status': status,
                'duration': round(duration, 2)
            }
            
            # Send to API (non-blocking, ignore errors)
            requests.post(
                f'{self.api_url}/api/database/log',
                json=log_data,
                timeout=0.5
            )
        except:
            pass  # Silently fail if API is unavailable
    
    def get_connection(self):
        """Get a connection from the pool"""
        return self.connection_pool.getconn()
    
    def return_connection(self, connection):
        """Return connection to the pool"""
        self.connection_pool.putconn(connection)

    def create_tables(self):
        """Create ALL expanded tables"""
        connection = self.get_connection()
        cursor = connection.cursor()

        try:
            # USERS TABLE
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(100) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    role VARCHAR(50) DEFAULT 'viewer',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # DETECTIONS TABLE
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS detections (
                    id SERIAL PRIMARY KEY,
                    camera_id VARCHAR(100),
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    object_label VARCHAR(100),
                    confidence FLOAT,
                    image_path VARCHAR(500),
                    bbox_coordinates JSONB,
                    model_name VARCHAR(100),
                    status VARCHAR(50) DEFAULT 'active'
                );
            """)

            # POSES TABLE
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS poses (
                    id SERIAL PRIMARY KEY,
                    detection_id INTEGER REFERENCES detections(id) ON DELETE CASCADE,
                    keypoints JSONB,
                    angles JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # BEHAVIORS TABLE
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS behaviors (
                    id SERIAL PRIMARY KEY,
                    pose_id INTEGER REFERENCES poses(id) ON DELETE CASCADE,
                    behavior_label VARCHAR(100),
                    probability FLOAT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # ALERTS TABLE
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS alerts (
                    id SERIAL PRIMARY KEY,
                    behavior_id INTEGER REFERENCES behaviors(id) ON DELETE CASCADE,
                    alert_level VARCHAR(50),
                    status VARCHAR(50) DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            # CAMERAS TABLE
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cameras (
                    id SERIAL PRIMARY KEY,
                    camera_id VARCHAR(100) UNIQUE NOT NULL,
                    location VARCHAR(255),
                    status VARCHAR(50) DEFAULT 'active',
                    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata JSONB
                );
            """)

            connection.commit()
            print("✓ All tables created successfully")

        except Exception as e:
            connection.rollback()
            print(f"✗ Error creating tables: {e}")
            raise
        finally:
            cursor.close()
            self.return_connection(connection)

    def save_detection(self, camera_id, object_label, confidence, image_path, 
                      bbox_coordinates, model_name, timestamp=None):
        """Save a detection record WITH LOGGING"""
        start_time = time.time()
        connection = self.get_connection()
        cursor = connection.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO detections 
                (camera_id, timestamp, object_label, confidence, image_path, 
                 bbox_coordinates, model_name)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id;
            """, (
                camera_id,
                timestamp or datetime.now(),
                object_label,
                confidence,
                image_path,
                json.dumps(bbox_coordinates),
                model_name
            ))
            
            detection_id = cursor.fetchone()[0]
            connection.commit()
            
            duration = (time.time() - start_time) * 1000
            
            # Console log
            print(f"✓ [INSERT] detections | ID: {detection_id} | {duration:.2f}ms")
            
            # API log
            self._log_to_api(
                operation_type='INSERT',
                table='detections',
                action=f'INSERT INTO detections (id={detection_id})',
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
            connection.rollback()
            duration = (time.time() - start_time) * 1000
            
            print(f"✗ [ERROR] detections | {str(e)} | {duration:.2f}ms")
            
            self._log_to_api(
                operation_type='INSERT',
                table='detections',
                action='INSERT INTO detections',
                data={'error': str(e)},
                status='error',
                duration=duration
            )
            raise
        finally:
            cursor.close()
            self.return_connection(connection)

    def save_pose(self, detection_id, keypoints, angles):
        """Save pose data WITH LOGGING"""
        start_time = time.time()
        connection = self.get_connection()
        cursor = connection.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO poses (detection_id, keypoints, angles)
                VALUES (%s, %s, %s)
                RETURNING id;
            """, (detection_id, json.dumps(keypoints), json.dumps(angles)))
            
            pose_id = cursor.fetchone()[0]
            connection.commit()
            
            duration = (time.time() - start_time) * 1000
            print(f"✓ [INSERT] poses | ID: {pose_id} | {duration:.2f}ms")
            
            self._log_to_api(
                operation_type='INSERT',
                table='poses',
                action=f'INSERT INTO poses (id={pose_id})',
                data={'pose_id': pose_id, 'detection_id': detection_id},
                status='success',
                duration=duration
            )
            
            return pose_id
            
        except Exception as e:
            connection.rollback()
            duration = (time.time() - start_time) * 1000
            print(f"✗ [ERROR] poses | {str(e)} | {duration:.2f}ms")
            
            self._log_to_api(
                operation_type='INSERT',
                table='poses',
                action='INSERT INTO poses',
                data={'error': str(e)},
                status='error',
                duration=duration
            )
            raise
        finally:
            cursor.close()
            self.return_connection(connection)

    def get_detections(self, camera_id=None, limit=100, offset=0):
        """Get detections WITH LOGGING"""
        start_time = time.time()
        connection = self.get_connection()
        cursor = connection.cursor()
        
        try:
            if camera_id:
                cursor.execute("""
                    SELECT * FROM detections 
                    WHERE camera_id = %s 
                    ORDER BY timestamp DESC 
                    LIMIT %s OFFSET %s;
                """, (camera_id, limit, offset))
            else:
                cursor.execute("""
                    SELECT * FROM detections 
                    ORDER BY timestamp DESC 
                    LIMIT %s OFFSET %s;
                """, (limit, offset))
            
            columns = [desc[0] for desc in cursor.description]
            results = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
            duration = (time.time() - start_time) * 1000
            print(f"✓ [SELECT] detections | Found {len(results)} | {duration:.2f}ms")
            
            self._log_to_api(
                operation_type='SELECT',
                table='detections',
                action=f'SELECT * FROM detections (LIMIT {limit})',
                data={'count': len(results), 'camera_id': camera_id},
                status='success',
                duration=duration
            )
            
            return results
            
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            print(f"✗ [ERROR] detections | {str(e)} | {duration:.2f}ms")
            
            self._log_to_api(
                operation_type='SELECT',
                table='detections',
                action='SELECT * FROM detections',
                data={'error': str(e)},
                status='error',
                duration=duration
            )
            raise
        finally:
            cursor.close()
            self.return_connection(connection)

    def close_all_connections(self):
        self.connection_pool.closeall()
        print("✓ All database connections closed")


# SINGLETON with logging enabled
db_instance = None

def get_db(enable_logging=True):
    global db_instance
    if db_instance is None:
        db_instance = CyberisAIDatabaseWithLogging(enable_api_logging=enable_logging)
    return db_instance


if __name__ == "__main__":
    # Test with logging
    db = get_db(enable_logging=True)
    
    # This will log to console AND send to API
    detection_id = db.save_detection(
        camera_id="CAM_001",
        object_label="person",
        confidence=0.95,
        image_path="/images/detection_001.jpg",
        bbox_coordinates={"x": 100, "y": 150, "width": 200, "height": 400},
        model_name="YOLOv8"
    )
    
    print(f"\n🎉 Detection saved with ID: {detection_id}")
    print("Check your frontend Database Monitor to see the log!")
    
    db.close_all_connections()