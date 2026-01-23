RADAR DETECTION SYSTEM - LAMBDA FUNCTIONS

OVERVIEW

These AWS Lambda functions power a radar/edge detection system that captures, stores, and retrieves object detection data from Jetson devices.


FUNCTIONS

1. LambdaStoreData.py

Purpose: Ingests detection events from Jetson edge devices.

Flow:
- Receives JSON payload with jetson_id, object_name, and optional image_base64
- Decodes and uploads image to S3 bucket (edge-images-zuyd)
- Logs metadata to DynamoDB (radar-logs table)

Input: POST body with detection data
Output: Confirmation with S3 image key


2. get_detections_data_from_UI.py

Purpose: Queries detection history for the dashboard UI.

Flow:
- Requires jetson_id parameter
- Optional filters: object_name, from/to timestamps, limit
- Queries DynamoDB with filters, returns newest first

Input: Query parameters
Output: JSON array of detection records


3. get_signed_image_url.py

Purpose: Generates temporary S3 access URLs for detection images.

Flow:
- Takes S3 key parameter
- Returns pre-signed URL valid for 1 hour

Input: key parameter (S3 object key)
Output: Signed URL for secure image access


4. jetson-login.py

Purpose: Authenticates Jetson devices via AWS Cognito.

Flow:
- Receives username/password credentials
- Computes secret hash for Cognito client
- Returns JWT tokens (access and ID) on success

Input: username and password in JSON body
Output: Access token, ID token, expiration


ARCHITECTURE

Jetson Device --> LambdaStoreData --> S3 (images) + DynamoDB (metadata)

Dashboard UI --> get_detections_data --> DynamoDB
Dashboard UI --> get_signed_image_url --> S3 (pre-signed URLs)
Dashboard UI --> jetson-login --> Cognito (authentication)


AWS RESOURCES

S3 Bucket: edge-images-zuyd
DynamoDB Table: radar-logs (partition key: jetson_id, sort key: timestamp)
Cognito: User pool for device authentication