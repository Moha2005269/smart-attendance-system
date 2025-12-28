import sqlite3
from pathlib import Path
from datetime import datetime

# Define DB Path
DB_PATH = Path("database/attendance.db")
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

def init_db():
    """Initialize the database tables."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Students Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            name TEXT NOT NULL,
            class_name TEXT
        )
    """)

    # Attendance Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            name TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            status TEXT,
            confidence REAL,
            photo_path TEXT
        )
    """)
    
    conn.commit()
    conn.close()

def add_student(student_id, password, name, class_name=""):
    """Register a new student."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO students (student_id, password, name, class_name) 
            VALUES (?, ?, ?, ?)
        """, (student_id, password, name, class_name))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False
    except Exception as e:
        print(f"Database Error (add_student): {e}")
        return False

def get_student(student_id, password):
    """Verify login."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, student_id, name, class_name 
        FROM students 
        WHERE student_id = ? AND password = ?
    """, (student_id, password))
    row = cursor.fetchone()
    conn.close()
    return row

def get_attendance_history(student_id):
    """Fetch history for the UI."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT timestamp, name, photo_path, confidence, status 
        FROM attendance 
        WHERE student_id = ? 
        ORDER BY timestamp DESC
    """, (student_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def record_attendance(user_id, status, confidence, liveness, snapshot):
    """
    Records attendance into the database.
    This is the function your error says is missing!
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Fetch name to keep records complete
        cursor.execute("SELECT name FROM students WHERE student_id = ?", (user_id,))
        result = cursor.fetchone()
        name = result[0] if result else "Unknown"

        cursor.execute("""
            INSERT INTO attendance (student_id, name, status, confidence, photo_path)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, name, status, confidence, snapshot))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Database Error (record_attendance): {e}")
        return False
