import tkinter as tk
from tkinter import messagebox
from detection import ObjectDetection
from utils import log_event, show_blurred_screen

class BlurApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Smart Screen Blur - Debug Mode")
        self.root.geometry("800x600")
        self.root.configure(bg='black')

        # UI elements
        self.top_frame = tk.Frame(root, bg='black')
        self.top_frame.pack(fill='x', side='top')

        # Canvas for blurring
        self.canvas = tk.Label(root, bg='black')
        self.canvas.place(relx=0, rely=0, relwidth=1, relheight=1)

        # UI underneath blur layer
        self.content_frame = tk.Frame(root, bg='black')
        self.content_frame.place(relx=0.5, rely=0.5, anchor='center')

        self.login_label = tk.Label(self.content_frame, text="🔐 Secure Login", font=("Helvetica", 18), fg="white", bg="black")
        self.login_label.pack(pady=(0, 20))

        self.entry_user = tk.Entry(self.content_frame, font=("Helvetica", 14), width=30, fg="white", bg="#333", insertbackground="white", relief="flat")
        self.entry_user.insert(0, "Username")
        self.entry_user.pack(pady=5)

        self.entry_pass = tk.Entry(self.content_frame, font=("Helvetica", 14), width=30, fg="white", bg="#333", insertbackground="white", relief="flat", show="*")
        self.entry_pass.insert(0, "password")
        self.entry_pass.pack(pady=5)

        self.login_button = tk.Button(self.content_frame, text="Login", font=("Helvetica", 14), bg="#555", fg="white", relief="flat")
        self.login_button.pack(pady=15)

        # Start detection
        self.detection = ObjectDetection(self.canvas)
        self.detection.start_detection()

        # Start toggling detection
        self.toggle_btn = tk.Button(self.top_frame, text="Turn Detection OFF", command=self.toggle_detection, bg="gray", fg="white")
        self.toggle_btn.pack(side="left", padx=10, pady=5)

    def toggle_detection(self):
        self.detection.toggle_detection()
        self.toggle_btn.config(text=f"{'Turn Detection ON' if not self.detection.detection_enabled else 'Turn Detection OFF'}")
        log_event(f"Detection {'Enabled' if self.detection.detection_enabled else 'Disabled'} by Button")
    
def run_blur_app():
    root = tk.Tk()
    app = BlurApp(root)
    root.mainloop()
