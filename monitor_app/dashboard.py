import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
import psutil
import sqlite3
import os
import monitor_app.utils as utils


class DashboardScreen(ttk.Frame):
    """
    Dashboard screen that mimics the provided CustomTkinter design
    while fitting inside the existing CellWatchApp container.
    """

    def __init__(self, parent):
        super().__init__(parent)
        self.pack(fill="both", expand=True)

        # Layout for this screen
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Main scrollable content (like the example DashboardApp.main_view)
        self.main_view = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.main_view.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        self.main_view.grid_columnconfigure((0, 1, 2, 3), weight=1)

        # Keep references to dynamic health labels
        self.lbl_cpu = None
        self.lbl_mem = None
        self.lbl_disk = None
        self.lbl_net = None
        
        # Keep references to stat card labels
        self.stat_labels = {}

        self.create_dashboard_content()
        self.update_system_health()
        self.update_dashboard_metrics()

    # ---- Adapted from your CustomTkinter DashboardApp ----
    def create_dashboard_content(self):
        # Section Title
        label_dashboard = ctk.CTkLabel(
            self.main_view,
            text="System Dashboard",
            font=("Roboto", 20, "bold"),
            anchor="w",
        )
        label_dashboard.grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 20))

        # Metric cards row
        self.stat_labels["Active Cameras"] = self.create_stat_card(0, "Active Cameras", "0", "#3b8ed0")
        self.stat_labels["Total Detections"] = self.create_stat_card(1, "Total Detections", "0", "#e5c07b")
        self.stat_labels["Active Alerts"] = self.create_stat_card(2, "Active Alerts", "0", "#c63939")
        self.stat_labels["System Status"] = self.create_stat_card(3, "System Status", "OFFLINE", "#2cc985")

        # System Health Title
        label_health = ctk.CTkLabel(
            self.main_view,
            text="System Health",
            font=("Roboto", 18, "bold"),
            anchor="w",
        )
        label_health.grid(row=2, column=0, columnspan=4, sticky="w", pady=(30, 10))

        # Health list panel
        self.health_frame = ctk.CTkFrame(self.main_view, fg_color="#2b2b2b")
        self.health_frame.grid(row=3, column=0, columnspan=4, sticky="ew")
        self.health_frame.grid_columnconfigure(1, weight=1)

        # Static labels + value labels we can update later
        # Row 0: CPU
        ctk.CTkLabel(self.health_frame, text="CPU Usage", font=("Roboto", 14)).grid(
            row=0, column=0, sticky="w", padx=20, pady=10
        )
        self.lbl_cpu = ctk.CTkLabel(
            self.health_frame,
            text="0%",
            font=("Roboto", 14, "bold"),
            text_color="#3b8ed0",
        )
        self.lbl_cpu.grid(row=0, column=1, sticky="e", padx=20, pady=10)

        # Separator
        sep0 = ctk.CTkFrame(self.health_frame, height=1, fg_color="#404040")
        sep0.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(35, 0))

        # Row 1: Memory
        ctk.CTkLabel(self.health_frame, text="Memory Usage", font=("Roboto", 14)).grid(
            row=1, column=0, sticky="w", padx=20, pady=10
        )
        self.lbl_mem = ctk.CTkLabel(
            self.health_frame,
            text="0%",
            font=("Roboto", 14, "bold"),
            text_color="#3b8ed0",
        )
        self.lbl_mem.grid(row=1, column=1, sticky="e", padx=20, pady=10)

        sep1 = ctk.CTkFrame(self.health_frame, height=1, fg_color="#404040")
        sep1.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(35, 0))

        # Row 2: Storage
        ctk.CTkLabel(self.health_frame, text="Storage", font=("Roboto", 14)).grid(
            row=2, column=0, sticky="w", padx=20, pady=10
        )
        self.lbl_disk = ctk.CTkLabel(
            self.health_frame,
            text="0 GB Free",
            font=("Roboto", 14, "bold"),
            text_color="#3b8ed0",
        )
        self.lbl_disk.grid(row=2, column=1, sticky="e", padx=20, pady=10)

        sep2 = ctk.CTkFrame(self.health_frame, height=1, fg_color="#404040")
        sep2.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(35, 0))

        # Row 3: Network
        ctk.CTkLabel(self.health_frame, text="Network Latency", font=("Roboto", 14)).grid(
            row=3, column=0, sticky="w", padx=20, pady=10
        )
        self.lbl_net = ctk.CTkLabel(
            self.health_frame,
            text="N/A",
            font=("Roboto", 14, "bold"),
            text_color="#3b8ed0",
        )
        self.lbl_net.grid(row=3, column=1, sticky="e", padx=20, pady=10)

    def create_stat_card(self, col_idx, title, value, accent_color):
        # Card container
        card = ctk.CTkFrame(self.main_view, fg_color="#2b2b2b")
        card.grid(row=1, column=col_idx, sticky="ew", padx=10)

        # Colored top border
        border = ctk.CTkFrame(card, height=6, fg_color=accent_color, corner_radius=0)
        border.pack(fill="x", side="top")

        # Content
        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=15, pady=15)

        ctk.CTkLabel(
            content,
            text=title,
            font=("Roboto", 12),
            text_color="gray",
            anchor="w",
        ).pack(fill="x")

        lbl_value = ctk.CTkLabel(
            content,
            text=value,
            font=("Roboto", 28, "bold"),
            text_color=accent_color,
            anchor="w",
        )
        lbl_value.pack(fill="x", pady=(5, 0))
        return lbl_value

    # ---- Real-time system metrics ----
    def update_system_health(self):
        try:
            cpu = psutil.cpu_percent(interval=None)
            mem = psutil.virtual_memory().percent
            disk = psutil.disk_usage("/").free  # bytes
            disk_gb = disk / (1024**3)

            if self.lbl_cpu is not None:
                self.lbl_cpu.configure(text=f"{cpu:.0f}%")
            if self.lbl_mem is not None:
                self.lbl_mem.configure(text=f"{mem:.0f}%")
            if self.lbl_disk is not None:
                self.lbl_disk.configure(text=f"{disk_gb:.1f} GB Free")

            # Simple latency check – may be None if host not reachable
            latency_ms = self._measure_latency_ms()
            if self.lbl_net is not None:
                if latency_ms is None:
                    self.lbl_net.configure(text="N/A")
                else:
                    self.lbl_net.configure(text=f"{latency_ms:.0f} ms")
        except Exception:
            # Fail quietly so the UI keeps running
            pass

        # Schedule next update
        self.after(2000, self.update_system_health)

    def update_dashboard_metrics(self):
        """Fetches metrics from GlobalState and incident database."""
        try:
            # 1. Get metrics from GlobalState
            metrics = utils.GlobalState.get_metrics()
            
            # 2. Get total detections from SQLite
            total_db = 0
            db_path = "incidents.db"
            if os.path.exists(db_path):
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM incidents")
                total_db = cursor.fetchone()[0]
                conn.close()
                utils.GlobalState.last_total_detections = total_db

            # 3. Update Labels
            if "Active Cameras" in self.stat_labels:
                self.stat_labels["Active Cameras"].configure(text=str(metrics["active_cams"]))
            
            if "Total Detections" in self.stat_labels:
                self.stat_labels["Total Detections"].configure(text=f"{total_db:,}")
            
            if "Active Alerts" in self.stat_labels:
                self.stat_labels["Active Alerts"].configure(text=str(metrics["active_alerts"]))
            
            if "System Status" in self.stat_labels:
                status = "ONLINE" if metrics["active_cams"] > 0 else "IDLE"
                self.stat_labels["System Status"].configure(text=status)

        except Exception as e:
            # print(f"Dashboard Metric Error: {e}")
            pass

        # Schedule next update (every 1 second)
        self.after(1000, self.update_dashboard_metrics)

    def _measure_latency_ms(self):
        """Very lightweight latency estimate to a public DNS server."""
        import socket
        import time

        host = "8.8.8.8"
        port = 53
        timeout = 0.5

        start = time.time()
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(timeout)
            sock.sendto(b"", (host, port))
            sock.recvfrom(512)
            end = time.time()
            return (end - start) * 1000.0
        except Exception:
            return None
        finally:
            try:
                sock.close()
            except Exception:
                pass
