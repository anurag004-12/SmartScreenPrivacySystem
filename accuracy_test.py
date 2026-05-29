"""
accuracy_test.py
Measures face recognition accuracy of Smart Privacy Guardian.
Run: python accuracy_test.py
"""

import cv2
import numpy as np
import sys
import os

sys.path.insert(0, os.path.abspath("."))

from src.core.face_recog import FaceRecognizer, compute_embedding
from config.settings import ADMIN_EMB_PATH, ADMIN_IMG_PATH, FACE_THRESHOLD

# ── Config ─────────────────────────────────────────────────────────────────
ADMIN_SAMPLES    = 20   # frames to capture as admin (true positives)
INTRUDER_SAMPLES = 20   # frames to capture as non-admin (true negatives)


def capture_samples(label, count):
    """Capture face crop samples from webcam."""
    print(f"\n[{label}] Position your face and press SPACE to start capturing {count} samples...")
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )
    samples = []

    while True:
        ret, frame = cap.read()
        if not ret:
            continue
        gray  = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(60, 60))
        preview = frame.copy()
        for (x, y, w, h) in faces:
            cv2.rectangle(preview, (x, y), (x+w, y+h), (0, 255, 0), 2)
        cv2.putText(preview, f"Press SPACE to capture | {label}",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        cv2.imshow("Accuracy Test", preview)
        key = cv2.waitKey(1) & 0xFF
        if key == ord(' ') and len(faces) > 0:
            break
        elif key == ord('q'):
            cap.release()
            cv2.destroyAllWindows()
            sys.exit(0)

    print(f"  Capturing {count} samples for [{label}]...")
    while len(samples) < count:
        ret, frame = cap.read()
        if not ret:
            continue
        gray  = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(60, 60))
        preview = frame.copy()
        if len(faces) > 0:
            x, y, w, h = faces[0]
            face_crop = frame[y:y+h, x:x+w]
            samples.append(face_crop)
            cv2.rectangle(preview, (x, y), (x+w, y+h), (0, 255, 0), 2)
            cv2.putText(preview, f"Captured: {len(samples)}/{count}",
                        (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.imshow("Accuracy Test", preview)
        cv2.waitKey(1)

    cap.release()
    cv2.destroyAllWindows()
    print(f"  Done — {len(samples)} samples captured.")
    return samples


def run_accuracy_test():
    print("=" * 55)
    print("   Smart Privacy Guardian — Accuracy Test")
    print("=" * 55)

    # Load recognizer
    recog = FaceRecognizer(ADMIN_EMB_PATH, ADMIN_IMG_PATH, threshold=FACE_THRESHOLD)
    if recog.admin_emb is None:
        print("\n[ERROR] No admin enrolled. Run app.py and enroll admin first.")
        sys.exit(1)

    print(f"\nThreshold : {recog.threshold}")
    print(f"Embed size: {recog.admin_emb.shape}")

    # ── Admin samples (True Positives) ─────────────────────────────────────
    admin_samples = capture_samples("ADMIN (your face)", ADMIN_SAMPLES)
    tp, fn = 0, 0
    admin_scores = []
    for crop in admin_samples:
        is_admin, score = recog.verify(crop)
        admin_scores.append(score)
        if is_admin:
            tp += 1
        else:
            fn += 1

    # ── Intruder samples (True Negatives) ──────────────────────────────────
    print("\n[INFO] Now ask someone else (or use a photo) for intruder samples.")
    intruder_samples = capture_samples("INTRUDER (different face/photo)", INTRUDER_SAMPLES)
    tn, fp = 0, 0
    intruder_scores = []
    for crop in intruder_samples:
        is_admin, score = recog.verify(crop)
        intruder_scores.append(score)
        if not is_admin:
            tn += 1
        else:
            fp += 1

    # ── Results ────────────────────────────────────────────────────────────
    total     = tp + fn + tn + fp
    accuracy  = (tp + tn) / total * 100
    precision = tp / (tp + fp) * 100 if (tp + fp) > 0 else 0
    recall    = tp / (tp + fn) * 100 if (tp + fn) > 0 else 0
    f1        = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
    far       = fp / (fp + tn) * 100 if (fp + tn) > 0 else 0  # False Accept Rate
    frr       = fn / (fn + tp) * 100 if (fn + tp) > 0 else 0  # False Reject Rate

    print("\n" + "=" * 55)
    print("   RESULTS")
    print("=" * 55)
    print(f"  Admin scores   — avg: {np.mean(admin_scores):.4f}  min: {np.min(admin_scores):.4f}  max: {np.max(admin_scores):.4f}")
    print(f"  Intruder scores— avg: {np.mean(intruder_scores):.4f}  min: {np.min(intruder_scores):.4f}  max: {np.max(intruder_scores):.4f}")
    print(f"\n  True Positives  (admin correctly recognized) : {tp}/{ADMIN_SAMPLES}")
    print(f"  False Negatives (admin wrongly rejected)     : {fn}/{ADMIN_SAMPLES}")
    print(f"  True Negatives  (intruder correctly blocked) : {tn}/{INTRUDER_SAMPLES}")
    print(f"  False Positives (intruder wrongly accepted)  : {fp}/{INTRUDER_SAMPLES}")
    print(f"\n  Accuracy  : {accuracy:.1f}%")
    print(f"  Precision : {precision:.1f}%")
    print(f"  Recall    : {recall:.1f}%")
    print(f"  F1 Score  : {f1:.1f}%")
    print(f"  FAR (False Accept Rate) : {far:.1f}%")
    print(f"  FRR (False Reject Rate) : {frr:.1f}%")
    print("=" * 55)

    # ── Suggestion ─────────────────────────────────────────────────────────
    if accuracy >= 90:
        print("  ✅ Excellent accuracy!")
    elif accuracy >= 75:
        print("  ⚠️  Good — consider re-enrolling in better lighting.")
    else:
        print("  ❌ Low accuracy — re-enroll admin in good lighting.")

    if far > 10:
        print("  ⚠️  High FAR — lower threshold in config/settings.py")
    if frr > 10:
        print("  ⚠️  High FRR — raise threshold in config/settings.py")


if __name__ == "__main__":
    run_accuracy_test()
