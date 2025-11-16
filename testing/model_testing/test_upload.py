import requests
import os

# Test file upload
url = "http://localhost:8000/detect"

# Check if we have any image files in the directory
image_files = [f for f in os.listdir('.') if f.lower().endswith(('.png', '.jpg', '.jpeg'))]

if image_files:
    # Use the first image file found
    file_path = image_files[0]
    print(f"Using image file: {file_path}")
else:
    # Create a simple test image if none exists
    try:
        import numpy as np
        import cv2
        # Create a simple black image
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        cv2.imwrite('test_image.jpg', img)
        file_path = 'test_image.jpg'
        print("Created test image: test_image.jpg")
    except ImportError:
        # If we can't create an image, use the README as fallback
        file_path = 'README.md'
        print("Using README.md as fallback (may not work for detection)")

try:
    with open(file_path, "rb") as f:
        files = {"file": f}
        response = requests.post(url, files=files)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
except Exception as e:
    print(f"Error: {e}")