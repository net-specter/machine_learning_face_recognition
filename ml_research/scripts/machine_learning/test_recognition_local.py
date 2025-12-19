import cv2
import numpy as np
import os
import joblib
import mediapipe as mp
import tensorflow as tf
import keras # Import Keras top-level for compatibility hack
from scipy.spatial.distance import cosine 
from deepface import DeepFace 

# CRITICAL FIX: Injecting the compatibility layer for older DeepFace versions
if not hasattr(tf, 'keras'):
    tf.keras = keras
    print("DEBUG: Fixed tensorflow.keras path for DeepFace.")


# --- CONFIGURATION & ASSET PATHS ---
MODEL_DIR = '../saved_models'
# Use an image known to be good from your training set for initial debugging:
TEST_IMAGE_PATH = '../datasets/raw/vichet/image.jpg' # <-- CHANGE THIS
ALIGNMENT_SIZE = (224, 224) 
IMAGE_SIZE = (224, 224) # Standard size for alignment/resize

mp_face_detection = mp.solutions.face_detection

# --- 1. Load Deployment Assets (Classifier Model) ---
try:
    CLASSIFIER = joblib.load(os.path.join(MODEL_DIR, 'face_recognition_model.pkl'))
    LABELS_MAP = joblib.load(os.path.join(MODEL_DIR, 'labels_to_names.pkl'))
    
    print(f"DEBUG: Classifier {CLASSIFIER.__class__.__name__} loaded successfully.")
    
except FileNotFoundError as e:
    print(f"FATAL: Cannot find required PKL file. Error: {e}")
    exit()

# Pre-load the DeepFace VGG-Face model for feature extraction
DeepFace.build_model('VGG-Face') 


# --- 2. Helper Functions (Feature Extraction Pipeline) ---

def preprocess_and_extract_features(image_path):
    """Runs the full Detection, Alignment, and Feature Extraction pipeline."""
    
    img = cv2.imread(image_path)
    
    if img is None:
        print(f"DEBUG CRITICAL: cv2.imread returned None for {image_path}. Check file integrity.")
        return None, None, None
    print("DEBUG OK: Image loaded.")
    
    # Initialize MediaPipe detector for this function call
    with mp_face_detection.FaceDetection(
        model_selection=1, min_detection_confidence=0.7) as face_detection:
        
        # A. Detection (MediaPipe)
        results = face_detection.process(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        
        if not results.detections:
            print("DEBUG FAILED: MediaPipe found NO face.")
            return None, None, None
        print("DEBUG OK: Face detected.")
        
        # Get the first detected face
        detection = results.detections[0] 
        
        # B. Alignment & Clamping Logic
        bbox_c = detection.location_data.relative_bounding_box
        h, w, _ = img.shape
        
        # Calculate pixel coordinates
        xmin = int(bbox_c.xmin * w)
        ymin = int(bbox_c.ymin * h)
        xmax = int(bbox_c.width * w) + xmin
        ymax = int(bbox_c.height * h) + ymin
        
        # Clamping (Defensive Programming)
        xmin, xmax = max(0, xmin), min(w, xmax)
        ymin, ymax = max(0, ymin), min(h, ymax)
        
        if xmax <= xmin or ymax <= ymin: 
            print("DEBUG FAILED: Invalid crop dimensions after clamping.")
            return None, None, None
             
        face_img = img[ymin:ymax, xmin:xmax]
        face_aligned_resized = cv2.resize(face_img, ALIGNMENT_SIZE) 

        # C. Feature Extraction (DeepFace)
        try:
            embedding_result = DeepFace.represent(
                img_path=face_aligned_resized, 
                model_name='VGG-Face', 
                enforce_detection=False, 
                detector_backend='skip'  
            )
            # The output vector
            input_vector = np.array(embedding_result[0]['embedding']).flatten()
            
            print("DEBUG OK: DeepFace embedding successful.")
            
            # Return input vector, bounding box coordinates, and the original image
            return input_vector, (xmin, ymin, xmax, ymax), img 
            
        except Exception as e:
            print(f"DEBUG FAILED: DeepFace embedding failed with error: {e}")
            return None, None, None

# --- 3. The Core Recognition Logic (Using Model.predict) ---

def recognize_and_predict(input_vector):
    """Uses the loaded Scikit-learn model to predict the class label and map to name."""
    
    # 1. Prediction
    input_vector_reshaped = input_vector.reshape(1, -1) 
    
    # The model predicts the numerical label (e.g., 0, 1)
    predicted_label = CLASSIFIER.predict(input_vector_reshaped)[0]
    
    # 2. Name Lookup
    # Map the numerical label back to the name string
    predicted_name = LABELS_MAP.get(predicted_label, "Unknown")
    
    # Optional: Confidence/Probability check (only works if SVC was trained with probability=True)
    if CLASSIFIER.__class__.__name__ == 'SVC' and hasattr(CLASSIFIER, 'predict_proba'):
        confidence = CLASSIFIER.predict_proba(input_vector_reshaped).max()
        print(f"DEBUG: SVC Confidence: {confidence:.2f}")

    return predicted_name

# --- 4. EXECUTION ---

if __name__ == '__main__':
    
    # Run the feature extraction pipeline
    input_vector, bbox, original_img = preprocess_and_extract_features(TEST_IMAGE_PATH)
    
    if input_vector is not None:
        result = recognize_and_predict(input_vector)
        print(f"\nFINAL RESULT (Predicted Name): {result}")
        
        # --- OPTIONAL: Visual Debug Display ---
        if bbox is not None and original_img is not None:
            xmin, ymin, xmax, ymax = bbox
            # Draw rectangle and text
            cv2.rectangle(original_img, (xmin, ymin), (xmax, ymax), (0, 255, 0), 2)
            cv2.putText(original_img, result, (xmin, ymin - 10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
            
            print("\nDisplaying image. Press any key to close window.")
            cv2.imshow('Recognition Test', original_img)
            cv2.waitKey(0)
            cv2.destroyAllWindows()
    else:
        print("\nFINAL RESULT: System failed before prediction. (See debug logs above)")