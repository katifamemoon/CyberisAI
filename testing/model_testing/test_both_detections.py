import requests
import cv2
import numpy as np
import os

def load_or_create_test_image(filename, create_func):
    """Load an existing test image or create a new one if it doesn't exist."""
    if os.path.exists(filename):
        print(f"Using existing {filename}")
        test_img = cv2.imread(filename)
        if test_img is None:
            print(f"Error: Could not load {filename}")
            return None
    else:
        print(f"{filename} not found, creating a test image...")
        test_img = create_func()
        cv2.imwrite(filename, test_img)
        print(f"Test image saved as {filename}")
    return test_img

def create_fire_test_image():
    """Create a simple test image with fire-like colors (reds and oranges)."""
    # Create a 480x640 image with fire-like colors
    img = np.zeros((480, 640, 3), dtype=np.uint8)
    
    # Add some orange/red regions to simulate fire
    cv2.rectangle(img, (100, 100), (300, 300), (0, 0, 255), -1)  # Red region
    cv2.rectangle(img, (350, 150), (500, 250), (0, 165, 255), -1)  # Orange region
    
    # Add some random noise to make it more realistic
    noise = np.random.randint(0, 50, (480, 640, 3), dtype=np.uint8)
    img = cv2.add(img, noise)
    
    return img

def create_weapon_test_image():
    """Create a simple test image with shapes that might resemble weapons."""
    # Create a 480x640 image
    img = np.zeros((480, 640, 3), dtype=np.uint8)
    
    # Add some shapes that might resemble weapons
    cv2.rectangle(img, (150, 100), (200, 300), (128, 128, 128), -1)  # Gray rectangle
    cv2.rectangle(img, (175, 50), (225, 100), (64, 64, 64), -1)  # Darker gray rectangle
    
    return img

def test_detection(model_name, image_filename, create_func):
    """Test detection for a specific model with a test image."""
    print(f"\n{'='*50}")
    print(f"Testing {model_name.upper()} detection")
    print(f"{'='*50}")
    
    # Switch to the specified model
    print(f"Switching to {model_name} model...")
    switch_response = requests.post("http://localhost:8000/models/switch", data={"model_name": model_name})
    print(f"Switch response: {switch_response.json()}")
    
    # Load or create test image
    test_img = load_or_create_test_image(image_filename, create_func)
    if test_img is None:
        return
    
    # Convert image to bytes
    result, img_bytes = cv2.imencode('.jpg', test_img)
    if not result:
        print("Error: Could not encode image")
        return
    img_bytes = img_bytes.tobytes()
    
    # Send to detection endpoint
    print(f"Sending image for {model_name} detection...")
    files = {"file": (image_filename, img_bytes, "image/jpeg")}
    response = requests.post("http://localhost:8000/detect", files=files)
    
    if response.status_code == 200:
        result = response.json()
        print(f"Detection result: {result}")
        
        if "detections" in result:
            detections = result["detections"]
            print(f"Number of detections: {len(detections)}")
            for i, detection in enumerate(detections):
                print(f"Detection {i+1}: {detection['class']} with confidence {detection['confidence']:.2f}")
        else:
            print("No detections key in response")
    else:
        print(f"Error: {response.status_code} - {response.text}")

def test_fire_detection():
    """Test fire/smoke detection."""
    test_detection("fire_smoke", "fire_test_image.jpg", create_fire_test_image)

def test_weapon_detection():
    """Test weapon detection."""
    test_detection("weapon", "weapon_test_image.jpg", create_weapon_test_image)

def test_both_models():
    """Test both models with their respective images."""
    print("Testing both fire/smoke and weapon detection models")
    
    # Test fire/smoke detection
    test_fire_detection()
    
    # Test weapon detection
    test_weapon_detection()
    
    print(f"\n{'='*50}")
    print("Both detection tests completed")
    print(f"{'='*50}")

if __name__ == "__main__":
    test_both_models()