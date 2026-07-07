from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
import torch
import pandas as pd
import io
from PIL import Image
import uvicorn
import logging
import cv2
import tempfile
import os

app = FastAPI(title="ML Detection Service")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ─── Logic from detections.py ──────────────────────────────────────────────────

# Open vocabulary classes for YOLO-World (All 80 COCO classes)
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

# Category mapping
CATEGORY_MAP = {
    "chair":      "Furniture", "couch": "Furniture", "bed": "Furniture", "dining table": "Furniture",
    "tie":        "Fashion", "backpack": "Fashion", "handbag": "Fashion", "suitcase": "Travel",
    "umbrella":   "Accessories", "bottle": "Kitchen", "cup": "Kitchen", "wine glass": "Kitchen",
    "bowl":       "Kitchen", "fork": "Kitchen", "knife": "Kitchen", "spoon": "Kitchen",
    "tv":         "Electronics", "laptop": "Electronics", "cell phone": "Electronics",
    "remote":     "Electronics", "mouse": "Electronics", "keyboard": "Electronics",
    "microwave":  "Appliances", "oven": "Appliances", "refrigerator": "Appliances",
    "book":       "Books", "vase": "Home Decor", "clock": "Home Decor", "teddy bear": "Toys",
    "skateboard": "Sports", "skis": "Sports", "surfboard": "Sports", "person": "Fashion"
}

# Product name mapping
PRODUCT_MAP = {
    "chair":      "Ergonomic Office Chair",
    "tie":        "Premium Silk Tie",
    "umbrella":   "Travel Umbrella",
    "cup":        "Ceramic Coffee Mug",
    "bottle":     "Hydro Flask Bottle",
    "tv":         "Samsung Smart TV",
    "wine glass": "Crystal Wine Glass Set",
    "book":       "Business Strategy Book",
    "bowl":       "Ceramic Bowl Set",
    "laptop":     "MacBook Air",
    "cell phone": "iPhone 15",
    "remote":     "Universal Remote",
    "suitcase":   "Travel Suitcase",
    "handbag":    "Leather Handbag",
    "vase":       "Decorative Vase",
    "skateboard": "Street Skateboard",
    "teddy bear": "Plush Teddy Bear",
    "skis":       "All-Mountain Skis",
    "surfboard":  "Beginner Surfboard",
}

# Price mapping
PRICE_MAP = {
    "chair":      149, "tie":         29, "umbrella":    24, "cup":         12,
    "bottle":      35, "tv":         699, "wine glass":  45, "book":        15,
    "bowl":        20, "laptop":     999, "cell phone": 799, "remote":      25,
    "suitcase":    89, "handbag":     79, "vase":        30, "skateboard": 120,
    "teddy bear":  18, "skis":       450, "surfboard":  350,
}

import random

logger.info("Loading YOLO-World model...")
from ultralytics import YOLOWorld
model = YOLOWorld('yolov8s-world.pt')
model.set_classes(SELECTED_CLASSES)
logger.info("Model loaded successfully.")


def enrich_detection(label: str, conf: float, box: dict) -> dict:
    """Attach product info from detections.py mappings to a raw YOLO detection."""
    return {
        "label":        label,
        "confidence":   conf,
        "box":          box,
        "category":     CATEGORY_MAP.get(label, "General"),
        "product_name": PRODUCT_MAP.get(label, label.title()),
        "price":        PRICE_MAP.get(label, random.randint(20, 200)),
        "shop_url":     f"https://www.amazon.com/s?k={label.replace(' ', '+')}"
    }


# ─── Endpoints ─────────────────────────────────────────────────────────────────

@app.post("/api/detect")
async def detect_objects(file: UploadFile = File(...)):
    """Detect shoppable objects in a single image (mirrors yolov8.py frame logic)."""
    try:
        image = Image.open(io.BytesIO(await file.read()))
        results = model.predict(image, conf=0.1)

        detections = []
        df = results[0].boxes.data.cpu().numpy()
        for row in df:
            x1, y1, x2, y2, conf, cls_id = row
            label = SELECTED_CLASSES[int(cls_id)]
            
            if label not in SELECTED_CLASSES:
                continue

            detections.append(enrich_detection(
                label, float(conf),
                {"x1": float(x1), "y1": float(y1), "x2": float(x2), "y2": float(y2)}
            ))

        return JSONResponse(content={"status": "success", "detections": detections})

    except Exception as e:
        logger.error(f"Detection error: {e}")
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})


@app.post("/api/analyze-video")
async def analyze_video(file: UploadFile = File(...)):
    """
    Process video frame by frame and return a per-frame timeline with product data.
    """
    try:
        fd, temp_path = tempfile.mkstemp(suffix=".mp4")
        with os.fdopen(fd, "wb") as f:
            f.write(await file.read())

        logger.info(f"Processing video: {temp_path}")
        cap = cv2.VideoCapture(temp_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_interval = 1  # Frame-by-frame processing!

        timeline = {}
        frame_count = 0

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            if frame_count % frame_interval == 0:
                # ── YOLO-World detection core ──
                results = model.predict(frame, conf=0.1, verbose=False)
                detections = []

                df = results[0].boxes.data.cpu().numpy()
                for row in df:
                    x1, y1, x2, y2, conf, cls_id = row
                    label = SELECTED_CLASSES[int(cls_id)]

                    if label not in SELECTED_CLASSES:
                        continue

                    # ── detections.py enrichment ──
                    detections.append(enrich_detection(
                        label, float(conf),
                        {"x1": float(x1), "y1": float(y1), "x2": float(x2), "y2": float(y2)}
                    ))

                timeline[str(frame_count)] = detections

            frame_count += 1

        cap.release()
        os.remove(temp_path)
        logger.info(f"Done. {frame_count} frames analyzed.")

        return JSONResponse(content={"status": "success", "timeline": timeline})

    except Exception as e:
        logger.error(f"Video processing error: {e}")
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e)})


@app.get("/health")
def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
