"""
Main Entry Point for Jetson Nano Object Detection System

Simple command-line interface to run detection in different modes.

Usage:
    python3 main.py --mode image --image photo.jpg
    python3 main.py --mode camera
    python3 main.py --mode camera --no-upload
"""

import argparse
import sys
from image_detector import process_image
from camera_detector import run_camera_detection
import config


def print_banner():
    """Print startup banner"""
    print("\n" + "=" * 60)
    print("  Jetson Nano Object Detection System")
    print("=" * 60)
    print(f"  Target classes: {', '.join(config.CLASS_NAMES.values())}")
    print(f"  Model: {config.MODEL_PATH}")
    print(f"  Confidence threshold: {config.CONFIDENCE_THRESHOLD}")
    print(f"  AWS upload: {'Enabled' if config.ENABLE_UPLOAD else 'Disabled'}")
    print("=" * 60 + "\n")


def main():
    """Main entry point"""
    
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="Jetson Nano Object Detection System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Detect in single image
  python3 main.py --mode image --image photo.jpg
  
  # Real-time camera detection
  python3 main.py --mode camera
  
  # Camera without AWS upload
  python3 main.py --mode camera --no-upload
  
  # Use different model
  python3 main.py --mode camera --model models/yolov8n.pt
  
  # Change confidence threshold
  python3 main.py --mode camera --confidence 0.7
        """
    )
    
    parser.add_argument(
        '--mode',
        type=str,
        required=True,
        choices=['image', 'camera'],
        help='Detection mode: "image" or "camera"'
    )
    
    parser.add_argument(
        '--image',
        type=str,
        help='Path to image file (required for image mode)'
    )
    
    parser.add_argument(
        '--no-upload',
        action='store_true',
        help='Disable AWS upload'
    )
    
    parser.add_argument(
        '--model',
        type=str,
        help=f'Path to YOLO model (default: {config.MODEL_PATH})'
    )
    
    parser.add_argument(
        '--confidence',
        type=float,
        help=f'Confidence threshold (default: {config.CONFIDENCE_THRESHOLD})'
    )
    
    args = parser.parse_args()
    
    # Override config if arguments provided
    if args.model:
        config.MODEL_PATH = args.model
    
    if args.confidence:
        config.CONFIDENCE_THRESHOLD = args.confidence
    
    if args.no_upload:
        config.ENABLE_UPLOAD = False
    
    # Print banner
    print_banner()
    
    # Run selected mode
    if args.mode == 'image':
        # Image mode
        if not args.image:
            print(" Error: --image required for image mode")
            print("\nUsage: python3 main.py --mode image --image photo.jpg")
            sys.exit(1)
        
        success = process_image(args.image, upload_enabled=config.ENABLE_UPLOAD)
        sys.exit(0 if success else 1)
    
    elif args.mode == 'camera':
        # Camera mode
        success = run_camera_detection(upload_enabled=config.ENABLE_UPLOAD)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
