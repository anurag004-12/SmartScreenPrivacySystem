# src/core/audio_alert.py

import os
import threading
import logging

try:
    from gtts import gTTS
    from playsound import playsound
    GTTS_AVAILABLE = True
except Exception as e:
    logging.warning("gTTS / playsound not available: %s", e)
    GTTS_AVAILABLE = False


class AudioAlert:
    """
    Simple voice alert wrapper.
    If gTTS/playsound are missing, it will fail silently (no crash).
    """

    def __init__(self, text="Unauthorized person detected. Locking screen for privacy.",
                 lang="en", filepath="assets/alert.mp3"):
        self.text = text
        self.lang = lang
        self.filepath = filepath
        self.playing = False

        if GTTS_AVAILABLE:
            try:
                if not os.path.exists(self.filepath):
                    os.makedirs("assets", exist_ok=True)
                    tts = gTTS(self.text, lang=self.lang)
                    tts.save(self.filepath)
                    logging.info("Generated alert audio at %s", self.filepath)
            except Exception as e:
                logging.warning("Failed to generate TTS audio: %s", e)

    def play_alert(self):
        if not GTTS_AVAILABLE:
            return  # gTTS/playsound not installed, skip

        if self.playing:
            return  # avoid overlapping alerts

        self.playing = True
        threading.Thread(target=self._play, daemon=True).start()

    def _play(self):
        try:
            playsound(self.filepath)
        except Exception as e:
            logging.warning("Failed to play alert sound: %s", e)
        finally:
            self.playing = False
