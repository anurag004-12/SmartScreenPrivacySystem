# config/settings.py
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(BASE_DIR, "models")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
LOGS_DIR = os.path.join(BASE_DIR, "logs")

ADMIN_EMB_PATH = os.path.join(MODELS_DIR, "admin_emb.npy")
ADMIN_IMG_PATH = os.path.join(ASSETS_DIR, "admin_face.jpg")
ALERT_AUDIO = os.path.join(ASSETS_DIR, "alert.mp3")
ONNX_MODEL_PATH = os.path.join(MODELS_DIR, "yolov5s.onnx")
LOG_FILE = os.path.join(LOGS_DIR, "app.log")

# Face recognition
FACE_EMBED_SIZE = 64
FACE_THRESHOLD = 0.80
FACE_MIN_SIZE = (60, 60)
FACE_SCALE_FACTOR = 1.1
FACE_MIN_NEIGHBORS = 5

# YOLO detection
YOLO_INPUT_SIZE = 640
YOLO_CONF_THRESHOLD = 0.20
YOLO_NMS_THRESHOLD = 0.40
YOLO_EVERY_N_FRAMES = 15
YOLO_URL = (
    "https://github.com/doleron/yolov5-opencv-cpp-python/raw/main/"
    "config_files/yolov5s.onnx"
)

THREAT_CLASSES = {
    67: "cell phone",
    63: "laptop",
    62: "tv",
    65: "remote",
    73: "book",
}
PERSON_CLASS = 0

# Camera
CAM_INDEX = 0
CAM_WIDTH = 480
CAM_HEIGHT = 270
CAM_FPS = 30

# UI
WINDOW_TITLE = "Smart Privacy Guardian"
WINDOW_WIDTH = 900
WINDOW_HEIGHT = 600
TIMER_MS = 30

# Liveness
# True keeps the app usable when dlib or its landmark model is unavailable.
LIVENESS_FAIL_OPEN = True

# Logging
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(message)s"
