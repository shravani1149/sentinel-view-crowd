import json
import os
import boto3
import tempfile
import uuid
from urllib.parse import unquote_plus
import cv2
import numpy as np
from ultralytics import YOLO
from deep_sort_realtime.deepsort_tracker import DeepSort

# S3 configuration
S3_BUCKET = os.environ.get('S3_BUCKET_NAME')
MODELS_BUCKET = os.environ.get('MODELS_BUCKET_NAME')
s3_client = boto3.client('s3')

# Model configuration
IMAGE_MODEL_PATH = 'yolov8n.pt'
VIDEO_MODEL_PATH = 'yolov8n.pt'

# Global state
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

# Initialize models
image_model = None
video_model = None

def download_models():
    try:
        if not os.path.exists(IMAGE_MODEL_PATH):
            s3_client.download_file(MODELS_BUCKET, 'yolov8n.pt', IMAGE_MODEL_PATH)
        if not os.path.exists(VIDEO_MODEL_PATH):
            s3_client.download_file(MODELS_BUCKET, 'yolov8s.pt', VIDEO_MODEL_PATH)
    except Exception as e:
        print(f"Error downloading models: {e}")

def initialize_models():
    global image_model, video_model
    if image_model is None:
        download_models()
        image_model = YOLO(IMAGE_MODEL_PATH)
        video_model = YOLO(VIDEO_MODEL_PATH)

def detect_objects(image, model, person_class_ids, harmful_class_ids):
    results = model(image)
    people = []
    harmful_objects = []
    
    for result in results:
        boxes = result.boxes
        if boxes is not None:
            for box in boxes.boxes:
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

def process_image(image_path):
    global processing_state
    
    try:
        image = cv2.imread(image_path)
        if image is None:
            raise Exception("Could not read image")
        
        person_class_ids = [0]  # COCO person class
        people, harmful_objects = detect_objects(image, image_model, person_class_ids, [])
        
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
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise Exception("Could not open video")
    
    frame_count = 0
    max_frames = 30
    people_counts = []
    person_class_ids = [0]
    
    while frame_count < max_frames and cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        if frame_count % 5 == 0:
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

def lambda_handler(event, context):
    """
    Direct Lambda handler without Flask/Mangum
    """
    try:
        # Parse the request
        http_method = event.get('httpMethod', 'GET')
        path = event.get('path', '/')
        query_params = event.get('queryStringParameters', {}) or {}
        
        # Handle CORS
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS'
        }
        
        # Handle OPTIONS preflight
        if http_method == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({'message': 'CORS preflight'})
            }
        
        # Route handling
        if path == '/prod/proxy/health' or path == '/prod/':
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({
                    "status": "healthy",
                    "processing": processing_state.get("counting", False)
                })
            }
        
        elif path == '/prod/proxy/stats':
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps(processing_state)
            }
        
        elif path == '/prod/proxy/start':
            processing_state['counting'] = True
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({
                    "message": "Processing started", 
                    "counting": True
                })
            }
        
        elif path == '/prod/proxy/stop':
            processing_state['counting'] = False
            return {
                'statusCode': 200,
                'headers': headers,
                'body': json.dumps({
                    "message": "Processing stopped", 
                    "counting": False
                })
            }
        
        elif path == '/prod/proxy/threshold':
            try:
                body = json.loads(event.get('body', '{}'))
                if 'threshold' in body:
                    processing_state['threshold'] = body['threshold']
                return {
                    'statusCode': 200,
                    'headers': headers,
                    'body': json.dumps({
                        "message": "Threshold updated", 
                        "threshold": processing_state['threshold']
                    })
                }
            except Exception as e:
                return {
                    'statusCode': 400,
                    'headers': headers,
                    'body': json.dumps({"error": str(e)})
                }
        
        elif path == '/prod/proxy/upload':
            try:
                # Handle file upload (simplified version)
                return {
                    'statusCode': 200,
                    'headers': headers,
                    'body': json.dumps({
                        "message": "Upload endpoint ready",
                        "note": "File upload processing to be implemented"
                    })
                }
            except Exception as e:
                return {
                    'statusCode': 500,
                    'headers': headers,
                    'body': json.dumps({"error": str(e)})
                }
        
        else:
            return {
                'statusCode': 404,
                'headers': headers,
                'body': json.dumps({
                    "error": "Endpoint not found",
                    "path": path,
                    "available_endpoints": [
                        "/prod/proxy/health",
                        "/prod/proxy/stats",
                        "/prod/proxy/start", 
                        "/prod/proxy/stop",
                        "/prod/proxy/threshold",
                        "/prod/proxy/upload"
                    ]
                })
            }
    
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS'
            },
            'body': json.dumps({
                "error": "Internal server error",
                "details": str(e)
            })
        }
