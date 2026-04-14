import json
import os
import boto3
import tempfile
import uuid
from urllib.parse import unquote_plus
from flask import Flask, request, jsonify
from flask_cors import CORS
from mangum import Mangum
import cv2
import numpy as np
from ultralytics import YOLO
from deep_sort_realtime.deepsort_tracker import DeepSort

app = Flask(__name__)
CORS(app)

# S3 configuration for file storage
S3_BUCKET = os.environ.get('S3_BUCKET_NAME')
MODELS_BUCKET = os.environ.get('MODELS_BUCKET_NAME')
s3_client = boto3.client('s3')

# Model configuration - use smaller models for Lambda
IMAGE_MODEL_PATH = 'yolov8n.pt'
VIDEO_MODEL_PATH = 'yolov8n.pt'  # Use smaller model for Lambda

# Download models from S3 on cold start
def download_models():
    try:
        if not os.path.exists(IMAGE_MODEL_PATH):
            s3_client.download_file(MODELS_BUCKET, 'yolov8n.pt', IMAGE_MODEL_PATH)
        if not os.path.exists(VIDEO_MODEL_PATH):
            s3_client.download_file(MODELS_BUCKET, 'yolov8s.pt', VIDEO_MODEL_PATH)
    except Exception as e:
        print(f"Error downloading models: {e}")

# Initialize models
image_model = None
video_model = None

def initialize_models():
    global image_model, video_model
    if image_model is None:
        download_models()
        image_model = YOLO(IMAGE_MODEL_PATH)
        video_model = YOLO(VIDEO_MODEL_PATH)

# Lambda handler
handler = Mangum(app)

# In-memory state (consider using DynamoDB for production)
processing_state = {
    "peopleCount": 0,
    "instantCount": 0,
    "uniqueCount": 0,
    "harmfulObjectCount": 0,
    "harmfulObjectLabels": [],
    "frameVersion": 0,
    "threshold": 50,
    "riskLevel": "safe",
    "counting": False,
    "mediaType": None,
    "processingSeconds": 0,
    "timestamp": "00:00:00"
}

def detect_objects(image, model, person_class_ids, harmful_class_ids):
    results = model(image)
    people = []
    harmful_objects = []
    
    for result in results:
        boxes = result.boxes
        if boxes is not None:
            for box in boxes:
                cls = int(box.cls[0])
                conf = float(box.conf[0])
                
                if cls in person_class_ids and conf > 0.5:
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    people.append({
                        'bbox': [int(x1), int(y1), int(x2), int(y2)],
                        'confidence': conf
                    })
                elif cls in harmful_class_ids and conf > 0.3:
                    harmful_objects.append({
                        'class': model.names[cls],
                        'confidence': conf
                    })
    
    return people, harmful_objects

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        initialize_models()
        
        if 'media' not in request.files:
            return jsonify({"error": "No file uploaded"}), 400
        
        file = request.files['media']
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        # Generate unique filename
        file_id = str(uuid.uuid4())
        filename = f"{file_id}_{file.filename}"
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp_file:
            file.save(tmp_file.name)
            
            # Process the file
            if file.filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                result = process_image(tmp_file.name)
            else:
                result = process_video(tmp_file.name)
            
            # Upload to S3
            s3_client.upload_file(tmp_file.name, S3_BUCKET, f"uploads/{filename}")
            
            # Clean up
            os.unlink(tmp_file.name)
        
        return jsonify({
            "message": "File uploaded successfully",
            "fileId": file_id,
            "result": result
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def process_image(image_path):
    global processing_state
    
    try:
        image = cv2.imread(image_path)
        if image is None:
            raise Exception("Could not read image")
        
        # Get person class IDs
        person_class_ids = [0]  # COCO person class
        
        # Detect people
        people, harmful_objects = detect_objects(image, image_model, person_class_ids, [])
        
        # Update state
        processing_state.update({
            "peopleCount": len(people),
            "instantCount": len(people),
            "uniqueCount": len(people),
            "harmfulObjectCount": len(harmful_objects),
            "harmfulObjectLabels": [obj['class'] for obj in harmful_objects],
            "mediaType": "image",
            "counting": False,
            "timestamp": "00:00:00"
        })
        
        return {
            "peopleCount": len(people),
            "harmfulObjectCount": len(harmful_objects),
            "detections": people
        }
        
    except Exception as e:
        raise Exception(f"Image processing failed: {str(e)}")

def process_video(video_path):
    # For Lambda, we'll process a limited number of frames
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise Exception("Could not open video")
    
    frame_count = 0
    max_frames = 30  # Limit frames for Lambda
    people_counts = []
    
    person_class_ids = [0]  # COCO person class
    
    while frame_count < max_frames and cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        if frame_count % 5 == 0:  # Process every 5th frame
            people, _ = detect_objects(frame, video_model, person_class_ids, [])
            people_counts.append(len(people))
        
        frame_count += 1
    
    cap.release()
    
    avg_people = sum(people_counts) // len(people_counts) if people_counts else 0
    
    processing_state.update({
        "peopleCount": avg_people,
        "instantCount": avg_people,
        "uniqueCount": avg_people,
        "mediaType": "video",
        "counting": False,
        "timestamp": "00:00:00"
    })
    
    return {
        "peopleCount": avg_people,
        "framesProcessed": frame_count
    }

@app.route('/stats', methods=['GET'])
def get_stats():
    return jsonify(processing_state)

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "healthy",
        "processing": processing_state.get("counting", False)
    })

@app.route('/threshold', methods=['POST'])
def update_threshold():
    data = request.get_json()
    if 'threshold' in data:
        processing_state['threshold'] = data['threshold']
    return jsonify({"message": "Threshold updated", "threshold": processing_state['threshold']})

@app.route('/start', methods=['POST'])
def start_processing():
    processing_state['counting'] = True
    return jsonify({"message": "Processing started", "counting": True})

@app.route('/stop', methods=['POST'])
def stop_processing():
    processing_state['counting'] = False
    return jsonify({"message": "Processing stopped", "counting": False})

# Root endpoint
@app.route('/')
def index():
    return jsonify({
        "status": "Sentinel View Lambda Backend is running",
        "version": "1.0.0"
    })

if __name__ == "__main__":
    app.run(debug=True)
