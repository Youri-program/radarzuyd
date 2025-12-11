# 🤖 Jetson Nano Setup Guide

## ⚠️ Important: Jetson Nano Requires Special Setup!

The Jetson Nano needs different installation steps than a regular computer.

---

## 📋 Prerequisites

Before starting, make sure your Jetson Nano has:
- ✅ JetPack installed (4.6+)
- ✅ Internet connection
- ✅ At least 10GB free space

Check your JetPack version:
```bash
cat /etc/nv_tegra_release
```

---

## 🚀 Installation Steps

### Step 1: Transfer Files to Jetson

```bash
# From your laptop
scp -r jetson_detection/ jetson@<jetson-ip>:~/

# Or use USB drive
```

### Step 2: SSH into Jetson

```bash
ssh jetson@<jetson-ip>
cd jetson_detection
```

---

### Step 3: Install PyTorch (CRITICAL!)

**DO NOT** use `pip install torch` - it won't work!

#### For JetPack 4.6 (Python 3.6):

```bash
# Download PyTorch wheel for Jetson
wget https://nvidia.box.com/shared/static/fjtbno0vpo676a25cgvuqc1wty0fkkg6.whl -O torch-1.10.0-cp36-cp36m-linux_aarch64.whl

# Install
pip3 install torch-1.10.0-cp36-cp36m-linux_aarch64.whl

# Install torchvision
sudo apt-get install libjpeg-dev zlib1g-dev libpython3-dev libavcodec-dev libavformat-dev libswscale-dev
pip3 install torchvision==0.11.0
```

#### For JetPack 5.0+ (Python 3.8):

```bash
# Install PyTorch
pip3 install torch torchvision

# Or download specific wheel from NVIDIA
# https://forums.developer.nvidia.com/t/pytorch-for-jetson/72048
```

---

### Step 4: Install Other Dependencies

**Don't use `pip install -r requirements.txt`!** That's for laptop only.

Instead, install manually:

```bash
# Install requests and numpy
pip3 install requests numpy==1.19.5

# Try to install ultralytics for YOLOv5
pip3 install ultralytics==6.2.0

# OR if that fails, use YOLOv5 directly:
# git clone https://github.com/ultralytics/yolov5
# cd yolov5
# pip3 install -r requirements.txt
# cd ..
```

**Why not use requirements.txt?**
- Laptop requirements include packages that don't work on Python 3.6
- Jetson needs special PyTorch installation
- Jetson uses system OpenCV (apt-get), not pip

**See `requirements-jetson.txt`** for reference (but install manually as shown above).

---

### Step 5: Configure for Jetson

Edit `config.py`:

```python
# Change device to cuda (Jetson has GPU)
DEVICE = "cuda"

# For CSI camera (if using Jetson's built-in camera)
# Keep CAMERA_INDEX = 0 for USB camera
# Or see "CSI Camera Setup" below
```

---

## 📹 Camera Setup

### USB Camera (Recommended for Testing)

Just plug in USB camera and it should work:
```python
# In config.py
CAMERA_INDEX = 0  # Usually 0
```

Test it:
```bash
ls /dev/video*
# Should show /dev/video0 or similar
```

---

### CSI Camera (Jetson's Built-In Camera Port)

If using CSI camera, you need GStreamer pipeline.

**Replace the camera opening code in `camera_detector.py`:**

Find this line (around line 32):
```python
cap = cv2.VideoCapture(config.CAMERA_INDEX)
```

Replace with:
```python
# CSI Camera with GStreamer
gst_pipeline = (
    "nvarguscamerasrc ! "
    "video/x-raw(memory:NVMM), width=640, height=480, format=NV12, framerate=30/1 ! "
    "nvvidconv flip-method=0 ! "
    "video/x-raw, width=640, height=480, format=BGRx ! "
    "videoconvert ! "
    "video/x-raw, format=BGR ! "
    "appsink"
)
cap = cv2.VideoCapture(gst_pipeline, cv2.CAP_GSTREAMER)
```

---

## ⚙️ Configuration for Jetson Performance

### Reduce Memory Usage

Edit `config.py`:

```python
# Lower resolution for faster processing
CAMERA_WIDTH = 416   # Instead of 640
CAMERA_HEIGHT = 416  # Instead of 480

# Lower confidence threshold if needed
CONFIDENCE_THRESHOLD = 0.4  # Instead of 0.5
```

---

### Use Smaller Model

YOLOv10s might be slow on Jetson Nano. Try smaller model:

```bash
# Download YOLOv8n (nano - fastest)
cd models
wget https://github.com/ultralytics/assets/releases/download/v8.2.0/yolov8n.pt
cd ..
```

Update `config.py`:
```python
MODEL_PATH = "models/yolov8n.pt"
```

---

### Enable Maximum Performance Mode

```bash
# Set Jetson to max performance
sudo nvpmodel -m 0
sudo jetson_clocks
```

---

## 🧪 Testing

### Test 1: Verify PyTorch

```bash
python3 -c "import torch; print(torch.__version__); print(torch.cuda.is_available())"
```

Should output:
```
1.10.0
True
```

### Test 2: Test Camera

```bash
# USB camera test
python3 -c "import cv2; cap = cv2.VideoCapture(0); print('Camera OK' if cap.isOpened() else 'Camera FAIL')"
```

### Test 3: Test YOLO

```bash
# Quick model test (without AWS)
python3 main.py --mode image --image test.jpg --no-upload
```

### Test 4: Test Camera Detection

```bash
# Camera without AWS upload
python3 main.py --mode camera --no-upload
```

### Test 5: Test with AWS

```bash
# Full system
python3 main.py --mode camera
```

---

## 🐛 Common Jetson Issues

### "ImportError: cannot import name 'PILLOW_VERSION'"

**Solution:**
```bash
pip3 install --upgrade pillow
```

### "CUDA out of memory"

**Solution:**
```python
# In config.py - use smaller resolution
CAMERA_WIDTH = 320
CAMERA_HEIGHT = 240
```

Or use smaller model (yolov8n.pt instead of yolov10s.pt)

### Camera shows "Failed to capture frame"

**For USB camera:**
```bash
# Check camera device
ls -l /dev/video*

# Try different index in config.py
CAMERA_INDEX = 1  # or 2
```

**For CSI camera:**
Use the GStreamer pipeline shown above.

### "torch.cuda.is_available() returns False"

**Solution:**
```bash
# Reinstall PyTorch for Jetson
# Follow Step 3 above carefully
```

---

## 🔧 Performance Tips

### 1. Use TensorRT (Advanced)

After benchmarking, convert model to TensorRT:
```bash
# Export to TensorRT format
yolo export model=yolov10s.pt format=engine device=0 half=True
```

Update config:
```python
MODEL_PATH = "models/yolov10s.engine"
```

### 2. Lower Resolution

```python
CAMERA_WIDTH = 320
CAMERA_HEIGHT = 240
```

### 3. Reduce FPS

```python
CAMERA_FPS = 15  # Instead of 30
```

### 4. Use Nano Model

```python
MODEL_PATH = "models/yolov8n.pt"  # Smallest, fastest
```

---

## 📊 Expected Performance

### With YOLOv8n @ 416x416:
- FPS: 10-15
- Memory: ~2GB
- Power: ~10W

### With YOLOv10s @ 640x480:
- FPS: 5-8
- Memory: ~3GB
- Power: ~15W

### With TensorRT @ 416x416:
- FPS: 20-25 ⚡
- Memory: ~1.5GB
- Power: ~8W

---

## ✅ Final Checklist

Before running on Jetson:

- [ ] JetPack installed
- [ ] PyTorch installed (Jetson version!)
- [ ] ultralytics installed
- [ ] opencv-python (apt-get version)
- [ ] Model file in models/ folder
- [ ] config.py: DEVICE = "cuda"
- [ ] Camera working (tested)
- [ ] Internet connection (for AWS)

---

## 🚀 Quick Start Command

```bash
cd jetson_detection
python3 main.py --mode camera
```

Press 'q' to quit!

---

## 💡 Pro Tips

1. **Start with USB camera** - easier than CSI
2. **Test without AWS first** - use --no-upload flag
3. **Use smaller model** - YOLOv8n runs faster
4. **Lower resolution** - 416x416 is good balance
5. **Enable max performance** - sudo jetson_clocks

---

## 📞 Need Help?

Common commands for debugging:

```bash
# Check CUDA
python3 -c "import torch; print(torch.cuda.is_available())"

# Check camera
ls /dev/video*

# Check JetPack version
cat /etc/nv_tegra_release

# Monitor GPU usage
tegrastats

# Check temperature
cat /sys/devices/virtual/thermal/thermal_zone*/temp
```

---

## ✨ Summary

**Jetson Nano is different!**
- ✅ Needs special PyTorch installation
- ✅ Might need CSI camera setup
- ✅ Benefits from smaller models
- ✅ Runs faster with TensorRT
- ✅ Has CUDA support

**Follow this guide carefully and you'll be up and running!** 🚀
