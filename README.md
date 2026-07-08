![](./assets/logo.png)

# অলীকবচন (Olikbochon) — Bridging Communication
Real-time sign language into text and speech, in English and Bengali.

A monolithic **Streamlit** web app that translates real-time fingerspelled
sign language into text captions and speech, in both **English** and
**Bengali** — 100% free and open-source, no paid APIs.

## Features

- **Live camera feed** via `streamlit-webrtc` — camera-first, full-width UI
- **Unmodified core detection logic** — MediaPipe HandLandmarker + your
  trained `RandomForestClassifier` (`model.p`), exactly as in
  `inference_classifier.py`
- **Smart buffering** — a held letter is only committed once it's stable
  for ~0.5s, so it isn't pushed 30x/second; pauses insert word boundaries
- **NLP pipeline** — word-boundary detection + spell-checking via
  `pyspellchecker`
- **Bengali translation** — via `deep-translator` (free, no API key)
- **Text-to-speech** — via `gTTS`, autoplayed in-browser
- **Minimal, modern UI** — custom CSS, YouTube-style captions, hidden
  Streamlit chrome

## Project structure

```
olikbochon/
├── app.py                  # Main Streamlit application
├── video_processor.py      # WebRTC VideoProcessorBase + debounce/buffer logic
├── sign_detector.py        # UNCHANGED core detection logic (landmarks + model)
├── nlp_pipeline.py         # Word boundary, spell-check, translation
├── tts_utils.py            # gTTS + autoplay HTML/base64 helper
├── style.py                # Custom CSS
├── model.p                 # Trained RandomForestClassifier
├── hand_landmarker.task    # MediaPipe hand landmark model
├── assets/
│   └── logo.png            # App logo
├── requirements.txt
└── README.md
```

## Quick start

```bash
pip install -r requirements.txt
streamlit run app.py
```

Then open the local URL Streamlit prints (usually `http://localhost:8501`),
allow camera access, click **Start**, and begin fingerspelling.

## How it works

1. **Start Recording** — `streamlit-webrtc` mounts your webcam feed.
2. **Detection loop** (`video_processor.py` → `recv()`) — every frame is
   passed to the original MediaPipe + RandomForest pipeline
   (`sign_detector.py`). Predicted letters are buffered only after being
   held steady, avoiding duplicate spam.
3. **Pause detection** — when your hand disappears for ~0.7s, a space is
   inserted into the buffer, marking a word boundary.
4. **Generate Speech & Caption** — click the button to run the buffered
   letters through the NLP pipeline (spelling correction), optionally
   translate to Bengali, and synthesize speech with gTTS.
5. **Output** — the corrected caption (and Bengali translation, if
   enabled) is displayed prominently, with autoplaying audio.

## Notes

- The original ML/detection code (`sign_detector.py`) mirrors
  `inference_classifier.py` line-for-line — including its existing
  label-decoding logic — since the task requires preserving that logic
  unchanged.
- For deployment behind NATs/firewalls (e.g. Streamlit Community Cloud),
  a public STUN server is already configured in `app.py`. Add a TURN
  server to `RTC_CONFIGURATION` if you need it in stricter network
  environments.
