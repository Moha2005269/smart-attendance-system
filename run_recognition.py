import cv2
import argparse
import time
import threading
import sys
import os
from src.recognizer.face_recognition_system import FaceRecognitionSystem

class VideoStream:
    """
    Threaded video stream reader to prevent I/O blocking.
    This increases FPS by overlapping frame capture with processing.
    """
    def __init__(self, src=0):
        self.stream = cv2.VideoCapture(src, cv2.CAP_DSHOW) # CAP_DSHOW for faster startup on Windows
        if not self.stream.isOpened():
             self.stream = cv2.VideoCapture(src)
             
        self.grabbed, self.frame = self.stream.read()
        self.stopped = False

    def start(self):
        threading.Thread(target=self.update, args=(), daemon=True).start()
        return self

    def update(self):
        while not self.stopped:
            if not self.grabbed:
                self.stop()
            else:
                (self.grabbed, self.frame) = self.stream.read()

    def read(self):
        return self.frame

    def stop(self):
        self.stopped = True
        self.stream.release()

def draw_hud(frame, results, fps):
    """
    Draws the Heads-Up Display (HUD) with debug info.
    """
    h, w = frame.shape[:2]
    
    # Draw FPS
    cv2.putText(frame, f"FPS: {fps:.1f}", (w - 120, 30), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    
    # Instructions
    cv2.putText(frame, "'Q' to Quit", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)

    for res in results:
        top, right, bottom, left = res["box"]
        label = res["label"]
        conf = res["confidence"]
        is_live = res["liveness_ok"]
        stats = res["stats"]

        # Color Logic
        if not is_live:
            color = (0, 0, 255) # Red (Possible Spoof/Static)
            status_text = "LIVENESS CHECK..."
        elif label == "Unknown":
            color = (0, 165, 255) # Orange
            status_text = "LIVE (Unknown)"
        else:
            color = (0, 255, 0) # Green
            status_text = "LIVE (Verified)"

        # 1. Bounding Box
        cv2.rectangle(frame, (left, top), (right, bottom), color, 2)

        # 2. Label Background & Text
        # Ensure label background doesn't go off screen
        text_str = f"{label} ({conf*100:.0f}%)"
        (text_w, text_h), _ = cv2.getTextSize(text_str, cv2.FONT_HERSHEY_DUPLEX, 0.6, 1)
        
        cv2.rectangle(frame, (left, bottom), (left + text_w + 10, bottom + 25), color, cv2.FILLED)
        cv2.putText(frame, text_str, (left + 5, bottom + 18), 
                    cv2.FONT_HERSHEY_DUPLEX, 0.6, (255, 255, 255), 1)

        # 3. Status Text (Above Box)
        cv2.putText(frame, status_text, (left, top - 10), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        
        # 4. Technical Debug Info (Bottom of screen)
        debug_info = (f"EAR: {stats['ear']:.2f} | Blinks: {stats['blinks']} | "
                      f"Yaw: {stats['yaw']:.1f} | Pitch: {stats['pitch']:.1f}")
        
        cv2.putText(frame, debug_info, (10, h - 20), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)

        # 5. Draw Eye Landmarks (for visual verification of EAR)
        # Eyes are indices 36-47 in the 68 point model
        if "landmarks" in res:
            for (x, y) in res["landmarks"][36:48]:
                cv2.circle(frame, (x, y), 1, (0, 255, 255), -1)

    return frame

def main():
    # Setup Argument Parser
    parser = argparse.ArgumentParser(description="Smart Attendance Recognition Runner")
    parser.add_argument("-e", "--encodings", default="models/encodings.pkl", help="Path to encodings.pkl")
    parser.add_argument("-p", "--predictor", default="models/shape_predictor_68_face_landmarks.dat", help="Path to dlib predictor")
    parser.add_argument("-c", "--camera", type=int, default=0, help="Camera Source ID")
    args = parser.parse_args()

    # Verify Paths before starting
    if not os.path.exists(args.predictor):
        print(f"[ERROR] Predictor not found at: {args.predictor}")
        print("Please download it from: http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2")
        return

    # Initialize Engine
    print("[INFO] Initializing Recognition Engine...")
    try:
        recognizer = FaceRecognitionSystem(model_path=args.encodings, predictor_path=args.predictor)
    except Exception as e:
        print(f"[CRITICAL ERROR] Could not start engine: {e}")
        return

    # Initialize Threaded Video
    print(f"[INFO] Starting Video Stream on Camera {args.camera}...")
    vs = VideoStream(src=args.camera).start()
    time.sleep(1.0) # Warmup

    fps_start = time.time()
    frame_count = 0
    fps = 0

    print("[INFO] System Ready. Press 'Q' to exit.")

    try:
        while True:
            frame = vs.read()
            if frame is None:
                print("[INFO] No frame received. Exiting...")
                break

            # --- CORE PROCESS ---
            results = recognizer.recognize_frame(frame)
            # --------------------

            # FPS Calculation
            frame_count += 1
            if frame_count % 10 == 0:
                fps_end = time.time()
                fps = 10 / (fps_end - fps_start)
                fps_start = fps_end

            # Visualization
            output_frame = draw_hud(frame, results, fps)
            cv2.imshow("Recognition View", output_frame)

            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                break

    except KeyboardInterrupt:
        print("[INFO] Stopping...")
    finally:
        vs.stop()
        cv2.destroyAllWindows()
        print("[INFO] Clean exit.")

if __name__ == "__main__":
    main()
