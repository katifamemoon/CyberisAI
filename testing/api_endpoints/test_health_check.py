import requests
import unittest
import os

class TestHealthCheckEndpoint(unittest.TestCase):
    """Test cases for the health check endpoint (/)"""
    
    def setUp(self):
        """Set up test environment"""
        self.base_url = "http://localhost:8000"
        
    def test_health_check(self):
        """Test that the health check endpoint returns a successful response"""
        response = requests.get(f"{self.base_url}/")
        
        # Check that the response status code is 200
        self.assertEqual(response.status_code, 200)
        
        # Check that the response contains the expected message
        data = response.json()
        self.assertIn("message", data)
        self.assertEqual(data["message"], "YOLO Object Detection API is running")
        
    def test_health_check_response_structure(self):
        """Test that the health check response has the correct structure"""
        response = requests.get(f"{self.base_url}/")
        data = response.json()
        
        # Check that response contains only the expected keys
        self.assertEqual(list(data.keys()), ["message"])
        
        # Check that the message is a string
        self.assertIsInstance(data["message"], str)

if __name__ == "__main__":
    unittest.main()