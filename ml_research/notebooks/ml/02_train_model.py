import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
import joblib
import os
import numpy as np
from tqdm import tqdm
from sklearn.preprocessing import LabelEncoder

# Forces synchronous error reporting for easier debugging
os.environ['CUDA_LAUNCH_BLOCKING'] = "1"

# =========================================================
# 1. CONFIGURATION
# =========================================================
OUTPUT_PATH = "../../saved_models"
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Hyperparameters
INPUT_DIM = 512         # Facenet512 embedding size
HIDDEN_DIM = 256        # Initial hidden layer size
BATCH_SIZE = 32         
LR = 0.001
EPOCHS = 150            # High limit, but Early Stopping will likely stop sooner
PATIENCE = 12           # Stop if no improvement for 12 epochs

# =========================================================
# 2. MODEL DEFINITION (Optimized Funnel Architecture)
# =========================================================
class FaceClassifier(nn.Module):
    def __init__(self, num_classes):
        super(FaceClassifier, self).__init__()
        self.net = nn.Sequential(
            nn.Linear(INPUT_DIM, HIDDEN_DIM),
            nn.BatchNorm1d(HIDDEN_DIM),
            nn.ReLU(),
            nn.Dropout(0.5),            # Strong dropout to kill overfitting
            
            nn.Linear(HIDDEN_DIM, 128),
            nn.ReLU(),
            nn.Dropout(0.3),
            
            nn.Linear(128, num_classes)
        )
    
    def forward(self, x):
        return self.net(x)

# =========================================================
# 3. TRAINING FUNCTION
# =========================================================
def train():
    print(f"🚀 Initializing Training on: {torch.cuda.get_device_name(0)}")

    # 1. Load Data
    try:
        X_train, y_train = joblib.load(f"{OUTPUT_PATH}/train_data.pkl")
        X_val, y_val = joblib.load(f"{OUTPUT_PATH}/val_data.pkl")
        labels_to_names = joblib.load(f"{OUTPUT_PATH}/labels_to_names.pkl")
    except FileNotFoundError:
        print("❌ Error: Training data not found. Run 01_data_prep_ML.py first.")
        return

    # 2. Process Labels (Ensure continuous 0, 1, 2... mapping)
    le = LabelEncoder()
    # Combine all labels found to ensure the encoder sees everything
    all_y = np.concatenate((y_train, y_val))
    le.fit(all_y)
    
    y_train_clean = le.transform(y_train)
    y_val_clean = le.transform(y_val)
    num_classes = len(le.classes_)
    
    print(f"📊 Dataset: {len(X_train)} samples | {num_classes} classes detected.")

    # 3. DataLoaders
    train_loader = DataLoader(
        TensorDataset(torch.Tensor(X_train), torch.LongTensor(y_train_clean)), 
        batch_size=BATCH_SIZE, shuffle=True, drop_last=True # drop_last prevents BatchNorm size-1 crash
    )
    val_loader = DataLoader(
        TensorDataset(torch.Tensor(X_val), torch.LongTensor(y_val_clean)), 
        batch_size=BATCH_SIZE
    )

    # 4. Model, Optimizer, Criterion
    model = FaceClassifier(num_classes).to(DEVICE)
    
    # Label Smoothing makes the model less "arrogant" and more robust
    criterion = nn.CrossEntropyLoss(label_smoothing=0.1) 
    
    # L2 Regularization (weight_decay) prevents weights from becoming too large
    optimizer = optim.Adam(model.parameters(), lr=LR, weight_decay=1e-4)
    
    # Learning Rate Scheduler: Reduces LR when learning slows down
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', patience=4, factor=0.5)

    # 5. Training Loop Variables
    best_val_loss = float('inf')
    best_val_acc = 0.0
    no_improve_counter = 0

    pbar = tqdm(range(EPOCHS), desc="Training Model", unit="epoch")

    for epoch in pbar:
        # --- Training Phase ---
        model.train()
        train_loss = 0
        for bx, by in train_loader:
            bx, by = bx.to(DEVICE), by.to(DEVICE)
            optimizer.zero_grad()
            outputs = model(bx)
            loss = criterion(outputs, by)
            loss.backward()
            optimizer.step()
            train_loss += loss.item()

        # --- Validation Phase ---
        model.eval()
        val_loss, correct, total = 0, 0, 0
        with torch.no_grad():
            for bx, by in val_loader:
                bx, by = bx.to(DEVICE), by.to(DEVICE)
                outputs = model(bx)
                val_loss += criterion(outputs, by).item()
                _, predicted = torch.max(outputs.data, 1)
                total += by.size(0)
                correct += (predicted == by).sum().item()

        avg_val_loss = val_loss / len(val_loader)
        val_acc = 100 * correct / total
        
        # Update progress bar stats
        pbar.set_postfix({'V-Loss': f"{avg_val_loss:.3f}", 'V-Acc': f"{val_acc:.1f}%"})
        
        # Step the scheduler
        scheduler.step(avg_val_loss)

        # --- Early Stopping & Save Best Brain ---
        if avg_val_loss < (best_val_loss - 1e-4):
            best_val_loss = avg_val_loss
            best_val_acc = val_acc
            
            # Save weights
            torch.save(model.state_dict(), f"{OUTPUT_PATH}/face_model.pth")
            # Save the fixed encoder
            joblib.dump(le, f"{OUTPUT_PATH}/label_encoder.pkl")
            # Save metrics for inference display
            joblib.dump({'best_acc': best_val_acc}, f"{OUTPUT_PATH}/metrics.pkl")
            
            no_improve_counter = 0
        else:
            no_improve_counter += 1

        if no_improve_counter >= PATIENCE:
            pbar.write(f"\n⏹ Early stopping triggered at epoch {epoch}. Model stabilized.")
            break

    print(f"\n✅ SUCCESS: Training finished.")
    print(f"🏆 Best Validation Accuracy: {best_val_acc:.2f}%")

if __name__ == "__main__":
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    train()