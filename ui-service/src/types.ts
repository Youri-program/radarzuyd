// src/types/index.ts (or types.ts)

/**
 * Single detection object
 */
export interface Detection {
  label: string;
  confidence: number;
  bbox?: number[];
}

/**
 * Detection record from DynamoDB
 */
export interface DetectionRecord {
  detection_id: string;       // Primary key
  timestamp: string;          // ISO 8601 format
  jetson_id: string;          // Device identifier
  object_name?: string;       // Primary detected object
  detections?: Detection[];   // Array of all detected objects
  image_key?: string;         // S3 key for image
  [key: string]: any;         // Allow other fields
}

/**
 * Response from /detections endpoint
 */
export interface GetDetectionsResponse {
  detections?: DetectionRecord[];  // May be array directly
  [key: string]: any;              // Flexible structure
}

/**
 * Response from /images/get endpoint
 */
export interface GetImageResponse {
  url: string;                // Pre-signed S3 URL
  expires_in?: number;        // URL expiration time
}

/**
 * Live detections for Live View page
 */
export interface LiveDetections {
  timestamp: string;
  fps: number;
  detections: Detection[];
  image_key?: string;
}

/**
 * Display item for History page
 */
export interface HistoryDisplayItem {
  detection_id: string;
  timestamp: string;
  object_name: string;
  imageUrl?: string;          // Loaded S3 URL
}