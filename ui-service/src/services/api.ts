// src/services/api.ts

import { AWS_DETECTIONS_URL, AWS_IMAGE_GET_URL, JETSON_ID } from '../config';
import { authenticatedFetch } from './auth';

// ============================================
// TYPE DEFINITIONS
// ============================================

export interface Detection {
  class: string;
  confidence: number;
  bbox?: [number, number, number, number];
}

export interface DetectionRecord {
  detection_id: string;
  timestamp: string;
  jetson_id: string;
  object_name: string;
  confidence?: number;
  fps?: number;
  detections: Detection[];
  image_key?: string;
}

export interface GetDetectionsResponse {
  detections?: DetectionRecord[];
  Items?: DetectionRecord[];
  [key: string]: any;
}

export interface GetImageResponse {
  url: string;
  expires_in?: number;
}

// ============================================
// API FUNCTIONS
// ============================================

/**
 * Fetch detection records from DynamoDB
 */
export async function getDetections(
  jetsonId: string = JETSON_ID,
  _options: { limit?: number } = {}
): Promise<DetectionRecord[]> {
  try {
    const url = `${AWS_DETECTIONS_URL}?jetson_id=${encodeURIComponent(jetsonId)}`;
    
    console.log(' Fetching detections from:', url);

    const response = await authenticatedFetch(url);

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      console.error('Response not OK:', response.status, error);
      throw new Error(`Failed to fetch detections: ${response.status}`);
    }

    const data: GetDetectionsResponse = await response.json();
    console.log(' Raw API response:', data);

    // Handle different response formats
    let detections: DetectionRecord[] = [];
    
    if (Array.isArray(data)) {
      detections = data;
    } else if (data.detections && Array.isArray(data.detections)) {
      detections = data.detections;
    } else if (data.Items && Array.isArray(data.Items)) {
      detections = data.Items;
    }

    console.log(` Loaded ${detections.length} detections`);
    return detections;

  } catch (error) {
    console.error(' Error fetching detections:', error);
    throw error;
  }
}

/**
 * Get pre-signed S3 URL for detection image
 */
export async function getImageUrl(imageKey: string): Promise<string> {
  try {
    const url = `${AWS_IMAGE_GET_URL}?key=${encodeURIComponent(imageKey)}`;
    
    console.log('  Fetching image URL for key:', imageKey);

    const response = await authenticatedFetch(url);

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      console.error('Failed to get image URL:', response.status, error);
      throw new Error(`Failed to get image URL: ${response.status}`);
    }

    const data: GetImageResponse = await response.json();
    console.log(' Got image URL');
    
    return data.url;

  } catch (error) {
    console.error(' Error fetching image URL:', error);
    throw error;
  }
}

/**
 * Get the latest detection for a specific Jetson device
 */
export async function getLatestDetection(jetsonId: string = JETSON_ID): Promise<DetectionRecord | null> {
  try {
    const detections = await getDetections(jetsonId, { limit: 1 });
    return detections.length > 0 ? detections[0] : null;
  } catch (error) {
    console.error(' Error fetching latest detection:', error);
    return null;
  }
}