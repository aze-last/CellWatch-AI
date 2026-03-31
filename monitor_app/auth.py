from tkinter import messagebox

import customtkinter as ctk
import os

# Configuration
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class LoginScreen(ctk.CTkFrame):
    def __init__(self, parent, on_login_success):
        # Initialize as a transparent frame filling the parent
        super().__init__(parent, fg_color="transparent")
        self.on_login_success = on_login_success
        self.pack(fill="both", expand=True)
        
        self.create_widgets()


    def create_widgets(self):
        # --- THE LOGIN CARD (Frame) ---
        self.login_frame = ctk.CTkFrame(self, corner_radius=15) 
        self.login_frame.place(relx=0.5, rely=0.5, anchor="center")

        # Title inside the card
        self.label_title = ctk.CTkLabel(
            self.login_frame, 
            text="CellWatch AI", 
            font=("Roboto Medium", 32, "bold")
        )
        self.label_title.grid(row=0, column=0, padx=40, pady=(30, 5))

        # Subtitle
        self.label_subtitle = ctk.CTkLabel(
            self.login_frame, 
            text="Institutional Monitoring System", 
            font=("Roboto", 14), 
            text_color="gray"
        )
        self.label_subtitle.grid(row=1, column=0, padx=10, pady=(0, 25))

        # Username Entry
        self.entry_user = ctk.CTkEntry(
            self.login_frame, 
            width=250, 
            height=40,
            placeholder_text="Username"
        )
        self.entry_user.grid(row=2, column=0, padx=40, pady=(10, 10))
        self.entry_user.bind("<Return>", self._on_enter_key)

        # Password Entry
        self.entry_pass = ctk.CTkEntry(
            self.login_frame, 
            width=250, 
            height=40,
            show="*", 
            placeholder_text="Password"
        )
        self.entry_pass.grid(row=3, column=0, padx=40, pady=(0, 25))
        self.entry_pass.bind("<Return>", self._on_enter_key)

        # Login Button
        self.btn_login = ctk.CTkButton(
            self.login_frame, 
            text="Login", 
            width=250, 
            height=40,
            font=("Roboto", 14, "bold"),
            command=self.login_event
        )
        self.btn_login.grid(row=4, column=0, padx=40, pady=(0, 30))
        self.entry_user.focus_set()

    def _on_enter_key(self, _event):
        self.login_event()

    def login_event(self):
        u = self.entry_user.get()
        p = self.entry_pass.get()
        
        print(f"Login attempt: {u}")
        
        # Authentication Logic
        if u == "admin" and p == "admin":
             self.on_login_success()
        else:
             messagebox.showerror("Error", "Invalid Credentials")
