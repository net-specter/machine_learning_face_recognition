import torch
import torch.nn as nn
import torch.optim as optim
import pennylane as qml
import joblib
import numpy as np
import os
from tqdm import tqdm
from torch.utils.data import DataLoader, TensorDataset
from sklearn.preprocessing import LabelEncoder

# =========================================================
# 1. CONFIGURATION
# =========================================================
OUTPUT_PATH = "../../saved_models"
DEVICE = torch.device("cpu")

# Quantum Params (MUST match preprocessing)
N_QUBITS = 8
N_LAYERS = 3                 # 2 is shallow → 3 learns better
LR = 0.002                   # Safer for quantum gradients
EPOCHS = 60
BATCH_SIZE = 32
PATIENCE = 10

torch.manual_seed(42)
np.random.seed(42)

# =========================================================
# 2. QUANTUM CIRCUIT
# =========================================================
try:
    dev = qml.device("lightning.qubit", wires=N_QUBITS)
except Exception:
    dev = qml.device("default.qubit", wires=N_QUBITS)

@qml.qnode(dev, interface="torch", diff_method="parameter-shift")
def quantum_net(inputs, weights):
    # Stable embedding for quantum models
    qml.AngleEmbedding(inputs, wires=range(N_QUBITS), rotation="Y")

    # Trainable entangling layers
    qml.StronglyEntanglingLayers(weights, wires=range(N_QUBITS))

    return [qml.expval(qml.PauliZ(i)) for i in range(N_QUBITS)]

# =========================================================
# 3. HYBRID MODEL
# =========================================================
class HybridFaceClassifier(nn.Module):
    def __init__(self, num_classes):
        super().__init__()

        q_weight_shapes = {"weights": (N_LAYERS, N_QUBITS, 3)}
        self.quantum = qml.qnn.TorchLayer(quantum_net, q_weight_shapes)

        # Normalize quantum outputs (VERY important)
        self.q_norm = nn.LayerNorm(N_QUBITS)

        self.classifier = nn.Sequential(
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
# 4. TRAINING FUNCTION
# =========================================================
def train():
    print(f"🚀 Initializing Hybrid Quantum Training on {DEVICE}...")

    # ---- Load Data ----
    try:
        X_train = joblib.load(f"{OUTPUT_PATH}/X_train_Q.pkl")
        y_train_raw = joblib.load(f"{OUTPUT_PATH}/Y_train_Q.pkl")
        X_val = joblib.load(f"{OUTPUT_PATH}/X_val_Q.pkl")
        y_val_raw = joblib.load(f"{OUTPUT_PATH}/Y_val_Q.pkl")
    except Exception as e:
        print("❌ Dataset not found. Run preprocessing first.")
        raise e

    # ---- Encode Labels ----
    le = LabelEncoder()
    y_train_np = le.fit_transform(y_train_raw)
    y_val_np = le.transform(y_val_raw)

    y_train = torch.tensor(y_train_np, dtype=torch.long)
    y_val = torch.tensor(y_val_np, dtype=torch.long)

    num_classes = len(le.classes_)

    # ---- Class Weights (FIXED) ----
    counts = np.bincount(y_train_np)
    weights = counts.sum() / (counts + 1e-8)
    class_weights = torch.tensor(weights, dtype=torch.float)

    # ---- Datasets ----
    train_ds = TensorDataset(torch.tensor(X_train, dtype=torch.float32), y_train)
    val_ds = TensorDataset(torch.tensor(X_val, dtype=torch.float32), y_val)

    train_loader = DataLoader(
        train_ds, batch_size=BATCH_SIZE, shuffle=True, drop_last=True
    )
    val_loader = DataLoader(val_ds, batch_size=BATCH_SIZE)

    # ---- Model ----
    model = HybridFaceClassifier(num_classes).to(DEVICE)

    optimizer = optim.AdamW(
        model.parameters(),
        lr=LR,
        weight_decay=0.01
    )

    criterion = nn.CrossEntropyLoss(
        weight=class_weights,
        label_smoothing=0.1
    )

    scheduler = optim.lr_scheduler.ReduceLROnPlateau(
        optimizer,
        mode="max",
        patience=3,
        factor=0.5,
        verbose=True
    )

    best_acc = 0.0
    early_stop = 0

    # =====================================================
    # TRAINING LOOP
    # =====================================================
    for epoch in range(EPOCHS):
        model.train()
        running_loss = 0.0

        for bx, by in tqdm(train_loader, desc=f"Epoch {epoch+1}", leave=False):
            bx, by = bx.to(DEVICE), by.to(DEVICE)

            optimizer.zero_grad()
            outputs = model(bx)
            loss = criterion(outputs, by)
            loss.backward()

            torch.nn.utils.clip_grad_norm_(model.parameters(), 2.0)
            optimizer.step()

            running_loss += loss.item()

        avg_loss = running_loss / len(train_loader)

        # ---- Validation ----
        model.eval()
        correct, total = 0, 0

        with torch.no_grad():
            for bx, by in val_loader:
                bx, by = bx.to(DEVICE), by.to(DEVICE)
                preds = model(bx).argmax(dim=1)
                correct += (preds == by).sum().item()
                total += by.size(0)

        val_acc = 100.0 * correct / total

        print(
            f"Epoch {epoch+1:03d} | "
            f"Loss: {avg_loss:.4f} | "
            f"Val Acc: {val_acc:.2f}% | "
            f"LR: {optimizer.param_groups[0]['lr']:.5f}"
        )

        scheduler.step(val_acc)

        # ---- Early Stopping ----
        if val_acc > best_acc:
            best_acc = val_acc
            early_stop = 0

            torch.save(
                model.state_dict(),
                f"{OUTPUT_PATH}/quantum_face_model.pth"
            )
            joblib.dump(
                le,
                f"{OUTPUT_PATH}/label_encoder_Q.pkl"
            )
        else:
            early_stop += 1
            if early_stop >= PATIENCE:
                print(f"🛑 Early stopping. Best Val Acc: {best_acc:.2f}%")
                break

    print("✅ Training complete.")

# =========================================================
if __name__ == "__main__":
    train()
