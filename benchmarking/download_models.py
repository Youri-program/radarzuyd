from ultralytics import YOLO
import os
import shutil

# Create models directory
os.makedirs('models', exist_ok=True)

# Download all YOLO models
models_to_download = [
    'yolov5nu.pt', 'yolov5su.pt', 'yolov5mu.pt',
    'yolo11n.pt', 'yolo11s.pt', 'yolo11m.pt'
]

print("Downloading YOLO models...")
for model_name in models_to_download:
    print(f"Downloading {model_name}...")
    model = YOLO(model_name)  # This automatically downloads
    
    # Move to models folder
    if os.path.exists(model_name):
        shutil.move(model_name, f'models/{model_name}')
    
    print(f"✓ {model_name} downloaded to models/")

print("\nAll models downloaded and ready!")