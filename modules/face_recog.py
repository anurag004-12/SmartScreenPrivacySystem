# modules/face_recog.py
import numpy as np
import cv2
import os
import logging

EMBED_SIZE = 32  # 32×32 → 1024-d vector


def compute_embedding(face_bgr):
    """
    Convert face image to grayscale, resize, flatten, and L2-normalize.
    """
    try:
        gray = cv2.cvtColor(face_bgr, cv2.COLOR_BGR2GRAY)
        feat = cv2.resize(gray, (EMBED_SIZE, EMBED_SIZE)).flatten().astype(np.float32)
        norm = np.linalg.norm(feat) + 1e-8
        return feat / norm
    except Exception as e:
        logging.warning(f"compute_embedding failed: {e}")
        return None


class FaceRecognizer:
    """
    Very lightweight "admin vs others" recognizer using cosine similarity
    between a stored admin embedding and current face crop.
    """

    def __init__(self, emb_path, img_path, threshold=0.55):
        self.emb_path = emb_path
        self.img_path = img_path
        self.threshold = threshold
        self.admin_emb = None

        # Try load existing embedding
        if os.path.exists(emb_path):
            try:
                with open(emb_path, 'rb') as f:
                    self.admin_emb = np.load(f).astype(np.float32)
                logging.info(f"Loaded admin embedding from {emb_path}")
            except Exception as e:
                logging.warning(f"Failed to load admin embedding: {e}")

        # Else, compute from admin image if exists
        elif os.path.exists(img_path):
            img = cv2.imread(img_path)
            if img is not None:
                # Detect face in the image and crop it before embedding
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                face_cascade = cv2.CascadeClassifier(
                    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
                )
                faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(40, 40))
                if len(faces) > 0:
                    x, y, w, h = faces[0]
                    img = img[y:y+h, x:x+w]
                emb = compute_embedding(img)
                if emb is not None:
                    os.makedirs(os.path.dirname(emb_path), exist_ok=True)
                    np.save(emb_path, emb)
                    self.admin_emb = emb
                    logging.info(f"Created admin embedding from {img_path}")

        if self.admin_emb is None:
            logging.warning("No admin embedding found. All faces will be 'unknown'.")

    def verify(self, face_crop):
        """
        face_crop: BGR face image.
        Returns: (is_admin: bool, score: float)
        """
        if self.admin_emb is None:
            return False, 0.0

        if face_crop is None or face_crop.size == 0:
            return False, 0.0

        emb = compute_embedding(face_crop)
        if emb is None:
            return False, 0.0

        score = float(np.dot(emb, self.admin_emb))  # cosine similarity
        is_admin = score >= self.threshold
        return is_admin, score
