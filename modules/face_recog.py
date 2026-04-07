# modules/face_recog.py
import numpy as np
import cv2
import os
import logging
import hashlib

EMBED_SIZE = 64
BASE_DIR = os.path.abspath("models")


def compute_embedding(face_bgr):
    try:
        gray = cv2.cvtColor(face_bgr, cv2.COLOR_BGR2GRAY)
        gray = cv2.equalizeHist(gray)
        feat = cv2.resize(gray, (EMBED_SIZE, EMBED_SIZE)).flatten().astype(np.float32)
        norm = np.linalg.norm(feat) + 1e-8
        return feat / norm
    except Exception as e:
        logging.warning(f"compute_embedding failed: {e}")
        return None


class FaceRecognizer:

    def __init__(self, emb_path, img_path, threshold=0.80):
        self.emb_path = emb_path
        self.img_path = img_path
        self.threshold = threshold
        self.admin_emb = None

        safe_emb_path = os.path.abspath(emb_path)
        if not safe_emb_path.startswith(BASE_DIR):
            logging.warning(f"Blocked unsafe embedding path: {emb_path}")
            return

        if os.path.exists(safe_emb_path):
            try:
                with open(safe_emb_path, 'rb') as f:
                    self.admin_emb = np.load(f).astype(np.float32)
                if not os.path.exists(safe_emb_path + ".sha256"):
                    self._save_checksum(self.admin_emb, safe_emb_path)
                logging.info(f"Loaded admin embedding from {safe_emb_path}")
            except Exception as e:
                logging.warning(f"Failed to load admin embedding: {e}")

        elif os.path.exists(img_path):
            img = cv2.imread(img_path)
            if img is not None:
                emb = compute_embedding(img)
                if emb is not None:
                    os.makedirs(os.path.dirname(safe_emb_path), exist_ok=True)
                    np.save(safe_emb_path, emb)
                    self._save_checksum(emb, safe_emb_path)
                    self.admin_emb = emb
                    logging.info(f"Created admin embedding from {img_path}")

        if self.admin_emb is None:
            logging.warning("No admin embedding found. All faces will be 'unknown'.")

    def _checksum(self, emb):
        return hashlib.sha256(emb.tobytes()).hexdigest()

    def _save_checksum(self, emb, path):
        with open(path + ".sha256", "w") as f:
            f.write(self._checksum(emb))

    def _verify_checksum(self, emb, path):
        chk_path = path + ".sha256"
        if not os.path.exists(chk_path):
            return True
        with open(chk_path, "r") as f:
            stored = f.read().strip()
        if stored != self._checksum(emb):
            logging.warning("Embedding integrity check failed — possible tampering.")
            return False
        return True

    def verify(self, face_crop):
        if self.admin_emb is None:
            return False, 0.0

        if face_crop is None or face_crop.size == 0:
            return False, 0.0

        safe_emb_path = os.path.abspath(self.emb_path)
        if not self._verify_checksum(self.admin_emb, safe_emb_path):
            return False, 0.0

        emb = compute_embedding(face_crop)
        if emb is None:
            return False, 0.0

        if emb.shape != self.admin_emb.shape:
            logging.warning("Embedding shape mismatch — please re-enroll admin.")
            return False, 0.0

        score = float(np.dot(emb, self.admin_emb))
        is_admin = score >= self.threshold
        logging.info(f"verify(): is_admin={is_admin}, score={score:.4f}")
        return is_admin, score
