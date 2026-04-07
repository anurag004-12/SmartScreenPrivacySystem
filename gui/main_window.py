import cv2
import time
from PyQt5 import QtWidgets, QtGui, QtCore
import numpy as np
import logging
import os
from modules.audio_alert import AudioAlert


class VideoLabel(QtWidgets.QLabel):
    def __init__(self):
        super().__init__()
        self.setScaledContents(True)

    def setImage(self, img):
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        h, w = rgb.shape[:2]
        qimg = QtGui.QImage(rgb.data, w, h, 3 * w, QtGui.QImage.Format_RGB888)
        self.setPixmap(QtGui.QPixmap.fromImage(qimg))


class MainWindow(QtWidgets.QWidget):
    def __init__(self, det, recog, live, blur):
        super().__init__()
        self.det = det
        self.recog = recog
        self.live = live
        self.blur = blur

        self.last_intruder_time = 0
        self.is_blurred = False
        self.audio_alert = AudioAlert()

        self.init_ui()
        self.det.start()

        if self.recog.admin_emb is None:
            self._show_enroll_prompt()

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)

    def init_ui(self):
        self.setWindowTitle("Smart Privacy Guardian")

        self.video_label = VideoLabel()
        self.status_label = QtWidgets.QLabel("Starting Camera...")
        self.status_label.setStyleSheet("font-size:16px; font-weight:bold;")

        self.alert_banner = QtWidgets.QLabel("")
        self.alert_banner.setStyleSheet("font-size:20px; font-weight:bold; color:white; background:red; padding:4px;")
        self.alert_banner.setVisible(False)

        self.enroll_btn = QtWidgets.QPushButton("Enroll Admin")
        self.enroll_btn.clicked.connect(self.enroll_admin)

        self.cam_btn = QtWidgets.QPushButton("Stop Camera")
        self.cam_btn.clicked.connect(self.toggle_camera)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.alert_banner)
        layout.addWidget(self.video_label)
        layout.addWidget(self.status_label)
        layout.addWidget(self.enroll_btn)
        layout.addWidget(self.cam_btn)

        self.setLayout(layout)
        self.resize(900, 600)

    def _show_enroll_prompt(self):
        self.alert_banner.setText("⚠ No Admin Enrolled — Click 'Enroll Admin' to get started")
        self.alert_banner.setStyleSheet("font-size:16px; font-weight:bold; color:white; background:#e67e00; padding:6px;")
        self.alert_banner.setVisible(True)

    def toggle_camera(self):
        if self.det.running:
            self.det.stop()
            self.timer.stop()
            self.cam_btn.setText("Start Camera")
            self.status_label.setText("Camera stopped.")
            if self.is_blurred:
                self.blur.hide_overlay()
                self.is_blurred = False
            self.alert_banner.setVisible(False)
        else:
            self.det.start()
            self.timer.start(30)
            self.cam_btn.setText("Stop Camera")
            self.status_label.setText("Camera running.")

    def enroll_admin(self):
        self.det.stop()
        time.sleep(0.4)

        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        cv2.namedWindow("Enroll - press c to capture")
        face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )

        while True:
            ret, frame = cap.read()
            if not ret:
                continue

            preview = frame.copy()
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60))
            for (x, y, w, h) in faces:
                cv2.rectangle(preview, (x, y), (x+w, y+h), (0, 255, 0), 2)
                cv2.putText(preview, "Face detected - press C", (x, y-8),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

            cv2.imshow("Enroll - press c to capture", preview)
            if cv2.waitKey(1) & 0xFF == ord('c'):
                os.makedirs("assets", exist_ok=True)

                if len(faces) > 0:
                    x, y, w, h = faces[0]
                    face_img = frame[y:y+h, x:x+w]
                else:
                    face_img = frame

                cv2.imwrite("assets/admin_face.jpg", face_img)

                emb_path = "models/admin_emb.npy"
                for f in [emb_path, emb_path + ".sha256"]:
                    if os.path.exists(f):
                        os.remove(f)

                self.recog = type(self.recog)(emb_path, "assets/admin_face.jpg", threshold=self.recog.threshold)

                self.alert_banner.setText("Admin Enrolled Successfully")
                self.alert_banner.setStyleSheet("background:green; color:white; font-size:20px;")
                self.alert_banner.setVisible(True)
                break
            elif cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cap.release()
        cv2.destroyAllWindows()
        self.det.start()

    def update_frame(self):
        res = self.det.get()
        if res is None:
            return

        frame, persons, threats, shoulder_surfers = res
        show = frame.copy()
        has_intruder = False

        for (x1, y1, x2, y2, label) in threats:
            cv2.rectangle(show, (x1, y1), (x2, y2), (0, 0, 255), 2)
            cv2.putText(show, f"Threat: {label}", (x1, y1 - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            has_intruder = True

        for (x1, y1, x2, y2) in shoulder_surfers:
            cv2.rectangle(show, (x1, y1), (x2, y2), (0, 165, 255), 2)
            cv2.putText(show, "Unknown Person", (x1, y1 - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 165, 255), 2)
            has_intruder = True

        for (x1, y1, x2, y2) in persons:
            face_crop = frame[y1:y2, x1:x2]
            admin, sim = self.recog.verify(face_crop)
            live = self.live.is_live(face_crop)

            if admin and live:
                cv2.putText(show, f"Admin {sim:.2f}", (x1, y1-5),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            else:
                cv2.putText(show, "Intruder!", (x1, y1-5),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                has_intruder = True

        self.handle_privacy(has_intruder, show)

    def handle_privacy(self, intruder, frame):
        if self.recog.admin_emb is None:
            self._show_enroll_prompt()
            self.video_label.setImage(frame)
            return

        if intruder:
            self.alert_banner.setText("⚠ Threat Detected! Screen Locked ⚠")
            self.alert_banner.setStyleSheet("font-size:20px; font-weight:bold; color:white; background:red; padding:4px;")
            self.alert_banner.setVisible(True)
            if not self.is_blurred:
                self.blur_screen()
                self.audio_alert.play_alert()
                self.is_blurred = True
        else:
            self.alert_banner.setVisible(False)
            if self.is_blurred:
                self.blur.hide_overlay()
                self.is_blurred = False

        self.video_label.setImage(frame)

    def blur_screen(self):
        blurred = self.blur.screenshot_blur()
        self.blur.show_overlay(blurred)

    def closeEvent(self, event):
        self.det.stop()
        event.accept()
