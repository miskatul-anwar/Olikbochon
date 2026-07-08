#inference_classifier.py
import pickle
import cv2
import os
import urllib.request
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision as mp_vision

# load model
model_dict = pickle.load(open('./model.p', 'rb'))
model = model_dict['model']

cap = cv2.VideoCapture(0)  # can change index acc to number of webcams, default 0 for mac, windows = 2

# --- MediaPipe Tasks API setup ---
# Newer mediapipe releases removed the legacy `mp.solutions.hands` API.
# The replacement is HandLandmarker, which needs a downloadable .task model file.
MODEL_PATH = './hand_landmarker.task'
MODEL_URL = 'https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task'

if not os.path.exists(MODEL_PATH):
    print('Downloading hand landmarker model (first run only)...')
    urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)

base_options = mp_python.BaseOptions(model_asset_path=MODEL_PATH)
options = mp_vision.HandLandmarkerOptions(
    base_options=base_options,
    num_hands=2,
    min_hand_detection_confidence=0.3,
    running_mode=mp_vision.RunningMode.IMAGE
)
detector = mp_vision.HandLandmarker.create_from_options(options)

# Static hand connections (same 21-point skeleton mp.solutions.hands.HAND_CONNECTIONS used to provide)
HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),
    (0, 5), (5, 6), (6, 7), (7, 8),
    (5, 9), (9, 10), (10, 11), (11, 12),
    (9, 13), (13, 14), (14, 15), (15, 16),
    (13, 17), (17, 18), (18, 19), (19, 20),
    (0, 17)
]

labels_dict = {
    0: 'A',  1: 'B',  2: 'C',  3: 'D',  4: 'E',  5: 'F',  6: 'G',
    7: 'H',  8: 'I',  9: 'J', 10: 'K', 11: 'L', 12: 'M', 13: 'N',
   14: 'O', 15: 'P', 16: 'Q', 17: 'R', 18: 'S', 19: 'T', 20: 'U',
   21: 'V', 22: 'W', 23: 'X', 24: 'Y', 25: 'Z'
}

while True:

    data_aux = []
    x_ = []
    y_ = []

    ret, frame = cap.read()
    frame = cv2.flip(frame, 1)  # <-- mirror camera

    H, W, _ = frame.shape

    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)

    results = detector.detect(mp_image)

    # iterate through results - show hands : DRAW LANDMARKS
    if results.hand_landmarks:
        for hand_landmarks in results.hand_landmarks:
            for connection in HAND_CONNECTIONS:
                start = hand_landmarks[connection[0]]
                end = hand_landmarks[connection[1]]
                x1c, y1c = int(start.x * W), int(start.y * H)
                x2c, y2c = int(end.x * W), int(end.y * H)
                cv2.line(frame, (x1c, y1c), (x2c, y2c), (0, 255, 0), 2)
            for lm in hand_landmarks:
                cx, cy = int(lm.x * W), int(lm.y * H)
                cv2.circle(frame, (cx, cy), 3, (0, 0, 255), -1)

        for hand_landmarks in results.hand_landmarks:
            for lm in hand_landmarks:
                # create an array of landmarks with the x and y of the landmarks and train the mode
                x = lm.x
                y = lm.y
                data_aux.append(x)
                data_aux.append(y)
                x_.append(x)
                y_.append(y)

        x1 = int(min(x_) * W)
        y1 = int(min(y_) * H)

        x2 = int(max(x_) * W)
        y2 = int(max(y_) * H)

        #model.predict([np.asarray(data_aux)])
        # Build feature vector and match the model's expected size
        feat = np.asarray(data_aux, dtype=float).ravel()
        expected = getattr(model, "n_features_in_", len(feat))  # sklearn stores expected input size

        # pad with zeros if too short, or trim if too long
        if feat.size < expected:
            feat = np.pad(feat, (0, expected - feat.size), mode='constant')
        elif feat.size > expected:
            feat = feat[:expected]

        prediction = model.predict([feat])[0]
        # (optional) print(pred) or draw it on the frame

        predicted_character = labels_dict[int(prediction[0])]

        print(predicted_character)

        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 0), 4)
        cv2.putText(frame, predicted_character, (x1, y1), cv2.FONT_HERSHEY_SIMPLEX, 1.3, (0, 0, 0), 3,
                    cv2.LINE_AA)

    cv2.imshow('frame', frame)
    cv2.waitKey(25) #wait 25 ms between each frame

cap.release()

cv2.destroyAllWindows()
