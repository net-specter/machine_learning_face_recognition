import torch
import torch.nn as nn
import pennylane as qml
import cv2
import joblib
import os
import numpy as np
import warnings
from deepface import DeepFace # 🔥 Switch back to DeepFace for consistency

# 1. SILENCE WARNINGS
warnings.filterwarnings("ignore")

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

# =========================================================
# 2. CONFIGURATION
# =========================================================
IMAGE_PATH = "../../test_images/image.png" 
OUTPUT_PATH = "../../saved_models"
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

N_QUBITS = 8
N_LAYERS = 4 
MODEL_NAME = "Facenet512" # 🔥 Must match 01_data_prep_QML.py

# =========================================================
# 3. MODEL DEFINITION
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
        self.classifier = nn.Sequential(
            nn.Linear(N_QUBITS, 64),
            nn.BatchNorm1d(64),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(64, num_classes)
        )
    def forward(self, x):
        return self.classifier(self.quantum(x))

# =========================================================
# 4. PREDICTION FUNCTION
# =========================================================
def predict_paper_style(img_path):
    if not os.path.exists(img_path):
        print(f"❌ File not found: {img_path}")
        return

    # Load All Assets
    try:
        std_scaler = joblib.load(os.path.join(OUTPUT_PATH, 'standardizer.pkl'))
        pca_model = joblib.load(os.path.join(OUTPUT_PATH, 'pca_model.pkl'))
        ica_model = joblib.load(os.path.join(OUTPUT_PATH, 'ica_model.pkl'))
        q_scaler = joblib.load(os.path.join(OUTPUT_PATH, 'quantum_scaler.pkl'))
        le = joblib.load(os.path.join(OUTPUT_PATH, 'label_encoder.pkl'))
        labels_to_names = joblib.load(os.path.join(OUTPUT_PATH, 'labels_to_names.pkl'))
    except Exception as e:
        print(f"❌ Asset Error: {e}")
        return

    # Initialize Model
    model = PaperHybridClassifier(len(le.classes_)).to(DEVICE)
    model.load_state_dict(torch.load(os.path.join(OUTPUT_PATH, 'hybrid_qml_model.pth'), map_location=DEVICE))
    model.eval()

    # print(f"✨ DeepFace analyzing: {os.path.basename(img_path)}")
    
    try:
        # 🔥 STEP 1: Extract Embedding using identical logic to Script 01
        # enforce_detection=True ensures we only process images with clear faces
        objs = DeepFace.represent(img_path=img_path, model_name=MODEL_NAME, detector_backend="opencv")
        emb = np.array(objs[0]["embedding"]).reshape(1, -1)
        
        with torch.no_grad():
            # 🔥 STEP 2: Dual Stream Processing
            emb_std = std_scaler.transform(emb)
            
            feat_pca = pca_model.transform(emb_std)
            feat_ica = ica_model.transform(emb_std)
            
            # Combine Global (PCA) and Local (ICA)
            feat_combined = np.hstack((feat_pca, feat_ica))
            
            # Final Quantum Scaling (0 to PI)
            feat_q = q_scaler.transform(feat_combined)
            
            # 🔥 STEP 3: Quantum Inference
            output = model(torch.Tensor(feat_q).to(DEVICE))
            probs = torch.nn.functional.softmax(output, dim=1)
            conf, pred = torch.max(probs, 1)
            
            # Map back to Name
            label_idx = pred.item()
            original_id = le.inverse_transform([label_idx])[0]
            name = labels_to_names[original_id]
            
            # --- FINAL OUTPUT ---
            print("\n" + "═"*40)
            if conf.item() > 0.50:
                print(f"👤 IDENTIFIED PERSON : {name}")
            else:
                print(f"👤 IDENTIFIED PERSON : Unknown (Closest Match: {name})")
            # print(f"📈 SYSTEM ACCURACY      : {model_accuracy}")
            print(f"🎯 MATCH CERTAINTY     : {conf.item()*100:.2f}%")
            
            if conf.item() >0.50:
                print("✅ STATUS: HIGHLY RELIABLE MATCH")
            else:
                print("⚠️ STATUS: LOW CONFIDENCE - PLEASE VERIFY")
            print("═"*40)
            

    except Exception as e:
        print(f"❌ Error during analysis: {e}")

if __name__ == "__main__":
    predict_paper_style(IMAGE_PATH)