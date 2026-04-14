import cv2
from ultralytics import YOLO
from deep_sort_realtime.deepsort_tracker import DeepSort

with open('debug_output.txt', 'w') as f:
    model = YOLO('models/best.pt')
    cap = cv2.VideoCapture('uploads/input_video.mp4')
    ret, frame = cap.read()
    if ret:
        frame = cv2.resize(frame, (1280, 720))
        results = model(frame, conf=0.25, iou=0.45, imgsz=1280, verbose=False)[0]
        f.write(f"YOLO conf=0.25 raw detections: {len(results.boxes)}\n")
        
        results_low = model(frame, conf=0.1, iou=0.45, imgsz=1280, verbose=False)[0]
        f.write(f"YOLO conf=0.1 raw detections: {len(results_low.boxes)}\n")
        
        tracker = DeepSort(max_age=40, n_init=2, nms_max_overlap=1.0, max_cosine_distance=0.3)
        detections = []
        for box in results_low.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
            conf = float(box.conf[0])
            class_id = int(box.cls[0])
            detections.append([[x1, y1, x2 - x1, y2 - y1], conf, str(class_id)])
            
        tracks = tracker.update_tracks(detections, frame=frame)
        confirmed = sum(1 for track in tracks if track.is_confirmed())
        f.write(f"DeepSORT tracks total: {len(tracks)}, confirmed: {confirmed}\n")
    else:
        f.write("Could not read frame\n")
