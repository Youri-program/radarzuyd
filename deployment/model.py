"""
YOLO Model Handler - Jetson Compatible Version

Loads YOLO model using torch.hub (no ultralytics needed!)
Filters detections to target classes only.
"""

import os
import cv2
import numpy as np
import torch
import config


class YOLODetector:
    """
    YOLO object detection handler
    
    Compatible with Jetson Nano Python 3.6
    Uses torch.hub instead of ultralytics package
    
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
            model_path: Path to YOLO model file (.pt)
            target_classes: List of class IDs to detect (e.g., [0] for person)
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
            print(f"   Torch will attempt to download it...")
        else:
            abs_path = os.path.abspath(model_path)
            file_size = os.path.getsize(model_path) / (1024 * 1024)  # MB
            print(f"✅ Found local model: {abs_path}")
            print(f"   File size: {file_size:.1f} MB")
        
        # Load model using torch.hub (works without ultralytics!)
        print("   Loading YOLOv5 via torch.hub...")
        
        # Option 1: Load custom weights
        if os.path.exists(model_path):
            # Load YOLOv5 from torch hub, then load custom weights
            self.model = torch.hub.load('ultralytics/yolov5', 'custom', path=model_path, force_reload=False)
        else:
            # Load pre-trained model
            model_name = os.path.basename(model_path).replace('.pt', '')
            self.model = torch.hub.load('ultralytics/yolov5', model_name)
        
        # Configure model
        self.model.to(device)
        self.model.conf = confidence_threshold  # Confidence threshold
        self.model.classes = target_classes if target_classes else None  # Filter classes
        
        self.target_classes = target_classes
        self.confidence_threshold = confidence_threshold
        self.device = device
        
        print("✅ Model loaded successfully!\n")
    
    def detect(self, image):
        """
        Run detection on an image
        
        Args:
            image: numpy array (BGR format from OpenCV)
            
        Returns:
            List of detection dictionaries:
            [
                {
                    'class_id': int,
                    'class_name': str,
                    'confidence': float,
                    'bbox': [x1, y1, x2, y2]
                },
                ...
            ]
        """
        # Run inference
        results = self.model(image)
        
        # Parse results
        detections = []
        
        # Get predictions (results.xyxy[0] format: x1, y1, x2, y2, conf, class)
        predictions = results.xyxy[0].cpu().numpy()
        
        for pred in predictions:
            x1, y1, x2, y2, conf, cls = pred
            class_id = int(cls)
            
            # Filter by target classes (if specified)
            if self.target_classes and class_id not in self.target_classes:
                continue
            
            # Filter by confidence
            if conf < self.confidence_threshold:
                continue
            
            # Get class name
            class_name = results.names[class_id]
            
            # Add to detections
            detections.append({
                'class_id': class_id,
                'class_name': class_name,
                'confidence': float(conf),
                'bbox': [int(x1), int(y1), int(x2), int(y2)]
            })
        
        return detections
    
    def get_class_name(self, class_id):
        """
        Get class name from class ID
        
        Args:
            class_id: COCO class ID
            
        Returns:
            Class name string
        """
        # Use config mapping if available
        if class_id in config.CLASS_NAMES:
            return config.CLASS_NAMES[class_id]
        
        # Otherwise use model's names
        return self.model.names[class_id]


# Test code
if __name__ == "__main__":
    """Test the detector"""
    print("=" * 50)
    print("YOLO Detector Test (Jetson Compatible)")
    print("=" * 50)
    
    try:
        # Create detector
        detector = YOLODetector()
        
        # Create dummy image
        test_image = np.zeros((480, 640, 3), dtype=np.uint8)
        
        print("\n📸 Testing detection on dummy image...")
        detections = detector.detect(test_image)
        
        print(f"✅ Detection test passed!")
        print(f"   Found {len(detections)} detections")
        
        print("\n🎉 Detector is ready!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
