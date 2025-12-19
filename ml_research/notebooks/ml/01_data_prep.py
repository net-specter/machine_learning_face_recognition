import os
import cv2
import joblib
import random
import numpy as np
import mediapipe as mp
import torch

from deepface import DeepFace
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import cosine_similarity
from tqdm import tqdm

# =====================================================
# CONFIGURATION
# =====================================================
DATASET_PATH = "../../datasets/raw"
OUTPUT_PATH = "../../saved_models"

ALIGNMENT_SIZE = (224, 224)
FRAME_SKIP_RATE = 3   # Reduced skip to get more data for the 80% train requirement
MODEL_NAME = "Facenet512" # Switch to Facenet512 for better ML accuracy
SEED = 42

random.seed(SEED)
np.random.seed(SEED)
os.makedirs(OUTPUT_PATH, exist_ok=True)

LABELS_TO_NAMES = {}

# MediaPipe Setup
mp_face_detection = mp.solutions.face_detection
mp_face_mesh = mp.solutions.face_mesh

# =====================================================
# UTILITY FUNCTIONS (Your Original Robust Pipeline)
# =====================================================

def is_good_face(face):
    h, w = face.shape[:2]
    if h < 80 or w < 80: return False
    gray = cv2.cvtColor(face, cv2.COLOR_BGR2GRAY)
    blur = cv2.Laplacian(gray, cv2.CV_64F).var()
    if blur < 70: return False # Adjusted slightly for variety
    if gray.std() < 15: return False
    return True

def align_face(img, landmarks):
    left_eye = landmarks[33:36].mean(axis=0)
    right_eye = landmarks[263:266].mean(axis=0)
    dy = float(right_eye[1] - left_eye[1])
    dx = float(right_eye[0] - left_eye[0])
    angle = np.degrees(np.arctan2(dy, dx))
    center = (float((left_eye[0] + right_eye[0]) / 2.0), float((left_eye[1] + right_eye[1]) / 2.0))
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    return cv2.warpAffine(img, M, (img.shape[1], img.shape[0]), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)

def apply_face_mask(face):
    h, w = face.shape[:2]
    mask = np.zeros((h, w), dtype=np.uint8)
    cv2.ellipse(mask, (w // 2, h // 2), (int(w * 0.45), int(h * 0.55)), 0, 0, 360, 255, -1)
    return cv2.bitwise_and(face, face, mask=mask)

def normalize_lighting(face):
    ycrcb = cv2.cvtColor(face, cv2.COLOR_BGR2YCrCb)
    y, cr, cb = cv2.split(ycrcb)
    y = cv2.equalizeHist(y)
    return cv2.cvtColor(cv2.merge([y, cr, cb]), cv2.COLOR_YCrCb2BGR)

def augment_image(face):
    img = face.copy()
    h, w = img.shape[:2]
    if random.random() < 0.4:
        img = np.clip(img * random.uniform(0.8, 1.2), 0, 255).astype(np.uint8)
    if random.random() < 0.3:
        M = cv2.getRotationMatrix2D((w // 2, h // 2), random.uniform(-5, 5), 1)
        img = cv2.warpAffine(img, M, (w, h), borderMode=cv2.BORDER_REFLECT)
    return img

# =====================================================
# MAIN PIPELINE
# =====================================================
def prepare_data():
    print(f"🔹 Initializing DeepFace with {MODEL_NAME}...")
    DeepFace.build_model(MODEL_NAME)

    X, y = [], []
    label_id = 0

    with mp_face_detection.FaceDetection(1, 0.7) as detector, \
         mp_face_mesh.FaceMesh(static_image_mode=True) as mesh:

        persons = sorted(os.listdir(DATASET_PATH))
        for person in persons:
            person_path = os.path.join(DATASET_PATH, person)
            if not os.path.isdir(person_path): continue

            LABELS_TO_NAMES[label_id] = person
            print(f"Processing {person}...")

            images = sorted(os.listdir(person_path))
            for i in tqdm(range(0, len(images), FRAME_SKIP_RATE)):
                img = cv2.imread(os.path.join(person_path, images[i]))
                if img is None: continue

                rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                detections = detector.process(rgb)
                if not detections.detections: continue

                # Bounding Box
                box = detections.detections[0].location_data.relative_bounding_box
                h, w, _ = img.shape
                x1, y1, x2, y2 = max(0, int(box.xmin * w)), max(0, int(box.ymin * h)), min(w, int((box.xmin + box.width) * w)), min(h, int((box.ymin + box.height) * h))
                
                face = img[y1:y2, x1:x2]
                if face.size == 0: continue

                # Mesh & Alignment
                mesh_res = mesh.process(cv2.cvtColor(face, cv2.COLOR_BGR2RGB))
                if not mesh_res.multi_face_landmarks: continue
                
                landmarks = np.array([[int(l.x * face.shape[1]), int(l.y * face.shape[0])] for l in mesh_res.multi_face_landmarks[0].landmark])
                
                face = align_face(face, landmarks)
                face = apply_face_mask(face)
                face = normalize_lighting(face)
                face = cv2.resize(face, ALIGNMENT_SIZE)

                if not is_good_face(face): continue

                # Augmentation & Embedding
                samples = [face]
                if random.random() < 0.6: # Increased augmentation for ML stability
                    samples.append(augment_image(face))

                for s in samples:
                    try:
                        rep = DeepFace.represent(img_path=s, model_name=MODEL_NAME, enforce_detection=False, detector_backend="skip")
                        feat = np.asarray(rep[0]["embedding"], dtype=np.float32)
                        
                        # Similarity check (prevent duplicate redundant data)
                        if len(X) > 0 and label_id == y[-1]:
                            sim = cosine_similarity([feat], [X[-1]])[0][0]
                            if sim > 0.98: continue

                        X.append(feat)
                        y.append(label_id)
                    except: continue

            label_id += 1

    X, y = np.asarray(X), np.asarray(y)

    # =====================================================
    # SPLIT: 80% Train, 15% Val, 5% Test
    # =====================================================
    # 1. Split 80% Train, 20% Temporary
    X_train, X_temp, y_train, y_temp = train_test_split(X, y, test_size=0.2, stratify=y, random_state=SEED)

    # 2. Split 20% Temporary into 75% Val (15% total) and 25% Test (5% total)
    X_val, X_test, y_val, y_test = train_test_split(X_temp, y_temp, test_size=0.25, stratify=y_temp, random_state=SEED)

    # Standardization (No PCA to prevent underfitting)
    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_val = scaler.transform(X_val)
    X_test = scaler.transform(X_test)

    # Save
    joblib.dump((X_train, y_train), f"{OUTPUT_PATH}/train_data.pkl")
    joblib.dump((X_val, y_val), f"{OUTPUT_PATH}/val_data.pkl")
    joblib.dump((X_test, y_test), f"{OUTPUT_PATH}/test_data.pkl")
    joblib.dump(scaler, f"{OUTPUT_PATH}/scaler.pkl")
    joblib.dump(LABELS_TO_NAMES, f"{OUTPUT_PATH}/labels_to_names.pkl")

    print(f"\n✅ DATA PREPARED. Train: {len(X_train)} | Val: {len(X_val)} | Test: {len(X_test)}")

if __name__ == "__main__":
    prepare_data()