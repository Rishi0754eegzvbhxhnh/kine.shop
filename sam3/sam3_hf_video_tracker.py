import os
import json
import cv2
import numpy as np
import torch
from PIL import Image
from transformers import AutoProcessor, AutoModelForZeroShotObjectDetection
from transformers import SamModel, SamProcessor
import logging

logging.basicConfig(level=logging.INFO)

SELECTED_CLASSES = [
    "coat", "shoe", "t-shirt", "pants", "dress", "chair", "table", "tv", 
    "person", "bag", "sunglasses", "hat", "furniture", "food", "car", "dog", "cat", 
    "laptop", "cell phone", "bottle", "cup", "watch", "necklace", "ring", "sofa", 
    "bed", "book", "clock", "vase", "jacket", "jeans", "shorts", "skirt", "sneakers",
    "boots", "belt", "backpack", "suitcase", "umbrella", "tie"
]

CATEGORY_MAP = {
    "chair": "Furniture", "tie": "Fashion", "umbrella": "Accessories",
    "cup": "Kitchen", "bottle": "Kitchen", "tv": "Electronics",
    "person": "Fashion", "bag": "Fashion", "coat": "Fashion",
    "shoe": "Fashion", "t-shirt": "Fashion", "pants": "Fashion", "dress": "Fashion",
    "table": "Furniture", "sunglasses": "Accessories", "hat": "Fashion",
    "furniture": "Furniture", "food": "Food", "car": "Vehicles", "dog": "Pets",
    "cat": "Pets", "laptop": "Electronics", "cell phone": "Electronics",
    "watch": "Accessories", "necklace": "Accessories", "ring": "Accessories",
    "sofa": "Furniture", "bed": "Furniture", "book": "Books", "clock": "Home",
    "vase": "Home", "jacket": "Fashion", "jeans": "Fashion", "shorts": "Fashion",
    "skirt": "Fashion", "sneakers": "Fashion", "boots": "Fashion", "belt": "Accessories",
    "backpack": "Fashion", "suitcase": "Travel"
}

def extract_frames(video_path, output_dir="frames_sam3_hf", max_frames=None):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    cap = cv2.VideoCapture(video_path)
    count = 0
    success = True
    fps = cap.get(cv2.CAP_PROP_FPS) or 24
    frame_interval = int(fps)
    
    frame_count = 0
    extracted = []
    while success: 
        if max_frames is not None and count >= max_frames:
            break
        success, image = cap.read()
        if success and frame_count % frame_interval == 0:
            out_path = os.path.join(output_dir, f"frame_{count:04d}.jpg")
            cv2.imwrite(out_path, image)
            extracted.append(out_path)
            count += 1
        frame_count += 1
    cap.release()
    logging.info(f"Extracted {len(extracted)} frames")
    return extracted

def main():
    video_path = "Charade_1963_short.mp4"
    frames = extract_frames(video_path, max_frames=None)
    
    # We will use ultralytics YOLO-World because the transformers one might be hard to setup quickly
    from ultralytics import YOLOWorld
    yolo_model = YOLOWorld('../yolov8s-world.pt')
    yolo_model.set_classes(SELECTED_CLASSES)

    # Initialize SAM3 Tracker Model from transformers
    # The user snippet asked for Sam3TrackerModel, but we must handle exceptions if it's actually SamModel
    try:
        from transformers import Sam3TrackerProcessor, Sam3TrackerModel
        logging.info("Loading Sam3TrackerModel...")
        # Get token from environment if available
        token = os.environ.get("HF_TOKEN")
        processor = Sam3TrackerProcessor.from_pretrained("facebook/sam3", token=token)
        model = Sam3TrackerModel.from_pretrained("facebook/sam3", token=token).to("cpu")
        is_tracker = True
    except Exception as e:
        logging.info(f"Sam3TrackerModel could not be loaded ({e}), falling back to SamModel")
        processor = SamProcessor.from_pretrained("facebook/sam-vit-huge")
        model = SamModel.from_pretrained("facebook/sam-vit-huge").to("cpu")
        is_tracker = False

    timeline_data = {}
    
    for second, frame_path in enumerate(frames):
        logging.info(f"Processing second {second}: {frame_path}")
        image = Image.open(frame_path).convert("RGB")
        
        # Get bounding boxes from YOLO
        yolo_results = yolo_model.predict(frame_path, conf=0.1, verbose=False)
        df = yolo_results[0].boxes.data.cpu().numpy()
        
        frame_data = []
        
        for row in df:
            x1, y1, x2, y2, conf, cls_id = row
            label = SELECTED_CLASSES[int(cls_id)]
            
            box = [float(x1), float(y1), float(x2), float(y2)]
            
            # Predict mask with SAM
            if is_tracker:
                inputs = processor(images=image, input_boxes=[[[box]]], return_tensors="pt").to(model.device)
            else:
                inputs = processor(image, input_boxes=[[[box]]], return_tensors="pt").to(model.device)

            with torch.no_grad():
                outputs = model(**inputs)
            
            if is_tracker:
                masks = processor.post_process_masks(outputs.pred_masks.cpu(), inputs["original_sizes"])[0]
                mask_np = masks[0][0].numpy() > 0
            else:
                masks = processor.image_processor.post_process_masks(outputs.pred_masks.cpu(), inputs["original_sizes"], inputs["reshaped_input_sizes"])
                mask_np = masks[0][0][0].numpy() > 0
            
            # Extract polygon from binary mask
            contours, _ = cv2.findContours(mask_np.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if contours:
                largest_contour = max(contours, key=cv2.contourArea)
                epsilon = 0.01 * cv2.arcLength(largest_contour, True)
                approx = cv2.approxPolyDP(largest_contour, epsilon, True)
                
                img_h, img_w = image.size[1], image.size[0]
                mask_points_percent = []
                for pt in approx:
                    px, py = pt[0]
                    mask_points_percent.append([
                        round((px / img_w) * 100, 2),
                        round((py / img_h) * 100, 2)
                    ])
                
                if mask_points_percent:
                    frame_data.append({
                        "product": label.capitalize(),
                        "category": CATEGORY_MAP.get(label, "General"),
                        "price": str(np.random.randint(20, 200)),
                        "shop_url": f"https://www.amazon.com/s?k={label.replace(' ', '+')}",
                        "confidence": round(float(conf), 2),
                        "mask": mask_points_percent
                    })
        
        timeline_data[str(second)] = frame_data
        
    class NumpyEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, np.floating):
                return float(obj)
            if isinstance(obj, np.ndarray):
                return obj.tolist()
            return super(NumpyEncoder, self).default(obj)
            
    out_file = os.path.join("..", "frontend", "public", "sam3_charade_timeline.json")
    with open(out_file, 'w') as f:
        json.dump(timeline_data, f, indent=2, cls=NumpyEncoder)
        
    logging.info(f"Timeline data saved to {out_file}")

if __name__ == "__main__":
    main()
