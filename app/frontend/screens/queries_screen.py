import customtkinter as ctk

class QueriesScreen(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent)

        title = ctk.CTkLabel(self, text="Reports & Queries", font=ctk.CTkFont(size=28, weight="bold"))
        title.pack(pady=20)

        label = ctk.CTkLabel(self, text="Run database reports and analytics")
        label.pack(pady=10)