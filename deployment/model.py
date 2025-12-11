"""
YOLO Model Handler - Jetson Compatible Version (YOLOv5 Direct)

Loads YOLO model using cloned YOLOv5 repository directly
No ultralytics package or torch.hub needed!
"""

import os
import sys
import cv2
import numpy as np
import torch
import config

# Add YOLOv5 directory to path
yolov5_path = os.path.join(os.path.dirname(__file__), 'yolov5')
if os.path.exists(yolov5_path):
    sys.path.insert(0, yolov5_path)


class YOLODetector:
    """
    YOLO object detection handler
    
    Compatible with Jetson Nano Python 3.6
    Uses YOLOv5 repository directly (no ultralytics!)
    
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
            raise FileNotFoundError(f"Model not found: {model_path}")
        else:
            abs_path = os.path.abspath(model_path)
            file_size = os.path.getsize(model_path) / (1024 * 1024)  # MB
            print(f"✅ Found local model: {abs_path}")
            print(f"   File size: {file_size:.1f} MB")
        
        # Check if YOLOv5 repo exists
        if not os.path.exists(yolov5_path):
            print(f"⚠️  ERROR: YOLOv5 directory not found at: {yolov5_path}")
            print(f"   Please run: git clone https://github.com/ultralytics/yolov5")
            raise FileNotFoundError(f"YOLOv5 repo not found. Run: git clone https://github.com/ultralytics/yolov5")
        
        print(f"✅ Found YOLOv5 repo: {yolov5_path}")
        
        # Import YOLOv5 model class
        try:
            from models.experimental import attempt_load
            from utils.general import non_max_suppression, scale_coords
            from utils.torch_utils import select_device
            
            # Store utilities for later use
            self.non_max_suppression = non_max_suppression
            self.scale_coords = scale_coords
            
        except ImportError as e:
            print(f"⚠️  ERROR: Could not import YOLOv5 modules")
            print(f"   Make sure YOLOv5 is cloned: git clone https://github.com/ultralytics/yolov5")
            raise e
        
        # Load model
        print("   Loading YOLOv5 model...")
        self.device = select_device(device)
        self.model = attempt_load(model_path, map_location=self.device)
        self.model.eval()
        
        # Get class names
        self.names = self.model.module.names if hasattr(self.model, 'module') else self.model.names
        
        # Store settings
        self.target_classes = target_classes
        self.confidence_threshold = confidence_threshold
        
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
        # Prepare image
        img_height, img_width = image.shape[:2]
        
        # Convert BGR to RGB
        img_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # Resize and pad to model input size
        img_resized = cv2.resize(img_rgb, (640, 640))
        
        # Convert to torch tensor
        img_tensor = torch.from_numpy(img_resized).to(self.device)
        img_tensor = img_tensor.permute(2, 0, 1).float() / 255.0  # HWC to CHW, normalize
        img_tensor = img_tensor.unsqueeze(0)  # Add batch dimension
        
        # Run inference
        with torch.no_grad():
            pred = self.model(img_tensor)[0]
        
        # Apply NMS
        pred = self.non_max_suppression(
            pred, 
            self.confidence_threshold, 
            0.45,  # IoU threshold
            classes=self.target_classes,
            agnostic=False
        )[0]
        
        # Parse detections
        detections = []
        
        if pred is not None and len(pred):
            # Rescale boxes to original image size
            pred[:, :4] = self.scale_coords(img_tensor.shape[2:], pred[:, :4], image.shape).round()
            
            # Process each detection
            for *xyxy, conf, cls in pred:
                class_id = int(cls)
                
                # Get class name
                class_name = self.names[class_id] if class_id < len(self.names) else f"class_{class_id}"
                
                # Use config name if available
                if class_id in config.CLASS_NAMES:
                    class_name = config.CLASS_NAMES[class_id]
                
                # Add detection
                detections.append({
                    'class_id': class_id,
                    'class_name': class_name,
                    'confidence': float(conf),
                    'bbox': [int(xyxy[0]), int(xyxy[1]), int(xyxy[2]), int(xyxy[3])]
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
        if class_id < len(self.names):
            return self.names[class_id]
        
        return f"class_{class_id}"


# Test code
if __name__ == "__main__":
    """Test the detector"""
    print("=" * 60)
    print("YOLO Detector Test (Jetson Compatible - Direct YOLOv5)")
    print("=" * 60)
    
    try:
        # Create detector
        print("\n1️⃣ Initializing detector...")
        detector = YOLODetector()
        
        # Create dummy image
        print("\n2️⃣ Creating test image...")
        test_image = np.zeros((480, 640, 3), dtype=np.uint8)
        
        print("\n3️⃣ Testing detection...")
        detections = detector.detect(test_image)
        
        print(f"✅ Detection test passed!")
        print(f"   Found {len(detections)} detections")
        
        print("\n" + "=" * 60)
        print("🎉 Detector is ready!")
        print("=" * 60)
        
    except FileNotFoundError as e:
        print(f"\n❌ Setup Error: {e}")
        print("\n📝 To fix:")
        print("   cd ~/radarzuyd/deployment")
        print("   git clone https://github.com/ultralytics/yolov5 -b v6.0")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
