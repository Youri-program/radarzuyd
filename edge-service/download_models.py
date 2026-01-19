from ultralytics import YOLO
import os

# Create models directory
os.makedirs('models', exist_ok=True)

# Download all YOLO models you want
models_to_download = [
    'yolov5n.pt', 'yolov5s.pt', 'yolov5m.pt'
]

print("Downloading YOLO models...")
for model_name in models_to_download:
    print(f"Downloading {model_name}...")
    model = YOLO(model_name)  # This automatically downloads
    
    # Move to models folder
    import shutil
    if os.path.exists(model_name):
        shutil.move(model_name, f'models/{model_name}')
    
    print(f"✓ {model_name} downloaded to models/")

print("\n All models downloaded and ready")