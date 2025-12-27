import face_recognition
import pickle
import os
import cv2

def force_encode():
    # 1. Setup paths
    dataset_path = "known_faces_data"
    encodings_path = "models/encodings.pkl"
    
    known_encodings = []
    known_names = []

    print(f"[DEBUG] Looking for images in: {os.path.abspath(dataset_path)}")

    # 2. Loop over the images in the folder
    for file_name in os.listdir(dataset_path):
        # Skip non-image files
        if not file_name.lower().endswith(('.jpg', '.jpeg', '.png')):
            continue

        image_path = os.path.join(dataset_path, file_name)
        name = os.path.splitext(file_name)[0]  # Extracts "Mhmad_hassn" from filename
        print(f"[PROCESSING] {name} ({file_name})...")

        # 3. Load image
        image = cv2.imread(image_path)
        if image is None:
            print(f"  [ERROR] Could not load image: {file_name}")
            continue

        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # 4. Detect faces
        boxes = face_recognition.face_locations(rgb, model="hog")
        
        if len(boxes) == 0:
            print(f"  [WARNING] NO FACE FOUND in {file_name}. Use a clearer photo.")
            continue
        
        if len(boxes) > 1:
            print(f"  [WARNING] Multiple faces found in {file_name}. Use a photo with only YOU.")
            continue

        # 5. Encode
        encodings = face_recognition.face_encodings(rgb, boxes)
        
        if len(encodings) > 0:
            known_encodings.append(encodings[0])
            known_names.append(name)
            print(f"  [SUCCESS] Encoded {name}.")

    # 6. Save to pickle
    if len(known_encodings) > 0:
        data = {"encodings": known_encodings, "names": known_names}
        with open(encodings_path, "wb") as f:
            f.write(pickle.dumps(data))
        print(f"\n[DONE] Saved {len(known_encodings)} encodings to {encodings_path}")
    else:
        print("\n[FAIL] No encodings were saved. Check your images.")

if __name__ == "__main__":
    force_encode()
