import requests

# Test file upload
url = "http://localhost:8000/detect"
files = {"file": open("README.md", "rb")}

response = requests.post(url, files=files)
print(f"Status Code: {response.status_code}")
print(f"Response: {response.json()}")