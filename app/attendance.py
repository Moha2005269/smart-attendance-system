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
from src.logger.csv_logger import CSVLogger  # <--- NEW: Import CSV Logger
from app.database import record_attendance

class AttendanceManager:
    """
    Bridge between UI, Database, and CSV Logging.
    """

    def __init__(self):
        # --- PATHS ---
        self.encodings_path = os.path.join(root_dir, "models", "encodings.pkl")
        self.predictor_path = os.path.join(root_dir, "models", "shape_predictor_68_face_landmarks.dat")
        self.csv_folder = os.path.join(root_dir, "attendance_records")

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
        # This creates a file like: attendance_records/04-07-2025_..._attendance.csv
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
            # Case-insensitive name match
            if res['label'].lower() == student_name.lower():
                confidence = res['confidence'] * 100
                match_found = True
                
                # Liveness Check
                is_live = res.get('liveness_ok', True) 
                if not is_live:
                    return False, "Liveness Check Failed"
                
                if confidence < 50:
                    return False, f"Low Confidence ({confidence:.0f}%)"
                break

        if match_found:
            # --- ACTION: SAVE SNAPSHOT ---
            photo_dir = os.path.join(root_dir, "attendance_photos")
            os.makedirs(photo_dir, exist_ok=True)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            photo_filename = f"{student_id}_{timestamp}.jpg"
            photo_path = os.path.join(photo_dir, photo_filename)
            cv2.imwrite(photo_path, frame)

            # --- ACTION: SAVE TO DATABASE ---
            try:
                record_attendance(
                    user_id=student_id,
                    status="Present", 
                    confidence=confidence, 
                    liveness=True, 
                    snapshot=photo_path
                )
            except Exception as e:
                print(f"DB Error: {e}")

            # --- ACTION: SAVE TO CSV (THE FIX) ---
            if self.csv_logger:
                self.csv_logger.log_attendance(student_name)
                print(f"📝 Logged to CSV: {student_name}")

            return True, f"Marked Present ({confidence:.0f}%)"

        return False, "Face not recognized"
