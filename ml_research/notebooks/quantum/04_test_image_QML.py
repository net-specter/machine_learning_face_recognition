import torch
import torch.nn as nn
import joblib
import os
import numpy as np
import pennylane as qml
import warnings
import cv2

from facenet_pytorch import InceptionResnetV1

# =========================================================
# 1. SILENCE WARNINGS
# =========================================================
warnings.filterwarnings("ignore")

# =========================================================
# 2. CONFIG
# =========================================================
IMAGE_PATH = "../../test_images/image.png"
OUTPUT_PATH = "../../saved_models"
DEVICE = torch.device("cpu")

N_QUBITS = 8
N_LAYERS = 3

# =========================================================
# 3. FACENET (PYTORCH ONLY)
# =========================================================
facenet = InceptionResnetV1(pretrained="vggface2").eval().to(DEVICE)

def extract_embedding(img_path):
    img = cv2.imread(img_path)
    if img is None:
        raise ValueError("Image not found")

    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = cv2.resize(img, (160, 160))
    img = img / 255.0

    img = torch.tensor(img).permute(2, 0, 1).unsqueeze(0).float().to(DEVICE)

    with torch.no_grad():
        emb = facenet(img)

    return emb.cpu().numpy()

# =========================================================
# 4. QUANTUM MODEL
# =========================================================
try:
    dev = qml.device("lightning.qubit", wires=N_QUBITS)
except Exception:
    dev = qml.device("default.qubit", wires=N_QUBITS)

@qml.qnode(dev, interface="torch", diff_method="parameter-shift")
def quantum_net(inputs, weights):
    qml.AngleEmbedding(inputs, wires=range(N_QUBITS), rotation="Y")
    qml.StronglyEntanglingLayers(weights, wires=range(N_QUBITS))
    return [qml.expval(qml.PauliZ(i)) for i in range(N_QUBITS)]

class HybridFaceClassifier(nn.Module):
    def __init__(self, num_classes):
        super().__init__()

        q_weight_shapes = {"weights": (N_LAYERS, N_QUBITS, 3)}
        self.quantum = qml.qnn.TorchLayer(quantum_net, q_weight_shapes)

        # match training architecture: larger classical head (128 -> 64)
        self.q_norm = nn.LayerNorm(N_QUBITS)

        self.classifier = nn.Sequential(
            nn.Linear(N_QUBITS, 128),
            nn.BatchNorm1d(128),
            nn.LeakyReLU(0.1),
            nn.Dropout(0.2),

            nn.Linear(128, 64),
            nn.BatchNorm1d(64),
            nn.LeakyReLU(0.1),
            nn.Dropout(0.2),

            nn.Linear(64, num_classes)
        )

    def forward(self, x):
        x = self.quantum(x)
        x = self.q_norm(x)
        return self.classifier(x)


# =========================================================
# 5. PREDICTION
# =========================================================
def predict_quantum(img_path):
    if not os.path.exists(img_path):
        print("❌ Image not found")
        return

    # Load assets
    scaler = joblib.load(f"{OUTPUT_PATH}/scaler_Q.pkl")
    le = joblib.load(f"{OUTPUT_PATH}/label_encoder_Q.pkl")
    labels_to_names = joblib.load(f"{OUTPUT_PATH}/labels_to_names.pkl")

    num_classes = len(le.classes_)
    model = HybridFaceClassifier(num_classes).to(DEVICE)
    model.load_state_dict(
        torch.load(f"{OUTPUT_PATH}/quantum_face_model.pth", map_location=DEVICE)
    )
    model.eval()

    # Extract embedding
    embedding = extract_embedding(img_path)

    # Preprocess
    embedding = scaler.transform(embedding)
    embedding = np.tanh(embedding[:, :N_QUBITS]) * np.pi
    x = torch.tensor(embedding, dtype=torch.float32).to(DEVICE)

    # Predict
    with torch.no_grad():
        logits = model(x)
        probs = torch.softmax(logits, dim=1)
        conf, idx = torch.max(probs, dim=1)

    pred_label = idx.item()
    name = labels_to_names.get(pred_label, "Unknown")


    print("\n" + "═" * 40)
    print("🔮 QUANTUM FACE PREDICTION")
    print("═" * 40)
    print(f"👤 Identity   : {name}")
    print(f"🎯 Confidence : {conf.item() * 100:.2f}%")
    print("═" * 40)

# =========================================================
if __name__ == "__main__":
    predict_quantum(IMAGE_PATH)
