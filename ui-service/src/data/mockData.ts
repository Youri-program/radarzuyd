import type { LiveDetections, HistoryItem, SystemStatus } from "../types";

export const mockLiveDetections: LiveDetections = {
  timestamp: "2025-02-01T12:00:00Z",
  fps: 8.7,
  detections: [
    { label: "person", confidence: 0.94 },
    { label: "bottle", confidence: 0.82 },
    { label: "chair", confidence: 0.77 },
  ],
};

export const mockHistory: HistoryItem[] = [
  { id: 1, timestamp: "2025-02-01T12:00:00Z", mainLabel: "person", numDetections: 3 },
  { id: 2, timestamp: "2025-02-01T11:59:32Z", mainLabel: "bottle", numDetections: 1 },
  { id: 3, timestamp: "2025-02-01T11:58:05Z", mainLabel: "dog", numDetections: 2 },
  { id: 4, timestamp: "2025-02-01T11:57:41Z", mainLabel: "person", numDetections: 2 },
];

export const mockStatus: SystemStatus = {
  backendOnline: true,
  modelName: "YOLOv8 (mock)",
  fps: 8.7,
};
