# syntax=docker/dockerfile:1

FROM python:3.11-slim

# --- System dependencies -----------------------------------------------
# - libgl1 / libglib2.0-0 / libsm6 / libxext6 / libxrender1: required by
#   OpenCV (cv2) for its minimal X11/GL runtime even in headless environments.
# - libgles2 / libegl1 / libgl1-mesa-dri: MediaPipe's HandLandmarker
#   dlopen()s libGLESv2.so.2 (and libEGL.so.1) for its GPU delegate even
#   when running in IMAGE mode — without these, task creation fails with
#   "OSError: libGLESv2.so.2: cannot open shared object file".
# - ffmpeg (+ libavdevice/libavformat/libavcodec/libswscale/libswresample):
#   required by PyAV (`av`), which streamlit-webrtc uses for encoding/
#   decoding the live video stream.
# - curl: used below to install `uv`.
RUN apt-get update && apt-get install -y --no-install-recommends \
        libgl1 \
        libglib2.0-0 \
        libsm6 \
        libxext6 \
        libxrender1 \
        libgles2 \
        libegl1 \
        libgl1-mesa-dri \
        ffmpeg \
        libavdevice-dev \
        libavformat-dev \
        libavcodec-dev \
        libswscale-dev \
        libswresample-dev \
        curl \
    && rm -rf /var/lib/apt/lists/*

# --- uv (fast Python package manager, matches the committed uv.lock) ---
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

WORKDIR /app

# Install dependencies first (better layer caching): only re-run `uv sync`
# when pyproject.toml / uv.lock actually change.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev

# Now copy the rest of the project (app code, core/ package, assets,
# and the bundled model files under core/model/).
COPY . .

RUN uv sync --frozen --no-dev

# Make sure the venv's binaries (streamlit, python, etc.) are on PATH.
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

ENTRYPOINT ["streamlit", "run", "app.py", \
    "--server.port=8501", \
    "--server.address=0.0.0.0"]
