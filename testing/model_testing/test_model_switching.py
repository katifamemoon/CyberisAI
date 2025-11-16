import requests
import time

def test_model_switching():
    # Test initial model
    print("Checking initial model...")
    response = requests.get("http://localhost:8000/models")
    print(f"Initial model response: {response.json()}")
    
    # Switch to fire_smoke model
    print("\nSwitching to fire_smoke model...")
    switch_response = requests.post("http://localhost:8000/models/switch", data={"model_name": "fire_smoke"})
    print(f"Switch response: {switch_response.json()}")
    
    # Check current model
    print("\nChecking current model after switch...")
    response = requests.get("http://localhost:8000/models")
    print(f"Current model response: {response.json()}")
    
    # Switch back to weapon model
    print("\nSwitching back to weapon model...")
    switch_response = requests.post("http://localhost:8000/models/switch", data={"model_name": "weapon"})
    print(f"Switch response: {switch_response.json()}")
    
    # Check current model
    print("\nChecking current model after switch back...")
    response = requests.get("http://localhost:8000/models")
    print(f"Current model response: {response.json()}")

if __name__ == "__main__":
    test_model_switching()