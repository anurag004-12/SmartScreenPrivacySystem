import pyautogui # type: ignore
from PIL import Image, ImageTk
import logging
from utils import log_event

# Logging setup
LOG_FILE = "blur_events.log"
logging.basicConfig(filename=LOG_FILE,
                    level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(message)s")

def log_event(event, source="System"):
    msg = f"{event} | Triggered by: {source}"
    print(msg)
    logging.info(msg)

def show_blurred_screen(canvas, state, reason="System"):
    if state:
        screenshot = pyautogui.screenshot()
        blurred = screenshot.filter(ImageFilter.GaussianBlur(radius=8))
        img_tk = ImageTk.PhotoImage(blurred)
        canvas.config(image=img_tk)
        canvas.image = img_tk
        canvas.lift()  # Put blur above everything
        log_event("🔒 Screen Blurred", reason)
    else:
        canvas.config(image=None)
        canvas.image = None
        canvas.lower()  # Put canvas below to show form
        log_event("🔓 Screen Unblurred", reason)
 
