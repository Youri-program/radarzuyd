# 🚀 Quick Start Guide

## Getting Started in 5 Minutes

### 1. Transfer to Jetson Nano

```bash
# On your laptop
scp -r jetson_detection/ jetson@jetson-ip:~/
```

Or use a USB drive.

---

### 2. Install Dependencies

```bash
# SSH into Jetson
ssh jetson@jetson-ip

cd jetson_detection

# Install packages
pip3 install -r requirements.txt
```

**Note:** On Jetson Nano, PyTorch might need special installation. See `requirements.txt` for instructions.

---

### 3. Add Your Model

```bash
# Copy your YOLOv5 model (Python 3.6+ compatible for Jetson)
cp /path/to/yolov5s.pt models/

# The system is configured for yolov5s.pt by default
```

**YOLOv5 models (Python 3.6+ compatible):**
- `yolov5n.pt` - Nano (fastest, smallest)
- `yolov5s.pt` - Small (good balance) ← **Default**
- `yolov5m.pt` - Medium (more accurate, slower)

**Download YOLOv5 models:**
```bash
cd models
# YOLOv5s (recommended)
wget https://github.com/ultralytics/yolov5/releases/download/v7.0/yolov5s.pt

# Or YOLOv5n (faster)
wget https://github.com/ultralytics/yolov5/releases/download/v7.0/yolov5n.pt
cd ..
```

**Change model in config.py:**
```python
MODEL_PATH = "models/yolov5n.pt"  # Use nano for speed
# or
MODEL_PATH = "models/yolov5s.pt"  # Use small for balance
```

---

### 4. Test with Image

```bash
# Test with a photo
python3 main.py --mode image --image test.jpg --no-upload
```

**Expected output:**
```
✅ Found 1 object:
  1. person: 95% confidence
✅ Saved result: test_detected.jpg
```

---

### 5. Run Camera Detection

```bash
# Real-time detection with green bounding boxes
python3 main.py --mode camera
```

**You'll see:**
- 🟢 Green boxes for person
- FPS counter and detection count on screen

Press **'q'** to quit.

---

## Common Commands

```bash
# Image detection
python3 main.py --mode image --image photo.jpg

# Camera without AWS
python3 main.py --mode camera --no-upload

# Use different model  
python3 main.py --mode camera --model models/yolov8n.pt

# Lower confidence threshold
python3 main.py --mode camera --confidence 0.3
```

---

## Configuration

Edit `config.py` to change:
- AWS upload URL
- Jetson device ID
- Classes to detect
- Confidence threshold
- Camera settings

---

## Troubleshooting

### "Camera not found"
```bash
# Check camera devices
ls /dev/video*

# Try different index in config.py
CAMERA_INDEX = 1
```

### "Model not found"
```bash
# Check model exists
ls models/

# Make sure filename matches config.py
MODEL_PATH = "models/yolov10s.pt"
```

### "CUDA out of memory"
```python
# In config.py, use smaller resolution
CAMERA_WIDTH = 320
CAMERA_HEIGHT = 240
```

---

## Next Steps

1. ✅ Test with images first
2. ✅ Test camera without upload
3. ✅ Enable AWS upload
4. ✅ Optimize for your use case

Read the full `README.md` for detailed explanations!
