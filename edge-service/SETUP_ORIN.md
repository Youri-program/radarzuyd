# Jetson Orin Nano Setup Guide

**Target:** Jetson Orin Nano with JetPack 6.1
**Python:** 3.10 (native, no manual installation needed!)  
**CUDA:** Supported out-of-the-box

---

## Quick Setup (30 minutes)

### Step 1: System Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install basic tools
sudo apt install -y git python3-pip python3-venv
```

---

### Step 2: Clone Repository

```bash
cd ~
git clone https://github.com/Youri-program/radarzuyd
cd radarzuyd/deployment
```

---

### Step 3: Create Virtual Environment

```bash
# Create venv
python3 -m venv ~/yolo_env

# Activate
source ~/yolo_env/bin/activate

# Upgrade pip
pip install --upgrade pip
```

---

### Step 4: Install Dependencies

```bash
# Install PyTorch with CUDA support
pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Install other dependencies
pip3 install -r requirements.txt

# Verify CUDA works
python3 << 'EOF'
import torch
print(f" PyTorch: {torch.__version__}")
print(f" CUDA available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f" GPU: {torch.cuda.get_device_name(0)}")
EOF
```

**Expected output:**
```
 PyTorch: 2.x.x
 CUDA available: True
 GPU: Orin Nano
```

---

### Step 5: Configure Settings

```bash
# Edit config
nano config.py

# Ensure DEVICE is set to "cuda"
# DEVICE = "cuda"  # For GPU acceleration

# Set your AWS endpoint
# AWS_UPLOAD_URL = "your-aws-endpoint"

# Save: Ctrl+O, Enter, Ctrl+X
```

---

### Step 6: Download Model

```bash
# Activate venv if not already
source ~/yolo_env/bin/activate

# Download YOLOv5 model
python3 download_models.py

# Or manually download
mkdir -p models
cd models
wget https://github.com/ultralytics/yolov5/releases/download/v7.0/yolov5n.pt
cd ..
```

---

### Step 7: Test

```bash
# Test with image (no AWS upload)
python3 main.py --mode image --image testimages/test_image3.jpg --no-upload

# Test camera (no AWS upload)
python3 main.py --mode camera --no-upload

# Test with AWS upload
python3 main.py --mode camera
```

---

## Performance Optimization (Optional)

### Enable Maximum Performance Mode

```bash
# Set to max performance
sudo nvpmodel -m 0

# Enable all clocks
sudo jetson_clocks

# Check status
sudo nvpmodel -q
```

**Result:** ~20-30% FPS improvement

---

### Monitor GPU Usage

```bash
# Install jtop
sudo pip3 install jetson-stats

# Run monitoring
jtop
```

---

## Troubleshooting

### PyTorch CUDA Not Available

```bash
# Check CUDA installation
nvcc --version
# Should show CUDA 11.4

# Reinstall PyTorch
pip3 uninstall torch torchvision
pip3 install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

### Camera Not Found

```bash
# List cameras
ls /dev/video*

# Try different camera index in config.py
CAMERA_INDEX = 1  # or 2, 3, etc.
```

### Out of Memory

```python
# In config.py, reduce image size
# For camera:
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480

# Or use smaller model
MODEL_PATH = "models/yolov5n.pt"  # Nano variant
```

---

## Daily Usage

```bash
# Every time you work:
cd ~/radarzuyd/deployment
source ~/yolo_env/bin/activate

# Run your code
python3 main.py --mode camera

# Deactivate when done
deactivate
```

---

