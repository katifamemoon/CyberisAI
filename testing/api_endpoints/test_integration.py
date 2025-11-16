import requests
import unittest
import cv2
import numpy as np
import os
import time

class TestAPIIntegration(unittest.TestCase):
    """Integration tests for the AI Safety Detection System API"""
    
    def setUp(self):
        """Set up test environment"""
        self.base_url = "http://localhost:8000"
        self.test_image_path = "integration_test_image.jpg"
        
        # Create a test image
        self.create_test_image()
        
    def tearDown(self):
        """Clean up after tests"""
        if os.path.exists(self.test_image_path):
            os.remove(self.test_image_path)
            
    def create_test_image(self):
        """Create a test image for integration tests"""
        # Create a 480x640 image with multiple colored regions
        img = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Add red region (might be detected as fire)
        cv2.rectangle(img, (50, 50), (200, 200), (0, 0, 255), -1)
        
        # Add orange region (might be detected as fire/smoke)
        cv2.rectangle(img, (250, 100), (400, 250), (0, 165, 255), -1)
        
        # Add gray region (might be detected as weapon)
        cv2.rectangle(img, (450, 150), (600, 300), (128, 128, 128), -1)
        
        # Add some noise to make it more realistic
        noise = np.random.randint(0, 50, (480, 640, 3), dtype=np.uint8)
        img = cv2.add(img, noise)
        
        # Save the test image
        cv2.imwrite(self.test_image_path, img)
        
    def test_full_workflow(self):
        """Test a full workflow: health check, model listing, model switching, and detection"""
        # 1. Health check
        response = requests.get(f"{self.base_url}/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["message"], "YOLO Object Detection API is running")
        
        # 2. Get available models
        response = requests.get(f"{self.base_url}/models")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("models", data)
        self.assertIn("current_model", data)
        self.assertIn("weapon", data["models"])
        self.assertIn("fire_smoke", data["models"])
        
        # 3. Switch to fire_smoke model
        response = requests.post(
            f"{self.base_url}/models/switch", 
            data={"model_name": "fire_smoke"}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["current_model"], "fire_smoke")
        
        # Wait for model switch to complete
        time.sleep(0.5)
        
        # 4. Run detection with fire_smoke model
        with open(self.test_image_path, "rb") as f:
            files = {"file": f}
            response = requests.post(f"{self.base_url}/detect", files=files)
            
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("detections", data)
        self.assertIn("image", data)
        self.assertIn("model_used", data)
        self.assertEqual(data["model_used"], "fire_smoke")
        
        # 5. Switch to weapon model
        response = requests.post(
            f"{self.base_url}/models/switch", 
            data={"model_name": "weapon"}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["current_model"], "weapon")
        
        # Wait for model switch to complete
        time.sleep(0.5)
        
        # 6. Run detection with weapon model
        with open(self.test_image_path, "rb") as f:
            files = {"file": f}
            response = requests.post(f"{self.base_url}/detect", files=files)
            
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("detections", data)
        self.assertIn("image", data)
        self.assertIn("model_used", data)
        self.assertEqual(data["model_used"], "weapon")
        
        # 7. Run detection with both models
        with open(self.test_image_path, "rb") as f:
            files = {"file": f}
            response = requests.post(f"{self.base_url}/detect/both", files=files)
            
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("weapon_detections", data)
        self.assertIn("fire_smoke_detections", data)
        self.assertIn("weapon_image", data)
        self.assertIn("fire_smoke_image", data)
        
    def test_model_persistence(self):
        """Test that model selection persists across requests"""
        # Switch to fire_smoke model
        response = requests.post(
            f"{self.base_url}/models/switch", 
            data={"model_name": "fire_smoke"}
        )
        self.assertEqual(response.status_code, 200)
        
        # Wait for model switch to complete
        time.sleep(0.5)
        
        # Make multiple detection requests and verify the model is consistent
        for _ in range(3):
            with open(self.test_image_path, "rb") as f:
                files = {"file": f}
                response = requests.post(f"{self.base_url}/detect", files=files)
                
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertEqual(data["model_used"], "fire_smoke")
            
    def test_error_handling(self):
        """Test error handling for various scenarios"""
        # Test switching to invalid model
        response = requests.post(
            f"{self.base_url}/models/switch", 
            data={"model_name": "nonexistent_model"}
        )
        self.assertEqual(response.status_code, 200)  # API returns 200 with error message
        data = response.json()
        self.assertIn("error", data)
        
        # Test detection without file
        response = requests.post(f"{self.base_url}/detect")
        self.assertEqual(response.status_code, 422)  # Validation error

if __name__ == "__main__":
    unittest.main()