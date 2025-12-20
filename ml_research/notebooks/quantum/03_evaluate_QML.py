import torch
import torch.nn as nn
import pennylane as qml
import joblib
import os
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from tqdm import tqdm

# =========================================================
# 1. CONFIGURATION & ARCHITECTURE (must match training)
# =========================================================
OUTPUT_PATH = "../../saved_models"
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

N_QUBITS = 8
N_LAYERS = 3

# Quantum device setup
dev = qml.device("lightning.qubit", wires=N_QUBITS)

@qml.qnode(dev, interface="torch", diff_method="parameter-shift")
def quantum_net(inputs, weights):
    # Match training embedding
    qml.AngleEmbedding(inputs, wires=range(N_QUBITS), rotation="Y")
    qml.StronglyEntanglingLayers(weights, wires=range(N_QUBITS))
    return [qml.expval(qml.PauliZ(i)) for i in range(N_QUBITS)]

# Hybrid model must match training architecture
class HybridFaceClassifier(nn.Module):
    def __init__(self, num_classes):
        super().__init__()
        q_weight_shapes = {"weights": (N_LAYERS, N_QUBITS, 3)}
        self.quantum = qml.qnn.TorchLayer(quantum_net, q_weight_shapes)
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
# 2. EVALUATION FUNCTION
# =========================================================
def evaluate():
    print(f"🚀 Starting Quantum Model Evaluation on {DEVICE}...")

    # ---- Load test data and assets ----
    try:
        X_test = joblib.load(f"{OUTPUT_PATH}/test_data.pkl")
        y_test_raw = joblib.load(f"{OUTPUT_PATH}/test_labels_raw.pkl")
        le = joblib.load(f"{OUTPUT_PATH}/label_encoder_Q.pkl")
        labels_to_names = joblib.load(f"{OUTPUT_PATH}/labels_to_names.pkl")
    except Exception as e:
        print(f"❌ Missing files. Run prep & training first: {e}")
        return

    # Encode labels and get class names
    y_test = np.array(le.transform(y_test_raw))
    class_names = [labels_to_names[i] for i in sorted(labels_to_names.keys())]
    num_classes = len(class_names)

    # ---- Initialize & load model ----
    model = HybridFaceClassifier(num_classes).to(DEVICE)
    model.load_state_dict(torch.load(f"{OUTPUT_PATH}/quantum_face_model.pth", map_location=DEVICE))
    model.eval()

    # ---- Batch inference ----
    X_test_tensor = torch.tensor(X_test, dtype=torch.float32).to(DEVICE)
    all_preds = []

    batch_size = 16
    print(f"✨ Processing {len(X_test)} samples through Quantum Circuit...")
    with torch.no_grad():
        for i in tqdm(range(0, len(X_test_tensor), batch_size), desc="Quantum Inference"):
            batch = X_test_tensor[i:i+batch_size]
            outputs = model(batch)
            preds = torch.argmax(outputs, dim=1)
            all_preds.extend(preds.cpu().numpy())

    y_pred = np.array(all_preds)
    acc = accuracy_score(y_test, y_pred)

    # ---- Results ----
    print("\n" + "="*50)
    print(f"🏆 FINAL QUANTUM SYSTEM ACCURACY: {acc*100:.2f}%")
    print("="*50)
    print("\n📄 Classification Report:")
    print(classification_report(y_test, y_pred, target_names=class_names))

    # ---- Confusion Matrix ----
    cm = confusion_matrix(y_test, y_pred)
    plt.figure(figsize=(10, 8))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Purples',
                xticklabels=class_names, yticklabels=class_names)
    plt.title(f"Hybrid Quantum Face Recognition\nTest Accuracy: {acc*100:.2f}%")
    plt.ylabel("Actual Person")
    plt.xlabel("Predicted Person")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(f"{OUTPUT_PATH}/evaluation_results.png")
    print(f"✅ Confusion matrix saved: {OUTPUT_PATH}/evaluation_results.png")
    plt.show()

if __name__ == "__main__":
    evaluate()
