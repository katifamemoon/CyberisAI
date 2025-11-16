import requests
import unittest
import cv2
import numpy as np
import os
import base64

class TestDetectionEndpoints(unittest.TestCase):
    """Test cases for the detection endpoints (/detect, /detect/both)"""
    
    def setUp(self):
        """Set up test environment"""
        self.base_url = "http://localhost:8000"
        self.test_image_path = "test_image.jpg"
        
        # Create a simple test image
        self.create_test_image()
        
    def tearDown(self):
        """Clean up after tests"""
        if os.path.exists(self.test_image_path):
            os.remove(self.test_image_path)
            
    def create_test_image(self):
        """Create a simple test image for detection tests"""
        # Create a 480x640 black image
        img = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Add some colored regions to make it more interesting
        cv2.rectangle(img, (100, 100), (300, 300), (0, 0, 255), -1)  # Red region
        cv2.rectangle(img, (350, 150), (500, 250), (0, 165, 255), -1)  # Orange region
        
        # Add some random noise
        noise = np.random.randint(0, 50, (480, 640, 3), dtype=np.uint8)
        img = cv2.add(img, noise)
        
        # Save the test image
        cv2.imwrite(self.test_image_path, img)
        
    def test_detect_endpoint_with_valid_image(self):
        """Test the detect endpoint with a valid image"""
        # First switch to a model to ensure one is active
        requests.post(f"{self.base_url}/models/switch", data={"model_name": "weapon"})
        
        with open(self.test_image_path, "rb") as f:
            files = {"file": f}
            response = requests.post(f"{self.base_url}/detect", files=files)
            
        # Check that the response status code is 200
        self.assertEqual(response.status_code, 200)
        
        # Check that the response has the expected structure
        data = response.json()
        expected_keys = {"detections", "image", "model_used"}
        self.assertEqual(set(data.keys()), expected_keys)
        
        # Check that detections is a list
        self.assertIsInstance(data["detections"], list)
        
        # Check that image is a base64 string
        try:
            base64.b64decode(data["image"])
            base64_valid = True
        except Exception:
            base64_valid = False
        self.assertTrue(base64_valid)
        
        # Check that model_used is a string
        self.assertIsInstance(data["model_used"], str)
        
    def test_detect_endpoint_without_file(self):
        """Test the detect endpoint without providing a file"""
        response = requests.post(f"{self.base_url}/detect")
        
        # Should return 422 for validation error
        self.assertEqual(response.status_code, 422)
        
    def test_detect_both_endpoint_with_valid_image(self):
        """Test the detect/both endpoint with a valid image"""
        with open(self.test_image_path, "rb") as f:
            files = {"file": f}
            response = requests.post(f"{self.base_url}/detect/both", files=files)
            
        # Check that the response status code is 200
        self.assertEqual(response.status_code, 200)
        
        # Check that the response has the expected structure
        data = response.json()
        expected_keys = {"weapon_detections", "fire_smoke_detections", "weapon_image", "fire_smoke_image"}
        self.assertEqual(set(data.keys()), expected_keys)
        
        # Check that detections are lists
        self.assertIsInstance(data["weapon_detections"], list)
        self.assertIsInstance(data["fire_smoke_detections"], list)
        
        # Check that images are base64 strings
        try:
            base64.b64decode(data["weapon_image"])
            base64_valid_weapon = True
        except Exception:
            base64_valid_weapon = False
        self.assertTrue(base64_valid_weapon)
        
        try:
            base64.b64decode(data["fire_smoke_image"])
            base64_valid_fire_smoke = True
        except Exception:
            base64_valid_fire_smoke = False
        self.assertTrue(base64_valid_fire_smoke)
        
    def test_detect_both_endpoint_without_file(self):
        """Test the detect/both endpoint without providing a file"""
        response = requests.post(f"{self.base_url}/detect/both")
        
        # Should return 422 for validation error
        self.assertEqual(response.status_code, 422)
        
    def test_detect_response_structure(self):
        """Test that the detect response has the correct structure"""
        # First switch to a model to ensure one is active
        requests.post(f"{self.base_url}/models/switch", data={"model_name": "weapon"})
        
        with open(self.test_image_path, "rb") as f:
            files = {"file": f}
            response = requests.post(f"{self.base_url}/detect", files=files)
            
        data = response.json()
        
        # If there are detections, check their structure
        if data["detections"]:
            detection = data["detections"][0]
            expected_detection_keys = {"class", "confidence", "box"}
            self.assertEqual(set(detection.keys()), expected_detection_keys)
            
            # Check box structure
            expected_box_keys = {"x1", "y1", "x2", "y2"}
            self.assertEqual(set(detection["box"].keys()), expected_box_keys)
            
            # Check that values are of correct types
            self.assertIsInstance(detection["class"], str)
            self.assertIsInstance(detection["confidence"], float)
            for coord in detection["box"].values():
                self.assertIsInstance(coord, int)

if __name__ == "__main__":
    unittest.main()