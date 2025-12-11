# 📱 Jetson Nano Object Detection System

A simple object detection system that runs on Jetson Nano, detects specific objects (person, book, cell phone), and uploads detections to AWS cloud.

---

## 🎯 What This Does

This system:
1. **Loads a YOLO model** (YOLOv5n/s/m - Python 3.6+ compatible)
2. **Detects persons** (COCO class 0)
3. **Works in 2 modes:**
   - Single image detection
   - Real-time camera feed detection
4. **Uploads detections to AWS** when objects are found (using teammate's AWSClient)

---

## 📂 Project Structure

```
jetson_detection/
├── README.md              # This file - explains everything
├── requirements.txt       # Python packages needed
├── config.py             # Configuration (AWS URL, classes to detect)
├── main.py               # Main program - run this!
├── model.py              # Loads and runs YOLO model
├── aws_uploader.py       # Uploads detections to AWS cloud
├── camera_detector.py    # Real-time camera detection
├── image_detector.py     # Single image detection
└── models/               # Put your YOLO model here
    └── yolov10s.pt       # Your trained model
```

---

## 🚀 Quick Start

### Step 1: Install Dependencies

```bash
cd jetson_detection
pip3 install -r requirements.txt
```

### Step 2: Add Your Model

Put your YOLO model in the `models/` folder:
```bash
cp /path/to/yolov10s.pt models/
```

### Step 3: Configure (Optional)

Edit `config.py` if you want to change:
- AWS upload URL
- Jetson device ID
- Classes to detect
- Model path

### Step 4: Run It!

**For single image:**
```bash
python3 main.py --mode image --image test.jpg
```

**For camera feed:**
```bash
python3 main.py --mode camera
```

**To disable AWS upload (testing):**
```bash
python3 main.py --mode camera --no-upload
```

---

## 🔍 How It Works

### Overview

```
┌─────────────┐
│   Camera    │  or  │   Image   │
│   /Image    │      │   File    │
└──────┬──────┘      └─────┬─────┘
       │                   │
       └───────┬───────────┘
               ▼
       ┌───────────────┐
       │  YOLO Model   │
       │  (model.py)   │
       └───────┬───────┘
               │
               ▼
       ┌───────────────────┐
       │ Filter Detections │ ← Only classes [0, 73, 67]
       └───────┬───────────┘
               │
               ▼
       ┌────────────────────┐
       │  AWS Uploader      │ ← Send to cloud
       │  (aws_uploader.py) │
       └────────────────────┘
```

---

## 📝 Detailed Explanation

### 1. **config.py** - Configuration

This file contains all settings:

```python
# AWS
AWS_PING_URL = "https://djpawwqotb.../prod/ping"   # Connection check endpoint
AWS_UPLOAD_URL = "https://djpawwqotb.../prod/upload"  # Where to send data
JETSON_ID = "jetson_nano_01"  # Your device name

# Detection
TARGET_CLASSES = [0]  # Only person
CONFIDENCE_THRESHOLD = 0.5     # Minimum confidence (50%)

# Model Settings
MODEL_PATH = "models/yolov5s.pt"  # YOLOv5 model (Python 3.6 compatible)
```

**Why separate config?**
- Easy to change settings without editing code
- All important values in one place
- Clear what can be customized

---

### 2. **model.py** - YOLO Model Handler

**What it does:**
1. Loads your YOLO model (`.pt`, `.onnx`, or `.engine`)
2. Runs inference on images
3. Filters results to only target classes [0, 73, 67]
4. Returns clean detection results

**Key functions:**

```python
class YOLODetector:
    def __init__(self, model_path, target_classes, confidence_threshold):
        """Load the YOLO model"""
        
    def detect(self, image):
        """
        Run detection on an image
        
        Args:
            image: numpy array (BGR format from OpenCV)
            
        Returns:
            List of detections with:
            - class_id: 0, 73, or 67
            - class_name: "person", "book", or "cell phone"
            - confidence: 0.0 to 1.0
            - bbox: [x1, y1, x2, y2]
        """
```

**Why it works this way:**
- Simple interface: give image, get detections
- Automatically filters to target classes
- Handles different model formats
- Returns clean, structured data

---

### 3. **aws_uploader.py** - AWS Cloud Integration (Teammate's Code)

**What it does:**
1. Takes an image and object name
2. Encodes image to base64 (AWS requirement)
3. Checks connection with ping endpoint
4. POSTs to AWS /upload endpoint

**Key class: AWSClient**
```python
client = AWSClient(
    ping_url="https://.../ping",
    upload_url="https://.../upload",
    jetson_id="jetson_nano_01"
)

# Upload detection
status = client.upload_detection(image, "person")
```

**Payload format:**
```json
{
  "jetson_id": "jetson_nano_01",
  "object_name": "person",
  "image_base64": "base64_encoded_image_data",
  "timestamp": "2024-12-08T21:30:00+00:00"
}
```

**Features:**
- Fast connection check with /ping endpoint (0.5s timeout)
- Automatic base64 encoding
- Returns HTTP status code or None
- Handles errors gracefully

**Created by teammate** for AWS Lambda integration.

---

### 4. **image_detector.py** - Single Image Mode

**What it does:**
1. Loads a single image file
2. Runs YOLO detection
3. Draws **colored bounding boxes** on image (green=person, orange=cellphone, blue=book)
4. Saves result with boxes
5. Uploads to AWS (if enabled)
6. Prints detection summary

**Example output:**
```
📸 Processing image: test.jpg
✅ Detected 2 objects:
  - person (95.3% confidence)
  - book (87.1% confidence)
📤 Uploading to AWS...
✅ Upload successful!
💾 Saved result to: test_detected.jpg
```

**Why useful:**
- Test your model quickly
- Debug detection issues
- Process existing images
- See visual results with color-coded boxes

**Color coding:**
Each detected class is drawn in a specific color:
- Person: Green box
- Cellphone: Orange box
- Book: Blue box

---

### 5. **camera_detector.py** - Real-Time Camera Mode

**What it does:**
1. Opens camera (USB or CSI)
2. Captures frames continuously
3. Runs YOLO on each frame
4. Shows live video with **colored bounding boxes** (green=person, orange=cellphone, blue=book)
5. Uploads NEW detections to AWS
6. Press 'q' to quit

**Visual display:**
```
┌─────────────────────────────┐
│   [Live Camera Feed]        │
│                             │
│   ┌─────────────┐           │ ← Green box
│   │  Person 95% │           │
│   └─────────────┘           │
│                             │
│   ┌──────────────┐          │ ← Orange box
│   │ Cellphone 87%│          │
│   └──────────────┘          │
│                             │
│   FPS: 15.2                 │
│   Detections: 2             │
└─────────────────────────────┘
```

**Smart uploading:**
- Uploads immediately when NEW object detected ⚡
- Tracks which classes have been uploaded (`seen_classes`)
- Doesn't re-upload same class continuously
- Resets and allows re-upload if object is gone for 3+ seconds

**How it works:**
```
Frame 1:  Detects person → Upload immediately ✅
Frame 2:  Person still there → No upload (already sent)
Frame 50: Person + book appear → Upload book ✅ (NEW!)
Frame 51: Person + book → No upload (both already sent)
Frame 100: Person leaves → seen_classes reset after 3 sec
Frame 150: Person returns → Upload person again ✅
```

**Why this approach?**
- Camera runs at 15-30 FPS
- Same object appears in every frame
- Without smart tracking: 30 uploads per second of same person! ❌
- With smart tracking: Upload only when detection changes ✅
- Uses set-based tracking for efficiency

**Color coding:**
Each class has a specific color for easy visual identification:
- Person: Green
- Cellphone: Orange
- Book: Blue

---

### 6. **main.py** - Entry Point

**What it does:**
Provides simple command-line interface to run the system

**Examples:**

```bash
# Detect in single image
python3 main.py --mode image --image photo.jpg

# Real-time camera
python3 main.py --mode camera

# Camera without AWS upload (testing)
python3 main.py --mode camera --no-upload

# Use different model
python3 main.py --mode camera --model models/yolov8n.pt

# Change confidence threshold
python3 main.py --mode camera --confidence 0.7
```

---

## 🎓 Understanding the Code Flow

### Single Image Detection Flow:

```
1. User runs: python3 main.py --mode image --image test.jpg
                    ↓
2. main.py calls image_detector.py
                    ↓
3. Load image with OpenCV (cv2.imread)
                    ↓
4. Pass to YOLODetector.detect()
                    ↓
5. YOLO processes image
                    ↓
6. Filter results to classes [0, 73, 67]
                    ↓
7. Draw bounding boxes on image
                    ↓
8. If detection found:
   - Upload to AWS (aws_uploader.py)
   - Save image with boxes
                    ↓
9. Print results to console
```

### Camera Detection Flow:

```
1. User runs: python3 main.py --mode camera
                    ↓
2. main.py calls camera_detector.py
                    ↓
3. Open camera (cv2.VideoCapture)
                    ↓
4. Loop forever:
   ┌──────────────────────────┐
   │ a. Capture frame         │
   │ b. Run YOLO detection    │
   │ c. Filter to target      │
   │    classes               │
   │ d. Draw boxes on frame   │
   │ e. Check if upload       │
   │    needed (debounce)     │
   │ f. Upload to AWS if yes  │
   │ g. Show frame on screen  │
   │ h. Check for 'q' key     │
   └─────────┬────────────────┘
             │
             └──── Repeat until 'q' pressed
```

---

## 🔧 Configuration Options

### In `config.py`:

```python
# === AWS Configuration ===
AWS_UPLOAD_URL = "https://..."  # Your AWS endpoint
JETSON_ID = "jetson_nano_01"    # Unique device identifier
ENABLE_UPLOAD = True            # Set False to disable AWS

# === Detection Configuration ===
TARGET_CLASSES = [0, 73, 67]    # Classes to detect:
                                # 0 = person
                                # 73 = book  
                                # 67 = cell phone
CONFIDENCE_THRESHOLD = 0.5      # Minimum confidence (0.0 - 1.0)

# === Model Configuration ===
MODEL_PATH = "models/yolov5s.pt"  # Path to YOLO model
                                  # YOLOv5 (Python 3.6+ compatible):
                                  #   yolov5n.pt (nano - fastest)
                                  #   yolov5s.pt (small - balanced)
                                  #   yolov5m.pt (medium - accurate)
                                  # Or .onnx, .engine formats
DEVICE = "cuda"                   # "cuda" for Jetson, "cpu" for laptop

# === Camera Configuration ===
CAMERA_INDEX = 0                # 0 = default camera
CAMERA_WIDTH = 640              # Frame width
CAMERA_HEIGHT = 480             # Frame height
CAMERA_FPS = 30                 # Target FPS

# === Upload Configuration ===
UPLOAD_DEBOUNCE_SECONDS = 3.0   # Wait time between uploads
```

---

## 🐛 Troubleshooting

### Problem: "Model file not found"

**Solution:**
```bash
# Check model exists
ls -la models/

# Make sure filename matches config.py
# If your model is "yolov10s.pt", config should have:
MODEL_PATH = "models/yolov10s.pt"
```

---

### Problem: "CUDA out of memory" on Jetson

**Solution:**
```python
# In config.py, reduce input size
CAMERA_WIDTH = 320   # Smaller = less memory
CAMERA_HEIGHT = 240
```

Or use a smaller model:
```bash
# Use YOLOv8n instead of YOLOv10s
MODEL_PATH = "models/yolov8n.pt"
```

---

### Problem: "Can't open camera"

**Solutions:**

1. Check camera connection:
```bash
ls /dev/video*
# Should see /dev/video0 or similar
```

2. Try different camera index:
```python
# In config.py
CAMERA_INDEX = 1  # Try 0, 1, 2, etc.
```

3. For CSI camera on Jetson:
```python
# Use this in camera_detector.py instead:
cap = cv2.VideoCapture("nvarguscamerasrc ! video/x-raw(memory:NVMM), width=640, height=480, format=NV12, framerate=30/1 ! nvvidconv flip-method=0 ! video/x-raw, width=640, height=480, format=BGRx ! videoconvert ! video/x-raw, format=BGR ! appsink", cv2.CAP_GSTREAMER)
```

---

### Problem: "AWS upload fails"

**Check:**
1. URL is correct in `config.py`
2. Internet connection works
3. AWS endpoint is active

**Test without upload:**
```bash
python3 main.py --mode camera --no-upload
```

---

### Problem: "No detections shown"

**Solutions:**

1. Lower confidence threshold:
```python
# In config.py
CONFIDENCE_THRESHOLD = 0.3  # From 0.5
```

2. Check if objects are in target classes:
```python
# To detect ALL classes (debugging):
TARGET_CLASSES = list(range(80))  # All COCO classes
```

3. Verify model works:
```bash
# Test on known image with person
python3 main.py --mode image --image test_person.jpg
```

---

## 📊 Performance Tips

### For Jetson Nano:

1. **Use TensorRT engine** (fastest):
```bash
# After benchmarking, use .engine file
MODEL_PATH = "models/yolov10s_fp16.engine"
```

2. **Reduce resolution**:
```python
CAMERA_WIDTH = 320
CAMERA_HEIGHT = 240
```

3. **Use smaller model**:
```python
MODEL_PATH = "models/yolov8n.pt"  # Smallest, fastest
```

4. **Limit FPS**:
```python
CAMERA_FPS = 15  # From 30
```

---

## 🔐 Security Notes

**AWS Upload URL:**
- Keep your `config.py` private
- Don't commit AWS URLs to public repos
- Use environment variables for production:

```python
import os
AWS_UPLOAD_URL = os.getenv("AWS_UPLOAD_URL", "default_url")
```

---

## 📈 Next Steps

### After Basic Testing:

1. **Benchmark models** on Jetson:
   - Test different YOLO variants
   - Convert to TensorRT
   - Measure FPS and accuracy

2. **Tune detection**:
   - Adjust confidence threshold
   - Add/remove target classes
   - Optimize camera settings

3. **Production deployment**:
   - Run on boot (systemd service)
   - Add logging to file
   - Implement error recovery

---

## ❓ FAQ

**Q: Can I detect other objects?**  
A: Yes! Change `TARGET_CLASSES` in `config.py`. See [COCO class list](https://tech.amikelive.com/node-718/what-object-categories-labels-are-in-coco-dataset/).

**Q: Does it work on laptop?**  
A: Yes! Just set `DEVICE = "cpu"` in config.py.

**Q: Can I use my own trained model?**  
A: Yes! Put your `.pt` file in `models/` and update `MODEL_PATH`.

**Q: How do I run on boot?**  
A: Create a systemd service. See `SYSTEMD_SETUP.md` (coming soon).

**Q: Can I use multiple cameras?**  
A: Yes, but requires code modification. Run multiple instances with different `CAMERA_INDEX`.

---

## 📞 Support

Having issues? Check:
1. This README's troubleshooting section
2. Your `config.py` settings match your setup
3. Model file exists and path is correct
4. Camera is connected and working

---

## ✨ Summary

**This system:**
- ✅ Simple Python scripts (no Docker complexity)
- ✅ Detects person, book, cell phone
- ✅ Works with images or camera
- ✅ Uploads to AWS automatically
- ✅ Easy to configure and modify
- ✅ Well documented and explained
- ✅ **Color-coded bounding boxes** for easy identification
- ✅ **Smart upload tracking** to avoid duplicates
- ✅ **Efficient set-based detection** logic

**Recent Improvements:**
- 🎨 **Colored Bounding Boxes**: Each class (person, cellphone, book) has a unique color
- 🧠 **Smart Upload Logic**: Uses set-based tracking (`seen_classes`) for efficiency
- 🔄 **Reset on Absence**: If object disappears for 3+ seconds, allows re-upload when it returns
- 📊 **Better Visual Feedback**: Color-coded boxes make it easy to identify objects at a glance

**To run:**
```bash
python3 main.py --mode camera
```

**That's it!** 🎉
