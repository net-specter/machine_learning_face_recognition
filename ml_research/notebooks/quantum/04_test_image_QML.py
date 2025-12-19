import torch
import torch.nn as nn
import joblib
import os
import numpy as np
import pennylane as qml
import warnings
from deepface import DeepFace

# 1. SILENCE WARNINGS
warnings.filterwarnings("ignore")

# =========================================================
# 2. CONFIGURATION & QUANTUM ARCHITECTURE
# =========================================================
IMAGE_PATH = "../../test_images/image.png"
OUTPUT_PATH = "../../saved_models"
MODEL_NAME = "Facenet512"
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Must match training
N_QUBITS = 8
N_LAYERS = 3

# Define Quantum Circuit
dev = qml.device("lightning.qubit", wires=N_QUBITS)

@qml.qnode(dev, interface="torch")
def quantum_net(inputs, weights):
    qml.AngleEmbedding(inputs, wires=range(N_QUBITS), rotation='Y')
    qml.StronglyEntanglingLayers(weights, wires=range(N_QUBITS))
    return [qml.expval(qml.PauliZ(i)) for i in range(N_QUBITS)]

class HybridFaceClassifier(nn.Module):
    def __init__(self, num_classes):
        super().__init__()
        q_weight_shapes = {"weights": (N_LAYERS, N_QUBITS, 3)}
        self.quantum = qml.qnn.TorchLayer(quantum_net, q_weight_shapes)  # matches saved "quantum"
        self.q_norm = nn.LayerNorm(N_QUBITS)
        self.classifier = nn.Sequential(  # matches saved "classifier"
            nn.Linear(N_QUBITS, 64),
            nn.BatchNorm1d(64),
            nn.LeakyReLU(0.1),
            nn.Dropout(0.3),
            nn.Linear(64, 32),
            nn.BatchNorm1d(32),
            nn.LeakyReLU(0.1),
            nn.Linear(32, num_classes)
        )

    def forward(self, x):
        x = self.quantum(x)
        x = self.q_norm(x)
        return self.classifier(x)



# =========================================================
# 3. PREDICTION FUNCTION
# =========================================================
def predict_quantum(img_path):
    if not os.path.exists(img_path):
        print(f"❌ File not found: {img_path}")
        return

    # Load preprocessing and model
    try:
        scaler = joblib.load(f"{OUTPUT_PATH}/scaler_Q.pkl")
        pca = joblib.load(f"{OUTPUT_PATH}/pca_Q.pkl")
        le = joblib.load(f"{OUTPUT_PATH}/label_encoder_Q.pkl")
        labels_to_names = joblib.load(f"{OUTPUT_PATH}/labels_to_names.pkl")
        num_classes = len(le.classes_)

        # Build model with correct output layer
        model = HybridFaceClassifier(num_classes)
        model = model.to(DEVICE)
        model.load_state_dict(torch.load(f"{OUTPUT_PATH}/quantum_face_model.pth", map_location=DEVICE))
        model.eval()
    except Exception as e:
        print(f"❌ Error loading assets: {e}")
        return

    # Extract embedding
    try:
        embedding_list = DeepFace.represent(img_path=img_path, model_name=MODEL_NAME, detector_backend="opencv", enforce_detection=True)
        if len(embedding_list) == 0:
            print("❌ No face detected.")
            return
        embedding = np.array(embedding_list[0]["embedding"]).reshape(1, -1)
    except Exception as e:
        print(f"❌ Error extracting embedding: {e}")
        return

    # Preprocess: scale, PCA, quantum range
    feat_scaled = scaler.transform(embedding)
    feat_reduced = pca.transform(feat_scaled)
    feat_quantum = np.tanh(feat_reduced) * np.pi
    feat_tensor = torch.tensor(feat_quantum, dtype=torch.float32).to(DEVICE)

    # Inference
    with torch.no_grad():
        output = model(feat_tensor)
        probs = torch.softmax(output, dim=1)
        conf, pred_idx = torch.max(probs, dim=1)
        pred_idx = pred_idx.item()
        conf = conf.item()

        name = labels_to_names.get(pred_idx, "Unknown")

        # Print results
        print("\n" + "═"*40)
        print(f"🔮 QUANTUM PREDICTION RESULT")
        print("—"*40)
        if conf > 0.70:
            print(f"👤 IDENTIFIED     : {name}")
        else:
            print(f"👤 IDENTIFIED     : Unknown (Likely {name})")
        print(f"🎯 QUANTUM CONFIDENCE : {conf*100:.2f}%")
        if conf > 0.85:
            print("✅ STATUS         : HIGHLY RELIABLE")
        else:
            print("⚠️ STATUS         : LOW CONFIDENCE")
        print("\n" + "═"*40)

if __name__ == "__main__":
    predict_quantum(IMAGE_PATH)
