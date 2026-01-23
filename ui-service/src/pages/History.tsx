// src/pages/History.tsx - FIXED FOR BACKEND FORMAT

import { useState, useEffect } from 'react';
import { getDetections, getImageUrl } from '../services/api';
import { TopBar } from '../components/TopBar';
import { Sidebar } from '../components/Sidebar';

interface BackendDetectionRecord {
  image_url: string;
  object_name: string;
  jetson_id: string;
  timestamp: string;
}

interface HistoryDisplayItem {
  detection_id: string;
  timestamp: string;
  object_name: string;
  image_key: string;
  imageUrl?: string;
  imageLoading?: boolean;
  imageError?: string;
}

type Page = "live" | "history";

export default function History() {
  const [detections, setDetections] = useState<HistoryDisplayItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [currentPage] = useState<Page>("history");

  // Load detections on mount
  useEffect(() => {
    loadDetections();
  }, []);

  const handleNavigate = (page: Page) => {
    if (page === "live") {
      window.location.href = "/live";
    }
  };

  /**
   * Parse timestamp from backend format: "20260119-133442-681725"
   * to JavaScript Date: "2026-01-19T13:34:42.681Z"
   */
  const parseTimestamp = (timestamp: string): string => {
    try {
      // Format: YYYYMMDD-HHMMSS-microseconds
      const datePart = timestamp.substring(0, 8);  // "20260119"
      const timePart = timestamp.substring(9, 15); // "133442"
      
      const year = datePart.substring(0, 4);
      const month = datePart.substring(4, 6);
      const day = datePart.substring(6, 8);
      
      const hour = timePart.substring(0, 2);
      const minute = timePart.substring(2, 4);
      const second = timePart.substring(4, 6);
      
      // Create ISO format string
      const isoString = `${year}-${month}-${day}T${hour}:${minute}:${second}Z`;
      
      return isoString;
    } catch (e) {
      console.warn('Failed to parse timestamp:', timestamp, e);
      return new Date().toISOString();
    }
  };

  const loadDetections = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const records = await getDetections() as unknown as BackendDetectionRecord[];
      
      console.log(' Transforming backend data to frontend format...');
      
      // Transform backend format to frontend format
      const items: HistoryDisplayItem[] = records.map(record => {
        const parsedTimestamp = parseTimestamp(record.timestamp);
        
        return {
          detection_id: record.timestamp, // Use timestamp as ID since backend doesn't provide detection_id
          timestamp: parsedTimestamp,
          object_name: record.object_name,
          image_key: record.image_url, // Backend calls it image_url, we call it image_key
        };
      });

      console.log(' Transformed data:', items);
      setDetections(items);
      
      if (items.length === 0) {
        console.log('  No detections found');
      }

    } catch (err) {
      console.error('Failed to load detections:', err);
      setError(err instanceof Error ? err.message : 'Failed to load detections');
    } finally {
      setLoading(false);
    }
  };

  const loadImage = async (detectionId: string) => {
    try {
      const detection = detections.find(d => d.detection_id === detectionId);
      if (!detection) return;

      if (!detection.image_key) {
        setDetections(prev => prev.map(d =>
          d.detection_id === detectionId
            ? { ...d, imageError: 'No image available for this detection' }
            : d
        ));
        return;
      }

      // Set loading state
      setDetections(prev => prev.map(d =>
        d.detection_id === detectionId
          ? { ...d, imageLoading: true, imageError: undefined }
          : d
      ));

      console.log('  Requesting image for key:', detection.image_key);

      // Fetch the pre-signed URL using image_key
      const url = await getImageUrl(detection.image_key);

      // Update with URL
      setDetections(prev => prev.map(d =>
        d.detection_id === detectionId
          ? { ...d, imageUrl: url, imageLoading: false }
          : d
      ));

    } catch (err) {
      console.error('Failed to load image:', err);
      setDetections(prev => prev.map(d =>
        d.detection_id === detectionId
          ? { 
              ...d, 
              imageLoading: false, 
              imageError: err instanceof Error ? err.message : 'Failed to load image' 
            }
          : d
      ));
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex">
      {/* Sidebar with props */}
      <Sidebar currentPage={currentPage} onNavigate={handleNavigate} />
      
      <div className="flex-1 flex flex-col">
        <TopBar onLogout={() => {}} />
        
        <main className="flex-1 p-8">
          <div className="max-w-6xl mx-auto">
            {/* Header */}
            <div className="flex items-center justify-between mb-8">
              <h1 className="text-3xl font-bold">Detection History</h1>
              <button
                onClick={loadDetections}
                disabled={loading}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-700 disabled:cursor-not-allowed rounded-lg transition-colors"
              >
                {loading ? 'Loading...' : 'Refresh'}
              </button>
            </div>

            {/* Error State */}
            {error && (
              <div className="mb-6 p-4 bg-red-500/10 border border-red-500/50 rounded-lg text-red-400">
                <p className="font-semibold">Error:</p>
                <p>{error}</p>
              </div>
            )}

            {/* Loading State */}
            {loading && (
              <div className="text-center py-12">
                <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
                <p className="mt-4 text-slate-400">Loading detections...</p>
              </div>
            )}

            {/* Empty State */}
            {!loading && !error && detections.length === 0 && (
              <div className="text-center py-12 bg-slate-900/50 rounded-lg border border-slate-800">
                <p className="text-slate-400 text-lg">No detections found</p>
                <p className="text-slate-500 mt-2">Detection records will appear here once available</p>
              </div>
            )}

            {/* Detections List */}
            {!loading && detections.length > 0 && (
              <div className="space-y-4">
                {detections.map((detection) => (
                  <div
                    key={detection.detection_id}
                    className="bg-slate-900 border border-slate-800 rounded-lg p-6 hover:border-slate-700 transition-colors"
                  >
                    <div className="flex items-start justify-between mb-4">
                      <div>
                        <h3 className="text-xl font-semibold text-blue-400">
                          {detection.object_name}
                        </h3>
                        <p className="text-slate-400 text-sm mt-1">
                          ID: {detection.detection_id}
                        </p>
                        <p className="text-slate-500 text-sm">
                          {new Date(detection.timestamp).toLocaleString()}
                        </p>
                      </div>

                      {!detection.imageUrl && !detection.imageLoading && (
                        <button
                          onClick={() => loadImage(detection.detection_id)}
                          disabled={detection.imageLoading || !detection.image_key}
                          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-700 disabled:cursor-not-allowed rounded-lg transition-colors text-sm"
                        >
                          {detection.image_key ? 'Load Image' : 'No Image'}
                        </button>
                      )}
                    </div>

                    {/* Loading State */}
                    {detection.imageLoading && (
                      <div className="mt-4 p-4 bg-slate-800/50 rounded-lg text-center">
                        <div className="inline-block animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500"></div>
                        <p className="mt-2 text-slate-400 text-sm">Loading image...</p>
                      </div>
                    )}

                    {/* Image Error */}
                    {detection.imageError && (
                      <div className="mt-4 p-4 bg-red-500/10 border border-red-500/50 rounded-lg text-red-400 text-sm">
                        {detection.imageError}
                      </div>
                    )}

                    {/* Image Display */}
                    {detection.imageUrl && (
                      <div className="mt-4">
                        <img
                          src={detection.imageUrl}
                          alt={`Detection: ${detection.object_name}`}
                          className="w-full max-w-2xl rounded-lg border border-slate-700"
                          onError={() => {
                            console.error('Image failed to load:', detection.imageUrl);
                            setDetections(prev => prev.map(d =>
                              d.detection_id === detection.detection_id
                                ? { ...d, imageUrl: undefined, imageError: 'Failed to load image' }
                                : d
                            ));
                          }}
                        />
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  );
}