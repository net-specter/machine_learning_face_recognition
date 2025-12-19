import cv2
import numpy as np
import joblib
import mediapipe as mp
from deepface import DeepFace
import pennylane as qml
from pennylane import numpy as pnp
import os

# ================= CONFIGURATION =================
IMAGE_PATH = "../../test_images/image.png"
OUTPUT_PATH = "../../saved_models"
N_QUBITS = 8

# Load transformers and model (use the filenames produced by 01_data_prep_QML.py)
standardizer = joblib.load(os.path.join(OUTPUT_PATH, 'standardizer.pkl'))
pca = joblib.load(os.path.join(OUTPUT_PATH, 'pca.pkl'))
quantum_scaler = joblib.load(os.path.join(OUTPUT_PATH, 'quantum_scaler.pkl'))
labels_to_names = joblib.load(os.path.join(OUTPUT_PATH, 'labels_to_names.pkl'))
weights = joblib.load(os.path.join(OUTPUT_PATH, 'qml_weights.pkl'))

# MediaPipe face detector
mp_face_detection = mp.solutions.face_detection

# QML Device
dev = qml.device("lightning.qubit", wires=N_QUBITS)

# ================= QUANTUM CIRCUIT =================
def angle_encoding(x):
    for i in range(N_QUBITS):
        qml.RX(x[i], wires=i)

@qml.qnode(dev)
def vqc(weights, x):
    angle_encoding(x)
    qml.StronglyEntanglingLayers(weights, wires=range(N_QUBITS))
    return qml.expval(qml.PauliZ(0))

# ================= FEATURE EXTRACTION =================
def extract_dl_features(img_bgr):
    try:
        embedding = DeepFace.represent(
            img_path=img_bgr,
            model_name="VGG-Face",
            enforce_detection=False,
            detector_backend="skip"
        )
        return np.array(embedding[0]['embedding'])
    except:
        return None

# ================= FACE DETECTION & ALIGNMENT =================
def detect_face(image_bgr):
    with mp_face_detection.FaceDetection(
        model_selection=1, min_detection_confidence=0.7
    ) as face_detection:
        results = face_detection.process(cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB))
        if results.detections:
            det = results.detections[0].location_data.relative_bounding_box
            h, w, _ = image_bgr.shape
            xmin = max(0, int(det.xmin * w))
            ymin = max(0, int(det.ymin * h))
            xmax = min(w, int(det.width * w) + xmin)
            ymax = min(h, int(det.height * h) + ymin)
            if xmax > xmin and ymax > ymin:
                face = image_bgr[ymin:ymax, xmin:xmax]
                face_resized = cv2.resize(face, (224, 224))
                return face_resized
    return None

# ================= PREDICTION =================
def predict_image(image_path):
    img = cv2.imread(image_path)
    if img is None:
        print("❌ Could not read image.")
        return

    face = detect_face(img)
    if face is None:
        print("❌ No face detected.")
        return

    features = extract_dl_features(face)
    if features is None:
        print("❌ Feature extraction failed.")
        return

    # Preprocessing pipeline: standardizer -> PCA -> select first N_QUBITS -> quantum_scaler
    features = np.asarray(features).reshape(1, -1)
    # Validate input dimensionality for the saved standardizer
    if hasattr(standardizer, 'n_features_in_') and features.shape[1] != standardizer.n_features_in_:
        print(f"❌ Standardizer expects {standardizer.n_features_in_} features, but input has {features.shape[1]}.")
        return

    features_std = standardizer.transform(features)
    features_pca = pca.transform(features_std)

    # Ensure we have enough PCA components to select N_QUBITS
    if features_pca.shape[1] < N_QUBITS:
        print(f"❌ PCA produced {features_pca.shape[1]} components, but {N_QUBITS} required.")
        return

    reduced = features_pca[:, :N_QUBITS]
    features_q = quantum_scaler.transform(reduced)
    features_pnp = pnp.array(features_q[0], dtype=np.float64)

    # QML prediction
    pred_val = vqc(weights, features_pnp)
    pred_prob = (pred_val + 1) / 2.0
    pred_class = int(pred_prob >= 0.5)
    class_name = labels_to_names[pred_class]

    print(f"Predicted Class: {class_name} | Probability: {pred_prob:.4f}")

# ================= MAIN =================
if __name__ == "__main__":
    predict_image(IMAGE_PATH)
