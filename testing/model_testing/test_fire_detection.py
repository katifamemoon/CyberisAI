import requests
import cv2
import numpy as np
import time
import os

def test_fire_detection():
    # First, switch to fire_smoke model
    print("Switching to fire_smoke model...")
    switch_response = requests.post("http://localhost:8000/models/switch", data={"model_name": "fire_smoke"})
    print(f"Switch response: {switch_response.json()}")
    
    # Check if fire_test_image.jpg exists
    if not os.path.exists("fire_test_image.jpg"):
        print("fire_test_image.jpg not found, creating a simple test image...")
        # Create a simple test image with fire-like colors (reds and oranges)
        test_img = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Add some orange/red regions to simulate fire
        cv2.rectangle(test_img, (100, 100), (300, 300), (0, 0, 255), -1)  # Red region
        cv2.rectangle(test_img, (350, 150), (500, 250), (0, 165, 255), -1)  # Orange region
        
        # Add some random noise to make it more realistic
        noise = np.random.randint(0, 50, (480, 640, 3), dtype=np.uint8)
        test_img = cv2.add(test_img, noise)
        
        # Save the test image for reference
        cv2.imwrite("fire_test_image.jpg", test_img)
        print("Test image saved as fire_test_image.jpg")
    else:
        print("Using existing fire_test_image.jpg")
        # Load the existing test image
        test_img = cv2.imread("fire_test_image.jpg")
        if test_img is None:
            print("Error: Could not load fire_test_image.jpg")
            return
    
    # Convert image to bytes
    result, img_bytes = cv2.imencode('.jpg', test_img)
    if not result:
        print("Error: Could not encode image")
        return
    img_bytes = img_bytes.tobytes()
    
    # Send to detection endpoint
    print("Sending image for fire detection...")
    files = {"file": ("test_fire.jpg", img_bytes, "image/jpeg")}
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

if __name__ == "__main__":
    test_fire_detection()