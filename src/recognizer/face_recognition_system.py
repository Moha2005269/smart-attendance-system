import os
import pickle
import math
import cv2
import dlib
import face_recognition
import numpy as np
from collections import deque

class LivenessState:
    """
    Maintains the temporal state for liveness detection.
    Tracks blink history and head pose consistency over time.
    """
    def __init__(self):
        self.blink_counter = 0
        self.total_blinks = 0
        self.consecutive_frames_closed = 0
        self.is_alive = False
        self.pose_history = deque(maxlen=10) 

class FaceRecognitionSystem:
    """
    Advanced Face Recognition Engine with Liveness Detection (EAR + Head Pose).
    """

    # --- CONSTANTS ---
    EYE_AR_THRESH = 0.22        # EAR below this indicates closed eye
    EYE_AR_CONSEC_FRAMES = 2    # Frames eyes must be closed to count as blink
    POSE_THRESHOLD = 15         # Degrees of rotation (Yaw) to consider "movement"
    
    # 3D Model Points (Standard Face) for PnP Solver
    # Nose tip, Chin, Left Eye Left Corner, Right Eye Right Corner, Left Mouth Corner, Right Mouth Corner
    MODEL_POINTS = np.array([
        (0.0, 0.0, 0.0),             # Nose tip
        (0.0, -330.0, -65.0),        # Chin
        (-225.0, 170.0, -135.0),     # Left eye left corner
        (225.0, 170.0, -135.0),      # Right eye right corner
        (-150.0, -150.0, -125.0),    # Left Mouth corner
        (150.0, -150.0, -125.0)      # Right mouth corner
    ], dtype="double")

    def __init__(self, model_path='models/encodings.pkl', predictor_path='models/shape_predictor_68_face_landmarks.dat'):
        """
        Args:
            model_path: Path to pickle file with known faces.
            predictor_path: Path to dlib 68-point landmark predictor.
        """
        self.model_path = model_path
        self.predictor_path = predictor_path
        self.known_encodings = []
        self.known_labels = []
        
        # State tracking (Simple single-subject assumption for demo purposes)
        self.global_liveness_state = LivenessState()

        self._load_resources()

    def _load_resources(self):
        """Loads models and encodings with error handling."""
        print(f"[INFO] Loading encodings from {self.model_path}...")
        print(f"[DEBUG] Absolute path check: {os.path.abspath(self.model_path)}")
        try:
            print(f"[DEBUG] Absolute path check: {os.path.abspath(self.model_path)}")
            if os.path.exists(self.model_path):
                with open(self.model_path, "rb") as f:
                    data = pickle.load(f)
                self.known_encodings = data.get("encodings", [])
                self.known_labels = data.get("names", [])
                print(f"[INFO] Loaded {len(self.known_encodings)} face encodings.")
            else:
                print(f"[WARNING] Encodings file not found at {self.model_path}. Starting empty.")
        except Exception as e:
            print(f"[ERROR] Failed to load encodings: {e}")

        print(f"[INFO] Loading landmark predictor...")
        if not os.path.exists(self.predictor_path):
            raise FileNotFoundError(
                f"\n[CRITICAL] Missing dlib predictor: {self.predictor_path}\n"
                "Please download 'shape_predictor_68_face_landmarks.dat' and place it in the 'models' folder."
            )
            
        self.detector = dlib.get_frontal_face_detector()
        self.predictor = dlib.shape_predictor(self.predictor_path)

    def _calculate_confidence_percentage(self, face_distance, face_match_threshold=0.6):
        """
        Maps Euclidean distance to a 0-100% confidence score.
        Non-linear mapping: 0.0->100%, 0.6->50%, >0.6->Low
        """
        if face_distance > face_match_threshold:
            range_val = (1.0 - face_match_threshold)
            linear_val = (1.0 - face_distance) / (range_val * 2.0)
            return max(0.0, linear_val) # Clamp to 0
        else:
            range_val = face_match_threshold
            linear_val = 1.0 - (face_distance / (range_val * 2.0))
            # Curve to boost high confidence matches
            return min(1.0, linear_val + ((1.0 - linear_val) * math.pow((linear_val - 0.5) * 2, 0.2)))

    def _get_eye_aspect_ratio(self, eye_points):
        """Calculates EAR using numpy (no scipy needed)."""
        # Vertical distances
        A = np.linalg.norm(eye_points[1] - eye_points[5])
        B = np.linalg.norm(eye_points[2] - eye_points[4])
        # Horizontal distance
        C = np.linalg.norm(eye_points[0] - eye_points[3])
        
        if C == 0: return 0
        ear = (A + B) / (2.0 * C)
        return ear

    def _get_head_pose(self, shape, img_h, img_w):
        """
        Estimates head pose (Yaw, Pitch, Roll) using SolvePnP.
        Maps 2D landmarks to 3D anthropometric face model.
        """
        # Extract specific 2D points from dlib shape to match self.MODEL_POINTS
        # Dlib indices: Nose=30, Chin=8, L_Eye=36, R_Eye=45, L_Mouth=48, R_Mouth=54
        image_points = np.array([
            (shape.part(30).x, shape.part(30).y),     # Nose tip
            (shape.part(8).x, shape.part(8).y),       # Chin
            (shape.part(36).x, shape.part(36).y),     # Left eye left corner
            (shape.part(45).x, shape.part(45).y),     # Right eye right corner
            (shape.part(48).x, shape.part(48).y),     # Left Mouth corner
            (shape.part(54).x, shape.part(54).y)      # Right mouth corner
        ], dtype="double")

        # Camera internals (approximate)
        focal_length = img_w
        center = (img_w / 2, img_h / 2)
        camera_matrix = np.array([
            [focal_length, 0, center[0]],
            [0, focal_length, center[1]],
            [0, 0, 1]
        ], dtype="double")
        
        dist_coeffs = np.zeros((4, 1)) # Assume no lens distortion

        success, rotation_vector, translation_vector = cv2.solvePnP(
            self.MODEL_POINTS, image_points, camera_matrix, dist_coeffs, flags=cv2.SOLVEPNP_ITERATIVE
        )

        if not success:
            return 0, 0, 0

        # Convert rotation vector to euler angles
        rmat, _ = cv2.Rodrigues(rotation_vector)
        proj_matrix = np.hstack((rmat, translation_vector))
        
        # decomposeProjectionMatrix returns (euler_x, euler_y, euler_z) -> (pitch, yaw, roll)
        euler_angles = cv2.decomposeProjectionMatrix(proj_matrix)[6] 
        
        pitch, yaw, roll = [float(val) for val in euler_angles]
        return pitch, yaw, roll

    def recognize_frame(self, frame):
        """
        Processes a frame: detects faces, recognizes them, and checks liveness.
        Returns a list of result dictionaries.
        """
        # 1. Optimization: Resize for faster detection (1/4th scale)
        small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY) # Full res for landmarks
        
        h, w = frame.shape[:2]

        # 2. Detect Faces
        face_locations = face_recognition.face_locations(rgb_small_frame)
        face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

        results = []

        for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
            # 3. Recognition Logic
            matches = face_recognition.compare_faces(self.known_encodings, face_encoding, tolerance=0.6)
            face_distances = face_recognition.face_distance(self.known_encodings, face_encoding)
            
            name = "Unknown"
            confidence = 0.0
            distance = 1.0

            if len(face_distances) > 0:
                best_match_index = np.argmin(face_distances)
                distance = face_distances[best_match_index]
                
                # Use the calculated distance to determine name and confidence
                if distance < 0.6:
                    name = self.known_labels[best_match_index]
                    confidence = self._calculate_confidence_percentage(distance)
                else:
                    # Weak match, treat as unknown but show low confidence
                    confidence = self._calculate_confidence_percentage(distance)

            # 4. Liveness Logic
            # Scale coords back to original frame
            scale = 4
            dlib_rect = dlib.rectangle(int(left * scale), int(top * scale), int(right * scale), int(bottom * scale))
            
            # Get landmarks
            shape = self.predictor(gray_frame, dlib_rect)
            
            # Convert to numpy
            coords = np.zeros((68, 2), dtype=int)
            for i in range(0, 68):
                coords[i] = (shape.part(i).x, shape.part(i).y)

            # EAR (Blink Detection)
            leftEye = coords[42:48]
            rightEye = coords[36:42]
            leftEAR = self._get_eye_aspect_ratio(leftEye)
            rightEAR = self._get_eye_aspect_ratio(rightEye)
            avg_ear = (leftEAR + rightEAR) / 2.0

            # Head Pose
            pitch, yaw, roll = self._get_head_pose(shape, h, w)

            # Update State Machine
            if avg_ear < self.EYE_AR_THRESH:
                self.global_liveness_state.consecutive_frames_closed += 1
            else:
                if self.global_liveness_state.consecutive_frames_closed >= self.EYE_AR_CONSEC_FRAMES:
                    self.global_liveness_state.total_blinks += 1
                    self.global_liveness_state.is_alive = True # Valid blink detected
                self.global_liveness_state.consecutive_frames_closed = 0

            # If user turns head significantly, mark as alive
            if abs(yaw) > self.POSE_THRESHOLD or abs(pitch) > self.POSE_THRESHOLD:
                self.global_liveness_state.is_alive = True

            # 5. Pack Results
            results.append({
                "label": name,
                "confidence": confidence,
                "liveness_ok": self.global_liveness_state.is_alive,
                "box": (top * scale, right * scale, bottom * scale, left * scale),
                "stats": {
                    "ear": avg_ear,
                    "blinks": self.global_liveness_state.total_blinks,
                    "yaw": yaw,
                    "pitch": pitch
                },
                "landmarks": coords # Optional: Remove if sending to UI is too slow
            })

        return results
