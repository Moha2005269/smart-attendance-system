import cv2
import sys
import os
from datetime import datetime

# 1. Setup Root Path to find 'src'
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
sys.path.append(root_dir)

# 2. Import your modules
from src.recognizer.face_recognition_system import FaceRecognitionSystem
from src.logger.csv_logger import CSVLogger
from app.database import record_attendance
import sqlite3 # Needed to fetch role

class AttendanceManager:
    """
    Bridge between UI, Database, and CSV Logging.
    """

    def __init__(self):
        # --- PATHS ---
        self.encodings_path = os.path.join(root_dir, "models", "encodings.pkl")
        self.predictor_path = os.path.join(root_dir, "models", "shape_predictor_68_face_landmarks.dat")
        self.csv_folder = os.path.join(root_dir, "attendance_records")
        self.db_path = os.path.join(root_dir, "database", "attendance.db") # For role lookup

        # --- LOAD ENGINE ---
        try:
            self.recognizer = FaceRecognitionSystem(
                model_path=self.encodings_path, 
                predictor_path=self.predictor_path
            )
            print("✅ Face Recognition Engine Loaded")
        except Exception as e:
            print(f"❌ Error loading Engine: {e}")
            self.recognizer = None

        # --- LOAD CSV LOGGER ---
        try:
            base_csv_path = os.path.join(self.csv_folder, "attendance.csv")
            self.csv_logger = CSVLogger(base_csv_path)
            print(f"✅ CSV Logger active: {self.csv_logger.file_path}")
        except Exception as e:
            print(f"❌ CSV Logger failed: {e}")
            self.csv_logger = None

        self.cap = None

    def start_camera(self):
        if self.cap is None or not self.cap.isOpened():
            self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
            if not self.cap.isOpened():
                self.cap = cv2.VideoCapture(0)

    def stop_camera(self):
        if self.cap:
            self.cap.release()
            self.cap = None

    def _get_user_role(self, user_id):
        """Helper to find if user is Student or Staff from DB"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            # We check the 'class_name' field. 
            # In our models.py logic, Staff save their Department into 'class_name'.
            # But to be precise, we can check a naming convention or just return 'User' if unsure.
            
            # Since we didn't add a specific 'role' column to the DB to keep it simple,
            # we will assume everyone is a Student unless we find a way to distinguish.
            # HOWEVER, for the CSV to look good, let's fetch the class/dept.
            
            cursor.execute("SELECT class_name FROM students WHERE student_id = ?", (user_id,))
            result = cursor.fetchone()
            conn.close()
            
            if result:
                # If the value looks like a Department (e.g., "IT Dept"), we call them Staff.
                # If it looks like a Class (e.g., "CS-101"), we call them Student.
                # For now, let's just log the 'Class/Dept' value itself as context.
                return result[0] 
            return "Unknown"
        except:
            return "Unknown"

    def detect_and_mark(self, student_id, student_name):
        """
        Runs recognition -> Saves to DB -> Saves to CSV
        """
        if not self.cap or not self.cap.isOpened():
            return False, "Camera not active"

        if not self.recognizer:
            return False, "Recognition Engine failed"

        # 1. Capture Frame
        ret, frame = self.cap.read()
        if not ret:
            return False, "Could not read frame"

        # 2. Run Recognition
        results = self.recognizer.recognize_frame(frame)

        # 3. Process Results
        match_found = False
        confidence = 0.0
        
        for res in results:
            if res['label'].lower() == student_name.lower():
                confidence = res['confidence'] * 100
                match_found = True
                
                is_live = res.get('liveness_ok', True) 
                if not is_live:
                    return False, "Liveness Check Failed"
                
                if confidence < 50:
                    return False, f"Low Confidence ({confidence:.0f}%)"
                break

        if match_found:
            # Save Snapshot
            photo_dir = os.path.join(root_dir, "attendance_photos")
            os.makedirs(photo_dir, exist_ok=True)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            photo_filename = f"{student_id}_{timestamp}.jpg"
            photo_path = os.path.join(photo_dir, photo_filename)
            cv2.imwrite(photo_path, frame)

            # Save to DB
            try:
                record_attendance(user_id=student_id, status="Present", confidence=confidence, liveness=True, snapshot=photo_path)
            except Exception as e:
                print(f"DB Error: {e}")

            # --- ACTION: SAVE TO CSV WITH ROLE ---
            if self.csv_logger:
                # We fetch the "Class/Dept" info to use as the Role/Info column
                role_info = self._get_user_role(student_id)
                self.csv_logger.log_attendance(student_name, student_id, role_info)
                print(f"📝 Logged to CSV: {student_name} ({role_info})")

            return True, f"Marked Present ({confidence:.0f}%)"

        return False, "Face not recognized"
