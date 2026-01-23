// src/services/jetson.ts
import {
  JETSON_MARK_THREAT_URL,
  JETSON_STOP_TRACKING_URL,
} from "../config";

export async function sendStopTracking(): Promise<void> {
  const res = await fetch(JETSON_STOP_TRACKING_URL, { method: "POST" });
  if (!res.ok) throw new Error(`Stop tracking failed: HTTP ${res.status}`);
}

export async function sendMarkThreat(): Promise<void> {
  const res = await fetch(JETSON_MARK_THREAT_URL, { method: "POST" });
  if (!res.ok) throw new Error(`Mark threat failed: HTTP ${res.status}`);
}
