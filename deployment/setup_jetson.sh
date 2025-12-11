#!/bin/bash
# Jetson Nano Setup Script
# Run this on Jetson Nano after cloning the repo

set -e  # Exit on error

echo "============================================"
echo "Jetson Nano Deployment Setup"
echo "============================================"
echo ""

# Check if running on Jetson
if [ ! -f /etc/nv_tegra_release ]; then
    echo "⚠️  Warning: This doesn't appear to be a Jetson Nano!"
    echo "   Continue anyway? (y/n)"
    read -r response
    if [ "$response" != "y" ]; then
        exit 1
    fi
fi

# Step 1: Check Python version
echo "📋 Step 1: Checking Python version..."
python_version=$(python3 --version)
echo "   Python version: $python_version"

if python3 -c 'import sys; exit(0 if sys.version_info >= (3, 6) else 1)'; then
    echo "   ✅ Python 3.6+ detected"
else
    echo "   ❌ Python 3.6+ required!"
    exit 1
fi
echo ""

# Step 2: Download PyTorch wheel
echo "📦 Step 2: Downloading PyTorch wheel..."
if [ ! -f "torch-1.10.0-cp36-cp36m-linux_aarch64.whl" ]; then
    echo "   Downloading from NVIDIA..."
    wget -q --show-progress https://nvidia.box.com/shared/static/fjtbno0vpo676a25cgvuqc1wty0fkkg6.whl \
        -O torch-1.10.0-cp36-cp36m-linux_aarch64.whl
    echo "   ✅ Downloaded"
else
    echo "   ✅ Already downloaded"
fi
echo ""

# Step 3: Install PyTorch
echo "🔧 Step 3: Installing PyTorch..."
if python3 -c "import torch" 2>/dev/null; then
    echo "   ⏭️  PyTorch already installed"
else
    echo "   Installing..."
    pip3 install torch-1.10.0-cp36-cp36m-linux_aarch64.whl
    echo "   ✅ PyTorch installed"
fi

# Verify
if python3 -c "import torch; print(f'   PyTorch {torch.__version__} ready!')" 2>/dev/null; then
    :
else
    echo "   ❌ PyTorch installation failed!"
    exit 1
fi
echo ""

# Step 4: Install OpenCV
echo "📦 Step 4: Installing OpenCV..."
if python3 -c "import cv2" 2>/dev/null; then
    echo "   ⏭️  OpenCV already installed"
else
    echo "   Installing via apt-get..."
    sudo apt-get update -qq
    sudo apt-get install -y python3-opencv
    echo "   ✅ OpenCV installed"
fi

# Verify
if python3 -c "import cv2; print(f'   OpenCV {cv2.__version__} ready!')" 2>/dev/null; then
    :
else
    echo "   ❌ OpenCV installation failed!"
    exit 1
fi
echo ""

# Step 5: Install other packages
echo "📦 Step 5: Installing dependencies..."
pip3 install -q requests numpy==1.19.5
echo "   ✅ requests and numpy installed"

echo "   Installing Ultralytics..."
if pip3 install -q ultralytics==6.2.0; then
    echo "   ✅ Ultralytics 6.2.0 installed"
else
    echo "   ⚠️  Ultralytics 6.2.0 failed, trying latest..."
    pip3 install -q ultralytics
    echo "   ✅ Ultralytics (latest) installed"
fi
echo ""

# # Step 6: Create models directory
# echo "📁 Step 6: Creating models directory..."
# mkdir -p models
# echo "   ✅ models/ directory ready"
# echo ""

# Step 7: Download YOLOv5n
echo "📥 Step 7: Downloading YOLOv5n model..."
if [ -f "models/yolov5n.pt" ]; then
    echo "   ⏭️  yolov5n.pt already exists"
else
    cd models
    echo "   Downloading from GitHub..."
    wget -q --show-progress https://github.com/ultralytics/yolov5/releases/download/v7.0/yolov5n.pt
    cd ..
    echo "   ✅ yolov5n.pt downloaded"
fi

# Verify file size
size=$(stat -f%z "models/yolov5n.pt" 2>/dev/null || stat -c%s "models/yolov5n.pt" 2>/dev/null || echo "0")
size_mb=$((size / 1024 / 1024))
echo "   File size: ${size_mb} MB"

if [ "$size_mb" -lt 3 ]; then
    echo "   ⚠️  File seems too small, may be corrupted!"
fi
echo ""

# Step 8: Check config.py
echo "⚙️  Step 8: Checking config.py..."
if [ -f "config.py" ]; then
    device=$(grep -m1 "^DEVICE = " config.py | cut -d'"' -f2)
    model=$(grep -m1 "^MODEL_PATH = " config.py | cut -d'"' -f2)
    
    echo "   Current settings:"
    echo "   - DEVICE = \"$device\""
    echo "   - MODEL_PATH = \"$model\""
    
    if [ "$device" != "cuda" ]; then
        echo ""
        echo "   ⚠️  WARNING: DEVICE is not set to 'cuda'!"
        echo "   You should edit config.py and change:"
        echo "   DEVICE = \"cuda\"  # For Jetson GPU"
    else
        echo "   ✅ DEVICE correctly set to 'cuda'"
    fi
    
    if [ "$model" != "models/yolov5n.pt" ]; then
        echo ""
        echo "   ℹ️  Note: MODEL_PATH is set to '$model'"
        echo "   Recommended for Jetson: models/yolov5n.pt"
    else
        echo "   ✅ MODEL_PATH correctly set to 'models/yolov5n.pt'"
    fi
else
    echo "   ❌ config.py not found!"
    echo "   Are you in the deployment folder?"
    exit 1
fi
echo ""

# Step 9: Test imports
echo "🧪 Step 9: Testing imports..."
if python3 << 'EOF'
try:
    import torch
    print(f"   ✅ PyTorch {torch.__version__}")
    import cv2
    print(f"   ✅ OpenCV {cv2.__version__}")
    import requests
    print("   ✅ requests")
    import numpy
    print(f"   ✅ numpy {numpy.__version__}")
    from ultralytics import YOLO
    print("   ✅ ultralytics")
except ImportError as e:
    print(f"   ❌ Import failed: {e}")
    exit(1)
EOF
then
    :
else
    echo ""
    echo "   ❌ Import test failed!"
    exit 1
fi
echo ""

# Summary
echo "============================================"
echo "✅ Setup Complete!"
echo "============================================"
echo ""
echo "📋 Next steps:"
echo ""
echo "1. Edit config.py (if needed):"
echo "   nano config.py"
echo "   - Set DEVICE = \"cuda\""
echo "   - Verify AWS URLs"
echo ""
echo "2. Test without upload:"
echo "   python3 main.py --mode camera --no-upload"
echo ""
echo "3. Test with AWS upload:"
echo "   python3 main.py --mode camera"
echo ""
echo "4. Enable max performance (optional):"
echo "   sudo nvpmodel -m 0"
echo "   sudo jetson_clocks"
echo ""
echo "🚀 Ready to run!"
echo "============================================"
