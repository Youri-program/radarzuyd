"""
YOLO Model Handler

Loads YOLO model and runs inference on images.
Filters detections to target classes only.
"""

import os
import cv2
import numpy as np
from ultralytics import YOLO
import config


class YOLODetector:
    """
    YOLO object detection handler
    
    Handles:
    - Loading YOLO model
    - Running inference
    - Filtering to target classes
    - Formatting results
    """
    
    def __init__(self, 
                 model_path=config.MODEL_PATH,
                 target_classes=config.TARGET_CLASSES,
                 confidence_threshold=config.CONFIDENCE_THRESHOLD,
                 device=config.DEVICE):
        """
        Initialize YOLO detector
        
        Args:
            model_path: Path to YOLO model file (.pt, .onnx, .engine)
            target_classes: List of class IDs to detect (e.g., [0, 73, 67])
            confidence_threshold: Minimum confidence (0.0 to 1.0)
            device: "cuda" or "cpu"
        """
        print(f"📦 Loading model: {model_path}")
        print(f"🎯 Target classes: {target_classes}")
        print(f"📊 Confidence threshold: {confidence_threshold}")
        print(f"💻 Device: {device}")
        
        # Check if model file exists locally
        if not os.path.exists(model_path):
            print(f"⚠️  WARNING: Model file not found at '{model_path}'")
            print(f"   Ultralytics will attempt to download it...")
        else:
            abs_path = os.path.abspath(model_path)
            file_size = os.path.getsize(model_path) / (1024 * 1024)  # MB
            print(f"✅ Found local model: {abs_path}")
            print(f"   File size: {file_size:.1f} MB")
        
        # Load model
        self.model = YOLO(model_path)
        self.target_classes = target_classes
        self.confidence_threshold = confidence_threshold
        self.device = device
        
        print("✅ Model loaded successfully!\n")
    
    def detect(self, image):
        """
        Run detection on an image
        
        Args:
            image: numpy array in BGR format (from OpenCV)
            
        Returns:
            List of detections, each containing:
            {
                'class_id': int,
                'class_name': str,
                'confidence': float,
                'bbox': [x1, y1, x2, y2]
            }
        """
        # Run YOLO inference
        results = self.model(image, device=self.device, verbose=False)
        
        # Extract detections
        detections = []
        
        for result in results:
            boxes = result.boxes
            
            for box in boxes:
                # Get detection info
                class_id = int(box.cls[0])
                confidence = float(box.conf[0])
                bbox = box.xyxy[0].cpu().numpy()  # [x1, y1, x2, y2]
                
                # Filter: only target classes and above threshold
                if class_id in self.target_classes and confidence >= self.confidence_threshold:
                    # Get class name
                    class_name = config.CLASS_NAMES.get(class_id, f"class_{class_id}")
                    
                    detections.append({
                        'class_id': class_id,
                        'class_name': class_name,
                        'confidence': confidence,
                        'bbox': bbox.tolist()
                    })
        
        return detections
    
    def draw_detections(self, image, detections):
        """
        Draw bounding boxes on image
        
        Args:
            image: numpy array (BGR)
            detections: List of detections from detect()
            
        Returns:
            Image with bounding boxes drawn
        """
        # Make a copy to avoid modifying original
        img_copy = image.copy()
        
        for det in detections:
            # Get bbox coordinates
            x1, y1, x2, y2 = [int(v) for v in det['bbox']]
            
            # Choose color based on class
            colors = {
                0: (0, 255, 0),    # person = green
                67: (255, 0, 0),   # cell phone = blue
                73: (0, 0, 255)    # book = red
            }
            color = colors.get(det['class_id'], (255, 255, 255))
            
            # Draw rectangle
            cv2.rectangle(img_copy, (x1, y1), (x2, y2), color, 2)
            
            # Draw label
            label = f"{det['class_name']} {det['confidence']:.2f}"
            (text_width, text_height), baseline = cv2.getTextSize(
                label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1
            )
            
            # Draw background for text
            cv2.rectangle(
                img_copy,
                (x1, y1 - text_height - baseline - 5),
                (x1 + text_width, y1),
                color,
                -1
            )
            
            # Draw text
            cv2.putText(
                img_copy,
                label,
                (x1, y1 - baseline - 2),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 255, 255),
                1
            )
        
        return img_copy


# Test code
if __name__ == "__main__":
    """Test the detector with a sample image"""
    import sys
    
    # Create detector
    detector = YOLODetector()
    
    # Load test image
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
    else:
        print("Usage: python3 model.py <image_path>")
        sys.exit(1)
    
    image = cv2.imread(image_path)
    if image is None:
        print(f"❌ Could not load image: {image_path}")
        sys.exit(1)
    
    print(f"📸 Processing: {image_path}")
    
    # Run detection
    detections = detector.detect(image)
    
    # Print results
    print(f"\n✅ Found {len(detections)} detections:")
    for det in detections:
        print(f"  - {det['class_name']}: {det['confidence']:.2%}")
    
    # Draw and save
    if detections:
        img_with_boxes = detector.draw_detections(image, detections)
        output_path = "test_output.jpg"
        cv2.imwrite(output_path, img_with_boxes)
        print(f"\n💾 Saved result to: {output_path}")