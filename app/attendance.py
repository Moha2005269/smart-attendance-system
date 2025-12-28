import cv2
import time
import sys
import os

# Ensure we can find the 'src' folder
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
sys.path.append(root_dir)

from tkinter import messagebox
from datetime import datetime
from pathlib import Path

# --- CONNECTING TO YOUR EXISTING LOGIC ---
# We point to where your actual recognition system lives
from src.recognizer.face_recognition_system import FaceRecognitionSystem
from app.database import record_attendance

class AttendanceManager:
    """
    Bridge between the UI (MainApp) and the Core Logic (FaceRecognitionSystem).
    """

    def __init__(self):
        # Initialize your existing engine
        # We assume encodings are in models/encodings.pkl based on your folder structure
        self.encodings_path = os.path.join(root_dir, "models", "encodings.pkl")
        self.predictor_path = os.path.join(root_dir, "models", "shape_predictor_68_face_landmarks.dat")
        
        # Check if files exist to prevent crash
        if not os.path.exists(self.encodings_path):
            print(f"Warning: Encodings not found at {self.encodings_path}")
        
        try:
            self.recognizer = FaceRecognitionSystem(
                model_path=self.encodings_path, 
                predictor_path=self.predictor_path
            )
            print("✅ Face Recognition Engine Loaded")
        except Exception as e:
            print(f"❌ Error loading Engine: {e}")
            self.recognizer = None

        self.cap = None

    def start_camera(self):
        """Starts the OpenCV video capture."""
        if self.cap is None or not self.cap.isOpened():
            self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
            if not self.cap.isOpened():
                self.cap = cv2.VideoCapture(0)

    def stop_camera(self):
        """Releases the camera."""
        if self.cap:
            self.cap.release()
            self.cap = None

    def detect_and_mark(self, student_id, student_name):
        """
        Captures one frame, runs recognition, and saves to DB if match found.
        """
        if not self.cap or not self.cap.isOpened():
            return False, "Camera not active"

        if not self.recognizer:
            return False, "Recognition Engine failed to load"

        # 1. Grab a single frame
        ret, frame = self.cap.read()
        if not ret:
            return False, "Could not read frame"

        # 2. Run your existing recognition logic
        # recognize_frame returns a list of matches
        results = self.recognizer.recognize_frame(frame)

        # 3. Process Results
        match_found = False
        confidence = 0.0
        
        for res in results:
            # Check if the face detected matches the logged-in user
            # We compare names case-insensitive
            if res['label'].lower() == student_name.lower():
                confidence = res['confidence'] * 100
                match_found = True
                
                # Check Liveness (if your system supports it)
                is_live = res.get('liveness_ok', True) 
                
                if not is_live:
                    return False, "Liveness Check Failed (Blink/Move head)"
                
                if confidence < 50:
                    return False, f"Low Confidence ({confidence:.0f}%)"

                break

        if match_found:
            # 4. Save Snapshot
            photo_dir = os.path.join(root_dir, "attendance_photos")
            os.makedirs(photo_dir, exist_ok=True)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            photo_filename = f"{student_id}_{timestamp}.jpg"
            photo_path = os.path.join(photo_dir, photo_filename)
            
            cv2.imwrite(photo_path, frame)

            # 5. Record to Database (Using your existing database function)
            # record_attendance(user_id, status, confidence, liveness, snapshot)
            try:
                record_attendance(
                    user_id=student_id, # Using ID as key
                    status="Present", 
                    confidence=confidence, 
                    liveness=True, 
                    snapshot=photo_path
                )
                return True, f"Marked Present ({confidence:.0f}%)"
            except Exception as e:
                print(f"DB Error: {e}")
                return True, "Marked locally (DB Error)"

        return False, "Face not recognized or incorrect user"
