"""
Camera Detector

Real-time object detection from camera feed:
1. Opens camera
2. Captures frames continuously
3. Runs YOLO detection with colored bounding boxes per class
4. Shows live video
5. Uploads NEW detections to AWS

Press 'q' to quit
"""

import cv2
import time
from model import YOLODetector
from aws_uploader import AWSClient
import config


# Per-class colors (BGR format for OpenCV)
CLASS_COLORS = {
    0: (0, 255, 0),      # person -> green
    67: (0, 165, 255),   # cellphone -> orange
    73: (255, 0, 0),     # book -> blue
}


def run_camera_detection(upload_enabled=config.ENABLE_UPLOAD):
    """
    Run real-time camera detection
    
    Args:
        upload_enabled: Whether to upload to AWS
        
    Controls:
        Press 'q' to quit
    """
    print("=" * 60)
    print("Real-Time Camera Detection")
    print("=" * 60)
    
    # Initialize detector
    print("\n")
    detector = YOLODetector()
    
    # Initialize uploader
    if upload_enabled:
        uploader = AWSClient()
    else:
        uploader = None
        print("  AWS upload disabled\n")
    
    # Open camera
    print("Opening camera...")
    cap = cv2.VideoCapture(config.CAMERA_INDEX)
    
    if not cap.isOpened():
        print(f" Could not open camera {config.CAMERA_INDEX}")
        return False
    
    # Set camera properties
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.CAMERA_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.CAMERA_HEIGHT)
    cap.set(cv2.CAP_PROP_FPS, config.CAMERA_FPS)
    
    print(f"Camera opened: {config.CAMERA_WIDTH}x{config.CAMERA_HEIGHT} @ {config.CAMERA_FPS}fps")
    print("\n" + "=" * 60)
    print("Press 'q' to quit")
    print("=" * 60 + "\n")
    
    # Track FPS
    fps_start_time = time.time()
    fps_frame_count = 0
    current_fps = 0
    
    # Track uploads - using teammate's approach with improvements
    seen_classes = set()  # Classes that have been uploaded this session
    last_seen_time = {}   # When each class was last detected
    current_time = time.time()
    
    try:
        while True:
            # Capture frame
            ret, frame = cap.read()
            
            if not ret:
                print(" Failed to capture frame")
                break
            
            current_time = time.time()
            
            # Run detection
            detections = detector.detect(frame)
            
            # Track current classes in frame
            current_classes = set()
            
            # Draw colored bounding boxes (teammate's style)
            annotated = frame.copy()
            for det in detections:
                class_id = det['class_id']
                class_name = det['class_name']
                current_classes.add(class_name)
                
                # Update last seen time
                last_seen_time[class_name] = current_time
                
                # Get bbox
                x1, y1, x2, y2 = [int(v) for v in det['bbox']]
                confidence = det['confidence']
                
                # Get color for this class
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
                
                # Draw text
                cv2.putText(
                    annotated,
                    label,
                    (x1, y1 - baseline),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (0, 0, 0),
                    1
                )
            
            # Find new classes (not seen before OR not seen recently)
            new_classes = set()
            for class_name in current_classes:
                # Check if never uploaded OR object returned after being gone
                if class_name not in seen_classes:
                    new_classes.add(class_name)
            
            # Check if any previously seen classes have been gone long enough to reset
            classes_to_reset = set()
            for class_name in list(seen_classes):
                if class_name not in current_classes:
                    # Object is not in current frame
                    time_since_seen = current_time - last_seen_time.get(class_name, current_time)
                    if time_since_seen > config.UPLOAD_DEBOUNCE_SECONDS:
                        # Object has been gone long enough - allow re-upload if it returns
                        classes_to_reset.add(class_name)
            
            # Reset classes that have been gone
            seen_classes -= classes_to_reset
            
            # Upload NEW detections to AWS
            if uploader and new_classes:
                print(f"\n New detection(s): {', '.join(new_classes)}")
                
                # Upload each new class
                for det in detections:
                    if det['class_name'] in new_classes:
                        # Use teammate's AWSClient: upload_detection(image, object_name)
                        status = uploader.upload_detection(frame, det['class_name'])
                        if status:
                            seen_classes.add(det['class_name'])
            
            # Calculate FPS
            fps_frame_count += 1
            fps_elapsed = time.time() - fps_start_time
            
            if fps_elapsed > 1.0:
                current_fps = fps_frame_count / fps_elapsed
                fps_frame_count = 0
                fps_start_time = time.time()
            
            # Add text overlays
            if config.SHOW_FPS:
                cv2.putText(
                    annotated,
                    f"FPS: {current_fps:.1f}",
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 0),
                    2
                )
            
            if config.SHOW_COUNT:
                cv2.putText(
                    annotated,
                    f"Detections: {len(detections)}",
                    (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 0),
                    2
                )
            
            # Show frame
            if config.SHOW_DISPLAY:
                cv2.imshow('YOLO Detection', annotated)
            
            # Check for 'q' key
            if cv2.waitKey(1) & 0xFF == ord('q'):
                print("\n Quitting...")
                break
    
    except KeyboardInterrupt:
        print("\n\n Interrupted by user")
    
    finally:
        # Cleanup
        cap.release()
        cv2.destroyAllWindows()
        print("\n Camera released")
    
    return True


# Run if called directly
if __name__ == "__main__":
    import sys
    
    # Check for --no-upload flag
    upload = "--no-upload" not in sys.argv
    
    run_camera_detection(upload_enabled=upload)
