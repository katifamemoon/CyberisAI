import requests
import unittest
import time

class TestModelsEndpoints(unittest.TestCase):
    """Test cases for the models endpoints (/models, /models/switch)"""
    
    def setUp(self):
        """Set up test environment"""
        self.base_url = "http://localhost:8000"
        
    def test_get_models(self):
        """Test that the get models endpoint returns available models"""
        response = requests.get(f"{self.base_url}/models")
        
        # Check that the response status code is 200
        self.assertEqual(response.status_code, 200)
        
        # Check that the response has the expected structure
        data = response.json()
        self.assertIn("models", data)
        self.assertIn("current_model", data)
        
        # Check that models is a list
        self.assertIsInstance(data["models"], list)
        
        # Check that current_model is either None or a string
        self.assertTrue(
            data["current_model"] is None or isinstance(data["current_model"], str)
        )
        
    def test_switch_model_valid_names(self):
        """Test switching between valid model names"""
        # Test switching to fire_smoke model
        response = requests.post(
            f"{self.base_url}/models/switch", 
            data={"model_name": "fire_smoke"}
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("message", data)
        self.assertIn("current_model", data)
        self.assertEqual(data["current_model"], "fire_smoke")
        
        # Wait a moment for the switch to complete
        time.sleep(0.5)
        
        # Verify the current model by checking the models endpoint
        response = requests.get(f"{self.base_url}/models")
        data = response.json()
        self.assertEqual(data["current_model"], "fire_smoke")
        
        # Test switching to weapon model
        response = requests.post(
            f"{self.base_url}/models/switch", 
            data={"model_name": "weapon"}
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("message", data)
        self.assertIn("current_model", data)
        self.assertEqual(data["current_model"], "weapon")
        
        # Wait a moment for the switch to complete
        time.sleep(0.5)
        
        # Verify the current model by checking the models endpoint
        response = requests.get(f"{self.base_url}/models")
        data = response.json()
        self.assertEqual(data["current_model"], "weapon")
        
    def test_switch_model_invalid_name(self):
        """Test switching to an invalid model name"""
        response = requests.post(
            f"{self.base_url}/models/switch", 
            data={"model_name": "invalid_model"}
        )
        
        # Should still return 200 but with an error message
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("error", data)
        
    def test_models_response_structure(self):
        """Test that the models response has the correct structure"""
        response = requests.get(f"{self.base_url}/models")
        data = response.json()
        
        # Check that response contains only the expected keys
        expected_keys = {"models", "current_model"}
        self.assertEqual(set(data.keys()), expected_keys)
        
        # Check that models list contains strings
        for model in data["models"]:
            self.assertIsInstance(model, str)

if __name__ == "__main__":
    unittest.main()