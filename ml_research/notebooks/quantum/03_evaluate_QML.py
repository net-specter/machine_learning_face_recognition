import torch
import torch.nn as nn
import pennylane as qml
import joblib
import os
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
from tqdm import tqdm
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score

warnings.filterwarnings("ignore")

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
OUTPUT_PATH = "../../saved_models"
N_QUBITS = 8
N_LAYERS = 4 

# =========================================================
# ARCHITECTURE (MUST MATCH TRAINING EXACTLY)
# =========================================================
dev = qml.device("lightning.qubit", wires=N_QUBITS)

@qml.qnode(dev, interface="torch", diff_method="adjoint")
def paper_quantum_net(inputs, weights):
    for i in range(N_LAYERS):
        qml.AngleEmbedding(inputs[:, :4], wires=range(0, 4), rotation="Y")
        qml.AngleEmbedding(inputs[:, 4:], wires=range(4, 8), rotation="X")
        qml.StronglyEntanglingLayers(weights[i:i+1], wires=range(N_QUBITS))
    return [qml.expval(qml.PauliZ(i)) for i in range(N_QUBITS)]

class PaperHybridClassifier(nn.Module):
    def __init__(self, num_classes):
        super().__init__()
        q_weight_shapes = {"weights": (N_LAYERS, N_QUBITS, 3)}
        self.quantum = qml.qnn.TorchLayer(paper_quantum_net, q_weight_shapes)
        
        # 🔥 THE FIX: Added Dropout(0.3) at index 3 to match training
        self.classifier = nn.Sequential(
            nn.Linear(N_QUBITS, 64),      # 0
            nn.BatchNorm1d(64),           # 1
            nn.ReLU(),                    # 2
            nn.Dropout(0.3),              # 3 <--- THIS WAS MISSING
            nn.Linear(64, num_classes)    # 4
        )
    def forward(self, x):
        return self.classifier(self.quantum(x))

def evaluate():
    print(f"🚀 Initializing Robust Paper-Style Evaluation on {DEVICE}...")

    X_test = joblib.load(f"{OUTPUT_PATH}/X_test_Q.pkl")
    y_test_raw = joblib.load(f"{OUTPUT_PATH}/Y_test_Q.pkl")
    le = joblib.load(f"{OUTPUT_PATH}/label_encoder.pkl")
    labels_to_names = joblib.load(f"{OUTPUT_PATH}/labels_to_names.pkl")

    y_test_clean = le.transform(y_test_raw)
    class_names = [str(labels_to_names[idx]) for idx in le.classes_]
    num_classes = len(class_names)

    model = PaperHybridClassifier(num_classes).to(DEVICE)
    model.load_state_dict(torch.load(f"{OUTPUT_PATH}/hybrid_qml_model.pth", map_location=DEVICE))
    model.eval()

    all_preds = []
    X_test_tensor = torch.Tensor(X_test).to(DEVICE)
    
    with torch.no_grad():
        for i in tqdm(range(0, len(X_test_tensor), 1), desc="Quantum Inference"):
            batch_x = X_test_tensor[i : i + 1]
            outputs = model(batch_x)
            _, predicted = torch.max(outputs, 1)
            all_preds.extend(predicted.cpu().numpy())

    y_pred = np.array(all_preds)
    final_acc = accuracy_score(y_test_clean, y_pred)

    print("\n" + "═"*45)
    print(f"🏆 FINAL PAPER-PROTOCOL ACCURACY: {final_acc*100:.2f}%")
    print("═"*45)
    print(classification_report(y_test_clean, y_pred, target_names=class_names))

    cm = confusion_matrix(y_test_clean, y_pred)
    plt.figure(figsize=(12, 10))
    sns.heatmap(cm, annot=True, fmt='d', cmap='YlGnBu', xticklabels=class_names, yticklabels=class_names)
    plt.show()

if __name__ == "__main__":
    evaluate()