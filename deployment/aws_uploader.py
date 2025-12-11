"""
AWS Client - Teammate's Implementation

Sends detection data to AWS Lambda endpoints.
Uses ping endpoint for fast connection checks.
"""

import requests
import base64
from datetime import datetime, timezone
import cv2
import config


class AWSClient:
    """
    AWS Client for uploading detections
    
    Created by teammate for AWS Lambda integration.
    Uses ping endpoint for fast connectivity checks.
    """
    
    def __init__(self, ping_url=config.AWS_PING_URL, 
                 upload_url=config.AWS_UPLOAD_URL, 
                 jetson_id=config.JETSON_ID):
        """
        Initialize AWS Client
        
        Args:
            ping_url: AWS ping endpoint for connection checks
            upload_url: AWS upload endpoint for detection data
            jetson_id: Unique identifier for this Jetson device
        """
        self.ping_url = ping_url
        self.upload_url = upload_url
        self.jetson_id = jetson_id
        
        print(f"  AWS Client initialized")
        print(f" Upload URL: {upload_url}")
        print(f" Jetson ID: {jetson_id}\n")

    def endpoint_ok(self):
        """
        Fast HEAD request to verify cloud connectivity.
        Uses /ping endpoint with Mock Integration (no Lambda).
        
        Note: Called internally by upload_detection()
        """
        try:
            r = requests.head(self.ping_url, timeout=0.5)
            return 200 <= r.status_code < 300
        except Exception:
            return False

    def upload_detection(self, image, object_name):
        """
        Upload detection data + image to AWS
        
        Args:
            image: OpenCV image (numpy array in BGR format)
            object_name: Name of detected object (e.g., "person")
            
        Returns:
            HTTP status code if successful, None if failed
        """
        # Check connection first (internal check)
        if not self.endpoint_ok():
            print("⚠️  AWS offline: skipping upload")
            return None

        # Encode image to base64
        _, buffer = cv2.imencode(".jpg", image)
        img_b64 = base64.b64encode(buffer).decode()

        # Build payload
        payload = {
            "jetson_id": self.jetson_id,
            "object_name": object_name,
            "image_base64": img_b64,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        # Send to AWS
        try:
            r = requests.post(self.upload_url, json=payload, timeout=2)
            if 200 <= r.status_code < 300:
                print(f"✅ Uploaded: {object_name} (Status: {r.status_code})")
                return r.status_code
            else:
                print(f"⚠️  Upload failed: HTTP {r.status_code}")
                return None
        except Exception as e:
            print(f"⚠️  Upload error: {e}")
            return None


# For backward compatibility with existing code
AWSUploader = AWSClient
