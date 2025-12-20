import os
import cv2
import joblib
import random
import numpy as np
import mediapipe as mp
from deepface import DeepFace
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.decomposition import PCA, FastICA # <--- QICA requirement
from sklearn.metrics.pairwise import cosine_similarity
from tqdm import tqdm
import warnings

warnings.filterwarnings("ignore")

# =====================================================
# CONFIGURATION (8 Qubits = 4 PCA + 4 ICA)
# =====================================================
DATASET_PATH = "../../datasets/raw"
OUTPUT_PATH = "../../saved_models"

IMG_SIZE = (224, 224)
MAX_SAMPLES_PER_PERSON = 100 # Reduced for higher quality focus
MODEL_NAME = "Facenet512"
N_QUBITS = 8 
SEED = 42

random.seed(SEED)
np.random.seed(SEED)
os.makedirs(OUTPUT_PATH, exist_ok=True)

LABELS_TO_NAMES = {}

# =====================================================
# FACE QUALITY & ALIGNMENT (From your pipeline)
# =====================================================
def is_good_face(face):
    h, w = face.shape[:2]
    if h < 100 or w < 100: return False
    gray = cv2.cvtColor(face, cv2.COLOR_BGR2GRAY)
    if cv2.Laplacian(gray, cv2.CV_64F).var() < 70: return False
    if gray.std() < 18: return False
    return True

def align_face(face, landmarks):
    left_eye = np.mean(landmarks[33:36], axis=0)
    right_eye = np.mean(landmarks[263:266], axis=0)
    dy, dx = right_eye[1] - left_eye[1], right_eye[0] - left_eye[0]
    angle = np.degrees(np.arctan2(dy, dx))
    cx, cy = (left_eye[0] + right_eye[0]) / 2, (left_eye[1] + right_eye[1]) / 2
    M = cv2.getRotationMatrix2D((cx, cy), angle, 1.0)
    return cv2.warpAffine(face, M, (face.shape[1], face.shape[0]), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)

# =====================================================
# MAIN PIPELINE (Dual Stream: PCA + ICA)
# =====================================================
def prepare_quantum_data():
    print(f"🔹 Initializing Dual-Stream Pipeline (PCA+ICA)")
    DeepFace.build_model(MODEL_NAME)

    X, y = [], []
    label_id = 0

    with mp.solutions.face_detection.FaceDetection(model_selection=1, min_detection_confidence=0.75) as face_detector, \
         mp.solutions.face_mesh.FaceMesh(static_image_mode=True) as face_mesh:

        persons = sorted(os.listdir(DATASET_PATH))
        for person in persons:
            person_path = os.path.join(DATASET_PATH, person)
            if not os.path.isdir(person_path): continue

            print(f"\n📁 Processing: {person}")
            LABELS_TO_NAMES[label_id] = person

            embeddings_buffer = []
            count = 0
            
            # Remove temporal redundancy by taking 1 frame every 5
            images = sorted(os.listdir(person_path))[::5] 
            random.shuffle(images)

            for img_name in tqdm(images):
                if count >= MAX_SAMPLES_PER_PERSON: break
                
                img = cv2.imread(os.path.join(person_path, img_name))
                if img is None: continue

                rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                det = face_detector.process(rgb)
                if not det.detections: continue

                # Bounding Box & Crop
                box = det.detections[0].location_data.relative_bounding_box
                h, w, _ = img.shape
                x1, y1 = max(0, int(box.xmin * w)), max(0, int(box.ymin * h))
                x2, y2 = min(w, int((box.xmin + box.width) * w)), min(h, int((box.ymin + box.height) * h))
                face = img[y1:y2, x1:x2]
                if face.size == 0: continue

                # Landmarks & Alignment
                mesh_res = face_mesh.process(cv2.cvtColor(face, cv2.COLOR_BGR2RGB))
                if not mesh_res.multi_face_landmarks: continue
                lms = np.array([[int(l.x * face.shape[1]), int(l.y * face.shape[0])] for l in mesh_res.multi_face_landmarks[0].landmark])
                
                face = align_face(face, lms)
                face = cv2.resize(face, IMG_SIZE)
                if not is_good_face(face): continue

                try:
                    rep = DeepFace.represent(img_path=cv2.cvtColor(face, cv2.COLOR_BGR2RGB), model_name=MODEL_NAME, enforce_detection=False, detector_backend="skip")
                    emb = np.asarray(rep[0]["embedding"], dtype=np.float32)

                    # --- REDUNDANCY FILTER (Cosine Similarity) ---
                    if embeddings_buffer:
                        if np.max(cosine_similarity([emb], embeddings_buffer)[0]) > 0.98:
                            continue

                    X.append(emb)
                    y.append(label_id)
                    embeddings_buffer.append(emb)
                    embeddings_buffer = embeddings_buffer[-20:] # Keep last 20 for similarity comparison
                    count += 1
                except: continue
            label_id += 1

    X, y = np.asarray(X), np.asarray(y)

    # =====================================================
    # DATA SPLIT (80/15/5)
    # =====================================================
    X_train, X_tmp, y_train, y_tmp = train_test_split(X, y, test_size=0.2, stratify=y, random_state=SEED)
    X_val, X_test, y_val, y_test = train_test_split(X_tmp, y_tmp, test_size=0.25, stratify=y_tmp, random_state=SEED)

    # =====================================================
    # THE PAPER PIPELINE: PCA (Global) + ICA (Local)
    # =====================================================
    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_val, X_test = scaler.transform(X_val), scaler.transform(X_test)

    # Stream 1: PCA for Global Eigenfaces (4 Qubits)
    pca = PCA(n_components=4, random_state=SEED)
    X_tr_pca = pca.fit_transform(X_train)
    X_val_pca, X_test_pca = pca.transform(X_val), pca.transform(X_test)

    # Stream 2: ICA for Independent Local Features (4 Qubits)
    ica = FastICA(n_components=4, random_state=SEED, max_iter=1000)
    X_tr_ica = ica.fit_transform(X_train)
    X_val_ica, X_test_ica = ica.transform(X_val), ica.transform(X_test)

    # --- FUSION: Combine into 8 features ---
    X_train_final = np.hstack((X_tr_pca, X_tr_ica))
    X_val_final = np.hstack((X_val_pca, X_val_ica))
    X_test_final = np.hstack((X_test_pca, X_test_ica))

    # --- QUANTUM SCALING [0, PI] ---
    q_scaler = MinMaxScaler(feature_range=(0, np.pi))
    X_train_q = q_scaler.fit_transform(X_train_final)
    X_val_q = q_scaler.transform(X_val_final)
    X_test_q = q_scaler.transform(X_test_final)

    # =====================================================
    # SAVE OUTPUTS
    # =====================================================
    joblib.dump(X_train_q, f"{OUTPUT_PATH}/X_train_Q.pkl")
    joblib.dump(y_train, f"{OUTPUT_PATH}/Y_train_Q.pkl")
    joblib.dump(X_val_q, f"{OUTPUT_PATH}/X_val_Q.pkl")
    joblib.dump(y_val, f"{OUTPUT_PATH}/Y_val_Q.pkl")
    joblib.dump(X_test_q, f"{OUTPUT_PATH}/X_test_Q.pkl")
    joblib.dump(y_test, f"{OUTPUT_PATH}/Y_test_Q.pkl")

    # Meta-assets for inference
    joblib.dump(scaler, f"{OUTPUT_PATH}/standardizer.pkl")
    joblib.dump(pca, f"{OUTPUT_PATH}/pca_model.pkl")
    joblib.dump(ica, f"{OUTPUT_PATH}/ica_model.pkl")
    joblib.dump(q_scaler, f"{OUTPUT_PATH}/quantum_scaler.pkl")
    joblib.dump(LABELS_TO_NAMES, f"{OUTPUT_PATH}/labels_to_names.pkl")

    print(f"\n✅ Dual-Stream Preprocessing Complete.")
    print(f"Total Unique Samples: {len(X)}")
    print(f"Features: 4 Global (PCA) + 4 Local (ICA) = 8 Qubits")

if __name__ == "__main__":
    prepare_quantum_data()