import os
import cv2
import joblib
import random
import numpy as np
import mediapipe as mp
from deepface import DeepFace
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.metrics.pairwise import cosine_similarity
from tqdm import tqdm

# =====================================================
# CONFIGURATION
# =====================================================
DATASET_PATH = "../../datasets/raw"
OUTPUT_PATH = "../../saved_models"

IMG_SIZE = (224, 224)
MAX_SAMPLES_PER_PERSON = 120
MODEL_NAME = "Facenet512"
N_QUBITS = 8
SEED = 42

random.seed(SEED)
np.random.seed(SEED)
os.makedirs(OUTPUT_PATH, exist_ok=True)

LABELS_TO_NAMES = {}

# =====================================================
# FACE QUALITY CHECK
# =====================================================
def is_good_face(face):
    h, w = face.shape[:2]
    if h < 100 or w < 100:
        return False

    gray = cv2.cvtColor(face, cv2.COLOR_BGR2GRAY)

    # Blur check
    if cv2.Laplacian(gray, cv2.CV_64F).var() < 80:
        return False

    # Contrast check
    if gray.std() < 20:
        return False

    return True

# =====================================================
# FACE ALIGNMENT (EYE-BASED)
# =====================================================
def align_face(face, landmarks):
    left_eye = np.mean(landmarks[33:36], axis=0)
    right_eye = np.mean(landmarks[263:266], axis=0)

    dy = right_eye[1] - left_eye[1]
    dx = right_eye[0] - left_eye[0]
    angle = np.degrees(np.arctan2(dy, dx))

    cx = (left_eye[0] + right_eye[0]) / 2.0
    cy = (left_eye[1] + right_eye[1]) / 2.0
    center = (float(cx), float(cy))

    M = cv2.getRotationMatrix2D(center, angle, 1.0)

    return cv2.warpAffine(
        face,
        M,
        (face.shape[1], face.shape[0]),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_REFLECT
    )

# =====================================================
# SAFE AUGMENTATION
# =====================================================
def augment_face(face):
    img = face.copy()

    if random.random() < 0.3:
        img = cv2.flip(img, 1)

    if random.random() < 0.3:
        alpha = random.uniform(0.9, 1.1)
        img = np.clip(img * alpha, 0, 255).astype(np.uint8)

    return img

# =====================================================
# MAIN PIPELINE
# =====================================================
def prepare_quantum_data():
    print(f"🔹 Loading DeepFace model: {MODEL_NAME}")
    DeepFace.build_model(MODEL_NAME)

    X, y = [], []
    label_id = 0

    with mp.solutions.face_detection.FaceDetection(
        model_selection=1, min_detection_confidence=0.75
    ) as face_detector, mp.solutions.face_mesh.FaceMesh(
        static_image_mode=True
    ) as face_mesh:

        persons = sorted(os.listdir(DATASET_PATH))
        if not persons:
            print("❌ Dataset folder is empty")
            return

        for person in persons:
            person_path = os.path.join(DATASET_PATH, person)
            if not os.path.isdir(person_path):
                continue

            LABELS_TO_NAMES[label_id] = person
            print(f"\n📁 Processing {person}")

            embeddings_buffer = []
            count = 0

            images = os.listdir(person_path)
            random.shuffle(images)

            for img_name in tqdm(images):
                if count >= MAX_SAMPLES_PER_PERSON:
                    break

                img = cv2.imread(os.path.join(person_path, img_name))
                if img is None:
                    continue

                rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                det = face_detector.process(rgb)

                if not det.detections:
                    continue

                box = det.detections[0].location_data.relative_bounding_box
                h, w, _ = img.shape

                x1 = max(0, int(box.xmin * w))
                y1 = max(0, int(box.ymin * h))
                x2 = min(w, int((box.xmin + box.width) * w))
                y2 = min(h, int((box.ymin + box.height) * h))

                face = img[y1:y2, x1:x2]
                if face.size == 0:
                    continue

                mesh_res = face_mesh.process(cv2.cvtColor(face, cv2.COLOR_BGR2RGB))
                if not mesh_res.multi_face_landmarks:
                    continue

                landmarks = np.array([
                    [int(l.x * face.shape[1]), int(l.y * face.shape[0])]
                    for l in mesh_res.multi_face_landmarks[0].landmark
                ])

                face = align_face(face, landmarks)
                face = cv2.resize(face, IMG_SIZE)

                if not is_good_face(face):
                    continue

                try:
                    rep = DeepFace.represent(
                        img_path=cv2.cvtColor(face, cv2.COLOR_BGR2RGB),
                        model_name=MODEL_NAME,
                        enforce_detection=False,
                        detector_backend="skip"
                    )

                    emb = np.asarray(rep[0]["embedding"], dtype=np.float32)

                    if embeddings_buffer:
                        sims = cosine_similarity([emb], embeddings_buffer)[0]
                        if np.max(sims) > 0.985:
                            continue

                    X.append(emb)
                    y.append(label_id)
                    embeddings_buffer.append(emb)
                    embeddings_buffer = embeddings_buffer[-15:]
                    count += 1

                    # Augmentation
                    if count < MAX_SAMPLES_PER_PERSON and random.random() < 0.4:
                        aug = augment_face(face)
                        rep2 = DeepFace.represent(
                            img_path=cv2.cvtColor(aug, cv2.COLOR_BGR2RGB),
                            model_name=MODEL_NAME,
                            enforce_detection=False,
                            detector_backend="skip"
                        )

                        emb2 = np.asarray(rep2[0]["embedding"], dtype=np.float32)
                        sims = cosine_similarity([emb2], embeddings_buffer)[0]
                        if np.max(sims) < 0.985:
                            X.append(emb2)
                            y.append(label_id)
                            embeddings_buffer.append(emb2)
                            count += 1

                except Exception:
                    continue

            label_id += 1

    # =====================================================
    # DATA ANALYSIS
    # =====================================================
    X = np.asarray(X)
    y = np.asarray(y)

    unique, counts = np.unique(y, return_counts=True)
    print("\n📊 Samples per class:")
    for u, c in zip(unique, counts):
        print(f"{LABELS_TO_NAMES[u]}: {c}")

    # =====================================================
    # TRAIN / VAL / TEST SPLIT
    # =====================================================
    X_train, X_tmp, y_train, y_tmp = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=SEED
    )

    X_val, X_test, y_val, y_test = train_test_split(
        X_tmp, y_tmp, test_size=0.25, stratify=y_tmp, random_state=SEED
    )

    # =====================================================
    # SCALING + PCA (QUANTUM READY)
    # =====================================================
    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_val = scaler.transform(X_val)
    X_test = scaler.transform(X_test)

    pca = PCA(n_components=N_QUBITS)
    X_train = pca.fit_transform(X_train)
    X_val = pca.transform(X_val)
    X_test = pca.transform(X_test)

    print("\n🧠 PCA explained variance:",
          np.sum(pca.explained_variance_ratio_))

    X_train = np.tanh(X_train) * np.pi
    X_val = np.tanh(X_val) * np.pi
    X_test = np.tanh(X_test) * np.pi

    # =====================================================
    # SAVE OUTPUTS
    # =====================================================
    joblib.dump(X_train, f"{OUTPUT_PATH}/X_train_Q.pkl")
    joblib.dump(y_train, f"{OUTPUT_PATH}/Y_train_Q.pkl")
    joblib.dump(X_val, f"{OUTPUT_PATH}/X_val_Q.pkl")
    joblib.dump(y_val, f"{OUTPUT_PATH}/Y_val_Q.pkl")
    joblib.dump(X_test, f"{OUTPUT_PATH}/test_data.pkl")
    joblib.dump(y_test, f"{OUTPUT_PATH}/test_labels_raw.pkl")

    joblib.dump(scaler, f"{OUTPUT_PATH}/scaler_Q.pkl")
    joblib.dump(pca, f"{OUTPUT_PATH}/pca_Q.pkl")
    joblib.dump(pca.explained_variance_ratio_,
                f"{OUTPUT_PATH}/pca_variance.pkl")
    joblib.dump(LABELS_TO_NAMES,
                f"{OUTPUT_PATH}/labels_to_names.pkl")

    print("\n✅ Dataset prepared successfully (Quantum-ready)")

# =====================================================
# ENTRY POINT
# =====================================================
if __name__ == "__main__":
    prepare_quantum_data()
