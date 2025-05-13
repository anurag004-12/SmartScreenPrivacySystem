import sys
import cv2
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QMessageBox
)
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import QTimer


class FaceCaptureApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Face Capture - Admin Registration")
        self.setStyleSheet("background-color: #121212; color: white; font-size: 16px;")

        self.image_label = QLabel()
        self.image_label.setStyleSheet("border: 2px solid #333;")
        self.capture_button = QPushButton("📸 Capture")
        self.save_button = QPushButton("💾 Save as Admin")
        self.cancel_button = QPushButton("❌ Cancel")
        self.toggle_camera_button = QPushButton("🔴 Stop Camera")

        self.save_button.setEnabled(False)
        self.cancel_button.setEnabled(False)

        # Layout setup
        vbox = QVBoxLayout()
        vbox.addWidget(self.image_label)
        hbox = QHBoxLayout()
        hbox.addWidget(self.capture_button)
        hbox.addWidget(self.save_button)
        hbox.addWidget(self.cancel_button)
        hbox.addWidget(self.toggle_camera_button)
        vbox.addLayout(hbox)
        self.setLayout(vbox)

        self.cap = None
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.captured_frame = None
        self.camera_active = False

        # Button events
        self.capture_button.clicked.connect(self.capture_image)
        self.save_button.clicked.connect(self.save_image)
        self.cancel_button.clicked.connect(self.cancel_capture)
        self.toggle_camera_button.clicked.connect(self.toggle_camera)

        # Start with camera on
        self.start_camera()

    def start_camera(self):
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            QMessageBox.critical(self, "Error", "Cannot access camera.")
            return
        self.timer.start(30)
        self.camera_active = True
        self.toggle_camera_button.setText("🔴 Stop Camera")

    def stop_camera(self):
        if self.cap:
            self.timer.stop()
            self.cap.release()
            self.cap = None
        self.camera_active = False
        self.toggle_camera_button.setText("🟢 Start Camera")
        self.image_label.clear()

    def toggle_camera(self):
        if self.camera_active:
            self.stop_camera()
        else:
            self.start_camera()

    def update_frame(self):
        ret, frame = self.cap.read()
        if ret:
            self.current_frame = frame
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb.shape
            bytes_per_line = ch * w
            qt_img = QImage(rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
            self.image_label.setPixmap(QPixmap.fromImage(qt_img))

    def capture_image(self):
        self.captured_frame = self.current_frame.copy()
        self.timer.stop()
        rgb = cv2.cvtColor(self.captured_frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        qt_img = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
        self.image_label.setPixmap(QPixmap.fromImage(qt_img))
        self.save_button.setEnabled(True)
        self.cancel_button.setEnabled(True)

    def save_image(self):
        cv2.imwrite("admin.jpg", self.captured_frame)
        QMessageBox.information(self, "Saved", "Admin face saved as admin.jpg")
        self.save_button.setEnabled(False)
        self.cancel_button.setEnabled(False)
        self.timer.start(30)

    def cancel_capture(self):
        self.save_button.setEnabled(False)
        self.cancel_button.setEnabled(False)
        self.timer.start(30)

    def closeEvent(self, event):
        self.stop_camera()


def run_face_capture():
    app = QApplication(sys.argv)
    window = FaceCaptureApp()
    window.resize(680, 500)
    window.show()
    sys.exit(app.exec_())


