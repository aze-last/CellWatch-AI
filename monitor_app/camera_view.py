import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk, ImageDraw
import monitor_app.utils as utils
import threading
import queue
import time
from monitor_app.incident_record import IncidentRecorder

# OpenCV
try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    print("OpenCV Import Error. Camera features disabled.")
    CV2_AVAILABLE = False
    cv2 = None

# AI engines (import module so we can access engines and YOLO flags)
try:
    import monitor_app.ai_engine as ai
    from monitor_app.ai_engine import BasicMotionEngine, MotionOptimizedEngine
    AI_AVAILABLE = True
except Exception as e:
    print(f"AI Engine Import Error: {e}")
    ai = None
    BasicMotionEngine = None
    MotionOptimizedEngine = None
    AI_AVAILABLE = False

# Global engines (shared across feeds)
_pose_engine = None
_yolo_engine = None


class CameraMonitorScreen(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.pack(fill="both", expand=True)

        global _pose_engine, _yolo_engine

        # --- motion-optimized engine (MoveNet + optional YOLO) ---
        if _pose_engine is None and AI_AVAILABLE and MotionOptimizedEngine is not None:
            try:
                print("Using MotionOptimizedEngine (MoveNet + optional YOLO)...")
                _pose_engine = MotionOptimizedEngine(
                    debug=False,
                    sensitivity="high",
                    enable_yolo=True,
                    prefer_gpu=True,
                    force_gpu=True,
                    force_yolo_gpu=True
                )
                _yolo_engine = None
            except Exception as e:
                print(f"MotionOptimizedEngine init failed: {e}")
                _pose_engine = None

        # --- fallback motion engine (no TensorFlow) ---
        if _pose_engine is None and AI_AVAILABLE and BasicMotionEngine is not None:
            try:
                print("Using BasicMotionEngine (motion-only, no TensorFlow)...")
                _pose_engine = BasicMotionEngine(sensitivity="high")
            except Exception as e:
                print(f"BasicMotionEngine init failed: {e}")
                _pose_engine = None

        self.cameras = []
        self.create_widgets()

    def create_widgets(self):
        # 2x2 Grid
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        # Camera 1 (Laptop webcam)
        cam1 = CameraFeedWidget(self, camera_id=1, source=0)
        cam1.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.cameras.append(cam1)

        # Camera 2 (External webcam index 1)
        cam2 = CameraFeedWidget(self, camera_id=2, source=1)
        cam2.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        self.cameras.append(cam2)

        # Camera 3 & 4 mocked
        for i in range(2, 4):
            cam_id = i + 1
            row = i // 2
            col = i % 2

            cam_feed = CameraFeedWidget(self, camera_id=cam_id, source=None)
            cam_feed.grid(row=row, column=col, sticky="nsew", padx=5, pady=5)
            self.cameras.append(cam_feed)

    def start_monitoring(self):
        for cam in self.cameras:
            cam.start()

    def stop_monitoring(self):
        for cam in self.cameras:
            cam.stop()


class CameraFeedWidget(ttk.Frame):
    def __init__(self, parent, camera_id, source=None):
        super().__init__(parent, style="Card.TFrame")
        self.camera_id = camera_id
        self.source = source
        self.cap = None
        self.running = False
        self.tk_image = None
        self.frame_index = 0  # unused with unified engine
        self.result_queue = queue.Queue(maxsize=1)
        self.worker_thread = None
        self.last_frame_rgb = None
        self.ui_frame_interval_ms = 33  # ~30 FPS UI refresh
        
        # Incident detection & recording logic
        self.recorder = IncidentRecorder(self.camera_id)

        self.setup_ui()

    def setup_ui(self):
        self.pack_propagate(False)

        header = ttk.Frame(self, style="Card.TFrame")
        header.pack(fill="x", padx=5, pady=5)

        src_text = "Webcam" if self.source in (0, 1) else "Simulated"
        self.lbl_title = ttk.Label(
            header,
            text=f"Cam {self.camera_id} ({src_text})",
            style="Card.TLabel",
            font=utils.FONT_BOLD
        )
        self.lbl_title.pack(side="left")

        self.lbl_status = ttk.Label(
            header,
            text="NORMAL",
            foreground=utils.COLOR_SUCCESS,
            style="Card.TLabel",
            font=utils.FONT_BOLD
        )
        self.lbl_status.pack(side="right")

        self.canvas = tk.Canvas(self, bg="black", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True, padx=2, pady=2)

        self.draw_placeholder()

    def start(self):
        if self.running:
            return
        self.running = True

        if CV2_AVAILABLE and self.source is not None:
            self.cap = cv2.VideoCapture(self.source)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

            # Start worker thread for real cameras
            self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
            self.worker_thread.start()
        
        # Track active cameras globally
        utils.GlobalState.register_camera(self.camera_id)
        self.update_loop()

    def _worker_loop(self):
        """Background thread for capturing and processing frames."""
        while self.running:
            if not self.cap or not self.cap.isOpened():
                time.sleep(0.1)
                continue

            ret, raw_frame = self.cap.read()
            if not ret:
                time.sleep(0.01)
                continue

            # Process AI in the background
            global _pose_engine
            frame_to_show = raw_frame
            alert_active = False
            res = {} # Default in case engine fails

            if _pose_engine:
                try:
                    res = _pose_engine.process_frame(raw_frame, str(self.camera_id))
                    frame_to_show = res.get("frame", raw_frame)
                    alert_active = bool(res.get("alert_triggered", False))
                except Exception as e:
                    print(f"Worker AI Error (Cam {self.camera_id}): {e}")

            # Convert to RGB and resize in background to save main thread time
            try:
                rgb = cv2.cvtColor(frame_to_show, cv2.COLOR_BGR2RGB)
                # We put the processed data into the queue
                if self.result_queue.full():
                    try:
                        self.result_queue.get_nowait() # Drop slowest if full
                    except queue.Empty:
                        pass
                self.result_queue.put((rgb, alert_active))
                
                # --- INCIDENT RECORDING LOGIC ---
                # Pass the processed frame (with overlays) to the recorder
                # This handles state transitions (IDLE -> RECORDING -> COOLDOWN)
                # and saves video clips + metadata.
                # NOTE: frame_to_show is BGR which is what OpenCV Writer needs.
                self.recorder.process_frame(frame_to_show, res)
            except Exception as e:
                print(f"Worker process error: {e}")

            # Small sleep to prevent 100% CPU usage if everything is too fast
            time.sleep(0.001)

    def stop(self):
        self.running = False
        if self.cap:
            self.cap.release()
            self.cap = None
        # Unregister camera
        utils.GlobalState.unregister_camera(self.camera_id)

    def update_loop(self):
        if not self.running:
            return

        frame_rgb = None
        alert_triggered = False

        # --- real camera (poll queue) ---
        if self.source is not None:
            try:
                # Try to get latest from worker (non-blocking)
                rgb_data, alert_triggered = self.result_queue.get_nowait()
                frame_rgb = rgb_data
            except queue.Empty:
                # If no new frame from worker, just continue with old or skip
                frame_rgb = None
                # We don't return here so we don't break the loop, 
                # but we'll skip the drawing block if frame_rgb is None
                pass
            
            # Special case for "Signal Lost" handled by worker not putting data
            if frame_rgb is None and (not self.cap or not self.cap.isOpened()):
                self.draw_placeholder("Signal Lost")
                self.after(30, self.update_loop)
                return

        # --- simulated cams ---
        else:
            self.draw_mock_simulation()
            self.after(50, self.update_loop)  # 20 FPS
            return

        # --- draw to canvas ---
        if frame_rgb is None:
            frame_rgb = self.last_frame_rgb

        if frame_rgb is not None:
            cw = self.canvas.winfo_width()
            ch = self.canvas.winfo_height()
            if cw < 10 or ch < 10:
                cw, ch = 320, 240

            img_pil = Image.fromarray(frame_rgb)
            img_pil = img_pil.resize((cw, ch))
            self.tk_image = ImageTk.PhotoImage(img_pil)
            self.last_frame_rgb = frame_rgb
            
            # Optimized rendering: Update existing item instead of recreating
            if not hasattr(self, 'image_id') or self.image_id is None:
                self.image_id = self.canvas.create_image(0, 0, image=self.tk_image, anchor="nw")
            else:
                self.canvas.itemconfig(self.image_id, image=self.tk_image)

        # --- status ---
        # Show status from the recorder (NORMAL, RECORDING, or COOLDOWN)
        status_text, status_color = self.recorder.get_status_info()
        self.lbl_status.configure(text=status_text, foreground=status_color)
        
        # Update global alert state
        utils.GlobalState.set_alert(self.camera_id, self.recorder.state == self.recorder.RECORDING)

        self.after(self.ui_frame_interval_ms, self.update_loop)  # Target ~30 FPS for UI responsiveness

    def draw_placeholder(self, text="No Signal"):
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w < 10:
            w, h = 300, 200

        img = Image.new("RGB", (w, h), (40, 40, 40))
        d = ImageDraw.Draw(img)
        d.text((w // 2 - 30, h // 2), text, fill="white")
        self.tk_image = ImageTk.PhotoImage(img)

        # Reuse the same canvas image item to avoid leaking items
        if not hasattr(self, 'image_id') or self.image_id is None:
            self.image_id = self.canvas.create_image(0, 0, image=self.tk_image, anchor="nw")
        else:
            self.canvas.itemconfig(self.image_id, image=self.tk_image)

    def draw_mock_simulation(self):
        behavior, is_alert, _ = utils.MockAI.detect_behavior_frame(self.camera_id)

        if is_alert:
            self.lbl_status.configure(text=f"ALERT: {behavior.upper()}", foreground=utils.COLOR_ALERT)
        else:
            self.lbl_status.configure(text=f"Status: {behavior}", foreground=utils.COLOR_SUCCESS)

        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w < 10:
            w, h = 300, 200

        color = (100, 50, 50) if is_alert else (50, 50, 50)
        img = Image.new("RGB", (w, h), color)
        d = ImageDraw.Draw(img)
        d.text((10, 10), f"SIMULATION (Cam {self.camera_id})", fill="white")
        d.text((w // 2 - 40, h // 2), f"Person: {behavior}", fill="white")

        self.tk_image = ImageTk.PhotoImage(img)

        # Reuse the same canvas image item to avoid leaking items
        if not hasattr(self, 'image_id') or self.image_id is None:
            self.image_id = self.canvas.create_image(0, 0, image=self.tk_image, anchor="nw")
        else:
            self.canvas.itemconfig(self.image_id, image=self.tk_image)
