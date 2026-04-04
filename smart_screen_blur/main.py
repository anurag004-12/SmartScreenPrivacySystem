# main.py
from modules.face_capture import FaceCaptureApp
from modules.blur_app import run_blur_app
import sys
from PyQt5.QtWidgets import QApplication
import tkinter as tk

def run_face_capture():
    app = QApplication(sys.argv)
    window = FaceCaptureApp()
    window.resize(680, 500)
    window.show()
    sys.exit(app.exec_())

def main():
    print("Welcome to Smart Screen Blur App")
    print("1. Run Face Capture")
    print("2. Run Smart Blur App")
    choice = input("Enter your choice (1 or 2): ")

    if choice == '1':
        run_face_capture()
    elif choice == '2':
        run_blur_app()
    else:
        print("Invalid choice. Please run again.")

if __name__ == "__main__":
    main()
