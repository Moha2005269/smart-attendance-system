import os
import urllib.request
import bz2
import shutil

def create_structure():
    # 1. Create Directories
    folders = [
        "src", 
        "src/recognizer", 
        "src/encoder", 
        "src/utils",
        "models", 
        "known_faces_data",
        "database",
        "attendance_records"
    ]
    
    print("[1/3] Creating directory structure...")
    for folder in folders:
        os.makedirs(folder, exist_ok=True)
        # Create __init__.py to make imports work
        init_path = os.path.join(folder, "__init__.py")
        if not os.path.exists(init_path) and "data" not in folder and "models" not in folder:
            with open(init_path, "w") as f:
                pass
    print("      Done.")

def download_dlib_model():
    # 2. Download and Extract Model
    model_url = "http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2"
    file_name = "shape_predictor_68_face_landmarks.dat.bz2"
    output_path = "models/shape_predictor_68_face_landmarks.dat"

    if os.path.exists(output_path):
        print(f"[2/3] Model found at {output_path}. Skipping download.")
        return

    print(f"[2/3] Downloading dlib model (this may take a minute)...")
    try:
        # Download
        urllib.request.urlretrieve(model_url, file_name)
        
        # Extract
        print("      Extracting...")
        with bz2.BZ2File(file_name) as fr, open(output_path, "wb") as fw:
            shutil.copyfileobj(fr, fw)
            
        # Cleanup
        os.remove(file_name)
        print("      Done.")
    except Exception as e:
        print(f"\n[ERROR] Failed to download model: {e}")
        print(f"Please manually download '{model_url}'")
        print(f"Extract it and place 'shape_predictor_68_face_landmarks.dat' in the 'models' folder.\n")

def check_requirements():
    print("[3/3] Checking critical libraries...")
    try:
        import dlib
        import cv2
        import face_recognition
        import numpy
        print("      All libraries (dlib, cv2, face_recognition, numpy) are installed!")
    except ImportError as e:
        print(f"      [WARNING] Missing library: {e}")
        print("      Run: pip install opencv-python dlib face-recognition numpy")

if __name__ == "__main__":
    create_structure()
    download_dlib_model()
    check_requirements()
    print("\n[READY] Setup complete. You can now run 'run_recognition.py'.")
