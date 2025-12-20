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
# 1. CONFIGURATION (RTX 4060 OPTIMIZED)
# =========================================================
OUTPUT_PATH = "../../saved_models"
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

N_QUBITS = 8
N_LAYERS = 4                 
LR = 0.005                   
EPOCHS = 50
BATCH_SIZE = 16              
PATIENCE = 8

# =========================================================
# 2. QUANTUM CIRCUIT (Fixed Slicing for Batches)
# =========================================================
dev = qml.device("lightning.qubit", wires=N_QUBITS)

@qml.qnode(dev, interface="torch", diff_method="adjoint")
def paper_quantum_net(inputs, weights):
    """
    Nature Paper Dual-Stream Logic:
    inputs[:, 0:4] -> Global Features (PCA)
    inputs[:, 4:8] -> Local Features (ICA)
    """
    for i in range(N_LAYERS):
        # 🔥 FIX: Use [:, :4] to slice the feature dimension, not the batch dimension
        # Qubits 0-3: Global Stream
        qml.AngleEmbedding(inputs[:, :4], wires=range(0, 4), rotation="Y")
        # Qubits 4-7: Local Stream
        qml.AngleEmbedding(inputs[:, 4:], wires=range(4, 8), rotation="X")

        # Quantum Matching (Entanglement between streams)
        qml.StronglyEntanglingLayers(weights[i:i+1], wires=range(N_QUBITS))

    return [qml.expval(qml.PauliZ(i)) for i in range(N_QUBITS)]

# =========================================================
# 3. HYBRID MODEL
# =========================================================
class PaperHybridClassifier(nn.Module):
    def __init__(self, num_classes):
        super().__init__()
        
        # Define the shapes of the weights for the TorchLayer
        q_weight_shapes = {"weights": (N_LAYERS, N_QUBITS, 3)}
        
        # TorchLayer automatically handles batching if the QNode is written correctly
        self.quantum = qml.qnn.TorchLayer(paper_quantum_net, q_weight_shapes)

        self.classifier = nn.Sequential(
            nn.Linear(N_QUBITS, 64),
            nn.BatchNorm1d(64),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(64, num_classes)
        )

    def forward(self, x):
        # Quantum output is shape (Batch, N_QUBITS)
        x = self.quantum(x)
        return self.classifier(x)

# =========================================================
# 4. TRAINING PIPELINE
# =========================================================
def train():
    print(f"🚀 Initializing Paper-Protocol Quantum Training on {DEVICE}")

    # Load Data
    X_train = joblib.load(f"{OUTPUT_PATH}/X_train_Q.pkl")
    y_train_raw = joblib.load(f"{OUTPUT_PATH}/Y_train_Q.pkl")
    X_val = joblib.load(f"{OUTPUT_PATH}/X_val_Q.pkl")
    y_val_raw = joblib.load(f"{OUTPUT_PATH}/Y_val_Q.pkl")

    le = LabelEncoder()
    y_train = torch.tensor(le.fit_transform(y_train_raw), dtype=torch.long)
    y_val = torch.tensor(le.transform(y_val_raw), dtype=torch.long)
    num_classes = len(le.classes_)

    train_loader = DataLoader(
        TensorDataset(torch.tensor(X_train, dtype=torch.float32), y_train), 
        batch_size=BATCH_SIZE, shuffle=True, drop_last=True
    )
    val_loader = DataLoader(
        TensorDataset(torch.tensor(X_val, dtype=torch.float32), y_val), 
        batch_size=BATCH_SIZE
    )

    model = PaperHybridClassifier(num_classes).to(DEVICE)
    optimizer = optim.AdamW(model.parameters(), lr=LR, weight_decay=0.01)
    criterion = nn.CrossEntropyLoss(label_smoothing=0.1)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=EPOCHS)

    best_acc = 0.0
    early_stop_counter = 0

    for epoch in range(EPOCHS):
        model.train()
        train_loss = 0.0
        
        pbar = tqdm(train_loader, desc=f"Epoch {epoch+1}", leave=False)
        for bx, by in pbar:
            bx, by = bx.to(DEVICE), by.to(DEVICE)
            optimizer.zero_grad()
            outputs = model(bx)
            loss = criterion(outputs, by)
            loss.backward()
            optimizer.step()
            train_loss += loss.item()

        # Validation
        model.eval()
        correct, total = 0, 0
        with torch.no_grad():
            for bx, by in val_loader:
                bx, by = bx.to(DEVICE), by.to(DEVICE)
                preds = model(bx).argmax(dim=1)
                correct += (preds == by).sum().item()
                total += by.size(0)

        val_acc = 100.0 * correct / total
        print(f"Epoch {epoch+1:02d} | Loss: {train_loss/len(train_loader):.4f} | Val Acc: {val_acc:.2f}%")

        scheduler.step()

        if val_acc > best_acc:
            best_acc = val_acc
            early_stop_counter = 0
            torch.save(model.state_dict(), f"{OUTPUT_PATH}/hybrid_qml_model.pth")
            joblib.dump(le, f"{OUTPUT_PATH}/label_encoder.pkl")
            joblib.dump({'best_acc': best_acc}, f"{OUTPUT_PATH}/metrics.pkl")
        else:
            early_stop_counter += 1
            if early_stop_counter >= PATIENCE:
                print(f"🛑 Early stopping at best accuracy: {best_acc:.2f}%")
                break

    print("✅ Paper-style training complete.")

if __name__ == "__main__":
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    train()