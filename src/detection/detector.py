# src/detection/detector.py
import cv2
import threading
import time
import logging
import numpy as np
import urllib.request
import os

from config.settings import (
    ONNX_MODEL_PATH, YOLO_URL, YOLO_INPUT_SIZE,
    YOLO_CONF_THRESHOLD, YOLO_NMS_THRESHOLD,
    YOLO_EVERY_N_FRAMES, THREAT_CLASSES, PERSON_CLASS,
    CAM_INDEX, CAM_WIDTH, CAM_HEIGHT, MODELS_DIR
)

ALLOWED_SCHEMES = ("https://",)


def _load_yolo():
    os.makedirs(MODELS_DIR, exist_ok=True)
    model_path = ONNX_MODEL_PATH
    legacy_model_path = os.path.join(MODELS_DIR, "yolov8n.onnx")

    if not os.path.exists(model_path) and os.path.exists(legacy_model_path):
        logging.warning(
            "Using legacy ONNX model path %s. Rename it to yolov5s.onnx when convenient.",
            legacy_model_path,
        )
        model_path = legacy_model_path

    if not os.path.exists(model_path):
        if not any(YOLO_URL.startswith(s) for s in ALLOWED_SCHEMES):
            raise ValueError(f"Blocked unsafe URL scheme: {YOLO_URL}")
        logging.info("Downloading YOLOv5s ONNX...")
        urllib.request.urlretrieve(YOLO_URL, model_path)
        logging.info("ONNX model downloaded.")
    net = cv2.dnn.readNetFromONNX(model_path)
    net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
    net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)
    return net


try:
    _yolo_net = _load_yolo()
    YOLO_AVAILABLE = True
    logging.info("YOLOv5s loaded successfully.")
except Exception as e:
    logging.warning(f"YOLO not available, phone detection disabled: {e}")
    _yolo_net = None
    YOLO_AVAILABLE = False


def _detect_threats(frame):
    h, w = frame.shape[:2]
    blob = cv2.dnn.blobFromImage(frame, 1 / 255.0,
                                  (YOLO_INPUT_SIZE, YOLO_INPUT_SIZE),
                                  swapRB=True, crop=False)
    _yolo_net.setInput(blob)
    outputs = _yolo_net.forward()[0]

    x_scale = w / YOLO_INPUT_SIZE
    y_scale = h / YOLO_INPUT_SIZE
    boxes, scores, class_ids = [], [], []

    for row in outputs:
        obj_conf = float(row[4])
        if obj_conf < YOLO_CONF_THRESHOLD:
            continue
        class_scores = row[5:]
        cls_id = int(np.argmax(class_scores))
        conf = obj_conf * float(class_scores[cls_id])
        if conf < YOLO_CONF_THRESHOLD:
            continue
        if cls_id not in THREAT_CLASSES and cls_id != PERSON_CLASS:
            continue
        cx, cy, bw, bh = row[:4]
        x1 = int((cx - bw / 2) * x_scale)
        y1 = int((cy - bh / 2) * y_scale)
        boxes.append([x1, y1, int(bw * x_scale), int(bh * y_scale)])
        scores.append(conf)
        class_ids.append(cls_id)

    threats, yolo_persons = [], []
    if boxes:
        indices = cv2.dnn.NMSBoxes(boxes, scores,
                                    YOLO_CONF_THRESHOLD, YOLO_NMS_THRESHOLD)
        for i in np.array(indices).flatten():
            x, y, bw, bh = boxes[i]
            if class_ids[i] == PERSON_CLASS:
                yolo_persons.append((x, y, x + bw, y + bh))
            else:
                threats.append((x, y, x + bw, y + bh,
                                 THREAT_CLASSES[class_ids[i]]))
    return threats, yolo_persons


class DetectionManager:
    def __init__(self, cam_index=CAM_INDEX):
        self.cam_index = cam_index
        self.cap = None
        self.running = False
        self._frame_count = 0

        self.last_frame = None
        self.last_persons = []
        self.last_threats = []
        self.last_yolo_persons = []
        self.last_shoulder_surfers = []
        self.lock = threading.Lock()

        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )
        # CLAHE for contrast normalization — fixes Haar in bright/dark conditions
        self.clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))

    def start(self):
        if self.running:
            return
        self.cap = cv2.VideoCapture(self.cam_index, cv2.CAP_DSHOW)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAM_WIDTH)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAM_HEIGHT)
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

            self._frame_count += 1

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = self.clahe.apply(gray)  # normalize contrast
            frontal = self.face_cascade.detectMultiScale(
                gray, scaleFactor=1.1, minNeighbors=4, minSize=(40, 40)
            )
            persons = [(x, y, x + w, y + h) for (x, y, w, h) in frontal]

            if YOLO_AVAILABLE and self._frame_count % YOLO_EVERY_N_FRAMES == 0:
                try:
                    threats, yolo_persons = _detect_threats(frame)
                except Exception as e:
                    logging.warning(f"YOLO inference error: {e}")
                    threats, yolo_persons = [], []
            else:
                with self.lock:
                    threats = list(self.last_threats)
                    yolo_persons = list(self.last_yolo_persons)

            shoulder_surfers = []
            for (px1, py1, px2, py2) in yolo_persons:
                overlap = any(
                    abs(px1 - hx1) < 80 and abs(py1 - hy1) < 80
                    for (hx1, hy1, hx2, hy2) in persons
                )
                if not overlap:
                    shoulder_surfers.append((px1, py1, px2, py2))

            with self.lock:
                self.last_frame = frame
                self.last_persons = list(persons)
                self.last_threats = threats
                self.last_yolo_persons = list(yolo_persons)
                self.last_shoulder_surfers = shoulder_surfers

            time.sleep(0.033)

    def get(self):
        with self.lock:
            if self.last_frame is None:
                return None
            return (
                self.last_frame.copy(),
                list(self.last_persons),
                list(self.last_threats),
                list(self.last_shoulder_surfers)
            )
