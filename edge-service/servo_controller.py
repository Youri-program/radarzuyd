import time
from typing import Optional

# ---- Hardware imports (Jetson/RPi) with Windows-safe fallback ----
HARDWARE_OK = True
_hw_import_error: Optional[Exception] = None

try:
    import board  # type: ignore
    import busio  # type: ignore
    from adafruit_pca9685 import PCA9685  # type: ignore
except Exception as e:
    HARDWARE_OK = False
    _hw_import_error = e


class PIDController:
    def __init__(self, Kp, Ki, Kd, dt, output_limits=(None, None)):
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        self.dt = dt

        self.integral = 0.0
        self.prev_error = 0.0

        self.min_output, self.max_output = output_limits

    def reset(self):
        """Reset the PID controller state."""
        self.integral = 0.0
        self.prev_error = 0.0

    def compute(self, setpoint, measurement):
        """Compute PID output.

        setpoint: desired value
        measurement: current value
        return: PID output
        """
        error = setpoint - measurement

        # Integral term
        self.integral += error * self.dt

        # Derivative term
        derivative = (error - self.prev_error) / self.dt

        # PID output
        output = self.Kp * error + self.Ki * self.integral + self.Kd * derivative

        # Simple anti-windup (saturation)
        if self.max_output is not None:
            output = min(self.max_output, output)
        if self.min_output is not None:
            output = max(self.min_output, output)

        self.prev_error = error
        return output


class ServoController:
    """PCA9685 servo controller.

    Key feature: you can choose an explicit Linux I2C bus number.

    - If i2c_bus is provided (e.g., 4), we try to use `adafruit_extended_bus.ExtendedI2C(i2c_bus)`.
      This is the most reliable way to select the exact /dev/i2c-<n> device.
    - If that library isn't installed, we fall back to the default `busio.I2C(board.SCL, board.SDA)`.

    On non-hardware platforms, this runs in MOCK mode (prints commands).
    
    IMPORTANT: Only sends commands when angles actually change to prevent servo jitter.
    """

    def __init__(
        self,
        channel_yaw: int = 0,
        channel_pitch: int = 1,
        freq: int = 50,
        min_pulse_us: int = 500,
        max_pulse_us: int = 2500,
        i2c_bus: Optional[int] = None,
        mock_print: bool = True,
    ):
        self.channel_yaw = channel_yaw
        self.channel_pitch = channel_pitch
        self.min_pulse_us = min_pulse_us
        self.max_pulse_us = max_pulse_us
        self.mock_print = mock_print

        self.pca = None
        
        # Track last sent angles to avoid redundant commands
        self._last_yaw: Optional[float] = None
        self._last_pitch: Optional[float] = None
        
        # Threshold for angle change (degrees) - ignore tiny changes
        self._angle_threshold = 0.1

        if not HARDWARE_OK:
            if self.mock_print:
                print("[WARN] PCA9685/I2C hardware not available. Running in MOCK mode.")
                if _hw_import_error:
                    print("       Details:", _hw_import_error)
            return

        try:
            # Prefer explicit bus selection if requested
            if i2c_bus is not None:
                try:
                    from adafruit_extended_bus import ExtendedI2C  # type: ignore

                    i2c = ExtendedI2C(i2c_bus)
                    if self.mock_print:
                        print(f"[INFO] Using ExtendedI2C bus {i2c_bus} (/dev/i2c-{i2c_bus}).")
                except Exception as e:
                    # Fallback: default board pins
                    if self.mock_print:
                        print(
                            f"[WARN] Could not use ExtendedI2C for bus {i2c_bus}. "
                            f"Falling back to busio.I2C(board.SCL, board.SDA). Details: {e}"
                        )
                    i2c = busio.I2C(board.SCL, board.SDA)
            else:
                i2c = busio.I2C(board.SCL, board.SDA)

            self.pca = PCA9685(i2c)
            self.pca.frequency = freq

        except Exception as e:
            # If anything fails, fall back to MOCK mode so the rest of the system can still run.
            self.pca = None
            if self.mock_print:
                print("[WARN] Could not initialize PCA9685. Running in MOCK mode.")
                print("       Details:", e)

    def angle_to_duty(self, angle_deg: float) -> int:
        """Convert degrees (0–180) to PCA9685 duty_cycle (0–65535)."""
        angle_deg = max(0.0, min(180.0, float(angle_deg)))

        # Pulse width in microseconds
        pulse_us = self.min_pulse_us + (angle_deg / 180.0) * (
            self.max_pulse_us - self.min_pulse_us
        )

        # PCA9685 duty calculation: duty = pulse_seconds * freq * 65535
        duty = int((pulse_us / 1_000_000.0) * float(self.pca.frequency) * 65535)
        return max(0, min(65535, duty))

    def set_angles(self, yaw_deg: float, pitch_deg: float, force: bool = False) -> None:
        """Set yaw and pitch angles.
        
        Args:
            yaw_deg: Yaw angle in degrees (0-180)
            pitch_deg: Pitch angle in degrees (0-180)
            force: If True, send command even if angles haven't changed
        """
        # Round to 1 decimal place for comparison
        yaw_deg = round(yaw_deg, 1)
        pitch_deg = round(pitch_deg, 1)
        
        # Check if angles have actually changed
        yaw_changed = (self._last_yaw is None or 
                      abs(yaw_deg - self._last_yaw) >= self._angle_threshold)
        pitch_changed = (self._last_pitch is None or 
                        abs(pitch_deg - self._last_pitch) >= self._angle_threshold)
        
        # Only send command if something changed or force is True
        if not force and not yaw_changed and not pitch_changed:
            return  # No change, don't send command
        
        if self.pca is None:
            if self.mock_print and (yaw_changed or pitch_changed or force):
                print(f"[MOCK] yaw={yaw_deg:.1f}° pitch={pitch_deg:.1f}°")
            self._last_yaw = yaw_deg
            self._last_pitch = pitch_deg
            return

        # Send commands only for changed servos
        if yaw_changed or force:
            yaw_duty = self.angle_to_duty(yaw_deg)
            self.pca.channels[self.channel_yaw].duty_cycle = yaw_duty
            self._last_yaw = yaw_deg
            
        if pitch_changed or force:
            pitch_duty = self.angle_to_duty(pitch_deg)
            self.pca.channels[self.channel_pitch].duty_cycle = pitch_duty
            self._last_pitch = pitch_deg

    def set_angle(self, channel: int, angle_deg: float) -> None:
        """Set a single servo channel angle."""
        if self.pca is None:
            if self.mock_print:
                print(f"[MOCK] ch={channel} angle={angle_deg:.1f}")
            return

        duty = self.angle_to_duty(angle_deg)
        self.pca.channels[channel].duty_cycle = duty

    def deinit(self) -> None:
        """Optional cleanup."""
        try:
            if self.pca is not None:
                self.pca.deinit()
        except Exception:
            pass


def sleep_ms(ms: int) -> None:
    time.sleep(ms / 1000.0)
