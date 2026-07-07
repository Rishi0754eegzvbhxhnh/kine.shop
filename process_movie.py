import os
import cv2
import torch
import pandas as pd
from pymongo import MongoClient

# Connect to MongoDB (allows overriding via ENV for Docker)
mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
client = MongoClient(mongo_uri)
db = client["shoppablestream"]
collection = db["videoMetadata"]

# Classes and mapping from ml-service (All 80 COCO classes)
SELECTED_CLASSES = [
    "person", "bicycle", "car", "motorcycle", "airplane", "bus", "train", "truck", "boat",
    "traffic light", "fire hydrant", "stop sign", "parking meter", "bench", "bird", "cat",
    "dog", "horse", "sheep", "cow", "elephant", "bear", "zebra", "giraffe", "backpack",
    "umbrella", "handbag", "tie", "suitcase", "frisbee", "skis", "snowboard", "sports ball",
    "kite", "baseball bat", "baseball glove", "skateboard", "surfboard", "tennis racket",
    "bottle", "wine glass", "cup", "fork", "knife", "spoon", "bowl", "banana", "apple",
    "sandwich", "orange", "broccoli", "carrot", "hot dog", "pizza", "donut", "cake", "chair",
    "couch", "potted plant", "bed", "dining table", "toilet", "tv", "laptop", "mouse", "remote",
    "keyboard", "cell phone", "microwave", "oven", "toaster", "sink", "refrigerator", "book",
    "clock", "vase", "scissors", "teddy bear", "hair drier", "toothbrush"
]

CATEGORY_MAP = {
    "chair":      "Furniture", "couch": "Furniture", "bed": "Furniture", "dining table": "Furniture",
    "tie":        "Fashion", "backpack": "Fashion", "handbag": "Fashion", "suitcase": "Travel",
    "umbrella":   "Accessories", "bottle": "Kitchen", "cup": "Kitchen", "wine glass": "Kitchen",
    "bowl":       "Kitchen", "fork": "Kitchen", "knife": "Kitchen", "spoon": "Kitchen",
    "tv":         "Electronics", "laptop": "Electronics", "cell phone": "Electronics",
    "remote":     "Electronics", "mouse": "Electronics", "keyboard": "Electronics",
    "microwave":  "Appliances", "oven": "Appliances", "refrigerator": "Appliances",
    "book":       "Books", "vase": "Home Decor", "clock": "Home Decor", "teddy bear": "Toys",
    "skateboard": "Sports", "skis": "Sports", "surfboard": "Sports", "person": "Fashion",
    "car": "Vehicles", "bicycle": "Vehicles", "motorcycle": "Vehicles", "airplane": "Vehicles",
    "bus": "Vehicles", "train": "Vehicles", "truck": "Vehicles", "boat": "Vehicles"
}

def enrich_detection(label, conf, box):
    return {
        "label": label,
        "confidence": conf,
        "box": box,
        "category": CATEGORY_MAP.get(label, "General"),
        "shop_url": f"https://www.amazon.com/s?k={label.replace(' ', '+')}"
    }

print("Loading YOLO-World model...")
from ultralytics import YOLOWorld
model = YOLOWorld('yolov8s-world.pt')
model.set_classes(SELECTED_CLASSES)

filename = "Charade_1963.mp4"
filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
print(f"Opening video {filepath}")

cap = cv2.VideoCapture(filepath)
fps = cap.get(cv2.CAP_PROP_FPS)
if fps == 0:
    fps = 24
frame_interval = 1  # Process every frame

timeline = {}
frame_count = 0

print(f"Processing entire video frame-by-frame (1 FPS is disabled)...")

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    if frame_count % frame_interval == 0:
        results = model.predict(frame, conf=0.1, verbose=False)
        detections = []
        df = results[0].boxes.data.cpu().numpy()
        for row in df:
            x1, y1, x2, y2, conf, cls_id = row
            label = SELECTED_CLASSES[int(cls_id)]
            if label not in SELECTED_CLASSES:
                continue
            detections.append(enrich_detection(
                label, float(conf), {"x1": float(x1), "y1": float(y1), "x2": float(x2), "y2": float(y2)}
            ))
        
        timeline[str(frame_count)] = detections
        if frame_count % 100 == 0:
            print(f"Processed {frame_count} frames...")

    frame_count += 1

cap.release()
print(f"Finished processing {frame_count} frames. Saving to MongoDB...")

# Upsert into MongoDB
collection.update_one(
    {"filename": filename},
    {"$set": {
        "status": "completed",
        "timeline": timeline,
        "_class": "com.shoppablestream.backend.models.VideoMetadata"
    }},
    upsert=True
)

print("Done!")
