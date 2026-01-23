import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk
import monitor_app.utils as utils


class ReportsScreen(ttk.Frame):
    """
    Reports screen redesigned to match the CustomTkinter mock:
    - Left sidebar for criteria
    - Right "paper" style preview area
    """

    def __init__(self, parent):
        super().__init__(parent)
        self.pack(fill="both", expand=True)

        # Layout grid: title row + main row (sidebar + preview)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)

        self.create_widgets()

    def create_widgets(self):
        # Top title (inside this screen; main nav is in main window)
        title = ctk.CTkLabel(
            self,
            text="Generate Reports",
            font=("Roboto", 20, "bold"),
            anchor="w",
        )
        title.grid(row=0, column=0, columnspan=2, sticky="ew", padx=25, pady=(20, 10))

        # --- Sidebar on the left ---
        self.sidebar = ctk.CTkFrame(self, width=280, corner_radius=0, fg_color="#2b2b2b")
        self.sidebar.grid(row=1, column=0, sticky="nsew", padx=(0, 2), pady=(0, 20))

        # --- Preview on the right ---
        self.preview_container = ctk.CTkFrame(self, fg_color="transparent")
        self.preview_container.grid(row=1, column=1, sticky="nsew", padx=25, pady=(0, 25))
        self.preview_container.grid_rowconfigure(1, weight=1)
        self.preview_container.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self.preview_container,
            text="Report Preview",
            font=("Roboto", 20, "bold"),
        ).grid(row=0, column=0, sticky="w", pady=(0, 15))

        # White paper-style area
        self.paper_preview = ctk.CTkFrame(self.preview_container, fg_color="white", corner_radius=5)
        self.paper_preview.grid(row=1, column=0, sticky="nsew")
        self.paper_preview.grid_rowconfigure(0, weight=1)
        self.paper_preview.grid_columnconfigure(0, weight=1)

        # Use a Text widget on top of the white paper for generated content
        self.preview_text = tk.Text(self.paper_preview, bg="white", fg="black", relief="flat")
        self.preview_text.grid(row=0, column=0, sticky="nsew", padx=15, pady=15)
        self.preview_text.insert("1.0", "[ PREVIEW GENERATED REPORT HERE ]")

        # Build the left criteria sidebar
        self.build_sidebar_content()

    def build_sidebar_content(self):
        ctk.CTkLabel(
            self.sidebar,
            text="Report Criteria",
            font=("Roboto", 18, "bold"),
        ).pack(pady=(30, 20), padx=20, anchor="w")

        # Report Type
        ctk.CTkLabel(
            self.sidebar,
            text="Report Type",
            font=("Roboto", 12),
            text_color="gray",
        ).pack(padx=20, anchor="w")
        self.combo_type = ctk.CTkOptionMenu(
            self.sidebar,
            values=[
                "Daily Incident Summary",
                "Weekly Behavior Analytics",
                "Alert Frequency Report",
                "System Health Log",
            ],
            width=240,
        )
        self.combo_type.set("Daily Incident Summary")
        self.combo_type.pack(pady=(5, 20), padx=20)

        # Date range
        ctk.CTkLabel(
            self.sidebar,
            text="Date Range",
            font=("Roboto", 12),
            text_color="gray",
        ).pack(padx=20, anchor="w")

        date_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        date_frame.pack(fill="x", padx=20, pady=5)

        self.date_from = ctk.CTkEntry(date_frame, placeholder_text="YYYY-MM-DD", width=115)
        self.date_from.pack(side="left")

        ctk.CTkLabel(date_frame, text="to", font=("Roboto", 12)).pack(side="left", padx=5)

        self.date_to = ctk.CTkEntry(date_frame, placeholder_text="YYYY-MM-DD", width=115)
        self.date_to.pack(side="left")

        # Filters by severity
        ctk.CTkLabel(
            self.sidebar,
            text="Filter by Severity",
            font=("Roboto", 12),
            text_color="gray",
        ).pack(padx=20, pady=(15, 5), anchor="w")
        self.chk_high = ctk.CTkCheckBox(self.sidebar, text="High (Aggressive)")
        self.chk_high.pack(padx=30, pady=5, anchor="w")
        self.chk_med = ctk.CTkCheckBox(self.sidebar, text="Medium (Suspicious)")
        self.chk_med.pack(padx=30, pady=5, anchor="w")
        self.chk_low = ctk.CTkCheckBox(self.sidebar, text="Low (General)")
        self.chk_low.pack(padx=30, pady=5, anchor="w")

        # Action buttons
        self.btn_generate = ctk.CTkButton(
            self.sidebar,
            text="GENERATE PREVIEW",
            font=("Roboto", 13, "bold"),
            height=40,
            command=self.generate_preview,
        )
        self.btn_generate.pack(fill="x", padx=20, pady=(40, 10))

        self.btn_export = ctk.CTkButton(
            self.sidebar,
            text="EXPORT AS PDF",
            font=("Roboto", 13, "bold"),
            fg_color="#2cc985",
            hover_color="#27ae60",
            height=40,
            command=self.export_pdf,
        )
        self.btn_export.pack(fill="x", padx=20, pady=10)

    # --- Actions ---
    def generate_preview(self):
        """Simple dummy preview generation using current criteria."""
        rpt_type = self.combo_type.get()
        date_from = self.date_from.get().strip() or "N/A"
        date_to = self.date_to.get().strip() or "N/A"

        severities = []
        if self.chk_high.get():
            severities.append("High")
        if self.chk_med.get():
            severities.append("Medium")
        if self.chk_low.get():
            severities.append("Low")
        sev_text = ", ".join(severities) if severities else "All"

        self.preview_text.delete("1.0", tk.END)
        self.preview_text.insert("1.0", f"{rpt_type}\n")
        self.preview_text.insert("end", "-" * len(rpt_type) + "\n\n")
        self.preview_text.insert("end", f"Date Range: {date_from} to {date_to}\n")
        self.preview_text.insert("end", f"Severities: {sev_text}\n\n")
        self.preview_text.insert(
            "end",
            "[This is a placeholder preview. Here you would render a table or\n"
            "chart with incidents, alerts, or system metrics based on filters.]",
        )

    def export_pdf(self):
        # Placeholder for real export logic
        messagebox.showinfo("Export", "PDF export is not implemented yet (demo only).")
