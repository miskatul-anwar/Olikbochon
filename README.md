<p align="center">
  <img src="./assets/logo.png" alt="Olikbochon logo" width="360">
</p>

<h1 align="center">অলীকবচন (Olikbochon)</h1>
<p align="center"><b>Bridging Communication — real-time sign-language fingerspelling into text and speech, in English and Bengali.</b></p>

<p align="center">
  <img alt="Python" src="https://img.shields.io/badge/Python-3.11%2B-blue?logo=python&logoColor=white">
  <img alt="Streamlit" src="https://img.shields.io/badge/Streamlit-app-FF4B4B?logo=streamlit&logoColor=white">
  <img alt="MediaPipe" src="https://img.shields.io/badge/MediaPipe-HandLandmarker-00897B">
  <img alt="scikit-learn" src="https://img.shields.io/badge/scikit--learn-RandomForest-F7931E?logo=scikitlearn&logoColor=white">
</p>

---

## Overview

**Olikbochon** (অলীকবচন) is a **Streamlit**-based real-time sign-language fingerspelling system that converts webcam hand gestures into readable, spell-corrected captions and, optionally, spoken audio in **English** or **Bengali**.

The project is organized as a full end-to-end pipeline, made up of two complementary parts:

1. **Application runtime** (`app.py`, `core/`) — real-time inference, captioning, translation, and speech synthesis.
2. **Data and model pipeline** (`process/`) — scripts for dataset collection, dataset construction, and classifier training, allowing the bundled model to be reproduced or retrained from scratch.

The project is built entirely on free and open-source components: no paid APIs, no cloud ML services, and no API keys are required to run it.

At a glance, the runtime pipeline is:

```text
Webcam frames
   -> MediaPipe Hand Landmarker (landmark extraction)
   -> RandomForest letter classifier
   -> Debounced letter buffering
   -> Text normalization + spell correction
   -> Optional Bengali translation
   -> gTTS speech synthesis
   -> Caption + audio output in Streamlit
```

And the offline model pipeline is:

```text
Data Collection -> Dataset Build -> Model Training -> Real-time Inference UI
```

---

## Table of contents

- [Features](#features)
- [Project structure](#project-structure)
- [How it works](#how-it-works)
  - [1. Hand detection and letter classification](#1-hand-detection-and-letter-classification)
  - [2. Debounced letter buffering](#2-debounced-letter-buffering)
  - [3. NLP post-processing](#3-nlp-post-processing)
  - [4. Text-to-speech](#4-text-to-speech)
- [Data and training pipeline](#data-and-training-pipeline)
- [Model details](#model-details)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Running the app](#running-the-app)
- [Usage guide](#usage-guide)
- [Configuration](#configuration)
- [Technologies used](#technologies-used)
- [Troubleshooting](#troubleshooting)
- [Known limitations and future improvements](#known-limitations-and-future-improvements)

---

## Features

- **Live camera feed** in the browser via `streamlit-webrtc` — a full-width, camera-first UI with a live caption bar drawn directly on the video frame.
- **Hand-landmark based fingerspelling recognition** — MediaPipe Tasks `HandLandmarker` (up to 2 hands) feeds an 84-feature vector into a trained `RandomForestClassifier` that predicts one of 26 English letters (A–Z) per frame.
- **Stability-gated letter commit** — a predicted letter is only added to the output buffer once it has been held steady for a configurable number of consecutive frames, so a single sign is not registered dozens of times per second.
- **Automatic word-boundary detection** — when no hand is detected for a short window, a space is inserted into the buffer, allowing multiple words to be fingerspelled in one continuous session.
- **NLP post-processing** — the raw letter stream is lower-cased, whitespace-normalized, and spell-corrected word-by-word with `pyspellchecker`, then re-capitalized into a clean caption.
- **Bengali translation** — optional, one-click translation of the corrected English caption into Bengali using `deep-translator`'s free `GoogleTranslator` wrapper (no API key required).
- **Text-to-speech** — the final caption (English or Bengali) is synthesized to MP3 with `gTTS` and autoplayed in-browser via a base64-embedded `<audio>` tag.
- **Buffer controls** — "Generate Speech & Caption" runs the NLP/TTS pipeline on everything signed so far; "Clear Buffer" resets the session.
- **Minimal, modern dark UI** — custom CSS (`core/style.py`) hides the default Streamlit chrome and applies a dark, gradient, rounded-corner theme with a dedicated caption box.
- **Reproducible model pipeline** — a dedicated `process/` directory covers dataset collection, dataset construction, and classifier training, so the shipped model can be regenerated or extended.
- **100% free/open-source stack** — no paid or metered third-party APIs anywhere in the pipeline.

---

## Project structure

```text
Olikbochon/
├── app.py
├── assets/
│   └── logo.png
├── core/
│   ├── __init__.py
│   ├── data/
│   │   └── data.pickle
│   ├── model/
│   │   ├── hand_landmarker.task
│   │   └── model.p
│   ├── nlp_pipeline.py
│   ├── sign_detector.py
│   ├── style.py
│   ├── tts_utils.py
│   └── video_processor.py
├── process/
│   ├── collect_imgs.py
│   ├── create_dataset.py
│   ├── inference_classifier.py
│   ├── test_setup.py
│   ├── train_classifier.py
│   └── data/
│       ├── .DS_Store
│       └── 0 ... 25/            # class-wise folders of training images
├── .gitignore
├── .python-version
├── pyproject.toml
├── requirements.txt
├── uv.lock
└── README.md
```

### Module responsibilities

**Runtime application** (`app.py` + `core/`)

| Module | Responsibility |
|---|---|
| `app.py` | Streamlit entry point — page setup, UI flow, controls, WebRTC integration, output rendering |
| `core/sign_detector.py` | Hand-landmark extraction and model-inference bridge |
| `core/video_processor.py` | Frame-level processing callback, stabilization/debounce logic, live caption overlay, buffer handling |
| `core/nlp_pipeline.py` | Post-processing of detected letters — text cleanup, spell correction, optional Bengali translation |
| `core/tts_utils.py` | gTTS audio generation and browser-playable autoplay `<audio>` helper |
| `core/style.py` | Custom Streamlit CSS / theme customizations |
| `core/model/` | Trained classifier (`model.p`) and MediaPipe hand-landmark model asset (`hand_landmarker.task`) |
| `core/data/data.pickle` | Serialized feature/label dataset produced by the data pipeline, consumed during training |

**Data and model pipeline** (`process/`)

| Script | Responsibility |
|---|---|
| `process/collect_imgs.py` | Captures class-wise hand-sign images from the webcam for dataset creation |
| `process/create_dataset.py` | Builds serialized dataset features (`core/data/data.pickle`) from raw captured images |
| `process/train_classifier.py` | Trains the `RandomForestClassifier` and saves the trained model artifact to `core/model/model.p` |
| `process/inference_classifier.py` | Standalone inference/testing script outside the Streamlit app context |
| `process/test_setup.py` | Environment and setup validation checks for local development |
| `process/data/` | Raw training images, organized into class-wise folders `0`–`25` |

---

## How it works

### 1. Hand detection and letter classification

`core/sign_detector.py` wraps the core inference logic in a `SignDetector` class:

1. Loads the trained model from `core/model/model.p` (a `dict` with a single `"model"` key holding a `sklearn.ensemble.RandomForestClassifier`).
2. Loads MediaPipe's Tasks-API `HandLandmarker` from `core/model/hand_landmarker.task`, downloading it automatically from Google's model storage if the file is not present locally.
3. For every incoming BGR frame (`predict_frame`):
   - Converts the frame to RGB and runs `HandLandmarker.detect()` (supports up to **2 hands**, `min_hand_detection_confidence=0.3`, single-image running mode).
   - Draws the 21-point hand skeleton and landmark dots directly on the frame for visual feedback.
   - Flattens each detected hand's landmark `(x, y)` coordinates into a feature vector, pads/truncates it to match the model's expected input size, and calls `model.predict(...)`.
   - Maps the numeric prediction to a letter via `LABELS_DICT` (`0` → `A`, … `25` → `Z`) and draws a bounding box and letter label over the hand.
   - Returns the annotated frame and the predicted letter (or `None` if no hand is visible).

### 2. Debounced letter buffering

`core/video_processor.py` defines `SignLanguageProcessor(VideoProcessorBase)`, the class handed to `streamlit-webrtc` as the per-frame callback:

- **`STABLE_FRAMES = 15`** (~0.5 s at 30 fps): a predicted letter must repeat for this many consecutive frames before it is committed to the letter buffer — this prevents the same sign from being appended dozens of times per second.
- **`RESET_FRAMES = 20`** (~0.7 s at 30 fps): if no hand is detected for this many consecutive frames, a single space is appended to the buffer (marking a word boundary), and the "last committed" guard is cleared so the same letter can be signed again immediately afterward (for example, double letters like "LL").
- A thread-safe lock protects the shared buffer, since `recv()` runs on a separate WebRTC thread from the main Streamlit thread.
- A live caption bar (the last ~40 buffered characters) is drawn as a semi-transparent bar across the bottom of the video, mimicking a live-caption style overlay.

### 3. NLP post-processing

`core/nlp_pipeline.py` converts the raw letter buffer into a clean caption when **Generate Speech & Caption** is clicked:

1. `letters_to_raw_text` — joins the buffered characters, collapses repeated whitespace, and lower-cases the result.
2. `spell_correct` — splits on whitespace and corrects each word individually with `pyspellchecker`. Single-character tokens are passed through unchanged (uppercased only for the words "a" or "i"), and the final sentence is capitalized.
3. `translate_to_bengali` *(optional)* — translates the corrected English caption to Bengali using `deep-translator`'s `GoogleTranslator`. If translation fails (for example, no internet access), the caption falls back to a visible "Translation unavailable" message rather than crashing the app.

### 4. Text-to-speech

`core/tts_utils.py` synthesizes the final caption (English or Bengali, depending on the sidebar toggle) into MP3 bytes using `gTTS`, and builds a hidden, autoplaying `<audio>` HTML tag (base64 data URI) so the caption is spoken as soon as it is generated. Streamlit's built-in `st.audio` player does not autoplay on its own, so both a visible player and the hidden autoplay tag are rendered together.

---

## Data and training pipeline

The `process/` directory provides an offline workflow for regenerating or extending the bundled classifier, decoupled from the real-time application:

1. **Collect class images** — run `process/collect_imgs.py` to capture webcam images for each letter class into `process/data/<class_id>/`.
2. **Build the dataset** — run `process/create_dataset.py` to extract MediaPipe hand-landmark features from the collected images and serialize them into `core/data/data.pickle`.
3. **Train the classifier** — run `process/train_classifier.py` to fit a `RandomForestClassifier` on the serialized dataset and export the trained model to `core/model/model.p`.
4. **Validate inference** — use `process/inference_classifier.py` for a standalone sanity check outside the Streamlit app, or `process/test_setup.py` to verify the local environment is correctly configured.
5. **Run the app** — the runtime application (`app.py`) automatically picks up the updated model from `core/model/model.p`.

> Keep the label mapping and feature format consistent between the training scripts (`process/`) and the inference code (`core/sign_detector.py`); the classifier expects a fixed-size flattened feature vector across up to two hands.

---

## Model details

| Property | Value |
|---|---|
| Model type | `sklearn.ensemble.RandomForestClassifier` |
| Trees (`n_estimators`) | 100 |
| Input features | 84 (up to 2 hands × 21 landmarks × 2 coordinates `(x, y)`) |
| Output classes | 26 (mapped to letters `A`–`Z` via `LABELS_DICT`) |
| Storage format | Pickled `dict` (`{"model": <classifier>}`) in `core/model/model.p` |
| Hand landmarks | MediaPipe Tasks `HandLandmarker` (`core/model/hand_landmarker.task`, float16 variant) |
| Training dataset | Class-wise raw images under `process/data/0` … `process/data/25` |
| Serialized features | `core/data/data.pickle`, produced by `process/create_dataset.py` |

If retraining the model, keep the feature layout consistent (flattened per-landmark `x, y` pairs across up to two hands), since `core/sign_detector.py` pads/truncates incoming feature vectors to `model.n_features_in_`.

> Note: the bundled model may have been trained with an older scikit-learn release than the one installed locally. Loading it with a newer `scikit-learn` can print an `InconsistentVersionWarning`; this is expected and does not currently prevent inference, but consider retraining or re-pickling the model against your pinned `scikit-learn` version for long-term reliability.

---

## Prerequisites

- **Python 3.11+** (pinned via `.python-version`; `pyproject.toml` requires `>=3.11`)
- A **webcam** and a browser that supports WebRTC (Chrome, Edge, Firefox)
- Internet access for:
  - The first run, to auto-download `hand_landmarker.task` if it is not already present
  - Bengali translation (`deep-translator`) and speech synthesis (`gTTS`), both of which call external free services at runtime
- (Optional) [`uv`](https://github.com/astral-sh/uv) if you prefer the lockfile-based workflow over plain `pip`

---

## Installation

### Option A — using pip and requirements.txt

```bash
git clone https://github.com/miskatul-anwar/Olikbochon.git
cd Olikbochon

python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

### Option B — using uv and the lockfile

```bash
git clone https://github.com/miskatul-anwar/Olikbochon.git
cd Olikbochon

uv sync
```

Either approach installs the same set of dependencies (see [Technologies used](#technologies-used) below).

---

## Running the app

```bash
streamlit run app.py
```

Streamlit prints a local URL (typically `http://localhost:8501`). Open it in a WebRTC-capable browser, grant camera permission when prompted, and click **Start** under the video panel.

---

## Usage guide

1. **Start the camera.** Click **Start** below the video panel to begin streaming from your webcam.
2. **Fingerspell letters.** Hold each hand shape steady for about half a second so it gets committed to the buffer; the live caption bar at the bottom of the video shows what has been captured so far.
3. **Pause between words.** Briefly drop your hand out of frame for under a second to insert a space/word boundary.
4. **Generate the caption.** Click **Generate Speech & Caption**. The buffered letters are spell-corrected, optionally translated to Bengali (sidebar toggle), and converted to speech.
5. **Review the output.** The corrected English caption (and Bengali translation, if enabled) appears in a highlighted caption box, along with an audio player that autoplays the synthesized speech. Expand "Show raw detected letters" to see the uncorrected buffer.
6. **Start over.** Click **Clear Buffer** to reset the letter buffer, captions, and audio, and begin a new session.

### Sidebar controls

| Control | Effect |
|---|---|
| **Translate to Bengali** (toggle) | Enables/disables the Bengali translation step and the "Bengali" speech option |
| **Speak output in** (radio) | Chooses whether the synthesized speech is English or Bengali (Bengali only available when translation is enabled) |

---

## Configuration

The app currently has no `.env` file or externally configurable settings — all tunables live directly in source:

| Setting | File | Default | Purpose |
|---|---|---|---|
| `STABLE_FRAMES` | `core/video_processor.py` | `15` | Frames a letter must hold steady before being committed |
| `RESET_FRAMES` | `core/video_processor.py` | `20` | Frames of no detected hand before inserting a word-boundary space |
| `MODEL_URL` | `core/sign_detector.py` | Google's hosted `hand_landmarker` (float16) | Fallback download source for `hand_landmarker.task` if it is missing locally |
| ICE servers | `app.py` (`RTC_CONFIGURATION`) | Public Google STUN server | WebRTC connectivity; add a TURN server here for stricter/NAT-heavy networks (for example, some cloud deployments) |

No API keys are required — `deep-translator`'s `GoogleTranslator` wrapper and `gTTS` both use free, unauthenticated endpoints.

---

## Technologies used

| Category | Library | Purpose |
|---|---|---|
| Web app / UI | [`streamlit`](https://streamlit.io/) | App framework and UI |
| Live video | [`streamlit-webrtc`](https://github.com/whitphx/streamlit-webrtc) | Browser webcam streaming into Python |
| Video frame I/O | [`av`](https://github.com/PyAV-Org/PyAV) | Converting between WebRTC frames and NumPy arrays |
| Computer vision | [`opencv-python-headless`](https://github.com/opencv/opencv-python) | Frame drawing (landmarks, boxes, caption bar), color conversion |
| Hand tracking | [`mediapipe`](https://developers.google.com/mediapipe) | `HandLandmarker` Tasks API for 21-point hand skeletons |
| Numerical computing | [`numpy`](https://numpy.org/) | Feature vector construction |
| ML classifier | [`scikit-learn`](https://scikit-learn.org/) | `RandomForestClassifier` training and inference |
| Spell-checking | [`pyspellchecker`](https://github.com/barrust/pyspellchecker) | Per-word correction of the raw fingerspelled text |
| Translation | [`deep-translator`](https://github.com/nidhaloff/deep-translator) | Free English to Bengali translation |
| Text-to-speech | [`gTTS`](https://github.com/pndurang/gTTS) | Free MP3 speech synthesis |

---

## Troubleshooting

- **Camera does not start / black video panel.** Confirm your browser has camera permission for the Streamlit site, and that no other application is holding the webcam. `streamlit-webrtc` requires HTTPS or `localhost` for camera access in most browsers.
- **Connection fails when deployed remotely** (for example, behind a NAT/firewall or on a hosted environment). The app only configures a public STUN server by default. Add a TURN server to `RTC_CONFIGURATION` in `app.py` for reliable connectivity in restrictive network environments.
- **`InconsistentVersionWarning` on startup.** `core/model/model.p` was pickled with an older `scikit-learn` release than the one installed. This is a warning, not a fatal error, but consider re-saving the model with your current `scikit-learn` version if you plan to maintain it long-term.
- **"No letters detected yet" when clicking Generate.** Make sure the camera stream is running (`Start` clicked) and that at least one letter has been held steady long enough (`STABLE_FRAMES`) to be committed before generating output.
- **Bengali translation shows "Translation unavailable".** `deep-translator`'s `GoogleTranslator` wrapper needs internet access; check your connection or firewall rules for outbound HTTPS.
- **No audio plays.** Some browsers block autoplay with sound until the user has interacted with the page; the visible `st.audio` player underneath the hidden autoplay tag can always be used to play the caption manually.
- **First run is slow to start.** If `hand_landmarker.task` is not already present, `core/sign_detector.py` downloads it from Google's model storage on first use — this only happens once.
- **Training/inference mismatch.** Ensure the feature structure and label mapping stay identical between the `process/` pipeline scripts and the runtime `core/` modules.

---

## Known limitations and future improvements

- **Fingerspelling only, English alphabet.** The model recognizes the 26 static English letters — there is no support for full ASL/BdSL word signs, numbers, or dynamic gestures.
- **No pre-recorded video upload.** The app is camera-only; there is no path for processing an uploaded video file.
- **Basic spell-checking only.** Correction is a simple per-word dictionary lookup (`pyspellchecker`) with no grammar- or context-aware correction, so word-order or grammatical errors in the fingerspelled sentence are not fixed.
- **Single continuous buffer.** There is no explicit "sentence" concept beyond space-separated words; long sessions accumulate into one buffer until cleared.
- **Dataset storage.** The raw training dataset is versioned directly under `process/data/`; consider an external storage or Git LFS strategy as the dataset grows.
- **No automated tests.** Beyond `process/test_setup.py`, the repository currently has no formal automated test suite.

---


