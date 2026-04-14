import cv2
from ultralytics import YOLO

with open('debug_output2.txt', 'w') as f:
    model = YOLO('models/best.pt')
    cap = cv2.VideoCapture('uploads/input_video.mp4')
    ret, frame = cap.read()
    if ret:
        for size in [640, 1280, 1920]:
            if size == 640:
                fr = cv2.resize(frame, (640, 360))
            else:
                fr = cv2.resize(frame, (1280, 720))
                
            for conf in [0.05, 0.1, 0.25]:
                results = model(fr, conf=conf, iou=0.45, imgsz=size, verbose=False)[0]
                f.write(f"Size: {size}, Conf: {conf}, Detections: {len(results.boxes)}\n")
    else:
        f.write("Could not read frame\n")
