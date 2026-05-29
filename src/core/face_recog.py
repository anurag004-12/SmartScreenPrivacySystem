# src/core/face_recog.py
import hashlib
import logging
import os

import cv2
import numpy as np

from config.settings import ASSETS_DIR, FACE_EMBED_SIZE, MODELS_DIR

EMBED_SIZE = FACE_EMBED_SIZE
BASE_DIR = os.path.abspath(MODELS_DIR)
ASSETS_BASE = os.path.abspath(ASSETS_DIR)
_KEY_FILE = os.path.join(BASE_DIR, "emb.key")


def _is_within(path, base_dir):
    try:
        safe_path = os.path.normcase(os.path.abspath(path))
        safe_base = os.path.normcase(os.path.abspath(base_dir))
        return os.path.commonpath([safe_path, safe_base]) == safe_base
    except ValueError:
        return False


def _get_fernet():
    """Return a Fernet instance, creating a local key on first run."""
    try:
        from cryptography.fernet import Fernet
    except ImportError:
        logging.warning(
            "cryptography package not installed; embedding stored unencrypted."
        )
        return None

    os.makedirs(BASE_DIR, exist_ok=True)
    if not os.path.exists(_KEY_FILE):
        key = Fernet.generate_key()
        with open(_KEY_FILE, "wb") as f:
            f.write(key)
        logging.info("Generated new embedding encryption key at %s", _KEY_FILE)

    with open(_KEY_FILE, "rb") as f:
        return Fernet(f.read())


def compute_embedding(face_bgr):
    try:
        gray = cv2.cvtColor(face_bgr, cv2.COLOR_BGR2GRAY)
        gray = cv2.equalizeHist(gray)
        feat = cv2.resize(gray, (EMBED_SIZE, EMBED_SIZE)).flatten().astype(np.float32)
        norm = np.linalg.norm(feat) + 1e-8
        return feat / norm
    except Exception as e:
        logging.warning("compute_embedding failed: %s", e)
        return None


class FaceRecognizer:
    def __init__(self, emb_path, img_path, threshold=0.80):
        self.emb_path = emb_path
        self.img_path = img_path
        self.threshold = threshold
        self.admin_emb = None

        safe_emb_path = os.path.abspath(emb_path)
        safe_img_path = os.path.abspath(img_path)

        if not _is_within(safe_emb_path, BASE_DIR):
            logging.warning("Blocked unsafe embedding path: %s", emb_path)
            return
        if not _is_within(safe_img_path, ASSETS_BASE):
            logging.warning("Blocked unsafe image path: %s", img_path)
            return

        if os.path.exists(safe_emb_path):
            self.admin_emb = self._load_embedding(safe_emb_path)
        elif os.path.exists(safe_img_path):
            self.admin_emb = self._create_embedding_from_image(
                safe_img_path, safe_emb_path
            )

        if self.admin_emb is None:
            logging.warning("No admin embedding found. All faces will be unknown.")

    def _create_embedding_from_image(self, img_path, emb_path):
        img = cv2.imread(img_path)
        if img is None:
            logging.warning("Failed to read admin image: %s", img_path)
            return None

        emb = compute_embedding(img)
        if emb is None:
            return None

        os.makedirs(os.path.dirname(emb_path), exist_ok=True)
        self._save_embedding(emb, emb_path)
        logging.info("Created admin embedding from %s", img_path)
        return emb

    def _save_embedding(self, emb, path):
        fernet = _get_fernet()
        if fernet:
            with open(path, "wb") as f:
                f.write(fernet.encrypt(emb.tobytes()))
            logging.info("Saved encrypted embedding to %s", path)
        else:
            np.save(path, emb)
            logging.warning("Saved unencrypted embedding.")
        self._save_checksum(emb, path)

    def _load_embedding(self, path):
        fernet = _get_fernet()
        if fernet:
            try:
                with open(path, "rb") as f:
                    data = fernet.decrypt(f.read())
                emb = np.frombuffer(data, dtype=np.float32).copy()
                return self._validate_embedding(emb, path, encrypted=True)
            except Exception as e:
                logging.info("Encrypted embedding load failed, trying legacy npy: %s", e)

        try:
            with open(path, "rb") as f:
                emb = np.load(f, allow_pickle=False).astype(np.float32)
            emb = self._validate_embedding(emb, path, encrypted=False)
            if emb is not None and fernet:
                self._save_embedding(emb, path)
                logging.info("Migrated legacy embedding to encrypted storage.")
            return emb
        except Exception as e:
            logging.warning("Failed to load embedding: %s", e)
            return None

    def _validate_embedding(self, emb, path, encrypted):
        if emb.ndim != 1 or emb.size != EMBED_SIZE * EMBED_SIZE:
            logging.warning("Invalid embedding shape: %s", emb.shape)
            return None
        if not self._verify_checksum(emb, path):
            logging.warning("Embedding integrity check failed; rejecting embedding.")
            return None

        state = "encrypted" if encrypted else "legacy unencrypted"
        logging.info("Loaded %s embedding from %s", state, path)
        return emb

    def _checksum(self, emb):
        return hashlib.sha256(emb.tobytes()).hexdigest()

    def _save_checksum(self, emb, path):
        with open(path + ".sha256", "w", encoding="utf-8") as f:
            f.write(self._checksum(emb))

    def _verify_checksum(self, emb, path):
        chk_path = path + ".sha256"
        if not os.path.exists(chk_path):
            self._save_checksum(emb, path)
            return True
        with open(chk_path, "r", encoding="utf-8") as f:
            stored = f.read().strip()
        return stored == self._checksum(emb)

    def verify(self, face_crop):
        if self.admin_emb is None:
            return False, 0.0
        if face_crop is None or face_crop.size == 0:
            return False, 0.0

        emb = compute_embedding(face_crop)
        if emb is None:
            return False, 0.0
        if emb.shape != self.admin_emb.shape:
            logging.warning("Embedding shape mismatch; please re-enroll admin.")
            return False, 0.0

        score = float(np.dot(emb, self.admin_emb))
        is_admin = score >= self.threshold
        logging.info("verify(): is_admin=%s, score=%.4f", is_admin, score)
        return is_admin, score
