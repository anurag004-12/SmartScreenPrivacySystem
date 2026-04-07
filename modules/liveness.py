# modules/liveness.py
class LivenessDetector:
    """
    Liveness detection disabled — always returns True.
    Motion-based detection was causing false negatives for admin.
    """
    def __init__(self):
        pass

    def is_live(self, face_bgr):
        return True

    def reset(self):
        pass
