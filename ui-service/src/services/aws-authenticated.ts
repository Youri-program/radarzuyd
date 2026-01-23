// src/services/aws.ts

import type { 
  HistoryItem, 
  LiveDetections, 
  GetDetectionsResponse,
  GetImageResponse,
  HistoryDisplayItem 
} from "../types";
import {
  AWS_DETECTIONS_URL,
  AWS_IMAGE_GET_URL,
  JETSON_ID,
} from "../config";
import { authenticatedFetch } from "./auth";

/**
 * Fetch latest detections (used in Live View)
 * Requires authentication token
 */
export async function getLatestDetections(): Promise<LiveDetections> {
  try {
    // Add jetson_id as query parameter
    const url = new URL(AWS_DETECTIONS_URL);
    url.searchParams.set("jetson_id", JETSON_ID);

    // Use authenticatedFetch which includes Authorization header
    const res = await authenticatedFetch(url.toString());

    if (!res.ok) {
      const errorText = await res.text();
      throw new Error(`AWS /detections failed: ${res.status} ${res.statusText} - ${errorText}`);
    }

    const data: GetDetectionsResponse = await res.json();

    // DynamoDB returns items in "Items" array
    const items = data.Items || [];

    if (items.length === 0) {
      // Return empty detections if no data
      return {
        timestamp: new Date().toISOString(),
        fps: 0,
        detections: [],
      };
    }

    // Get the most recent item (assuming sorted by timestamp, or take first)
    const latest = items[0];

    return {
      timestamp: latest.timestamp,
      fps: latest.fps ?? 0,
      detections: latest.detections || [],
      image_key: latest.image_key,
    };

  } catch (error) {
    console.error("Error fetching latest detections:", error);
    
    // Re-throw authentication errors so UI can handle them
    if (error instanceof Error && error.message.includes('login')) {
      throw error;
    }
    
    // Return empty detections on other errors
    return {
      timestamp: new Date().toISOString(),
      fps: 0,
      detections: [],
    };
  }
}

/**
 * Fetch historical detections (History page)
 * Requires authentication token
 */
export async function getHistory(): Promise<HistoryDisplayItem[]> {
  try {
    // Add jetson_id as query parameter
    const url = new URL(AWS_DETECTIONS_URL);
    url.searchParams.set("jetson_id", JETSON_ID);

    // Use authenticatedFetch which includes Authorization header
    const res = await authenticatedFetch(url.toString());

    if (!res.ok) {
      const errorText = await res.text();
      throw new Error(`AWS /detections failed: ${res.status} ${res.statusText} - ${errorText}`);
    }

    const data: GetDetectionsResponse = await res.json();

    // DynamoDB returns items in "Items" array
    const items: HistoryItem[] = data.Items || [];

    // Transform to display format
    return items.map((item) => ({
      id: item.detection_id,
      timestamp: item.timestamp,
      mainLabel: item.detections?.[0]?.label || "Unknown",
      numDetections: item.detections?.length || 0,
      imageKey: item.image_key,
    }));

  } catch (error) {
    console.error("Error fetching history:", error);
    
    // Re-throw authentication errors
    if (error instanceof Error && error.message.includes('login')) {
      throw error;
    }
    
    return [];
  }
}

/**
 * Get pre-signed S3 URL for an image
 * Requires authentication token
 */
export async function getImageUrl(imageKey: string): Promise<string> {
  try {
    const url = new URL(AWS_IMAGE_GET_URL);
    url.searchParams.set("image_key", imageKey);
    url.searchParams.set("jetson_id", JETSON_ID);

    // Use authenticatedFetch which includes Authorization header
    const res = await authenticatedFetch(url.toString());

    if (!res.ok) {
      const errorText = await res.text();
      throw new Error(`AWS /images/get failed: ${res.status} ${res.statusText} - ${errorText}`);
    }

    const data: GetImageResponse = await res.json();
    
    if (!data.url) {
      throw new Error("No URL returned from AWS");
    }

    return data.url;

  } catch (error) {
    console.error("Error fetching image URL:", error);
    throw error;
  }
}

/**
 * Helper: Refresh detections periodically
 * Useful for auto-updating the Live View
 */
export function startDetectionPolling(
  callback: (detections: LiveDetections) => void,
  intervalMs: number = 2000
): () => void {
  const poll = async () => {
    try {
      const detections = await getLatestDetections();
      callback(detections);
    } catch (error) {
      // If authentication error, stop polling
      if (error instanceof Error && error.message.includes('login')) {
        console.error('Authentication error in polling, stopping...');
        clearInterval(intervalId);
      }
    }
  };

  // Initial fetch
  poll();

  // Set up interval
  const intervalId = setInterval(poll, intervalMs);

  // Return cleanup function
  return () => clearInterval(intervalId);
}