import requests
import cv2
import numpy as np
import os

def test_weapon_detection():
    # First, switch to weapon model
    print("Switching to weapon model...")
    switch_response = requests.post("http://localhost:8000/models/switch", data={"model_name": "weapon"})
    print(f"Switch response: {switch_response.json()}")
    
    # Check if weapon_test_image.jpg exists
    if not os.path.exists("weapon_test_image.jpg"):
        print("weapon_test_image.jpg not found, creating a simple test image...")
        # Create a simple test image
        test_img = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Add some shapes that might resemble weapons
        cv2.rectangle(test_img, (150, 100), (200, 300), (128, 128, 128), -1)  # Gray rectangle
        cv2.rectangle(test_img, (175, 50), (225, 100), (64, 64, 64), -1)  # Darker gray rectangle
        
        # Save the test image for reference
        cv2.imwrite("weapon_test_image.jpg", test_img)
        print("Test image saved as weapon_test_image.jpg")
    else:
        print("Using existing weapon_test_image.jpg")
        # Load the existing test image
        test_img = cv2.imread("weapon_test_image.jpg")
        if test_img is None:
            print("Error: Could not load weapon_test_image.jpg")
            return
    
    # Convert image to bytes
    result, img_bytes = cv2.imencode('.jpg', test_img)
    if not result:
        print("Error: Could not encode image")
        return
    img_bytes = img_bytes.tobytes()
    
    # Send to detection endpoint
    print("Sending image for weapon detection...")
    files = {"file": ("test_weapon.jpg", img_bytes, "image/jpeg")}
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
    test_weapon_detection()