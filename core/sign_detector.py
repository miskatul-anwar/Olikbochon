"""
sign_detector.py
-----------------
Wraps the ORIGINAL core sign-detection logic from `inference_classifier.py`
(hand-landmark extraction via MediaPipe Tasks HandLandmarker + prediction via
the trained RandomForestClassifier in `model.p`) in a reusable class.

IMPORTANT: The detection logic itself (landmark extraction, feature-vector
construction, padding/trimming, and model.predict call) is preserved
UNCHANGED from the provided `inference_classifier.py`. Only the surrounding
loop (cv2.VideoCapture / cv2.imshow / while True) has been removed and
replaced with a single `predict_frame()` method suitable for calling once
per incoming WebRTC video frame.
"""

import os
import pickle
import urllib.request

import numpy as np
import cv2
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision as mp_vision


# Static hand connections (same 21-point skeleton mp.solutions.hands.HAND_CONNECTIONS used to provide)
HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),
    (0, 5), (5, 6), (6, 7), (7, 8),
    (5, 9), (9, 10), (10, 11), (11, 12),
    (9, 13), (13, 14), (14, 15), (15, 16),
    (13, 17), (17, 18), (18, 19), (19, 20),
    (0, 17)
]

LABELS_DICT = {
    0: 'A',  1: 'B',  2: 'C',  3: 'D',  4: 'E',  5: 'F',  6: 'G',
    7: 'H',  8: 'I',  9: 'J', 10: 'K', 11: 'L', 12: 'M', 13: 'N',
    14: 'O', 15: 'P', 16: 'Q', 17: 'R', 18: 'S', 19: 'T', 20: 'U',
    21: 'V', 22: 'W', 23: 'X', 24: 'Y', 25: 'Z'
}

MODEL_PATH_DEFAULT = os.path.join(os.path.dirname(__file__), './model/model.p')
LANDMARKER_PATH_DEFAULT = os.path.join(os.path.dirname(__file__), './model/hand_landmarker.task')
MODEL_URL = 'https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task'


class SignDetector:
    """
    Loads the trained model + MediaPipe HandLandmarker once, and exposes
    `predict_frame(frame_bgr)` which returns:
        (annotated_frame_bgr, predicted_character_or_None)

    All ML logic below mirrors inference_classifier.py exactly.
    """

    def __init__(self, model_path=MODEL_PATH_DEFAULT, landmarker_path=LANDMARKER_PATH_DEFAULT):
        # load model  (unchanged from inference_classifier.py)
        model_dict = pickle.load(open(model_path, 'rb'))
        self.model = model_dict['model']

        # --- MediaPipe Tasks API setup (unchanged from inference_classifier.py) ---
        if not os.path.exists(landmarker_path):
            urllib.request.urlretrieve(MODEL_URL, landmarker_path)

        base_options = mp_python.BaseOptions(model_asset_path=landmarker_path)
        options = mp_vision.HandLandmarkerOptions(
            base_options=base_options,
            num_hands=2,
            min_hand_detection_confidence=0.3,
            running_mode=mp_vision.RunningMode.IMAGE
        )
        self.detector = mp_vision.HandLandmarker.create_from_options(options)

    def predict_frame(self, frame):
        """
        frame: BGR ndarray (already flipped/mirrored by caller if desired).
        Returns (frame_with_overlay, predicted_character_or_None, confidence_or_None).

        This is the same per-frame body as the `while True:` loop in
        inference_classifier.py, just extracted into a function. The only
        addition beyond the original logic is reading the model's
        predict_proba() (when available) to report a confidence score
        alongside the predicted letter — the prediction itself is
        unchanged.
        """
        data_aux = []
        x_ = []
        y_ = []
        predicted_character = None
        confidence = None

        H, W, _ = frame.shape

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)

        results = self.detector.detect(mp_image)

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

            # Build feature vector and match the model's expected size
            feat = np.asarray(data_aux, dtype=float).ravel()
            expected = getattr(self.model, "n_features_in_", len(feat))  # sklearn stores expected input size

            # pad with zeros if too short, or trim if too long
            if feat.size < expected:
                feat = np.pad(feat, (0, expected - feat.size), mode='constant')
            elif feat.size > expected:
                feat = feat[:expected]

            prediction = self.model.predict([feat])[0]

            predicted_character = LABELS_DICT[int(prediction[0])]

            if hasattr(self.model, "predict_proba"):
                try:
                    proba = self.model.predict_proba([feat])[0]
                    confidence = float(np.max(proba))
                except Exception:
                    confidence = None

            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 0), 4)
            cv2.putText(frame, predicted_character, (x1, y1), cv2.FONT_HERSHEY_SIMPLEX, 1.3, (0, 0, 0), 3,
                        cv2.LINE_AA)

        return frame, predicted_character, confidence
