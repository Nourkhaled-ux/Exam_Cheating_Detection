
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import threading
import cv2
import os
from pathlib import Path

from database import DatabaseHandler
from detector import process_frame
from annotator import annotate_and_screenshot


class CheatDetectorApp:
    BG = "#F4F7FC"
    WHITE = "#FFFFFF"
    PRIMARY = "#2563EB"
    PRIMARY_HOVER = "#1D4ED8"
    LIGHT_BLUE = "#EFF6FF"
    TEXT = "#172554"
    SECONDARY = "#64748B"
    BORDER = "#E2E8F0"
    GREEN = "#16A34A"
    LIGHT_GREEN = "#DCFCE7"
    RED = "#DC2626"
    LIGHT_RED = "#FEE2E2"
    YELLOW = "#D97706"
    LIGHT_YELLOW = "#FEF3C7"

    def __init__(self, root):

        self.root = root
        self.root.title("Exam Monitoring System")
        self.root.configure(bg=self.BG)

        self.root.attributes("-fullscreen", True)

        self.db = DatabaseHandler()

        self.running = False
        self.video_thread = None
        self.current_photo = None

        self.root.bind("<F11>", self.toggle_fullscreen)
        self.root.bind("<Escape>", self.exit_fullscreen)

        self.root.protocol("WM_DELETE_WINDOW", self.close_app)

        self.configure_styles()
        self.build_ui()
        self.refresh_history()


    def configure_styles(self):

        style = ttk.Style()
        style.theme_use("clam")

        style.configure(
            "Treeview",
            background=self.WHITE,
            foreground=self.TEXT,
            fieldbackground=self.WHITE,
            rowheight=42,
            borderwidth=0,
            font=("Segoe UI", 10)
        )

        style.configure(
            "Treeview.Heading",
            background="#F1F5F9",
            foreground=self.SECONDARY,
            font=("Segoe UI", 9, "bold"),
            padding=12,
            borderwidth=0
        )

        style.map(
            "Treeview",
            background=[("selected", "#DBEAFE")],
            foreground=[("selected", self.TEXT)]
        )


    def create_card(self, parent, padx=0, pady=0):

        card = tk.Frame(
            parent,
            bg=self.WHITE,
            highlightthickness=1,
            highlightbackground=self.BORDER
        )

        card.pack_propagate(False)

        return card

    def create_button(self, parent, text, command,
                      bg=None, fg=None):

        return tk.Button(
            parent,
            text=text,
            command=command,
            bg=bg or self.PRIMARY,
            fg=fg or self.WHITE,
            activebackground=self.PRIMARY_HOVER,
            activeforeground=self.WHITE,
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            bd=0,
            cursor="hand2",
            padx=18,
            pady=11
        )

    

    def build_ui(self):

        

        header = tk.Frame(
            self.root,
            bg=self.WHITE,
            height=85,
            highlightthickness=1,
            highlightbackground=self.BORDER
        )

        header.pack(fill="x")
        header.pack_propagate(False)

        left_header = tk.Frame(header, bg=self.WHITE)
        left_header.pack(side="left", padx=35)

        logo = tk.Frame(
            left_header,
            bg=self.LIGHT_BLUE,
            width=48,
            height=48
        )

        logo.pack(side="left", padx=(0, 13))
        logo.pack_propagate(False)

        tk.Label(
            logo,
            text="◈",
            font=("Segoe UI", 25, "bold"),
            bg=self.LIGHT_BLUE,
            fg=self.PRIMARY
        ).place(relx=0.5, rely=0.5, anchor="center")

        title_frame = tk.Frame(left_header, bg=self.WHITE)
        title_frame.pack(side="left")

        tk.Label(
            title_frame,
            text="Exam Monitoring System",
            font=("Segoe UI", 18, "bold"),
            bg=self.WHITE,
            fg=self.TEXT
        ).pack(anchor="w")

        tk.Label(
            title_frame,
            text="Intelligent Exam Surveillance",
            font=("Segoe UI", 9),
            bg=self.WHITE,
            fg=self.SECONDARY
        ).pack(anchor="w")


        status_frame = tk.Frame(header, bg=self.WHITE)
        status_frame.pack(side="right", padx=35)

        self.header_status = tk.Label(
            status_frame,
            text="● SYSTEM READY",
            font=("Segoe UI", 10, "bold"),
            bg=self.LIGHT_GREEN,
            fg=self.GREEN,
            padx=15,
            pady=9
        )

        self.header_status.pack()

       

        main = tk.Frame(self.root, bg=self.BG)
        main.pack(fill="both", expand=True, padx=30, pady=22)

        main.grid_columnconfigure(0, weight=3)
        main.grid_columnconfigure(1, weight=2)
        main.grid_rowconfigure(1, weight=1)

        

        page_header = tk.Frame(main, bg=self.BG)

        page_header.grid(
            row=0,
            column=0,
            columnspan=2,
            sticky="ew",
            pady=(0, 20)
        )

        tk.Label(
            page_header,
            text="Monitoring Dashboard",
            font=("Segoe UI", 22, "bold"),
            bg=self.BG,
            fg=self.TEXT
        ).pack(anchor="w")

        tk.Label(
            page_header,
            text="Manage exam recordings and monitor suspicious activities.",
            font=("Segoe UI", 10),
            bg=self.BG,
            fg=self.SECONDARY
        ).pack(anchor="w", pady=(5, 0))

        

        video_card = tk.Frame(
            main,
            bg=self.WHITE,
            highlightthickness=1,
            highlightbackground=self.BORDER
        )

        video_card.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=(0, 15)
        )

        video_card.grid_columnconfigure(0, weight=1)
        video_card.grid_rowconfigure(1, weight=1)

        video_header = tk.Frame(video_card, bg=self.WHITE)

        video_header.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=22,
            pady=20
        )

        tk.Label(
            video_header,
            text="Video Monitoring",
            font=("Segoe UI", 14, "bold"),
            bg=self.WHITE,
            fg=self.TEXT
        ).pack(side="left")

        self.live_status = tk.Label(
            video_header,
            text="● STANDBY",
            font=("Segoe UI", 9, "bold"),
            bg=self.LIGHT_BLUE,
            fg=self.PRIMARY,
            padx=12,
            pady=7
        )

        self.live_status.pack(side="right")

        

        video_container = tk.Frame(
            video_card,
            bg="#E2E8F0"
        )

        video_container.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=22,
            pady=(0, 15)
        )

        video_container.grid_columnconfigure(0, weight=1)
        video_container.grid_rowconfigure(0, weight=1)

        self.canvas = tk.Label(
            video_container,
            text="VIDEO PREVIEW\n\nUpload an exam video to start monitoring",
            font=("Segoe UI", 15),
            bg="#E2E8F0",
            fg=self.SECONDARY,
            justify="center"
        )

        self.canvas.grid(
            row=0,
            column=0,
            sticky="nsew"
        )

        controls = tk.Frame(video_card, bg=self.WHITE)

        controls.grid(
            row=2,
            column=0,
            sticky="ew",
            padx=22,
            pady=20
        )

        controls.grid_columnconfigure(0, weight=1)
        controls.grid_columnconfigure(1, weight=1)

        self.upload_btn = self.create_button(
            controls,
            "＋  Upload Video",
            self.upload_video
        )

        self.upload_btn.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=(0, 7)
        )

        self.stop_btn = tk.Button(
            controls,
            text="■  Stop Monitoring",
            command=self.stop_processing,
            bg="#F1F5F9",
            fg=self.TEXT,
            activebackground="#E2E8F0",
            activeforeground=self.TEXT,
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            bd=0,
            cursor="hand2",
            pady=11
        )

        self.stop_btn.grid(
            row=0,
            column=1,
            sticky="ew",
            padx=(7, 0)
        )


        right = tk.Frame(
            main,
            bg=self.WHITE,
            highlightthickness=1,
            highlightbackground=self.BORDER
        )

        right.grid(
            row=1,
            column=1,
            sticky="nsew"
        )

        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(2, weight=1)

        alert_header = tk.Frame(right, bg=self.WHITE)

        alert_header.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=20,
            pady=20
        )

        tk.Label(
            alert_header,
            text="Detection Alerts",
            font=("Segoe UI", 15, "bold"),
            bg=self.WHITE,
            fg=self.TEXT
        ).pack(anchor="w")

        tk.Label(
            alert_header,
            text="Review recorded suspicious activities.",
            font=("Segoe UI", 9),
            bg=self.WHITE,
            fg=self.SECONDARY
        ).pack(anchor="w", pady=(5, 0))


        counter = tk.Frame(
            right,
            bg=self.LIGHT_BLUE,
            highlightthickness=1,
            highlightbackground="#DBEAFE"
        )

        counter.grid(
            row=1,
            column=0,
            sticky="ew",
            padx=20,
            pady=(0, 18)
        )

        tk.Label(
            counter,
            text="TOTAL RECORDED ALERTS",
            font=("Segoe UI", 9, "bold"),
            bg=self.LIGHT_BLUE,
            fg=self.SECONDARY
        ).pack(pady=(13, 2))

        self.alert_count = tk.Label(
            counter,
            text="0",
            font=("Segoe UI", 27, "bold"),
            bg=self.LIGHT_BLUE,
            fg=self.PRIMARY
        )

        self.alert_count.pack(pady=(0, 13))


        table_frame = tk.Frame(right, bg=self.WHITE)

        table_frame.grid(
            row=2,
            column=0,
            sticky="nsew",
            padx=20
        )

        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(0, weight=1)

        columns = ("Time", "Behavior", "Confidence")

        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings"
        )

        self.tree.heading("Time", text="TIME")
        self.tree.heading("Behavior", text="BEHAVIOR")
        self.tree.heading("Confidence", text="CONFIDENCE")

        self.tree.column("Time", width=145, anchor="center")
        self.tree.column("Behavior", width=110, anchor="center")
        self.tree.column("Confidence", width=100, anchor="center")

        scrollbar = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=self.tree.yview
        )

        self.tree.configure(
            yscrollcommand=scrollbar.set
        )

        self.tree.grid(
            row=0,
            column=0,
            sticky="nsew"
        )

        scrollbar.grid(
            row=0,
            column=1,
            sticky="ns"
        )


        screenshot_btn = tk.Button(
            right,
            text="▣  Open Screenshots Folder",
            command=self.open_screenshots,
            bg="#F1F5F9",
            fg=self.TEXT,
            activebackground="#E2E8F0",
            activeforeground=self.TEXT,
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            bd=0,
            cursor="hand2",
            pady=12
        )

        screenshot_btn.grid(
            row=3,
            column=0,
            sticky="ew",
            padx=20,
            pady=20
        )

 

        footer = tk.Frame(
            self.root,
            bg=self.WHITE,
            height=38,
            highlightthickness=1,
            highlightbackground=self.BORDER
        )

        footer.pack(side="bottom", fill="x")
        footer.pack_propagate(False)

        self.status_label = tk.Label(
            footer,
            text="Ready | Waiting for video input",
            font=("Segoe UI", 9),
            bg=self.WHITE,
            fg=self.SECONDARY
        )

        self.status_label.pack(side="left", padx=30)

        tk.Label(
            footer,
            text="YOLOv8  |  ByteTrack  |  MediaPipe  |  SQLite",
            font=("Segoe UI", 9),
            bg=self.WHITE,
            fg=self.SECONDARY
        ).pack(side="right", padx=30)

    def toggle_fullscreen(self, event=None):

        current = self.root.attributes("-fullscreen")

        self.root.attributes("-fullscreen", not current)

    def exit_fullscreen(self, event=None):

        self.root.attributes("-fullscreen", False)

        self.root.geometry("1250x780")
        self.root.minsize(1050, 650)


    def upload_video(self):

        if self.running:

            messagebox.showwarning(
                "Monitoring Active",
                "Stop the current video before uploading another."
            )

            return

        path = filedialog.askopenfilename(
            title="Select Exam Video",
            filetypes=[
                ("Video Files", "*.mp4 *.avi *.mov *.mkv"),
                ("All Files", "*.*")
            ]
        )

        if not path:
            return

        self.running = True

        self.live_status.config(
            text="● MONITORING",
            bg=self.LIGHT_GREEN,
            fg=self.GREEN
        )

        self.header_status.config(
            text="● MONITORING ACTIVE",
            bg=self.LIGHT_GREEN,
            fg=self.GREEN
        )

        self.status_label.config(
            text="Processing exam video..."
        )

        self.canvas.config(
            image="",
            text="Loading video..."
        )

        self.current_photo = None

        self.video_thread = threading.Thread(
            target=self.run_detection,
            args=(path,),
            daemon=True
        )

        self.video_thread.start()


    def run_detection(self, video_path):

        cap = cv2.VideoCapture(video_path)

        try:

            if not cap.isOpened():

                self.root.after(
                    0,
                    lambda: messagebox.showerror(
                        "Video Error",
                        "Could not open the selected video."
                    )
                )

                return

            while self.running and cap.isOpened():

                ret, frame = cap.read()

                if not ret:
                    break

                detections, cheating_ids = process_frame(frame)

                annotated = annotate_and_screenshot(
                    frame,
                    detections,
                    cheating_ids,
                    self.db
                )

                self.root.after(
                    0,
                    self.update_video,
                    annotated.copy()
                )

                if cheating_ids:

                    self.root.after(
                        0,
                        self.show_notification
                    )

                    self.root.after(
                        0,
                        self.refresh_history
                    )

        except Exception as e:

            error = str(e)

            self.root.after(
                0,
                lambda err=error: messagebox.showerror(
                    "Detection Error",
                    err
                )
            )

        finally:

            cap.release()

            try:
                self.root.after(
                    0,
                    self.processing_finished
                )
            except tk.TclError:
                pass

    def update_video(self, frame):

        if not self.root.winfo_exists():
            return

        width = max(self.canvas.winfo_width(), 400)
        height = max(self.canvas.winfo_height(), 300)

        frame = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2RGB
        )

        img = Image.fromarray(frame)

        img.thumbnail(
            (width - 10, height - 10)
        )

        photo = ImageTk.PhotoImage(img)

        self.canvas.config(
            image=photo,
            text=""
        )

        self.current_photo = photo


    def show_notification(self):

        messagebox.showwarning(
            "Suspicious Activity Detected",
            "A suspicious object was detected.\n\n"
            "Please review the alert history and saved screenshot."
        )


    def refresh_history(self):

        for row in self.tree.get_children():
            self.tree.delete(row)

        alerts = self.db.get_all_alerts()

        for alert in alerts:

            self.tree.insert(
                "",
                "end",
                values=(
                    alert[2],
                    alert[3],
                    f"{alert[4]:.2f}"
                )
            )

        self.alert_count.config(
            text=str(len(alerts))
        )

    
    def open_screenshots(self):

        screenshot_dir = (
            Path(__file__).resolve().parent
        )

        screenshot_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        os.startfile(str(screenshot_dir))

    def stop_processing(self):

        if self.running:

            self.running = False

            self.status_label.config(
                text="Stopping monitoring..."
            )

    def processing_finished(self):

        self.running = False

        self.live_status.config(
            text="● STANDBY",
            bg=self.LIGHT_BLUE,
            fg=self.PRIMARY
        )

        self.header_status.config(
            text="● SYSTEM READY",
            bg=self.LIGHT_GREEN,
            fg=self.GREEN
        )

        self.status_label.config(
            text="Ready | Monitoring session finished"
        )

        self.refresh_history()


    def close_app(self):

        self.running = False

        self.root.destroy()


if __name__ == "__main__":

    root = tk.Tk()

    app = CheatDetectorApp(root)

    root.mainloop()
