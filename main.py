"""
Smart Privacy Guardian - Stable Fast Version (Haar Detection)
Python 3.10 Compatible
"""

import sys
from PyQt5 import QtWidgets
import os
import logging

# Import modules
from gui.main_window import MainWindow
from modules.detection import DetectionManager
from modules.face_recog import FaceRecognizer
from modules.liveness import LivenessDetector
from modules.blur import ScreenBlurrer

from collections import namedtuple

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
logging.basicConfig(
    filename=os.path.join(LOG_DIR, "app.log"),
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

AppComponents = namedtuple('AppComponents', ['det', 'recog', 'live', 'blur'])


def build_components():
    det = DetectionManager()

    recog = FaceRecognizer(
        emb_path="models/admin_emb.npy",
        img_path="assets/admin_face.jpg",
        threshold=0.55
    )

    live = LivenessDetector()
    blur = ScreenBlurrer()

    return AppComponents(det=det, recog=recog, live=live, blur=blur)


def main():
    app = QtWidgets.QApplication(sys.argv)

    components = build_components()
    win = MainWindow(components.det, components.recog, components.live, components.blur)
    win.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
