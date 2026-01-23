"""
Single Image Detector

Processes a single image file:
1. Loads image
2. Runs YOLO detection
3. Draws colored bounding boxes per class
4. Saves result
5. Uploads to AWS (if enabled)
"""

import cv2
import os
from model import YOLODetector
from aws_uploader import AWSClient
import config


# Per-class colors (BGR format for OpenCV)
CLASS_COLORS = {
    0: (0, 255, 0),      # person -> green
    67: (0, 165, 255),   # cellphone -> orange
    73: (255, 0, 0),     # book -> blue
}


def draw_detections_colored(image, detections, model_names):
    """
    Draw colored bounding boxes based on class
    
    Args:
        image: numpy array (BGR)
        detections: List of detections
        model_names: Dict mapping class_id to class name
        
    Returns:
        Image with colored bounding boxes
    """
    annotated = image.copy()
    
    for det in detections:
        # Get bbox coordinates
        x1, y1, x2, y2 = [int(v) for v in det['bbox']]
        class_id = det['class_id']
        confidence = det['confidence']
        class_name = det['class_name']
        
        # Get color for this class (default = white)
        color = CLASS_COLORS.get(class_id, (255, 255, 255))
        
        # Draw rectangle
        cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
        
        # Create label
        label = f"{class_name} {confidence:.2f}"
        (text_width, text_height), baseline = cv2.getTextSize(
            label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1
        )
        
        # Draw filled rectangle for label background
        cv2.rectangle(
            annotated,
            (x1, y1 - text_height - baseline),
            (x1 + text_width, y1),
            color,
            -1
        )
        
        # Draw text (black on colored background)
        cv2.putText(
            annotated,
            label,
            (x1, y1 - baseline),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 0, 0),
            1
        )
    
    return annotated


def process_image(image_path, upload_enabled=config.ENABLE_UPLOAD):
    """
    Process a single image
    
    Args:
        image_path: Path to image file
        upload_enabled: Whether to upload to AWS
        
    Returns:
        True if successful
    """
    print("=" * 60)
    print("Single Image Detection")
    print("=" * 60)
    
    # Check if image exists
    if not os.path.exists(image_path):
        print(f" Image not found: {image_path}")
        return False
    
    # Load image
    print(f"\n Loading image: {image_path}")
    image = cv2.imread(image_path)
    
    if image is None:
        print(f" Could not read image: {image_path}")
        return False
    
    print(f" Image loaded: {image.shape[1]}x{image.shape[0]} pixels")
    
    # Initialize detector
    print("\n" + "="*60)
    detector = YOLODetector()
    
    # Run detection
    print(" Running detection...")
    detections = detector.detect(image)
    
    # Print results
    print("\n" + "="*60)
    print(f"Detection Results")
    print("="*60)
    
    if detections:
        print(f" Found {len(detections)} objects:")
        for i, det in enumerate(detections, 1):
            print(f"  {i}. {det['class_name']}: {det['confidence']:.2%} confidence")
    else:
        print(" No target objects detected")
        print(f"   (Looking for: {', '.join(config.CLASS_NAMES.values())})")
        return True
    
    # Draw colored bounding boxes
    print("\n Drawing colored bounding boxes...")
    image_with_boxes = draw_detections_colored(image, detections, config.CLASS_NAMES)
    
    # Save result
    base_name = os.path.splitext(os.path.basename(image_path))[0]
    output_path = f"{base_name}_detected.jpg"
    cv2.imwrite(output_path, image_with_boxes)
    print(f" Saved result: {output_path}")
    
    # Upload to AWS
    if upload_enabled and detections:
        print("\n" + "="*60)
        print("AWS Upload")
        print("="*60)
        
        uploader = AWSClient()
        
        # Upload each detected class once
        uploaded_classes = set()
        for det in detections:
            class_name = det['class_name']
            if class_name not in uploaded_classes:
                # Use teammate's AWSClient: upload_detection(image, object_name)
                status = uploader.upload_detection(image, class_name)
                if status:
                    uploaded_classes.add(class_name)
        
        if uploaded_classes:
            print(f" Uploaded {len(uploaded_classes)} unique detections")
        else:
            print("  Upload failed (check AWS settings)")
    elif not upload_enabled:
        print("\n  Skipping AWS upload (disabled)")
    
    print("\n" + "="*60)
    print(" Processing complete!")
    print("="*60)
    
    return True


# Run if called directly
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python3 image_detector.py <image_path> [--no-upload]")
        print("\nExample:")
        print("  python3 image_detector.py photo.jpg")
        print("  python3 image_detector.py photo.jpg --no-upload")
        sys.exit(1)
    
    image_path = sys.argv[1]
    upload = "--no-upload" not in sys.argv
    
    process_image(image_path, upload_enabled=upload)
