
import sqlite3
import datetime
import threading
from pathlib import Path


class DatabaseHandler:

    def __init__(self, db_path=None):

        if db_path is None:
            project_dir = Path(__file__).resolve().parent
            db_folder = project_dir.parent

            db_folder.mkdir(parents=True, exist_ok=True)

            db_path = db_folder / "alerts.db"

        self.conn = sqlite3.connect(
            str(db_path),
            check_same_thread=False
        )

        self.lock = threading.Lock()

        with self.lock:
            self.conn.execute("PRAGMA busy_timeout = 5000")
            self._create_table()

    def _create_table(self):

        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT,
                timestamp TEXT,
                behavior TEXT,
                confidence REAL,
                screenshot_path TEXT
            )
        """)

        self.conn.commit()

    def save_alert(
        self,
        student_id,
        behavior,
        confidence,
        screenshot_path
    ):

        ts = datetime.datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        with self.lock:

            self.conn.execute(
                """
                INSERT INTO alerts
                (student_id, timestamp, behavior, confidence, screenshot_path)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    str(student_id),
                    ts,
                    behavior,
                    confidence,
                    screenshot_path
                )
            )

            self.conn.commit()

    def get_all_alerts(self):

        with self.lock:

            cursor = self.conn.execute(
                "SELECT * FROM alerts ORDER BY id DESC"
            )

            return cursor.fetchall()
