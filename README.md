# AI Safety Detection System

This is a full-stack web application that integrates two trained YOLO object detection models for real-time detection of weapons, fire, and smoke from live video feed or uploaded footage.

## Features

- Real-time object detection using webcam
- Video file upload for detection
- Two specialized models: Weapon detection and Fire/Smoke detection
- Switch between models dynamically
- Visual alerts when objects are detected
- Responsive UI with dark/light mode toggle

## Project Structure

```
├── backend/
│   ├── models/
│   │   ├── weapon.pt
│   │   └── fire_smoke.pt
│   ├── main.py
│   ├── requirements.txt
│   └── .env
└── frontend/
    ├── src/
    ├── package.json
    └── ...
```

## Setup Instructions

### Backend Setup

1. Navigate to the backend directory:
   ```
   cd backend
   ```

2. Create a virtual environment (optional but recommended):
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install the required Python packages:
   ```
   pip install -r requirements.txt
   ```

4. Ensure your YOLO model files are in the [backend/models](file:///c%3A/CyberisAl/backend/models) directory:
   - [weapon.pt](file:///c%3A/CyberisAl/backend/models/weapon.pt)
   - [fire_smoke.pt](file:///c%3A/CyberisAl/backend/models/fire_smoke.pt)

5. Start the backend server:
   
   On Windows, you can double-click the `start_server.bat` file or run:
   ```
   python main.py
   ```
   
   The backend will start on `http://localhost:8000`

### Frontend Setup

1. Navigate to the frontend directory:
   ```
   cd frontend
   ```

2. Install the required Node packages:
   ```
   npm install
   ```

3. Start the development server:
   
   On Windows, you can double-click the `start_dev.bat` file or run:
   ```
   npm run dev
   ```
   
   The frontend will start on `http://localhost:3000` (or the next available port if 3000 is in use)

## API Endpoints

- `GET /` - Health check
- `GET /models` - Get available models
- `POST /models/switch` - Switch between models
- `POST /detect` - Detect objects in an image
- `POST /detect/both` - Detect objects using both models

## Usage

1. Open your browser and go to `http://localhost:3000`
2. Select the detection model (Weapon or Fire/Smoke)
3. Start the camera or upload a video/image
4. View detection results in real-time

## Environment Variables

Create a `.env` file in the backend directory with the following variables:

```
MODEL_WEAPON_PATH=models/weapon.pt
MODEL_FIRE_SMOKE_PATH=models/fire_smoke.pt
HOST=localhost
PORT=8000
```

## Dependencies

### Backend
- FastAPI
- Ultralytics (YOLOv8)
- OpenCV
- PyTorch
- NumPy

### Frontend
- React
- Tailwind CSS
- Axios

## Troubleshooting

1. If you encounter CUDA errors, make sure you have the appropriate PyTorch version for your system
2. If the camera doesn't work, check browser permissions
3. Ensure both model files are present in the [backend/models](file:///c%3A/CyberisAl/backend/models) directory