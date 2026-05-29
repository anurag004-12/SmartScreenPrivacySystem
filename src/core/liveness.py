# src/core/liveness.py
import logging
import os
import time

import cv2
import numpy as np

from config.settings import LIVENESS_FAIL_OPEN, MODELS_DIR

LEFT_EYE = list(range(36, 42))
RIGHT_EYE = list(range(42, 48))

EAR_THRESHOLD = 0.25
BLINK_FRAMES = 2
REQUIRED_BLINKS = 1
WINDOW_SECONDS = 5
COOLDOWN_SECONDS = 10


def _ear(eye_pts):
    a = np.linalg.norm(eye_pts[1] - eye_pts[5])
    b = np.linalg.norm(eye_pts[2] - eye_pts[4])
    c = np.linalg.norm(eye_pts[0] - eye_pts[3])
    return (a + b) / (2.0 * c + 1e-6)


class LivenessDetector:
    """
    Blink-based liveness detection using dlib 68-point landmarks.
    Uses LIVENESS_FAIL_OPEN when dlib or its model is unavailable.
    """

    def __init__(self):
        self._dlib_ok = False
        self._detector = None
        self._predictor = None

        try:
            import dlib

            model_path = os.path.join(MODELS_DIR, "shape_predictor_68_face_landmarks.dat")
            self._detector = dlib.get_frontal_face_detector()
            self._predictor = dlib.shape_predictor(model_path)
            self._dlib_ok = True
            logging.info("LivenessDetector: dlib loaded, blink detection active.")
        except Exception as e:
            logging.warning(
                "LivenessDetector unavailable (%s). Fail-open mode is %s.",
                e,
                LIVENESS_FAIL_OPEN,
            )

        self.reset()

    def reset(self):
        self._closed_frames = 0
        self._blink_count = 0
        self._window_start = time.time()
        self._last_passed_at = None

    def is_live(self, face_bgr):
        if not self._dlib_ok:
            return LIVENESS_FAIL_OPEN

        now = time.time()
        if self._last_passed_at is not None:
            if now - self._last_passed_at < COOLDOWN_SECONDS:
                return True
            self.reset()

        if now - self._window_start > WINDOW_SECONDS:
            self._closed_frames = 0
            self._blink_count = 0
            self._window_start = now

        try:
            gray = cv2.cvtColor(face_bgr, cv2.COLOR_BGR2GRAY)
            rects = self._detector(gray, 0)
            if len(rects) == 0:
                return False

            shape = self._predictor(gray, rects[0])
            pts = np.array(
                [[shape.part(i).x, shape.part(i).y] for i in range(68)],
                dtype=np.float32,
            )

            avg_ear = (_ear(pts[LEFT_EYE]) + _ear(pts[RIGHT_EYE])) / 2.0
            if avg_ear < EAR_THRESHOLD:
                self._closed_frames += 1
            else:
                if self._closed_frames >= BLINK_FRAMES:
                    self._blink_count += 1
                    logging.info("Liveness: blink detected (total=%d)", self._blink_count)
                self._closed_frames = 0

            if self._blink_count >= REQUIRED_BLINKS:
                self._last_passed_at = now
                logging.info("Liveness: passed")
                return True
        except Exception as e:
            logging.warning("Liveness check error: %s", e)

        return False
