"""
Export YOLOv11s to TensorRT
Simple script to convert yolo11s.pt to TensorRT engine.
"""

from ultralytics import YOLO
from pathlib import Path

# Configuration
MODEL_PATH = 'models/yolo11s.pt'
OUTPUT_NAME = 'yolo11s.engine'

print("=" * 70)
print("EXPORTING YOLOv11s TO TENSORRT")
print("=" * 70)
print()

# Check if model exists
if not Path(MODEL_PATH).exists():
    print(f"[ERROR] Model not found: {MODEL_PATH}")
    print("Please make sure yolo11s.pt is in the models/ folder")
    exit(1)

# Check if already exported
if Path(f'models/{OUTPUT_NAME}').exists():
    print(f"[WARNING] {OUTPUT_NAME} already exists!")
    response = input("Overwrite? (y/n): ")
    if response.lower() != 'y':
        print("Export cancelled")
        exit(0)

print(f"[INFO] Loading model: {MODEL_PATH}")
model = YOLO(MODEL_PATH)

print(f"[INFO] Exporting to TensorRT with FP16 precision...")
print("[INFO] This will take ~5-10 minutes")
print()

try:
    # Export to TensorRT with FP16
    model.export(format='engine', half=True, device=0)
    
    print()
    print("[SUCCESS] Export complete!")
    print("=" * 70)
    print(f"Saved: models/{OUTPUT_NAME}")
    print()
    
except Exception as e:
    print()
    print("[ERROR] Export failed!")
    print("=" * 70)
    print(f"Error: {e}")
    print()
    exit(1)
