# YOLOv5 Edge Deployment System

Real-time object detection on NVIDIA Jetson Orin Nano with AWS cloud integration.

---

## Overview

This deployment system runs YOLOv5 object detection on edge hardware, detects specific object class (person), and uploads detections to AWS cloud storage.

**Target Platform:** NVIDIA Jetson Orin Nano  
**JetPack Version:** 6.1
**Python Version:** 3.10

---

## Quick Start

### 1. Setup (First Time Only)

```bash
# Clone repository
git clone https://github.com/Youri-program/radarzuyd
cd radarzuyd/deployment

# Create virtual environment
python3 -m venv ~/yolo_env
source ~/yolo_env/bin/activate

# Install PyTorch with CUDA
pip3 install torch torchvision --index-url https://download.pytorch.org/whl/cu118

# Install dependencies
pip3 install -r requirements.txt

# Download model
python3 download_models.py
```

**See [SETUP_ORIN.md](SETUP_ORIN.md) for detailed setup instructions.**

---

### 2. Run Detection

```bash
# Activate environment
source ~/yolo_env/bin/activate

# Test with image
python3 main.py --mode image --image testimages/test_image3.jpg

# Run camera detection
python3 main.py --mode camera

# Camera without AWS upload (testing)
python3 main.py --mode camera --no-upload
```

---

## Configuration

Edit `config.py` to customize:

```python
# AWS Settings
AWS_UPLOAD_URL = "your-aws-endpoint"
JETSON_ID = "jetson_orin_01"

# Detection Settings
TARGET_CLASSES = [0, 73, 67]  # person, book, cell phone
CONFIDENCE_THRESHOLD = 0.5

# Model Settings
MODEL_PATH = "models/yolov5n.pt"
DEVICE = "cuda"  # Use GPU

# Camera Settings (for camera mode)
CAMERA_INDEX = 0
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
```

---

## Usage Examples

### Single Image Detection

```bash
python3 main.py --mode image --image path/to/image.jpg
```

### Camera Feed (with AWS upload)

```bash
python3 main.py --mode camera
```

### Camera Feed (no upload, testing)

```bash
python3 main.py --mode camera --no-upload
```

### Using Different Model

```bash
python3 main.py --mode camera --model models/yolov5s.pt
```

### Custom Confidence Threshold

```bash
python3 main.py --mode camera --confidence 0.3
```

---

## Performance

**On Jetson Orin Nano (YOLOv5n):**
- **FPS:** 25-35 FPS (with GPU)
- **Latency:** ~30-40ms per frame
- **Memory:** ~2GB

**Optimization Tips:**
1. Use max performance mode: `sudo nvpmodel -m 0 && sudo jetson_clocks`
2. Use smaller models (yolov5n) for speed
3. Reduce camera resolution if needed
4. Monitor with `jtop`

---

## System Architecture

```
┌─────────────┐
│   Camera    │
│  /Image     │
└──────┬──────┘
       │
       ▼
┌──────────────────┐
│  YOLOv5 Model    │ ← GPU Accelerated
│  (model.py)      │
└─────────┬────────┘
          │
          ▼
┌──────────────────────┐
│  Filter Detections   │ ← Only [0, 73, 67]
│  (camera/image       │
│   _detector.py)      │
└──────────┬───────────┘
           │
           ▼
┌──────────────────────┐
│  AWS Uploader        │ ← Cloud Integration
│  (aws_uploader.py)   │
└──────────────────────┘
```

---

## Requirements Coverage

This deployment addresses the following project requirements:

//

---

## Troubleshooting

### CUDA Not Available

```bash
# Verify CUDA
python3 -c "import torch; print(torch.cuda.is_available())"

# Should print: True
# If False, reinstall PyTorch with CUDA support
```

### Camera Not Found

```bash
# List available cameras
ls /dev/video*

# Try different index in config.py
CAMERA_INDEX = 1  # or 2, 3, etc.
```

### Low FPS

```bash
# Enable max performance
sudo nvpmodel -m 0
sudo jetson_clocks

# Use smaller model
MODEL_PATH = "models/yolov5n.pt"

# Reduce camera resolution in config.py
```

---

