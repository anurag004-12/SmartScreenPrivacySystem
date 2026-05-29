import cv2
import time
from PyQt5 import QtWidgets, QtGui, QtCore
import logging
import os

from src.core.audio_alert import AudioAlert
from config.settings import (
    ADMIN_EMB_PATH, ADMIN_IMG_PATH, ASSETS_DIR,
    WINDOW_TITLE, WINDOW_WIDTH, WINDOW_HEIGHT, TIMER_MS, CAM_INDEX
)

# ── Rate limiting ──────────────────────────────────────────────────────────
RECOG_INTERVAL_S  = 0.5   # minimum seconds between recognition calls per face
LOCKOUT_THRESHOLD = 5     # consecutive failures before lockout
LOCKOUT_SECONDS   = 10   # seconds to refuse all recognition after lockout


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
        self.det   = det
        self.recog = recog
        self.live  = live
        self.blur  = blur

        self.is_blurred = False
        self.audio_alert = AudioAlert()

        # Rate limiting state
        self._last_recog_time  = 0.0   # timestamp of last recognition call
        self._fail_streak      = 0     # consecutive non-admin detections
        self._lockout_until    = 0.0   # epoch time when lockout expires

        self.init_ui()
        self.det.start()

        if self.recog.admin_emb is None:
            self._show_enroll_prompt()

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(TIMER_MS)

    def init_ui(self):
        self.setWindowTitle(WINDOW_TITLE)

        self.video_label = VideoLabel()

        self.status_label = QtWidgets.QLabel("Starting Camera...")
        self.status_label.setStyleSheet("font-size:16px; font-weight:bold;")

        self.alert_banner = QtWidgets.QLabel("")
        self.alert_banner.setStyleSheet(
            "font-size:20px; font-weight:bold; color:white; background:red; padding:4px;")
        self.alert_banner.setVisible(False)

        self.counter_label = QtWidgets.QLabel("👥 Intruders: 0  |  📱 Threats: 0")
        self.counter_label.setStyleSheet(
            "font-size:14px; font-weight:bold; color:white; background:#1a6b1a; padding:4px; border-radius:4px;")
        self.counter_label.setAlignment(QtCore.Qt.AlignCenter)

        self.enroll_btn = QtWidgets.QPushButton("Enroll Admin")
        self.enroll_btn.clicked.connect(self.enroll_admin)

        self.cam_btn = QtWidgets.QPushButton("Stop Camera")
        self.cam_btn.clicked.connect(self.toggle_camera)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.alert_banner)
        layout.addWidget(self.video_label)
        layout.addWidget(self.counter_label)
        layout.addWidget(self.status_label)
        layout.addWidget(self.enroll_btn)
        layout.addWidget(self.cam_btn)

        self.setLayout(layout)
        self.resize(WINDOW_WIDTH, WINDOW_HEIGHT)

    def _show_enroll_prompt(self):
        self.alert_banner.setText("⚠ No Admin Enrolled — Click 'Enroll Admin' to get started")
        self.alert_banner.setStyleSheet(
            "font-size:16px; font-weight:bold; color:white; background:#e67e00; padding:6px;")
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
            self.timer.start(TIMER_MS)
            self.cam_btn.setText("Stop Camera")
            self.status_label.setText("Camera running.")

    def enroll_admin(self):
        self.det.stop()
        time.sleep(0.4)

        cap = cv2.VideoCapture(CAM_INDEX, cv2.CAP_DSHOW)
        cv2.namedWindow("Enroll - press c to capture")
        face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )

        while True:
            ret, frame = cap.read()
            if not ret:
                continue

            preview = frame.copy()
            gray  = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(
                gray, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60))
            for (x, y, w, h) in faces:
                cv2.rectangle(preview, (x, y), (x+w, y+h), (0, 255, 0), 2)
                cv2.putText(preview, "Face detected - press C", (x, y-8),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

            cv2.imshow("Enroll - press c to capture", preview)
            if cv2.waitKey(1) & 0xFF == ord('c'):
                os.makedirs(ASSETS_DIR, exist_ok=True)

                if len(faces) > 0:
                    x, y, w, h = faces[0]
                    face_img = frame[y:y+h, x:x+w]
                else:
                    face_img = frame

                cv2.imwrite(ADMIN_IMG_PATH, face_img)

                # Delete stale embedding and checksum
                for f in [ADMIN_EMB_PATH, ADMIN_EMB_PATH + ".sha256"]:
                    if os.path.exists(f):
                        os.remove(f)

                self.recog = type(self.recog)(
                    ADMIN_EMB_PATH, ADMIN_IMG_PATH,
                    threshold=self.recog.threshold
                )

                self.alert_banner.setText("Admin Enrolled Successfully")
                self.alert_banner.setStyleSheet(
                    "background:green; color:white; font-size:20px;")
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
        has_intruder  = False
        intruder_count = 0
        threat_count   = len(threats)

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
            intruder_count += 1

        now = time.time()

        # Lockout check — too many consecutive failures
        if now < self._lockout_until:
            remaining = int(self._lockout_until - now)
            for (x1, y1, x2, y2) in persons:
                cv2.putText(show, f"Locked out ({remaining}s)", (x1, y1-5),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
            has_intruder = True
            intruder_count += len(persons)
        elif now - self._last_recog_time >= RECOG_INTERVAL_S:
            # Rate limit passed — run recognition
            self._last_recog_time = now

            for (x1, y1, x2, y2) in persons:
                face_crop = frame[y1:y2, x1:x2]
                admin, sim = self.recog.verify(face_crop)
                live = self.live.is_live(face_crop)

                if admin and live:
                    cv2.putText(show, f"Admin {sim:.2f}", (x1, y1-5),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                    self._fail_streak = 0   # reset on success
                else:
                    label = "No blink detected" if (admin and not live) else "Intruder!"
                    cv2.putText(show, label, (x1, y1-5),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                    has_intruder = True
                    intruder_count += 1
                    self._fail_streak += 1
                    if self._fail_streak >= LOCKOUT_THRESHOLD:
                        self._lockout_until = now + LOCKOUT_SECONDS
                        self._fail_streak   = 0
                        logging.warning(
                            "Rate limiter: %d consecutive failures — "
                            "locking out recognition for %ds.",
                            LOCKOUT_THRESHOLD, LOCKOUT_SECONDS
                        )
        else:
            # Within rate limit window — reuse last frame's visual state
            for (x1, y1, x2, y2) in persons:
                cv2.putText(show, "Checking...", (x1, y1-5),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 0), 2)

        self.counter_label.setText(
            f"👥 Intruders: {intruder_count}  |  📱 Threats: {threat_count}")
        if intruder_count > 0 or threat_count > 0:
            self.counter_label.setStyleSheet(
                "font-size:14px; font-weight:bold; color:white; "
                "background:#8b0000; padding:4px; border-radius:4px;")
        else:
            self.counter_label.setStyleSheet(
                "font-size:14px; font-weight:bold; color:white; "
                "background:#1a6b1a; padding:4px; border-radius:4px;")
        self.counter_label.repaint()

        self.handle_privacy(has_intruder, show)

    def handle_privacy(self, intruder, frame):
        if self.recog.admin_emb is None:
            self._show_enroll_prompt()
            self.video_label.setImage(frame)
            return

        if intruder:
            self.alert_banner.setText("⚠ Threat Detected! Screen Locked ⚠")
            self.alert_banner.setStyleSheet(
                "font-size:20px; font-weight:bold; color:white; background:red; padding:4px;")
            self.alert_banner.setVisible(True)
            counter_text = self.counter_label.text()
            if not self.is_blurred:
                self.blur_screen(counter_text)
                self.audio_alert.play_alert()
                self.is_blurred = True
            else:
                self.blur.show_overlay(self.blur.screenshot_blur(), counter_text)
        else:
            self.alert_banner.setVisible(False)
            if self.is_blurred:
                self.blur.hide_overlay()
                self.is_blurred = False

        self.video_label.setImage(frame)

    def blur_screen(self, counter_text=""):
        blurred = self.blur.screenshot_blur()
        self.blur.show_overlay(blurred, counter_text)

    def closeEvent(self, event):
        self.det.stop()
        event.accept()

