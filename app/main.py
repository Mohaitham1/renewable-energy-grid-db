import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import customtkinter as ctk
from frontend.main_window import MainWindow

# ctk.set_appearance_mode("light")
# ctk.set_default_color_theme("blue")

if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")
    
    app = MainWindow()
    app.mainloop()