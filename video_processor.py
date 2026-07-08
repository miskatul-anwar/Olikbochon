"""
video_processor.py
-------------------
streamlit-webrtc VideoProcessorBase implementation. Runs the (unchanged)
core sign-detection logic from sign_detector.py on every incoming frame,
draws the live overlay + caption bar, and maintains a thread-safe,
debounced letter buffer:

  * A letter is only "committed" to the buffer once it has been held
    steady for STABLE_FRAMES consecutive frames (avoids pushing the same
    letter ~30x/second).
  * When no hand is detected for RESET_FRAMES consecutive frames, a single
    space token is appended (marks a word boundary / pause) and the
    "last committed" guard is cleared so the same letter can be signed
    again right after (e.g. double letters like "LL").
"""

import threading
import time

import av
import cv2
from streamlit_webrtc import VideoProcessorBase

from sign_detector import SignDetector

STABLE_FRAMES = 15   # ~0.5s at 30fps: how long a letter must be held to commit
RESET_FRAMES = 20    # ~0.7s at 30fps: how long no-hand before we mark a pause/space


class SignLanguageProcessor(VideoProcessorBase):
    def __init__(self):
        self.detector = SignDetector()

        self.lock = threading.Lock()
        self.letter_buffer = []       # committed letters + space tokens
        self.current_display_letter = ""  # for live caption bar (not yet committed)

        self._current_letter = None
        self._stable_count = 0
        self._no_hand_count = 0
        self._last_committed = None

    def recv(self, frame):
        img = frame.to_ndarray(format="bgr24")
        img = cv2.flip(img, 1)  # mirror, matches inference_classifier.py behavior

        img, predicted_character = self.detector.predict_frame(img)

        with self.lock:
            if predicted_character is not None:
                self._no_hand_count = 0

                if predicted_character == self._current_letter:
                    self._stable_count += 1
                else:
                    self._current_letter = predicted_character
                    self._stable_count = 1

                self.current_display_letter = predicted_character

                if (self._stable_count == STABLE_FRAMES
                        and predicted_character != self._last_committed):
                    self.letter_buffer.append(predicted_character)
                    self._last_committed = predicted_character
            else:
                self._no_hand_count += 1
                self.current_display_letter = ""
                if self._no_hand_count == RESET_FRAMES:
                    # mark a pause/word-boundary, but only once, and only
                    # if something has actually been signed since the last space
                    if self.letter_buffer and self.letter_buffer[-1] != " ":
                        self.letter_buffer.append(" ")
                    self._current_letter = None
                    self._stable_count = 0
                    self._last_committed = None

            caption_preview = "".join(self.letter_buffer[-40:]).strip()

        # --- draw a YouTube-style caption bar at the bottom of the frame ---
        h, w, _ = img.shape
        bar_height = 60
        overlay = img.copy()
        cv2.rectangle(overlay, (0, h - bar_height), (w, h), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.6, img, 0.4, 0, img)

        caption_text = caption_preview if caption_preview else "..."
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = max(0.6, min(1.2, w / 900))
        thickness = 2
        text_size = cv2.getTextSize(caption_text, font, font_scale, thickness)[0]
        text_x = max(10, (w - text_size[0]) // 2)
        text_y = h - (bar_height // 2) + text_size[1] // 2
        cv2.putText(img, caption_text, (text_x, text_y), font, font_scale,
                    (255, 255, 255), thickness, cv2.LINE_AA)

        return av.VideoFrame.from_ndarray(img, format="bgr24")

    # --- helper methods used by the main Streamlit thread ---
    def get_buffer_copy(self):
        with self.lock:
            return list(self.letter_buffer)

    def clear_buffer(self):
        with self.lock:
            self.letter_buffer = []
            self._current_letter = None
            self._stable_count = 0
            self._no_hand_count = 0
            self._last_committed = None

    def get_live_letter(self):
        with self.lock:
            return self.current_display_letter
