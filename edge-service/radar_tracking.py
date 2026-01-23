import asyncio
import json
import logging
import os
import platform
import time
import math
from dataclasses import dataclass
from fractions import Fraction
from typing import Optional, List, Dict, Any

import cv2
from aiohttp import web
from aiortc import RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.media import MediaStreamTrack
from av import VideoFrame
from ultralytics import YOLO
from servo_controller import ServoController  # Solo ServoController, NO PID

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("radar_system")

# ----------------------------
# CORS 
# ----------------------------
CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Methods": "POST, OPTIONS, GET",
}

# ----------------------------
# Global WebRTC connections
# ----------------------------
PCS = set()

# ----------------------------
# YOLO CONFIG
# ----------------------------
MODEL_PATH = "./models/yolo11s.pt"  
PERSON_CLASS_ID = 0
YOLO_CLASSES = [PERSON_CLASS_ID]
yolo_model = YOLO(MODEL_PATH)

# OpenCV colors 
ORANGE_BGR = (0, 165, 255)
RED_BGR = (0, 0, 255)
BLACK_BGR = (0, 0, 0)
GREEN_BGR = (0, 255, 0)

# ----------------------------
# SERVO CONFIG
# ----------------------------
SERVO_NEUTRAL = 90
SERVO_MIN = 30
SERVO_MAX = 150
CHANNEL_YAW = 0
CHANNEL_PITCH = 1

# ----------------------------
# SMOOTH TRACKING CONFIG
# ----------------------------
# Cuántos píxeles de error = 1 grado de movimiento objetivo
PIXELS_PER_DEGREE = 15.0  # Aún más bajo = más sensible (antes: 20.0)

# Factor de suavizado: qué % del camino recorrer cada frame
# Con servos posicionales podemos ser más agresivos
SMOOTH_FACTOR = 0.3  #  Más alto = más rápido (antes: 0.2)

# THROTTLING: Cuánto tiempo entre comandos de motor (segundos)
MOTOR_COMMAND_INTERVAL = 0.033  # ~30 comandos/segundo (antes: 0.1)
# Valores sugeridos para servos posicionales:
# 0.033 = 30 comandos/seg (muy rápido) ← NUEVO
# 0.05 = 20 comandos/seg (rápido)
# 0.1 = 10 comandos/seg (moderado)

# Return to neutral speed (degrees per second)
RETURN_SPEED = 30.0

# ----------------------------
# PITCH CONTROL FLAG
# ----------------------------
PITCH_ENABLED = True  #  ACTIVADO para testing
PITCH_SMOOTH_FACTOR = 0.1  #  MUY conservador (YAW usa 0.3)
PITCH_PIXELS_PER_DEGREE = 30.0  #  Menos sensible que YAW (YAW usa 15.0)

# ----------------------------
# HISTORY CONFIG
# ----------------------------
HISTORY_DIR = "./history"
os.makedirs(HISTORY_DIR, exist_ok=True)
HISTORY_JSONL = os.path.join(HISTORY_DIR, "events.jsonl")

SCAN_SNAPSHOT_EVERY_S = 8.0
TRACK_SNAPSHOT_EVERY_S = 1.0


# ----------------------------
# Tracking / mission state
# ----------------------------
@dataclass
class MissionState:
    tracking_on: bool = False
    mission_id: Optional[str] = None
    current_yaw_angle: Optional[float] = None  # None = no inicializado aún
    current_pitch_angle: Optional[float] = None  # None = no inicializado aún
    returning_to_neutral: bool = False
    camera_ready: bool = False
    last_motor_command_time: float = 0.0  #  Timestamp del último comando
    

STATE = MissionState()


def now_ms() -> int:
    return int(time.time() * 1000)


def new_mission_id() -> str:
    return f"mission_{now_ms()}"


def write_history_event(event: Dict[str, Any]) -> None:
    with open(HISTORY_JSONL, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")


def save_snapshot(image_bgr, filename: str) -> str:
    path = os.path.join(HISTORY_DIR, filename)
    cv2.imwrite(path, image_bgr)
    return path


# ----------------------------
# Initialize Servo Controller ONLY (NO PID)
# ----------------------------
servo_controller = ServoController(
    channel_yaw=0,
    channel_pitch=1,
    i2c_bus=7,
    mock_print=True
)

#  NO INICIALIZAR SERVOS AL ARRANCAR
# Los servos se moverán SOLO cuando se active tracking
log.info("=" * 70)
log.info(" SERVO CONTROLLER READY")
log.info("=" * 70)
log.info("  Servos will NOT move until tracking is activated")
log.info("  Initial position will be set on first tracking command")
log.info("=" * 70)

# Guardar que aún no hemos inicializado
STATE.current_yaw_angle = None  # None = no inicializado
STATE.current_pitch_angle = None


def control_motors_smooth(error_x, error_y, frame_width=1280):
    """
    Control SUAVIZADO de servos - movimiento gradual hacia el objetivo.
    CON THROTTLING: Solo envía comandos cada MOTOR_COMMAND_INTERVAL segundos.
    AHORA CON PITCH: Controlado de forma más conservadora que YAW.
    
    error_x: horizontal error in pixels (positive = target to the right)
    error_y: vertical error in pixels (positive = target below center)
    frame_width: ancho del frame para cálculos
    """
    #  THROTTLING: Verificar si ha pasado suficiente tiempo desde el último comando
    current_time = time.time()
    time_since_last_command = current_time - STATE.last_motor_command_time
    
    if time_since_last_command < MOTOR_COMMAND_INTERVAL:
        # No ha pasado suficiente tiempo, skip este frame
        log.debug(f"⏸ THROTTLED - Skipping command (last: {time_since_last_command:.2f}s ago)")
        return
    
    #  PRIMERA VEZ: Inicializar a neutral si aún no se ha hecho
    if STATE.current_yaw_angle is None:
        log.info("=" * 70)
        log.info("FIRST TRACKING COMMAND - Initializing servos to neutral")
        log.info("=" * 70)
        STATE.current_yaw_angle = SERVO_NEUTRAL
        STATE.current_pitch_angle = SERVO_NEUTRAL
        servo_controller.set_angles(SERVO_NEUTRAL, SERVO_NEUTRAL, force=True)
        STATE.last_motor_command_time = current_time
        log.info(f" SERVOS INITIALIZED → YAW={SERVO_NEUTRAL}°, PITCH={SERVO_NEUTRAL}°")
        log.info("=" * 70)
        return  # No mover en el primer frame, solo inicializar
    
    # ===== YAW CONTROL (rápido/responsivo) =====
    angle_correction_yaw = error_x / PIXELS_PER_DEGREE
    target_yaw = SERVO_NEUTRAL + angle_correction_yaw
    target_yaw = max(SERVO_MIN, min(SERVO_MAX, target_yaw))
    
    prev_yaw = STATE.current_yaw_angle
    angle_diff_yaw = target_yaw - STATE.current_yaw_angle
    STATE.current_yaw_angle += angle_diff_yaw * SMOOTH_FACTOR
    
    # ===== PITCH CONTROL (conservador) =====
    if PITCH_ENABLED:
        angle_correction_pitch = error_y / PITCH_PIXELS_PER_DEGREE
        target_pitch = SERVO_NEUTRAL + angle_correction_pitch
        target_pitch = max(SERVO_MIN, min(SERVO_MAX, target_pitch))
        
        prev_pitch = STATE.current_pitch_angle
        angle_diff_pitch = target_pitch - STATE.current_pitch_angle
        STATE.current_pitch_angle += angle_diff_pitch * PITCH_SMOOTH_FACTOR  # Más lento
    else:
        # PITCH desactivado - mantener en neutral
        STATE.current_pitch_angle = SERVO_NEUTRAL
        prev_pitch = SERVO_NEUTRAL
        target_pitch = SERVO_NEUTRAL
        angle_diff_pitch = 0
    
    #  LOG ANTES de enviar comando
    if PITCH_ENABLED:
        log.info(
            f" MOTOR CMD → YAW: {prev_yaw:.2f}° → {STATE.current_yaw_angle:.2f}° "
            f"(target: {target_yaw:.1f}°, error_x: {error_x:.0f}px, diff: {angle_diff_yaw:.2f}°) | "
            f"PITCH: {prev_pitch:.2f}° → {STATE.current_pitch_angle:.2f}° "
            f"(target: {target_pitch:.1f}°, error_y: {error_y:.0f}px, diff: {angle_diff_pitch:.2f}°)"
        )
    else:
        log.info(
            f" MOTOR CMD → YAW: {prev_yaw:.2f}° → {STATE.current_yaw_angle:.2f}° "
            f"(target: {target_yaw:.1f}°, error: {error_x:.0f}px, diff: {angle_diff_yaw:.2f}°, "
            f"interval: {time_since_last_command:.2f}s)"
        )
    
    # Enviar a los servos
    servo_controller.set_angles(STATE.current_yaw_angle, STATE.current_pitch_angle)
    STATE.last_motor_command_time = current_time
    
    #  LOG DESPUÉS de enviar comando
    log.info(f" MOTOR SENT → YAW={STATE.current_yaw_angle:.2f}°, PITCH={STATE.current_pitch_angle:.2f}°")


def return_to_neutral():
    """
    Return YAW servo to neutral position gradually.
    PITCH is always at neutral (disabled).
    """
    # Si nunca se inicializaron los servos, no hacer nada
    if STATE.current_yaw_angle is None:
        STATE.returning_to_neutral = False
        log.info("  Servos were never initialized, skipping return to neutral")
        return True
    
    moved = False
    step = RETURN_SPEED * 0.033  # ~1 degree per frame at 30fps
    
    prev_yaw = STATE.current_yaw_angle
    
    # Return yaw to neutral
    if abs(STATE.current_yaw_angle - SERVO_NEUTRAL) > step:
        if STATE.current_yaw_angle > SERVO_NEUTRAL:
            STATE.current_yaw_angle -= step
        else:
            STATE.current_yaw_angle += step
        moved = True
    else:
        STATE.current_yaw_angle = SERVO_NEUTRAL
    
    # Pitch always stays at neutral
    STATE.current_pitch_angle = SERVO_NEUTRAL
    
    if moved:
        #  LOG de retorno a neutral
        log.info(
            f" RETURNING → YAW: {prev_yaw:.2f}° → {STATE.current_yaw_angle:.2f}° "
            f"(step: {step:.2f}°, remaining: {abs(STATE.current_yaw_angle - SERVO_NEUTRAL):.2f}°)"
        )
        servo_controller.set_angles(STATE.current_yaw_angle, STATE.current_pitch_angle)
        log.info(f" RETURN SENT → YAW={STATE.current_yaw_angle:.2f}°")
        return False
    else:
        STATE.returning_to_neutral = False
        log.info(" YAW servo at neutral position (90.0°)")
        return True


class CameraVideoTrack(MediaStreamTrack):
    """
    Video track with YOLO detection and SMOOTH YAW control.
    """
    kind = "video"

    def __init__(self, camera_index=0, width=1280, height=720, fps=30):
        super().__init__()
        self.camera_index = camera_index
        self.width = width
        self.height = height
        self.fps = fps

        backend = cv2.CAP_DSHOW if platform.system() == "Windows" else 0
        self.cap = cv2.VideoCapture(self.camera_index, backend)
        if not self.cap.isOpened():
            raise RuntimeError(f"Could not open camera index {self.camera_index}")

        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        self.cap.set(cv2.CAP_PROP_FPS, self.fps)

        self._frame_time = 1.0 / float(self.fps)
        self._pts = 0
        self._time_base = Fraction(1, 90000)
        self._last_snapshot_t = 0.0

        log.info(f"📹 Camera opened index={self.camera_index}, {self.width}x{self.height}@{self.fps}")
        
        # Marcar cámara como lista
        STATE.camera_ready = True
        log.info(" Camera ready - servo control now enabled")

    async def recv(self):
        await asyncio.sleep(self._frame_time)

        ok, frame = self.cap.read()
        if not ok or frame is None:
            frame = self._black_frame()

        annotated, detections = self._run_yolo_and_annotate(frame)

        # Solo controlar servos si cámara está lista y hay tracking activo
        if STATE.camera_ready and STATE.tracking_on and detections:
            # TRACKING MODE: Follow largest person with SMOOTH movement
            STATE.returning_to_neutral = False
            
            largest_detection = max(
                detections, 
                key=lambda x: (x["x2"] - x["x1"]) * (x["y2"] - x["y1"])
            )
            
            cx = (largest_detection["x1"] + largest_detection["x2"]) // 2
            cy = (largest_detection["y1"] + largest_detection["y2"]) // 2
            
            # Calculate horizontal and vertical errors
            error_x = cx - self.width // 2   # YAW
            error_y = cy - self.height // 2  #  PITCH (ahora se usa)
            
            self._draw_crosshair(annotated, cx, cy, RED_BGR)
            
            # Control suavizado con YAW y PITCH
            control_motors_smooth(error_x, error_y)
            
        elif not STATE.tracking_on and STATE.returning_to_neutral:
            # RETURNING TO NEUTRAL
            return_to_neutral()
        
        self._maybe_log_history(annotated, detections)

        vf = VideoFrame.from_ndarray(annotated, format="bgr24")
        vf.pts = self._pts
        vf.time_base = self._time_base
        self._pts += int(90000 / self.fps)
        return vf

    def _run_yolo_and_annotate(self, frame_bgr):
        box_color = RED_BGR if STATE.tracking_on else ORANGE_BGR
        detections: List[Dict[str, Any]] = []
        annotated = frame_bgr.copy()

        try:
            results = yolo_model(frame_bgr, classes=YOLO_CLASSES, verbose=False)
            boxes = results[0].boxes
            people_count = 0

            for box in boxes:
                cls_id = int(box.cls[0])
                if cls_id != PERSON_CLASS_ID:
                    continue

                x1, y1, x2, y2 = map(int, box.xyxy[0])
                conf = float(box.conf[0])

                detections.append({"x1": x1, "y1": y1, "x2": x2, "y2": y2, "conf": conf})
                people_count += 1

                cv2.rectangle(annotated, (x1, y1), (x2, y2), box_color, 2)

                label = f"Person {conf:.2f}"
                (tw, th), baseline = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
                y_top = max(0, y1 - th - baseline)
                cv2.rectangle(annotated, (x1, y_top), (x1 + tw, y1), box_color, -1)
                cv2.putText(
                    annotated,
                    label,
                    (x1, y1 - baseline),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    BLACK_BGR,
                    1,
                    cv2.LINE_AA,
                )

            # Status overlay
            status = "TRACKING" if STATE.tracking_on else "SCANNING"
            if STATE.returning_to_neutral:
                status = "RETURNING"
                
            overlay = f"{status} | Detected: {people_count} | YAW+PITCH TESTING"
            cv2.putText(
                annotated,
                overlay,
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                box_color,
                2,
                cv2.LINE_AA,
            )
            
            # Servo info
            yaw_display = f"{STATE.current_yaw_angle:.1f}°" if STATE.current_yaw_angle is not None else "NOT INIT"
            pitch_display = f"{STATE.current_pitch_angle:.1f}°" if STATE.current_pitch_angle is not None else "NOT INIT"
            pitch_status = "ACTIVE (TESTING)" if PITCH_ENABLED else "DISABLED"
            servo_info = f"YAW: {yaw_display} | PITCH: {pitch_display} ({pitch_status})"
            cv2.putText(
                annotated,
                servo_info,
                (10, self.height - 20),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                GREEN_BGR,
                2,
                cv2.LINE_AA,
            )
            
            # Draw vertical center line
            self._draw_vertical_centerline(annotated)

        except Exception:
            log.exception("YOLO failed")
            detections = []

        return annotated, detections

    def _draw_vertical_centerline(self, frame):
        """Draw a vertical line at center (YAW reference)."""
        cx = self.width // 2
        color = GREEN_BGR
        thickness = 2
        
        # Vertical line
        cv2.line(frame, (cx, 0), (cx, self.height), color, thickness)
        
        # Center circle
        cy = self.height // 2
        cv2.circle(frame, (cx, cy), 5, color, -1)
    
    def _draw_crosshair(self, frame, x, y, color):
        """Draw crosshair on target."""
        size = 15
        thickness = 2
        
        cv2.line(frame, (x - size, y), (x + size, y), color, thickness)
        cv2.line(frame, (x, y - size), (x, y + size), color, thickness)

    def _maybe_log_history(self, annotated_bgr, detections: List[Dict[str, Any]]):
        t = time.time()
        interval = TRACK_SNAPSHOT_EVERY_S if STATE.tracking_on else SCAN_SNAPSHOT_EVERY_S

        if len(detections) == 0:
            return

        if (t - self._last_snapshot_t) < interval:
            return

        self._last_snapshot_t = t

        ts = now_ms()
        mission_part = STATE.mission_id if STATE.mission_id else "scan"
        filename = f"{mission_part}_{ts}.jpg"
        path = save_snapshot(annotated_bgr, filename)

        event = {
            "timestamp_ms": ts,
            "mode": "tracking" if STATE.tracking_on else "scanning",
            "mission_id": STATE.mission_id,
            "servo_yaw": STATE.current_yaw_angle,
            "servo_pitch": STATE.current_pitch_angle,
            "control_type": "smooth",
            "smooth_factor": SMOOTH_FACTOR,
            "detections": detections,
            "snapshot_path": path,
        }
        write_history_event(event)

    def _black_frame(self):
        return (0 * (cv2.UMat(480, 640, cv2.CV_8UC3)).get())

    def stop(self):
        try:
            if self.cap:
                self.cap.release()
        except Exception:
            pass
        super().stop()


# ----------------------------
# HTTP endpoints
# ----------------------------
async def offer(request: web.Request):
    try:
        data = await request.json()
        sdp = data["sdp"]
        typ = data["type"]
    except Exception:
        return web.json_response(
            {"error": "Invalid JSON (expected sdp/type)."}, 
            status=400, 
            headers=CORS_HEADERS
        )

    pc = RTCPeerConnection()
    PCS.add(pc)
    log.info("New PeerConnection. Total=%d", len(PCS))

    @pc.on("connectionstatechange")
    async def on_connectionstatechange():
        log.info("PC state: %s", pc.connectionState)
        if pc.connectionState in ("failed", "closed", "disconnected"):
            await pc.close()
            PCS.discard(pc)
            log.info("PeerConnection closed. Total=%d", len(PCS))

    try:
        track = CameraVideoTrack(camera_index=0, width=1280, height=720, fps=30)
    except Exception as e:
        log.exception("Camera error")
        return web.json_response({"error": str(e)}, status=500, headers=CORS_HEADERS)

    pc.addTrack(track)

    await pc.setRemoteDescription(RTCSessionDescription(sdp=sdp, type=typ))
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)

    return web.json_response(
        {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type},
        headers=CORS_HEADERS,
    )


async def offer_options(request: web.Request):
    return web.Response(status=204, headers=CORS_HEADERS)


async def mark_threat(request: web.Request):
    if not STATE.tracking_on:
        STATE.tracking_on = True
        STATE.returning_to_neutral = False
        STATE.mission_id = new_mission_id()

        event = {
            "timestamp_ms": now_ms(),
            "event": "mark_threat",
            "mission_id": STATE.mission_id,
        }
        write_history_event(event)
        
        log.info("=" * 70)
        log.info(f" TRACKING STARTED (SMOOTH CONTROL)")
        log.info(f" Mission ID: {STATE.mission_id}")
        log.info(f" Current YAW: {STATE.current_yaw_angle:.2f}°")
        log.info(f"  Motor commands will now be sent on every frame with detections")
        log.info("=" * 70)

    return web.json_response(
        {
            "ok": True, 
            "tracking_on": STATE.tracking_on, 
            "mission_id": STATE.mission_id
        }, 
        headers=CORS_HEADERS
    )


async def stop_tracking(request: web.Request):
    if STATE.tracking_on:
        event = {
            "timestamp_ms": now_ms(),
            "event": "stop_tracking",
            "mission_id": STATE.mission_id,
        }
        write_history_event(event)
        
        log.info("=" * 70)
        log.info(f"  TRACKING STOPPED")
        log.info(f" Mission ID: {STATE.mission_id}")
        
        #  DETENER SERVOS INMEDIATAMENTE enviando comando explícito
        if STATE.current_yaw_angle is not None:
            log.info(f" Current YAW position: {STATE.current_yaw_angle:.2f}°")
            log.info(f" STOPPING servos - sending STOP command")
            
            # Enviar comando explícito para mantener posición actual
            servo_controller.set_angles(
                STATE.current_yaw_angle, 
                STATE.current_pitch_angle, 
                force=True  # Force para asegurar que se envía
            )
            log.info(f" STOP COMMAND SENT → Servos held at YAW={STATE.current_yaw_angle:.2f}°")
        else:
            log.info("Servos were never initialized")
        
        log.info("=" * 70)

    STATE.tracking_on = False
    STATE.mission_id = None
    STATE.returning_to_neutral = False

    return web.json_response(
        {
            "ok": True, 
            "tracking_on": STATE.tracking_on, 
            "mission_id": STATE.mission_id,
            "servo_position": STATE.current_yaw_angle
        }, 
        headers=CORS_HEADERS
    )


async def get_status(request: web.Request):
    return web.json_response(
        {
            "tracking_on": STATE.tracking_on,
            "mission_id": STATE.mission_id,
            "servo_yaw": STATE.current_yaw_angle if STATE.current_yaw_angle is not None else "not_initialized",
            "servo_pitch": STATE.current_pitch_angle if STATE.current_pitch_angle is not None else "not_initialized",
            "camera_ready": STATE.camera_ready,
            "control_type": "smooth",
            "smooth_factor": SMOOTH_FACTOR,
            "returning_to_neutral": STATE.returning_to_neutral,
        },
        headers=CORS_HEADERS
    )


async def generic_options(request: web.Request):
    return web.Response(status=204, headers=CORS_HEADERS)


async def on_shutdown(app: web.Application):
    coros = [pc.close() for pc in PCS]
    await asyncio.gather(*coros, return_exceptions=True)
    PCS.clear()
    
    log.info("Returning servos to neutral position...")
    servo_controller.set_angles(SERVO_NEUTRAL, SERVO_NEUTRAL, force=True)


def create_app():
    app = web.Application()

    app.router.add_route("POST", "/offer", offer)
    app.router.add_route("OPTIONS", "/offer", offer_options)
    app.router.add_route("POST", "/mark_threat", mark_threat)
    app.router.add_route("POST", "/stop_tracking", stop_tracking)
    app.router.add_route("GET", "/status", get_status)
    app.router.add_route("OPTIONS", "/mark_threat", generic_options)
    app.router.add_route("OPTIONS", "/stop_tracking", generic_options)

    app.on_shutdown.append(on_shutdown)
    return app


if __name__ == "__main__":
    log.info("=" * 70)
    log.info(" RADAR TRACKING SYSTEM - SMOOTH CONTROL")
    log.info("=" * 70)
    log.info(f" Camera: 1280x720@30fps")
    log.info(f" YAW: Active (Smooth Control) | PITCH: DISABLED")
    log.info(f"  Sensitivity: {PIXELS_PER_DEGREE} pixels/degree")
    log.info(f" Smoothness: {SMOOTH_FACTOR} (0.05=very smooth, 0.2=responsive)")
    log.info(f" Server: http://0.0.0.0:8080")
    log.info("=" * 70)
    
    if servo_controller.pca is None:
        log.warning("  Running in MOCK mode (no PCA9685 hardware detected)")
        log.warning("    Servo commands will be logged but not executed")
    else:
        log.info(" Hardware mode: PCA9685 detected and ready")
    
    log.info("=" * 70)
    log.info(" Waiting for camera to initialize before enabling servo control...")
    log.info("")
    log.info(" TIP: Adjust these values in the code if needed:")
    log.info(f"   - PIXELS_PER_DEGREE = {PIXELS_PER_DEGREE} (higher = slower)")
    log.info(f"   - SMOOTH_FACTOR = {SMOOTH_FACTOR} (lower = smoother)")
    log.info("=" * 70)
    
    web.run_app(create_app(), host="0.0.0.0", port=8080)
