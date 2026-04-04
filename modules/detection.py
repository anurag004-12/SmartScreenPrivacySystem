# modules/detection.py
import cv2
import threading
import time


class DetectionManager:
    """
    Lightweight detection manager using Haar cascade for faces.
    Runs in a background thread and stores the latest frame + detections.
    GUI pulls frames via get().
    """

    def __init__(self, cam_index=0):
        self.cam_index = cam_index
        self.cap = None
        self.running = False

        self.last_frame = None
        self.last_persons = []
        self.lock = threading.Lock()

        # Haar face detector
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )

    def start(self):
        if self.running:
            return

        self.cap = cv2.VideoCapture(self.cam_index, cv2.CAP_DSHOW)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 360)

        self.running = True
        threading.Thread(target=self._loop, daemon=True).start()

    def stop(self):
        self.running = False
        if self.cap is not None:
            self.cap.release()
            self.cap = None

    def _loop(self):
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                time.sleep(0.01)
                continue

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(
                gray, scaleFactor=1.1, minNeighbors=5, minSize=(40, 40)
            )

            persons = []
            for (x, y, w, h) in faces:
                persons.append((x, y, x + w, y + h))

            with self.lock:
                self.last_frame = frame
                self.last_persons = persons

            # Small sleep to avoid 100% CPU
            time.sleep(0.01)

    def get(self):
        """
        Returns (frame, persons) or None if nothing yet.
        persons = list of (x1, y1, x2, y2)
        """
        with self.lock:
            if self.last_frame is None:
                return None
            # return copies to avoid race
            frame_copy = self.last_frame.copy()
            persons_copy = list(self.last_persons)
        return frame_copy, persons_copy
