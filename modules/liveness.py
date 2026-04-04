# modules/liveness.py
class LivenessDetector:
    """
    Placeholder liveness detector.
    Always returns True to avoid blocking or false negatives.
    Can be replaced later with motion / blink detection.
    """
    def __init__(self):
        pass

    def is_live(self, face_bgr):
        # For now, we treat all real-time faces as 'live'
        return True
