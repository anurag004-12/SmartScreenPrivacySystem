import logging
import os
import time

import cv2
from PyQt5 import QtCore, QtGui, QtWidgets

from src.core.audio_alert import AudioAlert
from config.settings import (
    ADMIN_EMB_PATH,
    ADMIN_IMG_PATH,
    ASSETS_DIR,
    CAM_INDEX,
    TIMER_MS,
    WINDOW_HEIGHT,
    WINDOW_TITLE,
    WINDOW_WIDTH,
)

RECOG_INTERVAL_S = 0.5
LOCKOUT_THRESHOLD = 5
LOCKOUT_SECONDS = 10


class VideoLabel(QtWidgets.QLabel):
    def __init__(self):
        super().__init__()
        self.setAlignment(QtCore.Qt.AlignCenter)
        self.setMinimumSize(460, 270)
        self.setStyleSheet(
            "background:#111827; border:1px solid #263244; border-radius:8px;"
            "color:#9ca3af;"
        )
        self.setText("Camera feed")

    def setImage(self, img):
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        h, w = rgb.shape[:2]
        qimg = QtGui.QImage(rgb.data, w, h, 3 * w, QtGui.QImage.Format_RGB888)
        pixmap = QtGui.QPixmap.fromImage(qimg)
        self.setPixmap(
            pixmap.scaled(
                self.size(),
                QtCore.Qt.KeepAspectRatio,
                QtCore.Qt.SmoothTransformation,
            )
        )


class MainWindow(QtWidgets.QWidget):
    def __init__(self, det, recog, live, blur):
        super().__init__()
        self.det = det
        self.recog = recog
        self.live = live
        self.blur = blur

        self.audio_alert = AudioAlert()
        self._alert_played = False
        self._last_recog_time = 0.0
        self._fail_streak = 0
        self._lockout_until = 0.0
        self._dashboard_started = False
        self._ui_restricted = False

        self.init_ui()

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_frame)

    def init_ui(self):
        self.setWindowTitle(WINDOW_TITLE)
        self.resize(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.setMinimumSize(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.setStyleSheet(
            """
            QWidget {
                background:#f7f8fa;
                color:#172033;
                font-family: Segoe UI, Arial, sans-serif;
                font-size:14px;
            }
            QPushButton {
                background:#2563eb;
                color:white;
                border:none;
                border-radius:6px;
                padding:9px 14px;
                font-weight:600;
            }
            QPushButton:hover { background:#1d4ed8; }
            QPushButton:disabled { background:#cbd5e1; color:#64748b; }
            QLabel#TitleLabel {
                color:#0f172a;
                font-size:34px;
                font-weight:700;
            }
            QLabel#PanelLabel {
                color:#64748b;
                font-size:12px;
                font-weight:600;
                text-transform:uppercase;
            }
            """
        )

        self.stack = QtWidgets.QStackedWidget()
        self.stack.addWidget(self._build_welcome_screen())
        self.stack.addWidget(self._build_dashboard())

        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(self.stack)

    def _build_welcome_screen(self):
        page = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(page)
        layout.setContentsMargins(56, 48, 56, 48)
        layout.setSpacing(22)
        layout.addStretch(1)

        title = QtWidgets.QLabel("Smart Privacy Guardian")
        title.setObjectName("TitleLabel")
        title.setAlignment(QtCore.Qt.AlignCenter)

        subtitle = QtWidgets.QLabel("Privacy monitoring dashboard")
        subtitle.setAlignment(QtCore.Qt.AlignCenter)
        subtitle.setStyleSheet("color:#64748b; font-size:16px;")

        get_started = QtWidgets.QPushButton("Get Started")
        get_started.setFixedWidth(160)
        get_started.clicked.connect(self.start_dashboard)

        button_row = QtWidgets.QHBoxLayout()
        button_row.addStretch(1)
        button_row.addWidget(get_started)
        button_row.addStretch(1)

        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addLayout(button_row)
        layout.addStretch(1)
        return page

    def _build_dashboard(self):
        page = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(page)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        header = QtWidgets.QHBoxLayout()
        title = QtWidgets.QLabel("Smart Privacy Guardian")
        title.setStyleSheet("font-size:22px; font-weight:700; color:#0f172a;")

        self.status_badge = QtWidgets.QLabel("System Active")
        self.status_badge.setAlignment(QtCore.Qt.AlignCenter)
        self.status_badge.setFixedHeight(34)
        self.status_badge.setMinimumWidth(150)

        header.addWidget(title)
        header.addStretch(1)
        header.addWidget(self.status_badge)

        content = QtWidgets.QHBoxLayout()
        content.setSpacing(16)

        self.video_label = VideoLabel()
        content.addWidget(self.video_label, 3)

        side_panel = QtWidgets.QFrame()
        side_panel.setStyleSheet(
            "QFrame { background:white; border:1px solid #e2e8f0; border-radius:8px; }"
        )
        side_layout = QtWidgets.QVBoxLayout(side_panel)
        side_layout.setContentsMargins(16, 16, 16, 16)
        side_layout.setSpacing(12)

        status_caption = QtWidgets.QLabel("Status")
        status_caption.setObjectName("PanelLabel")
        self.status_label = QtWidgets.QLabel("System Active")
        self.status_label.setStyleSheet("font-size:20px; font-weight:700;")
        self.detail_label = QtWidgets.QLabel("Camera is ready.")
        self.detail_label.setWordWrap(True)
        self.detail_label.setStyleSheet("color:#64748b;")

        self.counter_label = QtWidgets.QLabel("Intruders: 0\nThreats: 0")
        self.counter_label.setStyleSheet(
            "background:#f1f5f9; border-radius:6px; padding:12px;"
            "font-size:15px; font-weight:600;"
        )

        self.controls_container = QtWidgets.QWidget()
        controls = QtWidgets.QVBoxLayout(self.controls_container)
        controls.setContentsMargins(0, 0, 0, 0)
        controls.setSpacing(10)

        self.enroll_btn = QtWidgets.QPushButton("Enroll Admin")
        self.enroll_btn.clicked.connect(self.enroll_admin)
        self.cam_btn = QtWidgets.QPushButton("Stop Camera")
        self.cam_btn.clicked.connect(self.toggle_camera)
        controls.addWidget(self.enroll_btn)
        controls.addWidget(self.cam_btn)

        side_layout.addWidget(status_caption)
        side_layout.addWidget(self.status_label)
        side_layout.addWidget(self.detail_label)
        side_layout.addWidget(self.counter_label)
        side_layout.addStretch(1)
        side_layout.addWidget(self.controls_container)

        content.addWidget(side_panel, 1)
        layout.addLayout(header)
        layout.addLayout(content, 1)

        self._set_status(active=True, intruder=False)
        return page

    def start_dashboard(self):
        self.stack.setCurrentIndex(1)
        if not self._dashboard_started:
            self.det.start()
            self.timer.start(TIMER_MS)
            self._dashboard_started = True
        if self.recog.admin_emb is None:
            self._show_enroll_prompt()

    def _show_enroll_prompt(self):
        self._set_status(
            active=True,
            intruder=False,
            detail="No admin enrolled. Enroll an admin face to begin protection.",
        )

    def _set_status(self, active, intruder, detail=None):
        if intruder:
            text = "Intruder Detected"
            badge_style = "background:#dc2626; color:white; border-radius:17px; font-weight:700;"
            label_color = "#b91c1c"
        elif active:
            text = "System Active"
            badge_style = "background:#16a34a; color:white; border-radius:17px; font-weight:700;"
            label_color = "#15803d"
        else:
            text = "System Paused"
            badge_style = "background:#64748b; color:white; border-radius:17px; font-weight:700;"
            label_color = "#475569"

        self.status_badge.setText(text)
        self.status_badge.setStyleSheet(badge_style)
        self.status_label.setText(text)
        self.status_label.setStyleSheet(f"font-size:20px; font-weight:700; color:{label_color};")
        if detail is not None:
            self.detail_label.setText(detail)

    def _restrict_app_ui(self, restricted):
        if self._ui_restricted == restricted:
            return

        self._ui_restricted = restricted
        self.controls_container.setDisabled(restricted)
        if restricted:
            self.detail_label.setText(
                "App controls are temporarily disabled until the scene is clear."
            )
        else:
            self.detail_label.setText("System Active")

    def toggle_camera(self):
        if self.det.running:
            self.det.stop()
            self.timer.stop()
            self.cam_btn.setText("Start Camera")
            self._set_status(active=False, intruder=False, detail="Camera stopped.")
            self._restrict_app_ui(False)
        else:
            self.det.start()
            self.timer.start(TIMER_MS)
            self.cam_btn.setText("Stop Camera")
            self._set_status(active=True, intruder=False, detail="System Active")

    def enroll_admin(self):
        if self.det.running:
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
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(
                gray, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60)
            )
            for (x, y, w, h) in faces:
                cv2.rectangle(preview, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.putText(
                    preview,
                    "Face detected - press C",
                    (x, y - 8),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 255, 0),
                    2,
                )

            cv2.imshow("Enroll - press c to capture", preview)
            key = cv2.waitKey(1) & 0xFF
            if key == ord("c"):
                os.makedirs(ASSETS_DIR, exist_ok=True)

                if len(faces) > 0:
                    x, y, w, h = faces[0]
                    face_img = frame[y : y + h, x : x + w]
                else:
                    face_img = frame

                cv2.imwrite(ADMIN_IMG_PATH, face_img)

                for path in [ADMIN_EMB_PATH, ADMIN_EMB_PATH + ".sha256"]:
                    if os.path.exists(path):
                        os.remove(path)

                self.recog = type(self.recog)(
                    ADMIN_EMB_PATH,
                    ADMIN_IMG_PATH,
                    threshold=self.recog.threshold,
                )
                self._set_status(
                    active=True,
                    intruder=False,
                    detail="Admin enrolled successfully.",
                )
                break
            if key == ord("q"):
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
        intruder_count = 0
        threat_count = len(threats)

        for (x1, y1, x2, y2, label) in threats:
            cv2.rectangle(show, (x1, y1), (x2, y2), (0, 0, 255), 2)
            cv2.putText(
                show,
                f"Threat: {label}",
                (x1, y1 - 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 0, 255),
                2,
            )
            has_intruder = True

        for (x1, y1, x2, y2) in shoulder_surfers:
            cv2.rectangle(show, (x1, y1), (x2, y2), (0, 165, 255), 2)
            cv2.putText(
                show,
                "Unknown Person",
                (x1, y1 - 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 165, 255),
                2,
            )
            has_intruder = True
            intruder_count += 1

        now = time.time()
        if now < self._lockout_until:
            remaining = int(self._lockout_until - now)
            for (x1, y1, x2, y2) in persons:
                cv2.putText(
                    show,
                    f"App restricted ({remaining}s)",
                    (x1, y1 - 5),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 0, 255),
                    2,
                )
            has_intruder = True
            intruder_count += len(persons)
        elif now - self._last_recog_time >= RECOG_INTERVAL_S:
            self._last_recog_time = now

            for (x1, y1, x2, y2) in persons:
                face_crop = frame[y1:y2, x1:x2]
                admin, sim = self.recog.verify(face_crop)
                live = self.live.is_live(face_crop)

                if admin and live:
                    cv2.putText(
                        show,
                        f"Admin {sim:.2f}",
                        (x1, y1 - 5),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        (0, 255, 0),
                        2,
                    )
                    self._fail_streak = 0
                else:
                    label = "No blink detected" if (admin and not live) else "Intruder"
                    cv2.putText(
                        show,
                        label,
                        (x1, y1 - 5),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (0, 0, 255),
                        2,
                    )
                    has_intruder = True
                    intruder_count += 1
                    self._fail_streak += 1
                    if self._fail_streak >= LOCKOUT_THRESHOLD:
                        self._lockout_until = now + LOCKOUT_SECONDS
                        self._fail_streak = 0
                        logging.warning(
                            "Rate limiter: %d consecutive failures; restricting app UI for %ds.",
                            LOCKOUT_THRESHOLD,
                            LOCKOUT_SECONDS,
                        )
        else:
            for (x1, y1, x2, y2) in persons:
                cv2.putText(
                    show,
                    "Checking...",
                    (x1, y1 - 5),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (200, 200, 0),
                    2,
                )

        self.counter_label.setText(f"Intruders: {intruder_count}\nThreats: {threat_count}")
        self.handle_privacy(has_intruder, show)

    def handle_privacy(self, intruder, frame):
        if self.recog.admin_emb is None:
            self._show_enroll_prompt()
            self.video_label.setImage(frame)
            return

        if intruder:
            self._set_status(active=True, intruder=True)
            self._restrict_app_ui(True)
            if not self._alert_played:
                self.audio_alert.play_alert()
                self._alert_played = True
        else:
            self._set_status(active=True, intruder=False, detail="System Active")
            self._restrict_app_ui(False)
            self._alert_played = False

        self.video_label.setImage(frame)

    def closeEvent(self, event):
        if self.det.running:
            self.det.stop()
        self.blur.hide_overlay()
        event.accept()
