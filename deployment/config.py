"""
Configuration for Jetson Nano Object Detection System

This file contains all settings for the detection system.
Edit these values to customize behavior.
"""

# ============================================
# AWS Cloud Configuration
# ============================================

# AWS ping endpoint (for connection check)
AWS_PING_URL = "https://djpawwqotb.execute-api.eu-central-1.amazonaws.com/prod/ping"

# AWS upload endpoint - where detections are sent
AWS_UPLOAD_URL = "https://djpawwqotb.execute-api.eu-central-1.amazonaws.com/prod/upload"

# Unique identifier for this Jetson device
JETSON_ID = "jetson_nano_01"

# Enable/disable AWS uploads (set False for testing without cloud)
ENABLE_UPLOAD = True


# ============================================
# Detection Configuration
# ============================================

# Target classes to detect (COCO dataset class IDs)
# 0  = person
TARGET_CLASSES = [0]

# Class names (for display)
CLASS_NAMES = {
    0: "person"
}

# Minimum confidence threshold (0.0 to 1.0)
# Detections below this confidence are ignored
CONFIDENCE_THRESHOLD = 0.5


# ============================================
# Model Configuration
# ============================================

# Path to YOLO model file
# Supported formats: .pt, .onnx, .engine (when benchmarking is done .engine will be used on jetson nano; converting to tensorRT.)
# YOLOv5 models (Python 3.6+ compatible):
#   - yolov5n.pt (nano - fastest, smallest)
#   - yolov5s.pt (small - good balance)
#   - yolov5m.pt (medium - more accurate)
MODEL_PATH = "models/yolov5n.pt"

# Device to use for inference
# "cuda" = GPU (Jetson Nano)
# "cpu"  = CPU (laptop/testing)
DEVICE = "cuda"


# ============================================
# Camera Configuration
# ============================================

# Camera device index
# 0 = default camera
# 1, 2, etc. = other cameras
CAMERA_INDEX = 0

# Camera resolution
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480

# Target FPS (actual FPS depends on processing speed)
CAMERA_FPS = 30


# ============================================
# Upload Configuration
# ============================================

# Minimum time between uploads of SAME class (seconds)
# Uploads NEW detections immediately, but waits this time
# before re-uploading the same class (prevents flicker spam)
UPLOAD_DEBOUNCE_SECONDS = 3.0

# Upload timeout (seconds)
UPLOAD_TIMEOUT = 5.0


# ============================================
# Display Configuration
# ============================================

# Show video window (set False for headless operation)
SHOW_DISPLAY = True

# Display FPS on video
SHOW_FPS = True

# Display detection count
SHOW_COUNT = True
