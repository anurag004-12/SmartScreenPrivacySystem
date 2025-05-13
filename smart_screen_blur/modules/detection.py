import cv2
import time
from deepface import DeepFace
from ultralytics import YOLO
import uuid
from utils import log_event, show_blurred_screen
from detection import is_admin_face


class ObjectDetection:
    def __init__(self, canvas):
        self.canvas = canvas
        self.model = YOLO('yolov5su.pt')
        self.model.classes = [0, 67]  # person, phone
        self.admin_image_path = "admin.jpg"
        self.last_admin_seen = time.time()
        self.detection_paused = False
        self.detection_enabled = True

    def start_detection(self):
        self.cap = cv2.VideoCapture(0)
        while True:
            if not self.detection_enabled:
                show_blurred_screen(self.canvas, False, reason="Detection Off")
                time.sleep(1)
                continue

            if self.detection_paused:
                show_blurred_screen(self.canvas, False, reason="Paused Detection")
                time.sleep(1)
                continue

            ret, frame = self.cap.read()
            if not ret:
                continue

            small_frame = cv2.resize(frame, (320, 240))
            results = self.model(small_frame, verbose=False)[0]
            detected_classes = [self.model.names[int(cls)] for cls in results.boxes.cls]

            unknown_person_detected = False
            phone_detected = 'cell phone' in detected_classes

            if 'person' in detected_classes:
                if self.is_admin_face(frame):
                    print("[✔] Admin detected")
                    self.last_admin_seen = time.time()
                    unknown_person_detected = False
                else:
                    unknown_person_detected = True
                    print("[!] Unknown face detected")
            else:
                print("[•] No face detected")

            if phone_detected or unknown_person_detected:
                show_blurred_screen(self.canvas, True, reason="Unknown Face or Phone")
            else:
                if time.time() - self.last_admin_seen < 5:
                    show_blurred_screen(self.canvas, False, reason="Verified Admin")
                else:
                    show_blurred_screen(self.canvas, True, reason="No Admin Recently")

            time.sleep(2)

    def is_admin_face(self, frame):
        try:
            resized_frame = cv2.resize(frame, (640, 480))
            filename = f"temp_{uuid.uuid4().hex}.jpg"
            cv2.imwrite(filename, resized_frame)
            result = DeepFace.verify(
                img1_path=self.admin_image_path,
                img2_path=filename,
                enforce_detection=False,
                model_name="Facenet"
            )
            return result.get("verified", False)
        except Exception as e:
            print(f"[FaceCheck Error] {e}")
            return False

    def toggle_detection(self):
        self.detection_enabled = not self.detection_enabled
        log_event(f"Detection {'Enabled' if self.detection_enabled else 'Disabled'} by Button")
 
