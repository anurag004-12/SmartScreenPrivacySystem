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

        # Smooth update timer instead of thread loop
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

        # Enroll button
        self.enroll_btn = QtWidgets.QPushButton("Enroll Admin")
        self.enroll_btn.clicked.connect(self.enroll_admin)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.alert_banner)
        layout.addWidget(self.video_label)
        layout.addWidget(self.status_label)
        layout.addWidget(self.enroll_btn)

        self.setLayout(layout)
        self.resize(900, 600)

    def enroll_admin(self):
        self.det.stop()
        time.sleep(0.4)

        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        cv2.namedWindow("Enroll - press c to capture")

        while True:
            ret, frame = cap.read()
            if not ret:
                continue
            cv2.imshow("Enroll - press c to capture", frame)
            if cv2.waitKey(1) & 0xFF == ord('c'):
                os.makedirs("assets", exist_ok=True)
                cv2.imwrite("assets/admin_face.jpg", frame)

                # Delete stale embedding so FaceRecognizer recomputes from new image
                emb_path = "models/admin_emb.npy"
                if os.path.exists(emb_path):
                    os.remove(emb_path)

                # generate embedding again, preserve original threshold
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
        
        frame, persons = res

        show = frame.copy()
        has_intruder = False

        for (x1, y1, x2, y2) in persons:
            face_crop = show[y1:y2, x1:x2]
            admin, sim = self.recog.verify(face_crop)
            live = self.live.is_live(face_crop)

            if admin and live:
                cv2.putText(show, f"Admin {sim:.2f}", (x1, y1-5),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2)
            else:
                cv2.putText(show, "Intruder!", (x1, y1-5),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,0,255), 2)
                has_intruder = True

        self.handle_privacy(has_intruder, show)

    def handle_privacy(self, intruder, frame):
        if intruder:
            self.alert_banner.setText("⚠ Intruder Detected! Screen Locked ⚠")
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
