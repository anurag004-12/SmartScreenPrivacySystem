"""
Smart Privacy Guardian
AI-Based Real-Time Screen Privacy Protection System
Author: Anurag Patel — B.Tech CSE (AI & ML)
"""

import sys
import os
import logging
from collections import namedtuple
from PyQt5 import QtWidgets

from config.settings import LOGS_DIR, LOG_FILE, LOG_LEVEL, LOG_FORMAT
from src.detection.detector import DetectionManager
from src.core.face_recog import FaceRecognizer
from src.core.liveness import LivenessDetector
from src.core.blur import ScreenBlurrer
from src.ui.main_window import MainWindow
from config.settings import ADMIN_EMB_PATH, ADMIN_IMG_PATH, FACE_THRESHOLD

# ── Logging setup ──────────────────────────────────────────────────────────
os.makedirs(LOGS_DIR, exist_ok=True)
logging.basicConfig(
    filename=LOG_FILE,
    level=getattr(logging, LOG_LEVEL),
    format=LOG_FORMAT
)

AppComponents = namedtuple('AppComponents', ['det', 'recog', 'live', 'blur'])


def build_components() -> AppComponents:
    det   = DetectionManager()
    recog = FaceRecognizer(
        emb_path=ADMIN_EMB_PATH,
        img_path=ADMIN_IMG_PATH,
        threshold=FACE_THRESHOLD
    )
    live  = LivenessDetector()
    blur  = ScreenBlurrer()
    return AppComponents(det=det, recog=recog, live=live, blur=blur)


def main():
    app = QtWidgets.QApplication(sys.argv)
    components = build_components()
    win = MainWindow(components.det, components.recog, components.live, components.blur)
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
