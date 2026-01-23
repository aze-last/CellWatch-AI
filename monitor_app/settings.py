import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import monitor_app.utils as utils

class SettingsScreen(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.pack(fill="both", expand=True)
        self.create_widgets()
        
    def create_widgets(self):
        # Container with padding
        container = ttk.Frame(self)
        container.pack(fill="both", expand=True, padx=40, pady=20)
        
        ttk.Label(container, text="System Settings", style="Header.TLabel").pack(anchor="w", pady=(0, 20))
        
        # Settings Groups
        self.create_camera_settings(container)
        self.create_detection_settings(container)
        
        # Save Button
        ttk.Button(container, text="Save Configuration", style="Success.TButton", command=self.save_settings).pack(pady=30, anchor="e")

    def create_camera_settings(self, parent):
        group = ttk.LabelFrame(parent, text="Camera Sources", padding=15)
        group.pack(fill="x", pady=10)
        
        for i in range(1, 5):
            row = ttk.Frame(group)
            row.pack(fill="x", pady=5)
            ttk.Label(row, text=f"Camera {i} URL:", width=15).pack(side="left")
            ttk.Entry(row, width=60).pack(side="left", padx=10)
            ttk.Button(row, text="Test").pack(side="left")

    def create_detection_settings(self, parent):
        group = ttk.LabelFrame(parent, text="Detection Sensitivity", padding=15)
        group.pack(fill="x", pady=10)
        
        # Sliders
        self.create_slider(group, "Motion Threshold", 0.7)
        self.create_slider(group, "Aggression Confidence", 0.85)
        self.create_slider(group, "Contraband Confidence", 0.90)

    def create_slider(self, parent, label, default):
        row = ttk.Frame(parent)
        row.pack(fill="x", pady=5)
        ttk.Label(row, text=label, width=25).pack(side="left")
        scale = ttk.Scale(row, from_=0.0, to=1.0, value=default)
        scale.pack(side="left", fill="x", expand=True, padx=10)
        ttk.Label(row, text=f"{default}", width=5).pack(side="right") # Static for now

    def save_settings(self):
        messagebox.showinfo("Settings", "Configuration saved successfully.")
