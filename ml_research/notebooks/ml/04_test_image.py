import torch
import torch.nn as nn
import cv2
import joblib
import os
import numpy as np
import warnings
from PIL import Image
from facenet_pytorch import MTCNN, InceptionResnetV1

# 1. SILENCE WARNINGS
warnings.filterwarnings("ignore")

# =========================================================
# 2. CONFIGURATION
# =========================================================
IMAGE_PATH = "../../test_images/image.png"
# OUTPUT_PATH = "../../saved_models"
OUTPUT_PATH = "../../models/ml"

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# 🔥 ARCHITECTURE MUST MATCH 02_TRAIN_MODEL.PY EXACTLY
class FaceClassifier(nn.Module):
    def __init__(self, num_classes):
        super(FaceClassifier, self).__init__()
        self.net = nn.Sequential(
            nn.Linear(512, 256),        # net.0
            nn.BatchNorm1d(256),         # net.1
            nn.ReLU(),                   # net.2
            nn.Dropout(0.5),             # net.3
            nn.Linear(256, 128),         # net.4
            nn.ReLU(),                   # net.5
            nn.Dropout(0.3),             # net.6 (The missing layer!)
            nn.Linear(128, num_classes)  # net.7
        )
    
    def forward(self, x):
        return self.net(x)

# =========================================================
# 3. PREDICTION FUNCTION
# =========================================================
def predict_with_accuracy(img_path):
    # 1. Check if image exists
    if not os.path.exists(img_path):
        print(f"❌ Error: File not found at {img_path}")
        return

    # 2. Load Assets
    try:
        # Load the Label Encoder saved during training to get the right names
        le = joblib.load(os.path.join(OUTPUT_PATH, 'label_encoder.pkl'))
        labels_to_names = joblib.load(os.path.join(OUTPUT_PATH, 'labels_to_names.pkl'))
        scaler = joblib.load(os.path.join(OUTPUT_PATH, 'scaler.pkl'))
        
        if os.path.exists(os.path.join(OUTPUT_PATH, 'metrics.pkl')):
            metrics = joblib.load(os.path.join(OUTPUT_PATH, 'metrics.pkl'))
            model_accuracy = f"{metrics['best_acc']:.2f}%"
        else:
            model_accuracy = "Run training to see score"
            
    except Exception as e:
        print(f"❌ Error loading training files: {e}")
        return

    # 3. Initialize Model with correct classes
    num_classes = len(le.classes_)
    model = FaceClassifier(num_classes).to(DEVICE)
    
    # Load Weights (Now architecture matches perfectly)
    model.load_state_dict(torch.load(os.path.join(OUTPUT_PATH, 'face_model.pth'), weights_only=False))
    model.eval()

    # 4. Initialize Extractors
    mtcnn = MTCNN(device=DEVICE)
    resnet = InceptionResnetV1(pretrained='vggface2').eval().to(DEVICE)

    # 5. Process Image
    img = cv2.imread(img_path)
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    face = mtcnn(Image.fromarray(img_rgb))
    
    if face is not None:
        with torch.no_grad():
            face = face.unsqueeze(0).to(DEVICE)
            embedding = resnet(face).cpu().numpy()
            embedding_scaled = scaler.transform(embedding)
            
            output = model(torch.Tensor(embedding_scaled).to(DEVICE))
            probs = torch.nn.functional.softmax(output, dim=1)
            conf, pred = torch.max(probs, 1)
            
            # Use label encoder to get original ID, then name map for name
            label_id = le.inverse_transform([pred.item()])[0]
            name = labels_to_names[label_id]
            
            # --- FINAL OUTPUT ---
            print("\n" + "═"*40)
            if conf.item() > 0.85:
                print(f"👤 IDENTIFIED PERSON : {name}")
            else:
                print(f"👤 IDENTIFIED PERSON : Unknown (Closest Match: {name})")
            # print(f"📈 SYSTEM ACCURACY      : {model_accuracy}")
            print(f"🎯 MATCH CERTAINTY     : {conf.item()*100:.2f}%")
            
            if conf.item() > 0.85:
                print("✅ STATUS: HIGHLY RELIABLE MATCH")
            else:
                print("⚠️ STATUS: LOW CONFIDENCE - PLEASE VERIFY")
            print("═"*40)
    else:
        print("❌ No face detected.")

if __name__ == "__main__":
    predict_with_accuracy(IMAGE_PATH)