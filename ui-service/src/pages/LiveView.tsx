import { useRef, useState, useEffect } from "react";
import { DetectionList } from "../components/DetectionList";
import { JETSON_OFFER_URL } from "../config";
import { sendMarkThreat, sendStopTracking } from "../services/jetson";
import { getLatestDetections, startDetectionPolling } from "../services/aws-authenticated";

type StreamState = "idle" | "connecting" | "streaming" | "error";

export const LiveView: React.FC = () => {
  const videoRef = useRef<HTMLVideoElement | null>(null);

  const [streamState, setStreamState] = useState<StreamState>("idle");
  const [streamError, setStreamError] = useState<string>("");

  const [controlLoading, setControlLoading] = useState<null | "stop" | "threat">(null);
  const [controlMsg, setControlMsg] = useState<string>("");

  // Used to hide the center overlay once the <video> is actually playing
  const [hasVideo, setHasVideo] = useState(false);

  // Detections from AWS (now real data!)
  const [detData, setDetData] = useState(() => ({
    timestamp: new Date().toISOString(),
    fps: 0,
    detections: [] as any[],
  }));

  // Loading state for detections
  const [detectionsLoading, setDetectionsLoading] = useState(false);

  // Auto-refresh toggle
  const [autoRefresh, setAutoRefresh] = useState(false);

  // Manual refresh detections
  const refreshDetections = async () => {
    setDetectionsLoading(true);
    try {
      const latest = await getLatestDetections();
      setDetData(latest);
    } catch (error) {
      console.error("Failed to refresh detections:", error);
    } finally {
      setDetectionsLoading(false);
    }
  };

  // Handle auto-refresh toggle click
  const handleAutoRefreshToggle = () => {
    if (!autoRefresh) {
      // Turning ON: immediately fetch data, then start polling
      refreshDetections();
    }
    setAutoRefresh(!autoRefresh);
  };

  // Auto-refresh effect (polls AWS every 2 seconds when enabled)
  useEffect(() => {
    if (!autoRefresh) return;

    const stopPolling = startDetectionPolling((detections) => {
      setDetData(detections);
    }, 2000); // Poll every 2 seconds

    return stopPolling; // Cleanup on unmount or when autoRefresh toggles off
  }, [autoRefresh]);

  // Load initial detections on mount
  useEffect(() => {
    refreshDetections();
  }, []);

  const startStream = async () => {
    if (streamState === "connecting" || streamState === "streaming") return;

    setStreamState("connecting");
    setStreamError("");
    setHasVideo(false);

    try {
      const pc = new RTCPeerConnection({
        iceServers: [{ urls: "stun:stun.l.google.com:19302" }],
      });

      pc.ontrack = (event) => {
        const stream = event.streams?.[0];
        if (videoRef.current && stream) {
          videoRef.current.srcObject = stream;

          // When playback starts, mark stream as running and remove overlay
          videoRef.current
            .play()
            .then(() => {
              setHasVideo(true);
              setStreamState("streaming");
            })
            .catch((e) => {
              console.error("video.play() failed", e);
              // Still set state to streaming because track exists,
              // but overlay will remain until video actually plays.
              setStreamState("streaming");
            });
        }
      };

      pc.addTransceiver("video", { direction: "recvonly" });

      const offer = await pc.createOffer();
      await pc.setLocalDescription(offer);

      const res = await fetch(JETSON_OFFER_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ type: offer.type, sdp: offer.sdp }),
      });

      if (!res.ok) throw new Error(`Jetson /offer returned HTTP ${res.status}`);

      const answer = await res.json();
      await pc.setRemoteDescription(new RTCSessionDescription(answer));
    } catch (err) {
      console.error(err);
      setStreamState("error");
      setStreamError(
        "Stream unavailable. Check Jetson URL / backend status, then try again."
      );
    }
  };

  const handleStopTracking = async () => {
    setControlMsg("");
    setControlLoading("stop");
    try {
      await sendStopTracking();
      setControlMsg("Stop tracking command sent successfully.");
    } catch (err) {
      console.error(err);
      setControlMsg("Failed to send stop tracking command (Jetson API not reachable yet).");
    } finally {
      setControlLoading(null);
    }
  };

  const handleMarkThreat = async () => {
    setControlMsg("");
    setControlLoading("threat");
    try {
      await sendMarkThreat();
      setControlMsg("Mark as threat command sent successfully.");
    } catch (err) {
      console.error(err);
      setControlMsg("Failed to send mark threat command (Jetson API not reachable yet).");
    } finally {
      setControlLoading(null);
    }
  };

  return (
    <div className="grid grid-cols-1 xl:grid-cols-[2fr_1fr] gap-6">
      {/* Live video + controls */}
      <section className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-slate-100">Live View</h2>
          <span className="text-xs text-slate-400">
            Last update:{" "}
            {new Date(detData.timestamp).toLocaleTimeString([], {
              hour: "2-digit",
              minute: "2-digit",
              second: "2-digit",
            })}
          </span>
        </div>

        <div className="space-y-3">
          <div className="relative rounded-xl border border-slate-800 bg-black h-[360px] overflow-hidden">
            <video
              ref={videoRef}
              autoPlay
              playsInline
              muted
              onPlaying={() => {
                setHasVideo(true);
                setStreamState("streaming");
              }}
              className="w-full h-full object-contain"
            />

            {/* Overlay: show only until video is actually playing */}
            {!hasVideo && (
              <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                <span className="text-xs text-slate-400">
                  {streamState === "idle" && "Stream not started."}
                  {streamState === "connecting" && "Connecting…"}
                  {streamState === "error" && "Stream unavailable."}
                </span>
              </div>
            )}
          </div>

          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="flex flex-wrap gap-2">
              <button
                onClick={startStream}
                disabled={streamState === "connecting" || streamState === "streaming"}
                className="px-3 py-1.5 rounded-md text-sm bg-slate-100 text-slate-900 hover:bg-white disabled:bg-slate-600 disabled:text-slate-300"
              >
                {streamState === "streaming"
                  ? "Stream running"
                  : streamState === "connecting"
                  ? "Connecting…"
                  : "Start live stream"}
              </button>

              <button
                onClick={handleAutoRefreshToggle}
                disabled={detectionsLoading}
                className={`px-3 py-1.5 rounded-md text-sm transition-colors ${
                  autoRefresh
                    ? "bg-emerald-600 text-white hover:bg-emerald-500"
                    : "bg-slate-800 text-slate-100 hover:bg-slate-700 disabled:bg-slate-700 disabled:text-slate-400"
                }`}
              >
                {detectionsLoading && !autoRefresh
                  ? "Loading…"
                  : autoRefresh
                  ? "⏸ Auto-refresh ON"
                  : "▶ Auto-refresh OFF"}
              </button>

              <button
                onClick={handleStopTracking}
                disabled={controlLoading !== null}
                className="px-3 py-1.5 rounded-md text-sm bg-slate-800 text-slate-100 hover:bg-slate-700 disabled:bg-slate-700 disabled:text-slate-400"
              >
                {controlLoading === "stop" ? "Sending…" : "Stop tracking"}
              </button>

              <button
                onClick={handleMarkThreat}
                disabled={controlLoading !== null}
                className="px-3 py-1.5 rounded-md text-sm bg-red-600 text-white hover:bg-red-500 disabled:bg-red-900 disabled:text-slate-300"
              >
                {controlLoading === "threat" ? "Sending…" : "Mark as threat"}
              </button>
            </div>

            {streamState === "error" && (
              <span className="text-xs text-red-400 max-w-xs text-right">
                {streamError}
              </span>
            )}
          </div>

          {controlMsg && (
            <div className="text-xs text-slate-300 border border-slate-800 bg-slate-900/60 rounded-md px-3 py-2">
              {controlMsg}
            </div>
          )}
        </div>
      </section>

      {/* Detections panel */}
      <section className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-slate-100">Current Detections</h2>
          {autoRefresh && (
            <span className="text-xs text-emerald-400 flex items-center gap-1">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              Live
            </span>
          )}
        </div>
        <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-4 h-[360px] flex flex-col">
          <div className="flex items-center justify-between text-xs text-slate-400 mb-2">
            <span>{detData.detections.length} objects detected</span>
            <span>Estimated FPS: {Number(detData.fps).toFixed(1)}</span>
          </div>
          <div className="flex-1 overflow-auto">
            {detectionsLoading && !autoRefresh ? (
              <div className="flex items-center justify-center h-full text-sm text-slate-500">
                Loading detections...
              </div>
            ) : (
              <DetectionList detections={detData.detections} />
            )}
          </div>
        </div>
      </section>
    </div>
  );
};