import cv2
from ultralytics import YOLO

model = YOLO('models/best.pt')
cap = cv2.VideoCapture('uploads/input_video.mp4')
ret, frame = cap.read()
if ret:
    frame = cv2.resize(frame, (1280, 720))
    results = model(frame, conf=0.01, iou=0.45, imgsz=1280, verbose=False)[0]
    print(f"Number of detections at 0.01: {len(results.boxes)}")
    if len(results.boxes) > 0:
        for i, box in enumerate(results.boxes):
            cls_id = int(box.cls[0])
            conf = float(box.conf[0])
            print(f"Detection {i}: class ID: {cls_id}, label: {model.names[cls_id]}, conf: {conf}")
else:
    print("Could not read frame")
