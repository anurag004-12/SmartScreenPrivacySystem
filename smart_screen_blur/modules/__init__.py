import sys
from tkinter import Tk
from .blurr_app import BlurrApp

def start_app():
    root = Tk()
    app = BlurrApp(root)
    root.mainloop()

if __name__ == "__main__":
    start_app()
 
