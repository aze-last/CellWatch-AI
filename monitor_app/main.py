import tkinter as tk
from tkinter import ttk
import sys
import os

# Add project root to path to ensure imports work correctly
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# --- OPTIONAL FIX FOR CUSTOM TKINTER INSTALLATIONS ---
try:
    # We look for Tcl/Tk relative to the executable OR in common Laragon paths
    base_python = os.path.dirname(sys.executable)
    
    # 1. Try to find TCL
    tcl_path = None
    possible_tcl = [
        os.path.join(base_python, "tcl", "tcl8.6"),
        os.path.join(base_python, "Lib", "tcl8.6"),
        "C:\\laragon\\bin\\python\\python-3.13\\tcl\\tcl8.6" # Hardcoded fallback for user
    ]
    for p in possible_tcl:
        if os.path.exists(os.path.join(p, "init.tcl")):
            tcl_path = p
            break
            
    # 2. Try to find TK
    tk_path = None
    possible_tk = [
        os.path.join(base_python, "tcl", "tk8.6"),
        os.path.join(base_python, "Lib", "tk8.6"),
        "C:\\laragon\\bin\\python\\python-3.13\\tcl\\tk8.6" # Hardcoded fallback for user
    ]
    for p in possible_tk:
        if os.path.exists(os.path.join(p, "tk.tcl")):
            tk_path = p
            break

    if tcl_path:
        os.environ["TCL_LIBRARY"] = tcl_path
        print(f"Applied TCL_LIBRARY: {tcl_path}")
    if tk_path:
        os.environ["TK_LIBRARY"] = tk_path
        print(f"Applied TK_LIBRARY: {tk_path}")

except Exception as e:
    print(f"Warning: Could not auto-fix Tkinter paths: {e}")
# ------------------------------------------------------

from monitor_app import utils, auth, camera_view, incidents, dashboard, settings, reports, alerts

class CellWatchApp(tk.Tk):
    def __init__(self):
        super().__init__()
        
        self.title(utils.APP_TITLE)
        self.geometry(utils.WINDOW_SIZE)
        self.configure(bg=utils.COLOR_BG_DARK)
        
        # Apply theme
        self.style = utils.apply_dark_theme(self)
        
        # Placeholder for current user
        self.current_user = None
        
        # Main container for all screens
        self.container = ttk.Frame(self)
        self.container.pack(fill="both", expand=True)
        
        # Navigation bar (initially hidden, shown after login)
        self.nav_bar = None
        
        # Initialize
        self.show_login()

    def show_login(self):
        # Clear container
        for widget in self.container.winfo_children():
            widget.destroy()
            
        if self.nav_bar:
            self.nav_bar.destroy()
            self.nav_bar = None
            
        login_screen = auth.LoginScreen(self.container, on_login_success=self.on_login_success)
        login_screen.pack(fill="both", expand=True)

    def on_login_success(self):
        self.current_user = "admin" # Mock
        self.create_navigation()
        self.show_dashboard_placeholder() # Temporarily show a placeholder until dashboard is built

    def create_navigation(self):
        # Create a top navigation bar
        self.nav_bar = ttk.Frame(self, style="Card.TFrame")
        self.nav_bar.pack(side="top", fill="x", before=self.container) # Pack before container
        
        # Logo / Title
        from PIL import Image, ImageTk
        try:
            logo_path = os.path.join(os.path.dirname(__file__), "assets", "logo.png")
            logo_img = Image.open(logo_path).resize((40, 40), Image.Resampling.LANCZOS)
            self.logo_photo = ImageTk.PhotoImage(logo_img)
            lbl_logo = ttk.Label(self.nav_bar, image=self.logo_photo, background=utils.COLOR_BG_LIGHT)
            lbl_logo.pack(side="left", padx=(10, 5), pady=10)
        except Exception as e:
            print(f"Could not load nav logo: {e}")

        lbl_title = ttk.Label(self.nav_bar, text=" CELLWATCH AI", style="Header.TLabel", background=utils.COLOR_BG_LIGHT)
        lbl_title.pack(side="left", padx=(0, 10), pady=10)
        
        # Navigation Buttons (Placeholder commands for now)
        buttons = [
            ("Dashboard", self.show_dashboard_placeholder),
            ("Live Monitor", lambda: self.switch_screen("Live Monitor")),
            ("Incidents", lambda: self.switch_screen("Incidents")),
            ("Reports", lambda: self.switch_screen("Reports")),
            ("Settings", lambda: self.switch_screen("Settings")),
            ("ALERTS", self.open_alerts),
            ("Logout", self.logout)
        ]
        
        btn_frame = ttk.Frame(self.nav_bar, style="Card.TFrame")
        btn_frame.pack(side="right", padx=10)
        
        for text, cmd in buttons:
            btn = ttk.Button(btn_frame, text=text, command=cmd)
            btn.pack(side="left", padx=5)

    def switch_screen(self, screen_name):
        # Clear current screen
        for widget in self.container.winfo_children():
            # If it has a 'stop_monitoring' method, call it (for camera view)
            if hasattr(widget, 'stop_monitoring'):
                widget.stop_monitoring()
            widget.destroy()
            
        # Initialize new screen
        if screen_name == "Live Monitor":
            screen = camera_view.CameraMonitorScreen(self.container)
            screen.start_monitoring()
        elif screen_name == "Incidents":
            screen = incidents.IncidentsScreen(self.container, current_user=self.current_user)
        elif screen_name == "Dashboard":
            screen = dashboard.DashboardScreen(self.container)
        elif screen_name == "Settings":
            screen = settings.SettingsScreen(self.container)
        elif screen_name == "Reports":
            # Reports not yet implemented, create placeholder module/class or use fallback
            if 'monitor_app.reports' in sys.modules:
               screen = reports.ReportsScreen(self.container)
            else:
               # Placeholder logic handled by 'else' block below if reports.py doesn't exist
               # check if we can import it
               try:
                   import monitor_app.reports as rpt
                   screen = rpt.ReportsScreen(self.container)
               except:
                   lbl = ttk.Label(self.container, text=f"{screen_name} Screen (Under Construction)", style="Header.TLabel")
                   lbl.place(relx=0.5, rely=0.5, anchor="center")
                   return

    def show_dashboard_placeholder(self):
        self.switch_screen("Dashboard")

    def open_alerts(self):
        alerts.AlertPanel(self)

    def logout(self):
        self.current_user = None
        self.show_login()

if __name__ == "__main__":
    app = CellWatchApp()
    app.mainloop()
