import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import './App.css';

function App() {
  const [currentModel, setCurrentModel] = useState('weapon');
  const [detectionResults, setDetectionResults] = useState([]);
  const [alertMessage, setAlertMessage] = useState('');
  const [isCameraActive, setIsCameraActive] = useState(false);
  const [processedImage, setProcessedImage] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);

  // Initialize and get available models
  useEffect(() => {
    const fetchModels = async () => {
      try {
        const response = await axios.get('http://localhost:8000/models');
        setCurrentModel(response.data.current_model);
      } catch (error) {
        console.error('Error fetching models:', error);
      }
    };

    fetchModels();
  }, []);

  // Start camera
  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true });
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        streamRef.current = stream;
        setIsCameraActive(true);
      }
    } catch (err) {
      console.error('Error accessing camera:', err);
      setAlertMessage('Could not access camera. Please check permissions.');
    }
  };

  // Stop camera
  const stopCamera = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
      streamRef.current = null;
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
    setIsCameraActive(false);
  };

  // Capture frame from video and send for detection
  const captureAndDetect = async () => {
    if (!videoRef.current || !canvasRef.current) return;

    const video = videoRef.current;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');

    // Set canvas dimensions to match video
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    // Draw video frame to canvas
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

    // Convert canvas to blob and send for detection
    canvas.toBlob(async (blob) => {
      const formData = new FormData();
      formData.append('file', blob, 'frame.jpg');

      try {
        setIsLoading(true);
        const response = await axios.post(`http://localhost:8000/detect`, formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        });

        // Check if response contains error
        if (response.data.error) {
          setAlertMessage(`Error: ${response.data.error}`);
          setDetectionResults([]);
          setProcessedImage(null);
          return;
        }

        // Set detection results and image
        setDetectionResults(response.data.detections || []);
        setProcessedImage(response.data.image ? `data:image/jpeg;base64,${response.data.image}` : null);
        
        // Check for alerts
        const detections = response.data.detections || [];
        const alerts = detections.map(d => d.class);
        if (alerts.length > 0) {
          setAlertMessage(`${alerts.join(', ')} detected!`);
        } else {
          setAlertMessage('');
        }
      } catch (error) {
        console.error('Detection error:', error);
        setAlertMessage('Detection failed. Please try again.');
        setDetectionResults([]);
        setProcessedImage(null);
      } finally {
        setIsLoading(false);
      }
    }, 'image/jpeg');
  };

  // Handle file upload
  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    try {
      setIsLoading(true);
      const response = await axios.post('http://localhost:8000/detect', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      // Check if response contains error
      if (response.data.error) {
        setAlertMessage(`Error: ${response.data.error}`);
        setDetectionResults([]);
        setProcessedImage(null);
        return;
      }

      // Set detection results and image
      setDetectionResults(response.data.detections || []);
      setProcessedImage(response.data.image ? `data:image/jpeg;base64,${response.data.image}` : null);
      
      // Check for alerts
      const detections = response.data.detections || [];
      const alerts = detections.map(d => d.class);
      if (alerts.length > 0) {
        setAlertMessage(`${alerts.join(', ')} detected!`);
      } else {
        setAlertMessage('');
      }
    } catch (error) {
      console.error('Upload error:', error);
      setAlertMessage('Upload failed. Please try again.');
      setDetectionResults([]);
      setProcessedImage(null);
    } finally {
      setIsLoading(false);
    }
  };

  // Switch model
  const switchModel = async (model) => {
    try {
      const formData = new FormData();
      formData.append('model_name', model);
      await axios.post('http://localhost:8000/models/switch', formData);
      setCurrentModel(model);
      setAlertMessage(`Switched to ${model} detection model`);
    } catch (error) {
      console.error('Model switch error:', error);
      setAlertMessage('Failed to switch model');
    }
  };

  // Continuous detection when camera is active
  useEffect(() => {
    let interval;
    if (isCameraActive) {
      interval = setInterval(captureAndDetect, 500); // Detect every 500ms
    }
    return () => clearInterval(interval);
  }, [isCameraActive]);

  return (
    <div className="min-h-screen bg-gray-100 dark:bg-gray-900 text-gray-900 dark:text-white transition-colors duration-200">
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 shadow">
        <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8 flex justify-between items-center">
          <h1 className="text-3xl font-bold text-indigo-600">AI Safety Detection System</h1>
          <div className="flex space-x-4">
            <button 
              onClick={() => document.documentElement.classList.toggle('dark')}
              className="px-4 py-2 bg-gray-200 dark:bg-gray-700 rounded-md hover:bg-gray-300 dark:hover:bg-gray-600 transition"
            >
              Toggle Theme
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        {/* Model Selection */}
        <div className="mb-8 p-6 bg-white dark:bg-gray-800 rounded-lg shadow">
          <h2 className="text-xl font-semibold mb-4">Select Detection Model</h2>
          <div className="flex space-x-4">
            <button
              onClick={() => switchModel('weapon')}
              className={`px-6 py-3 rounded-md font-medium ${
                currentModel === 'weapon'
                  ? 'bg-red-600 text-white'
                  : 'bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600'
              }`}
            >
              Weapon Detection
            </button>
            <button
              onClick={() => switchModel('fire_smoke')}
              className={`px-6 py-3 rounded-md font-medium ${
                currentModel === 'fire_smoke'
                  ? 'bg-orange-600 text-white'
                  : 'bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600'
              }`}
            >
              Fire & Smoke Detection
            </button>
          </div>
        </div>

        {/* Camera and Controls */}
        <div className="mb-8 p-6 bg-white dark:bg-gray-800 rounded-lg shadow">
          <h2 className="text-xl font-semibold mb-4">Video Source</h2>
          
          {/* Camera Preview */}
          <div className="mb-6">
            <div className="relative">
              <video
                ref={videoRef}
                autoPlay
                muted
                className="w-full max-w-2xl mx-auto rounded-lg border-2 border-gray-300 dark:border-gray-600"
              />
              <canvas ref={canvasRef} className="hidden" />
              
              {/* Processed Image Overlay */}
              {processedImage && (
                <img
                  src={processedImage}
                  alt="Processed"
                  className="w-full max-w-2xl mx-auto rounded-lg border-2 border-gray-300 dark:border-gray-600 mt-4"
                />
              )}
            </div>
          </div>

          {/* Controls */}
          <div className="flex flex-wrap gap-4 justify-center">
            {!isCameraActive ? (
              <button
                onClick={startCamera}
                className="px-6 py-3 bg-green-600 text-white rounded-md hover:bg-green-700 font-medium"
              >
                Start Camera
              </button>
            ) : (
              <button
                onClick={stopCamera}
                className="px-6 py-3 bg-red-600 text-white rounded-md hover:bg-red-700 font-medium"
              >
                Stop Camera
              </button>
            )}
            
            <label className="px-6 py-3 bg-blue-600 text-white rounded-md hover:bg-blue-700 font-medium cursor-pointer">
              Upload Video
              <input
                type="file"
                accept="video/*,image/*"
                onChange={handleFileUpload}
                className="hidden"
              />
            </label>
          </div>
        </div>

        {/* Alerts */}
        {alertMessage && (
          <div className="mb-8 p-4 bg-yellow-100 dark:bg-yellow-900 border-l-4 border-yellow-500 text-yellow-700 dark:text-yellow-200">
            <p className="font-bold">Alert!</p>
            <p>{alertMessage}</p>
          </div>
        )}

        {/* Results */}
        <div className="p-6 bg-white dark:bg-gray-800 rounded-lg shadow">
          <h2 className="text-xl font-semibold mb-4">Detection Results</h2>
          
          {isLoading && (
            <div className="text-center py-4">
              <p>Processing...</p>
            </div>
          )}
          
          {(Array.isArray(detectionResults) && detectionResults.length > 0) ? (
            <div>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {detectionResults.map((detection, index) => (
                  <div key={index} className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
                    <h3 className="font-semibold">{detection.class}</h3>
                    <p>Confidence: {(detection.confidence * 100).toFixed(2)}%</p>
                    <p>
                      Box: ({detection.box.x1}, {detection.box.y1}) to ({detection.box.x2}, {detection.box.y2})
                    </p>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <p className="text-gray-500 dark:text-gray-400">
              {isLoading ? '' : 'No detections yet. Start the camera or upload a video to begin.'}
            </p>
          )}
        </div>
      </main>

      <footer className="mt-12 py-6 bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <p className="text-center text-gray-500 dark:text-gray-400">
            AI Safety Detection System - Real-time Object Detection
          </p>
        </div>
      </footer>
    </div>
  );
}

export default App;