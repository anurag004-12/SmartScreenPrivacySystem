# modules/blur.py
import cv2
import numpy as np
import pyautogui
from PyQt5 import QtWidgets, QtGui, QtCore


class ScreenBlurrer:
    def __init__(self):
        self.overlay = None
        self.label = None

    def screenshot_blur(self, kernel=(51, 51)):
        img = pyautogui.screenshot()
        bgr = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        # ensure odd kernel
        kx = kernel[0] if kernel[0] % 2 == 1 else kernel[0] + 1
        ky = kernel[1] if kernel[1] % 2 == 1 else kernel[1] + 1
        blurred = cv2.GaussianBlur(bgr, (kx, ky), 0)
        return blurred

    def show_overlay(self, blurred_bgr):
        h, w = blurred_bgr.shape[:2]
        rgb = cv2.cvtColor(blurred_bgr, cv2.COLOR_BGR2RGB)
        qimg = QtGui.QImage(rgb.data, w, h, 3 * w, QtGui.QImage.Format_RGB888)
        pix = QtGui.QPixmap.fromImage(qimg)

        if self.overlay is None:
            self.overlay = QtWidgets.QWidget()
            self.overlay.setWindowFlags(
                QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint
            )
            self.overlay.setAttribute(QtCore.Qt.WA_TranslucentBackground)

        if self.label is None:
            self.label = QtWidgets.QLabel(self.overlay)

        self.label.setPixmap(pix)
        self.label.resize(w, h)
        self.overlay.showFullScreen()

    def hide_overlay(self):
        if self.overlay:
            self.overlay.hide()
        self.overlay = None
        self.label = None
