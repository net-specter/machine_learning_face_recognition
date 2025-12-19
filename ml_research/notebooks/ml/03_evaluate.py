import torch
import torch.nn as nn
import joblib
import os
import numpy as np
from tqdm import tqdm
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import matplotlib.pyplot as plt
import seaborn as sns
import warnings

# Silence warnings for a clean output
warnings.filterwarnings("ignore")

# =========================================================
# 1. CONFIGURATION
# =========================================================
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
OUTPUT_PATH = "../../saved_models"

# 🔥 ARCHITECTURE: Must match your training script exactly
class FaceClassifier(nn.Module):
    def __init__(self, num_classes):
        super(FaceClassifier, self).__init__()
        self.net = nn.Sequential(
            nn.Linear(512, 256),
            nn.BatchNorm1d(256),
            nn.ReLU(),
            nn.Dropout(0.5),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(128, num_classes)
        )
    
    def forward(self, x):
        return self.net(x)

# =========================================================
# 2. EVALUATION FUNCTION
# =========================================================
def evaluate():
    print(f"🚀 Starting Evaluation on {DEVICE}...")

    # Load Test Data
    try:
        X_test, y_test = joblib.load(f"{OUTPUT_PATH}/test_data.pkl")
        le = joblib.load(f"{OUTPUT_PATH}/label_encoder.pkl")
        labels_to_names = joblib.load(f"{OUTPUT_PATH}/labels_to_names.pkl")
    except FileNotFoundError as e:
        print(f"❌ Error: Missing files. {e}")
        return

    # Transform numeric test labels to the continuous mapping (0, 1, 2...)
    y_test_clean = le.transform(y_test)
    
    # Get actual names for the report
    class_names = [str(labels_to_names[idx]) for idx in le.classes_]
    num_classes = len(class_names)

    # Initialize Model and Load Weights
    model = FaceClassifier(num_classes).to(DEVICE)
    model.load_state_dict(torch.load(f"{OUTPUT_PATH}/face_model.pth", map_location=DEVICE))
    model.eval()

    # Run Inference
    all_preds = []
    X_test_tensor = torch.Tensor(X_test).to(DEVICE)
    
    print(f"✨ Analyzing {len(X_test)} images...")
    with torch.no_grad():
        # Process in batches for safety
        for i in range(0, len(X_test_tensor), 16):
            batch = X_test_tensor[i : i + 16]
            outputs = model(batch)
            _, predicted = torch.max(outputs, 1)
            all_preds.extend(predicted.cpu().numpy())

    y_pred = np.array(all_preds)
    acc = accuracy_score(y_test_clean, y_pred)

    # --- DISPLAY RESULTS ---
    print("\n" + "═"*45)
    print(f"🏆 FINAL SYSTEM ACCURACY: {acc*100:.2f}%")
    print("═"*45)

    print("\n📄 Detailed Classification Report:")
    print(classification_report(y_test_clean, y_pred, target_names=class_names))

    # Plot Confusion Matrix
    print("\n📊 Generating Confusion Matrix...")
    cm = confusion_matrix(y_test_clean, y_pred)
    plt.figure(figsize=(12, 10))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                xticklabels=class_names, yticklabels=class_names)
    plt.title(f"Face Recognition Performance\nAccuracy: {acc*100:.2f}%")
    plt.ylabel('Actual Identity')
    plt.xlabel('Predicted Identity')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    evaluate()