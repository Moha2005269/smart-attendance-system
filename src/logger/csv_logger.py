import csv
import os
from pathlib import Path
from datetime import datetime

class CSVLogger:
    """
    Logs attendance to a CSV file.
    """

    def __init__(self, file_path: str):
        self.base_path = Path(file_path)
        # Create folder if it doesn't exist
        self.base_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Use ONE file per day
        self.date_str = datetime.now().strftime("%d-%m-%Y")
        self.file_path = self.base_path.parent / f"{self.date_str}_attendance.csv"
        
        self.logged_users = set() # Track IDs to prevent duplicate logs in one session
        self._write_header()

    def _write_header(self) -> None:
        """Write CSV header if file doesn't exist."""
        if not self.file_path.exists() or self.file_path.stat().st_size == 0:
            with self.file_path.open(mode="w", newline="", encoding='utf-8') as file:
                writer = csv.writer(file)
                # Updated Header with Role
                writer.writerow(["Name", "ID", "Role", "Time", "Status"])

    def log_attendance(self, name: str, user_id: str, role: str) -> None:
        """
        Log attendance for a person.
        """
        # Simple duplicate check for this session
        if user_id not in self.logged_users:
            self.logged_users.add(user_id)
            
            timestamp = datetime.now().strftime("%H:%M:%S")
            with self.file_path.open(mode="a", newline="", encoding='utf-8') as file:
                writer = csv.writer(file)
                # Writing the Role column
                writer.writerow([name, user_id, role, timestamp, "Present"])
