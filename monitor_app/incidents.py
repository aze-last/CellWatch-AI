import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk
import sqlite3
import json
import os
import cv2
import time
from PIL import Image, ImageTk
from datetime import datetime
import monitor_app.utils as utils

def ensure_incidents_schema(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS incidents (
            event_id TEXT PRIMARY KEY,
            camera_id TEXT,
            timestamp_start TEXT,
            timestamp_end TEXT,
            event_type TEXT,
            confidence_scores TEXT,
            video_path TEXT,
            comments TEXT,
            reviewed_by TEXT,
            reviewed_at TEXT,
            retention_days INTEGER,
            review_status TEXT DEFAULT 'PENDING'
        )
    ''')

    cursor.execute("PRAGMA table_info(incidents)")
    existing = {row[1] for row in cursor.fetchall()}
    columns = [
        ("timestamp_end", "TEXT", None),
        ("event_type", "TEXT", None),
        ("confidence_scores", "TEXT", None),
        ("video_path", "TEXT", None),
        ("comments", "TEXT", None),
        ("reviewed_by", "TEXT", None),
        ("reviewed_at", "TEXT", None),
        ("retention_days", "INTEGER", None),
        ("review_status", "TEXT", "'PENDING'"),
    ]
    for name, col_type, default in columns:
        if name in existing:
            continue
        default_clause = f" DEFAULT {default}" if default is not None else ""
        cursor.execute(f"ALTER TABLE incidents ADD COLUMN {name} {col_type}{default_clause}")

    conn.commit()
    conn.close()

class IncidentsScreen(ttk.Frame):
    def __init__(self, parent, current_user="Unknown"):
        super().__init__(parent)
        self.pack(fill="both", expand=True)
        self.db_path = "incidents.db"
        self.current_user = current_user

        # 🚀 SELF-HEALING DATABASE (Fixes 'no such column' errors)
        try:
            ensure_incidents_schema(self.db_path)
            print("Database audit columns verified.")
        except Exception as e:
            print(f"Migration Warning: {e}")

        # CustomTkinter tabs
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.tabview = ctk.CTkTabview(self)
        self.tabview.grid(row=0, column=0, sticky="nsew", padx=20, pady=(10, 20))

        self.tab_handling = self.tabview.add("Incident Handling & Validation")
        self.tab_history = self.tabview.add("Incident History Log")

        # Create components
        self.review_tab = IncidentReviewDetail(
            self.tab_handling, 
            self.db_path, 
            self.on_incident_updated,
            self.current_user
        )
        self.review_tab.pack(fill="both", expand=True)

        self.log_tab = IncidentLogTable(self.tab_history, self.db_path, self.on_log_selected)
        self.log_tab.pack(fill="both", expand=True)

    def on_log_selected(self, event_data):
        """Called when a user clicks a row in the history log."""
        self.tabview.set("Incident Handling & Validation")
        self.review_tab.load_incident(event_data)

    def on_incident_updated(self):
        """Called when an incident is confirmed/ignored to refresh the table."""
        self.log_tab.refresh_data()

class IncidentReviewDetail(ttk.Frame):
    def __init__(self, parent, db_path, on_update_callback, current_user):
        super().__init__(parent)
        self.db_path = db_path
        self.on_update_callback = on_update_callback
        self.current_user = current_user
        self.current_incident = None
        
        # Video Playback State
        self.video_cap = None
        self.is_playing = False
        self._playback_job = None
        
        self.create_widgets()
        self._check_playback_stop()

    def stop_monitoring(self):
        """Cleanup thread when leaving screen."""
        self.stop_playback()
        
    def create_widgets(self):
        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(0, weight=1)

        # ================== LEFT PANEL (VIDEO) ==================
        self.left_panel = ctk.CTkFrame(self, fg_color="transparent")
        self.left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 15), pady=10)

        ctk.CTkLabel(
            self.left_panel, text="Evidence Playback", font=("Roboto", 18, "bold")
        ).pack(anchor="w", pady=(0, 10))

        # Video player container (The "Black Space")
        self.video_player_container = ctk.CTkFrame(self.left_panel, fg_color="black", corner_radius=0)
        self.video_player_container.pack(fill="both", expand=True)
        
        self.video_label = ctk.CTkLabel(
            self.video_player_container, text="Select an incident from History Log", 
            text_color="gray", compound="center"
        )
        self.video_label.pack(fill="both", expand=True)

        # Playback controls
        self.controls_frame = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        self.controls_frame.pack(pady=15)

        btn_font = ("Roboto", 12, "bold")
        ctk.CTkButton(self.controls_frame, text="<< 10s", width=90, height=35, font=btn_font).pack(side="left", padx=5)
        self.btn_play = ctk.CTkButton(self.controls_frame, text="Play / Pause", width=110, height=35, font=btn_font, command=self.open_video)
        self.btn_play.pack(side="left", padx=5)
        ctk.CTkButton(self.controls_frame, text="10s >>", width=90, height=35, font=btn_font).pack(side="left", padx=5)

        # ================== RIGHT PANEL (DETAILS) ==================
        self.right_panel = ctk.CTkFrame(self, fg_color="#2b2b2b")
        self.right_panel.grid(row=0, column=1, sticky="nsew", pady=10)

        details_container = ctk.CTkFrame(self.right_panel, fg_color="transparent")
        details_container.pack(fill="x", padx=25, pady=25)

        ctk.CTkLabel(details_container, text="Incident Details", font=("Roboto", 18, "bold")).pack(anchor="w", pady=(0, 15))

        self.vars = {
            "id": tk.StringVar(value="-"),
            "cam": tk.StringVar(value="-"),
            "time": tk.StringVar(value="-"),
            "type": tk.StringVar(value="-"),
            "status": tk.StringVar(value="PENDING")
        }

        def add_detail_row(parent, label, var, color="white"):
            row = ctk.CTkFrame(parent, fg_color="transparent")
            row.pack(fill="x", pady=4)
            ctk.CTkLabel(row, text=label, font=("Roboto", 12, "bold"), width=110, anchor="w", text_color="#aaaaaa").pack(side="left")
            ctk.CTkLabel(row, textvariable=var, font=("Roboto", 12), anchor="w", text_color=color).pack(side="left")

        add_detail_row(details_container, "Incident ID:", self.vars["id"])
        add_detail_row(details_container, "Camera:", self.vars["cam"])
        add_detail_row(details_container, "Timestamp:", self.vars["time"])
        add_detail_row(details_container, "Status:", self.vars["status"])
        add_detail_row(details_container, "Detected:", self.vars["type"], color="#d9534f")

        ctk.CTkFrame(self.right_panel, height=2, fg_color="#404040").pack(fill="x", padx=25, pady=5)

        validation_container = ctk.CTkFrame(self.right_panel, fg_color="transparent")
        validation_container.pack(fill="both", expand=True, padx=25, pady=25)

        ctk.CTkLabel(validation_container, text="Operator Validation", font=("Roboto", 18, "bold")).pack(anchor="w", pady=(0, 10))
        self.comment_box = ctk.CTkTextbox(validation_container, height=100, font=("Roboto", 12))
        self.comment_box.pack(fill="x", pady=(5, 20))

        btn_style = {"height": 40, "font": ("Roboto", 13, "bold")}
        ctk.CTkButton(validation_container, text="CONFIRM INCIDENT", fg_color="#d9534f", hover_color="#c9302c", 
                      command=lambda: self.update_status("CONFIRMED"), **btn_style).pack(fill="x", pady=5)
        ctk.CTkButton(validation_container, text="FALSE ALARM / IGNORE", fg_color="#5cb85c", hover_color="#4cae4c", 
                      command=lambda: self.update_status("FALSE ALARM"), **btn_style).pack(fill="x", pady=5)
        ctk.CTkButton(validation_container, text="MARK FOR REVIEW", fg_color="#0275d8", hover_color="#025aa5", 
                      command=lambda: self.update_status("NEEDS REVIEW"), **btn_style).pack(fill="x", pady=5)

    def load_incident(self, data):
        self.current_incident = data
        self.vars["id"].set(data.get("event_id", "-"))
        self.vars["cam"].set(f"Cam {data.get('camera_id', '-')}")
        
        # Format timestamp
        ts = data.get("timestamp_start", "")
        if ts:
            try:
                dt = datetime.fromisoformat(ts)
                ts = dt.strftime("%Y-%m-%d %H:%M:%S")
            except: pass
        self.vars["time"].set(ts)
        self.vars["type"].set(data.get("event_type", "Unknown"))
        
        self.comment_box.delete("1.0", tk.END)
        self.comment_box.insert("1.0", data.get("comments") or "")
        
        video_path = data.get("video_path", "")
        if video_path and os.path.exists(video_path):
            self.video_label.configure(text=f"Video Loaded:\n{os.path.basename(video_path)}\nClick 'Play' to watch in-app", image="")
        else:
            self.video_label.configure(text="Video file not found", image="")
        
        self.stop_playback() # Reset player handle

    def open_video(self):
        """Toggles in-app video playback."""
        if self.is_playing:
            self.stop_playback()
            return

        if self.current_incident and self.current_incident.get("video_path"):
            path = os.path.abspath(self.current_incident["video_path"])
            if os.path.exists(path):
                self.start_playback(path)
            else:
                messagebox.showerror("Error", "Video file no longer exists.")

    def start_playback(self, path):
        self.stop_playback()
        self.video_cap = cv2.VideoCapture(path)
        if not self.video_cap.isOpened():
            messagebox.showerror("Error", "Fail to open video file codec.")
            return
        
        self.is_playing = True
        self.btn_play.configure(text="Stop Player", fg_color="#d9534f")
        self._play_next_frame()

    def stop_playback(self):
        self.is_playing = False
        if self._playback_job:
            self.after_cancel(self._playback_job)
            self._playback_job = None
        if self.video_cap:
            self.video_cap.release()
            self.video_cap = None
        self.btn_play.configure(text="Play / Pause", fg_color=["#3B8ED0", "#1F6AA5"])
        self.video_label.configure(image="")

    def _play_next_frame(self):
        if not self.is_playing or not self.video_cap:
            return

        ret, frame = self.video_cap.read()
        if not ret:
            self.stop_playback()
            return

        # Convert OpenCV (BGR) to RGB for UI
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Dynamically resize to fit the UI container
        w = self.video_label.winfo_width()
        h = self.video_label.winfo_height()
        if w > 10 and h > 10:
            frame = cv2.resize(frame, (w, h))
            target_w, target_h = w, h
        else:
            target_h, target_w = frame.shape[:2]

        # Convert to CTk compatible image
        img = Image.fromarray(frame)
        ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(target_w, target_h))
        self._update_video_frame(ctk_img)

        # Maintain approx 15-20 FPS playback
        self._playback_job = self.after(45, self._play_next_frame)

    def _update_video_frame(self, img):
        # Keep a reference to avoid Tk image garbage collection.
        self._current_frame_img = img
        self.video_label.configure(image=img, text="")

    def _check_playback_stop(self):
        # Cleanup routine
        if not self.is_playing and self.btn_play.cget("text") == "Stop Player":
            self.stop_playback()
        self.after(1000, self._check_playback_stop)

    def update_status(self, status):
        """
        STRICT VALIDATION RULES:
        1. Only update if an incident is selected.
        2. Prevent downgrading 'CONFIRMED' incidents (ABSOLUTE RULE).
        3. Save 'reviewed_by' (Operator Name) and 'reviewed_at' (Timestamp).
        """
        if not self.current_incident:
            messagebox.showwarning("Warning", "Please select an incident first.")
            return

        current_status = self.current_incident.get("review_status", "PENDING")
        if current_status == "CONFIRMED":
            messagebox.showwarning("Security Audit", "Confirmed incidents are locked for evidence integrity.")
            return
        
        comments = self.comment_box.get("1.0", tk.END).strip()
        review_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Academic Retention Policy mapping
        retention_map = {"CONFIRMED": 90, "FALSE ALARM": 7, "NEEDS REVIEW": 15}
        retention = retention_map.get(status, 15)

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE incidents 
                SET review_status=?, comments=?, reviewed_by=?, reviewed_at=?, retention_days=?
                WHERE event_id=?
            ''', (status, comments, self.current_user, review_time, retention, self.current_incident["event_id"]))
            conn.commit()
            conn.close()
            
            self.vars["status"].set(status)
            messagebox.showinfo("Audit Saved", f"Decision: {status}\nOperator: {self.current_user}\nTime: {review_time}")
            
            if self.on_update_callback:
                self.on_update_callback()
        except Exception as e:
            messagebox.showerror("Database Error", str(e))

class IncidentLogTable(ttk.Frame):
    def __init__(self, parent, db_path, on_select_callback):
        super().__init__(parent)
        self.db_path = db_path
        self.on_select_callback = on_select_callback
        self.create_widgets()
        self.refresh_data()
        
    def create_widgets(self):
        toolbar = ttk.Frame(self)
        toolbar.pack(fill="x", pady=5)
        
        ttk.Button(toolbar, text="🔄 Refresh Log", command=self.refresh_data).pack(side="left", padx=5)
        ttk.Button(toolbar, text="📂 Open Records Folder", command=lambda: os.startfile("recordings")).pack(side="left", padx=5)
        
        columns = ("id", "time", "cam", "type", "status")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=15)
        
        self.tree.heading("id", text="Event ID")
        self.tree.heading("time", text="Timestamp")
        self.tree.heading("cam", text="Cam")
        self.tree.heading("type", text="Incident Type")
        self.tree.heading("status", text="Validation Status")
        
        for col in columns: self.tree.column(col, width=150, anchor="center")
        
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.on_row_click)
        
    def refresh_data(self):
        # Clear existing
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        if not os.path.exists(self.db_path):
            return

        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM incidents ORDER BY timestamp_start DESC")
            self.rows = cursor.fetchall()
            
            for row in self.rows:
                ts = row["timestamp_start"]
                try:
                    dt = datetime.fromisoformat(ts)
                    ts = dt.strftime("%H:%M:%S")
                except: pass
                
                self.tree.insert("", tk.END, iid=row["event_id"], values=(
                    row["event_id"],
                    ts,
                    f"Cam {row['camera_id']}",
                    row["event_type"],
                    row["review_status"]
                ))
            conn.close()
        except Exception as e:
            print(f"Table Refresh Error: {e}")

    def on_row_click(self, event):
        selected = self.tree.selection()
        if not selected: return
        event_id = selected[0]
        
        # Find raw data from self.rows
        for row in self.rows:
            if row["event_id"] == event_id:
                if self.on_select_callback:
                    self.on_select_callback(dict(row))
                break
