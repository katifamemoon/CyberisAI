# Testing Framework for AI Safety Detection System

This directory contains all the test cases for the AI Safety Detection System.

## Directory Structure

```
testing/
├── api_endpoints/      # Tests for API endpoints
├── model_testing/      # Tests for model functionality
└── run_all_tests.py    # Test runner script
```

## Test Categories

### API Endpoints Tests
Tests for all REST API endpoints:
- Health check endpoint (`/`)
- Models endpoints (`/models`, `/models/switch`)
- Detection endpoints (`/detect`, `/detect/both`)

### Model Testing
Tests for specific model functionality and integration tests.

## Running Tests

### Running All Tests
```bash
python testing/run_all_tests.py
```

### Running API Endpoint Tests
```bash
python -m unittest testing.api_endpoints.test_health_check
python -m unittest testing.api_endpoints.test_models_endpoints
python -m unittest testing.api_endpoints.test_detection_endpoints
```

### Running Individual Test Files
```bash
python testing/model_testing/test_fire_detection.py
python testing/model_testing/test_weapon_detection.py
python testing/model_testing/test_both_detections.py
python testing/model_testing/test_model_switching.py
python testing/model_testing/test_upload.py
```

## Test Requirements

- The backend server must be running on `http://localhost:8000`
- Required Python packages: `requests`, `opencv-python`, `numpy`

## Test Descriptions

### API Endpoint Tests
1. **test_health_check.py** - Tests the root endpoint (`/`) to ensure the API is running
2. **test_models_endpoints.py** - Tests model listing and switching functionality
3. **test_detection_endpoints.py** - Tests object detection endpoints with image uploads

### Model Testing
1. **test_fire_detection.py** - Tests fire/smoke detection model with sample images
2. **test_weapon_detection.py** - Tests weapon detection model with sample images
3. **test_both_detections.py** - Tests both models in sequence
4. **test_model_switching.py** - Tests switching between different models
5. **test_upload.py** - Tests file upload functionality

## Expected Results

All tests should pass when the backend server is running and models are properly loaded.