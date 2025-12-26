from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
from typing import Optional

DEFAULT_CSV_PATH = "attendance_records/attendance_log.csv"

def log_attendance(
    student_id: str,
    name: str,
    confidence: Optional[float] = None,
    liveness_ok: bool = False,
    snapshot_path: Optional[str] = None,
    csv_path: str = DEFAULT_CSV_PATH,
) -> None:
    Path(csv_path).parent.mkdir(parents=True, exist_ok=True)
    file_exists = Path(csv_path).exists()

    row = [
        datetime.now().isoformat(timespec="seconds"),
        (student_id or "").strip(),
        (name or "").strip(),
        "" if confidence is None else float(confidence),
        int(bool(liveness_ok)),
        "" if snapshot_path is None else str(snapshot_path),
    ]

    with open(csv_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["timestamp", "student_id", "name", "confidence", "liveness_ok", "snapshot_path"])
        writer.writerow(row)
