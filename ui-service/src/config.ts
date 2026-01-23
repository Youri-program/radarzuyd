// src/config.ts - FIXED VERSION

/* =========================
   Jetson / Local Backend
   ========================= */

export const JETSON_BASE_URL = "http://127.0.0.1:8080";
export const JETSON_OFFER_URL = `${JETSON_BASE_URL}/offer`;
export const JETSON_STOP_TRACKING_URL = `${JETSON_BASE_URL}/stop_tracking`;
export const JETSON_MARK_THREAT_URL = `${JETSON_BASE_URL}/mark_threat`;

/* =========================
   AWS Cloud Backend
   ========================= */

// CORRECT AWS BASE URL (was jpamaqgotb, now djpawwqotb)
const AWS_BASE = "https://djpawwqotb.execute-api.eu-central-1.amazonaws.com/prod";

// Jetson ID
export const JETSON_ID = "jetson_nano_01";

// Direct endpoints - NO CORS PROXY (backend has CORS enabled now)
export const AWS_LOGIN_URL = `${AWS_BASE}/login`;
export const AWS_DETECTIONS_URL = `${AWS_BASE}/detections`;
export const AWS_IMAGE_GET_URL = `${AWS_BASE}/images/get`;
export const AWS_UPLOAD_URL = `${AWS_BASE}/upload`;

/* =========================
   Test Credentials
   ========================= */

export const TEST_USERNAME = "testuser";
export const TEST_PASSWORD = "TestPass123!";