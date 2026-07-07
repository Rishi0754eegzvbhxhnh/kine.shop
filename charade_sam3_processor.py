import os
import sys
import json
import cv2
import numpy as np
import torch
from ultralytics import YOLOWorld
from PIL import Image

# Make sure sam3 is in path
sys.path.append(os.path.abspath("sam3"))
from sam3 import build_sam3_image_model
from sam3.model.sam3_image_processor import Sam3Processor
from sam3.visualization_utils import normalize_bbox

# Classes and mapping
SELECTED_CLASSES = [
    "coat", "shoe", "t-shirt", "pants", "dress", "chair", "table", "tv", 
    "person", "bag", "sunglasses", "hat", "furniture", "food"
]

CATEGORY_MAP = {
    "chair": "Furniture", "tie": "Fashion", "umbrella": "Accessories",
    "cup": "Kitchen", "bottle": "Kitchen", "tv": "Electronics",
    "book": "Books", "laptop": "Electronics", "cell phone": "Electronics",
    "handbag": "Fashion", "vase": "Home Decor", "suitcase": "Travel",
    "remote": "Electronics", "wine glass": "Kitchen", "bowl": "Kitchen",
    "teddy bear": "Toys", "skateboard": "Sports", "skis": "Sports",
    "surfboard": "Sports",
}

def generate_masks():
    print("Initializing YOLO-World and SAM3 Models...")
    
    # Initialize YOLO-World
    yolo_model = YOLOWorld('yolov8s-world.pt')
    yolo_model.set_classes(SELECTED_CLASSES)
    
    # Initialize SAM3
    sam3_root = "sam3"
    bpe_path = os.path.join("sam3", "sam3", "assets", "bpe_simple_vocab_16e6.txt.gz")
    print(f"Loading SAM3 model with BPE path: {bpe_path}")
    
    sam3_model = build_sam3_image_model(bpe_path=bpe_path)
    sam3_model.eval()
    
    processor = Sam3Processor(sam3_model, confidence_threshold=0.5)
    
    timeline_data = {}
    
    # Check if Charade_Frames exists
    frames_dir = "Charade_Frames"
    if not os.path.exists(frames_dir):
        print(f"Error: {frames_dir} not found. Please extract Charade_1963.mp4 frames first.")
        return
        
    frames = sorted([f for f in os.listdir(frames_dir) if f.endswith('.jpg')])
    
    # We will process 1 frame every 24 frames to simulate 1 FPS
    # Assuming 24fps video
    frame_interval = 24
    
    second = 0
    for i in range(0, len(frames), frame_interval):
        frame_file = frames[i]
        frame_path = os.path.join(frames_dir, frame_file)
        print(f"Processing second {second}: {frame_file}")
        
        # Load image for YOLO and SAM3
        image_np = cv2.imread(frame_path)
        image_rgb = cv2.cvtColor(image_np, cv2.COLOR_BGR2RGB)
        height, width = image_rgb.shape[:2]
        
        # Pass image to SAM3 processor
        image_pil = Image.fromarray(image_rgb)
        inference_state = processor.set_image(image_pil)
        
        # 1. Get Bounding Boxes from YOLO
        yolo_results = yolo_model.predict(frame_path, conf=0.1, verbose=False)
        frame_data = []
        
        df = yolo_results[0].boxes.data.cpu().numpy()
        for row in df:
            x1, y1, x2, y2, conf, cls_id = row
            label = SELECTED_CLASSES[int(cls_id)]
            
            # Convert xyxy to cxcywh
            w = x2 - x1
            h = y2 - y1
            cx = x1 + w/2
            cy = y1 + h/2
            
            # Normalize bounding box for SAM3 prompt
            box_cxcywh = torch.tensor([[cx, cy, w, h]], dtype=torch.float32)
            norm_box = normalize_bbox(box_cxcywh, width, height).flatten().tolist()
            
            # Reset prompts for each object
            processor.reset_all_prompts(inference_state)
            
            # 2. Get Pixel Mask from SAM3
            inference_state = processor.add_geometric_prompt(
                state=inference_state, box=norm_box, label=True
            )
            
            # Extract mask
            mask_points_percent = []
            if inference_state and "out_binary_masks" in inference_state:
                binary_masks = inference_state["out_binary_masks"]
                if len(binary_masks) > 0:
                    # Get the first mask
                    mask_tensor = binary_masks[-1] # Usually the last added prompt result
                    # SAM3 mask shape might be [1, 1, H, W] or [H, W]. Let's squeeze it
                    mask_np = mask_tensor.squeeze().cpu().numpy().astype(np.uint8)
                    
                    if np.any(mask_np):
                        # Resize mask to original image size if it's not already
                        if mask_np.shape != (height, width):
                            mask_np = cv2.resize(mask_np, (width, height), interpolation=cv2.INTER_NEAREST)
                            
                        # Find contours
                        contours, _ = cv2.findContours(mask_np, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                        if contours:
                            largest_contour = max(contours, key=cv2.contourArea)
                            
                            # Simplify contour
                            epsilon = 0.01 * cv2.arcLength(largest_contour, True)
                            approx = cv2.approxPolyDP(largest_contour, epsilon, True)
                            
                            for pt in approx:
                                px, py = pt[0]
                                mask_points_percent.append([
                                    round((px / width) * 100, 2),
                                    round((py / height) * 100, 2)
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
        second += 1
        
        # Uncomment the lines below if you want to limit the processing time for testing
        # if second >= 10:
        #     break
            
    with open("sam3_charade_timeline.json", "w") as f:
        json.dump(timeline_data, f, indent=2)
        
    print("Timeline data with actual SAM3 polygon masks saved to sam3_charade_timeline.json")

if __name__ == "__main__":
    generate_masks()
