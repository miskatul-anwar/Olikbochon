"""
app.py
------
অলীকবচন (Olikbochon) — a monolithic Streamlit application that translates
real-time (fingerspelled) sign language into text captions and speech,
in both English and Bengali.

Run with:
    streamlit run app.py
"""

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from streamlit_webrtc import (
    webrtc_streamer,
    WebRtcMode,
    RTCConfiguration,
    VideoHTMLAttributes,
)

from core.video_processor import SignLanguageProcessor
from core.nlp_pipeline import run_pipeline
from core.tts_utils import synthesize_speech, custom_audio_player_html
from core.style import CUSTOM_CSS

# ----------------------------------------------------------------------------
# Page config (must be first Streamlit call)
# ----------------------------------------------------------------------------
st.set_page_config(
    page_title="অলীকবচন | Olikbochon",
    page_icon="assets/logo.png",
    layout="wide",
)

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ----------------------------------------------------------------------------
# Session state defaults
# ----------------------------------------------------------------------------
if "english_text" not in st.session_state:
    st.session_state.english_text = ""
if "bengali_text" not in st.session_state:
    st.session_state.bengali_text = ""
if "raw_text" not in st.session_state:
    st.session_state.raw_text = ""
if "audio_bytes" not in st.session_state:
    st.session_state.audio_bytes = None
if "detection_log" not in st.session_state:
    st.session_state.detection_log = []

# ----------------------------------------------------------------------------
# Logo — top of the page, small and centered
# ----------------------------------------------------------------------------
logo_col_left, logo_col_center, logo_col_right = st.columns([1, 1, 1])
with logo_col_center:
    st.image("assets/logo.png", use_container_width=True)

# ----------------------------------------------------------------------------
# Camera-first video stream
# ----------------------------------------------------------------------------
import base64
import json
import os
import urllib.request


def _get_secret(key):
    """Reads from Streamlit secrets first (st.secrets), then env vars —
    works whether you're on Community Cloud (secrets.toml via the
    dashboard) or Fly.io/Docker (env vars / `fly secrets set`)."""
    try:
        if key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    return os.environ.get(key)


@st.cache_data(ttl=3000)  # Twilio tokens are valid ~24h; refresh well before that
def _fetch_twilio_ice_servers(account_sid, auth_token):
    url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Tokens.json"
    credentials = base64.b64encode(f"{account_sid}:{auth_token}".encode()).decode()
    req = urllib.request.Request(
        url, method="POST", headers={"Authorization": f"Basic {credentials}"}
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read())["ice_servers"]


def get_ice_servers():
    """
    A STUN-only config isn't enough here: Streamlit Community Cloud (and
    plenty of office/campus networks) blocks direct peer-to-peer WebRTC
    traffic, which is what causes the "Connection is taking longer than
    expected" error — a TURN relay is required to work around that.

    Priority:
      1. Twilio's Network Traversal Service, if TWILIO_ACCOUNT_SID /
         TWILIO_AUTH_TOKEN are set as Streamlit secrets or env vars —
         the option streamlit-webrtc's own docs recommend as most stable.
      2. The Open Relay Project's free public TURN server as a no-signup
         fallback — works immediately with zero setup, though (being
         free/shared) it's not guaranteed 100% uptime.
    """
    account_sid = _get_secret("TWILIO_ACCOUNT_SID")
    auth_token = _get_secret("TWILIO_AUTH_TOKEN")

    if account_sid and auth_token:
        try:
            return _fetch_twilio_ice_servers(account_sid, auth_token)
        except Exception:
            pass  # fall through to the free relay below

    return [
        {"urls": ["stun:stun.l.google.com:19302"]},
        {
            "urls": ["turn:openrelay.metered.ca:80"],
            "username": "openrelayproject",
            "credential": "openrelayproject",
        },
        {
            "urls": ["turn:openrelay.metered.ca:443"],
            "username": "openrelayproject",
            "credential": "openrelayproject",
        },
        {
            "urls": ["turn:openrelay.metered.ca:443?transport=tcp"],
            "username": "openrelayproject",
            "credential": "openrelayproject",
        },
    ]


RTC_CONFIGURATION = RTCConfiguration({"iceServers": get_ice_servers()})

# NOTE on the Start/Stop + "Select Device" control that appears directly
# under the video: streamlit-webrtc renders the live video *and* its
# Start/Stop/device-select controls together as a single component — the
# public API doesn't expose a way to split them into separate widgets, so
# that control can't be relocated into the button row below without
# patching the third-party package itself. It stays in its native spot
# here, immediately under the video.
#
# NOTE on sizing: streamlit-webrtc renders the video inside its own
# component <iframe>, which starts at a small default height and only
# grows to fit whatever is inside it. Sizing the video with `vh` (percent
# of *viewport* height) doesn't work here because inside that iframe, `vh`
# is relative to the iframe's own (still-tiny) height, not your browser
# window. Fixed pixel dimensions sidestep that problem and reliably
# render at a large, consistent, landscape size matching the design.
#
# The box below uses `aspect-ratio: 16/9` + `height: auto` (instead of a
# hardcoded pixel height) together with a matching 16:9 `ideal` camera
# request. That way the rendered box always matches the actual stream's
# proportions exactly, so `object-fit: contain` never has to letterbox
# (empty bars) or crop the frame — whatever width the column gives it,
# the height follows automatically at the correct ratio.
cam_col_left, cam_col_center, cam_col_right = st.columns([1, 10, 1])

with cam_col_center:
    ctx = webrtc_streamer(
        key="olikbochon-sign-stream",
        mode=WebRtcMode.SENDRECV,
        rtc_configuration=RTC_CONFIGURATION,
        video_processor_factory=SignLanguageProcessor,
        media_stream_constraints={
            "video": {
                "width": {"ideal": 1280},
                "height": {"ideal": 720},
                "aspectRatio": {"ideal": 1.7777777778},
            },
            "audio": False,
        },
        async_processing=True,
        video_html_attrs=VideoHTMLAttributes(
            autoPlay=True,
            controls=False,
            style={
                "width": "100%",
                "aspect-ratio": "16 / 9",
                "height": "auto",
                "display": "block",
                "object-fit": "contain",
            },
        ),
    )

# ----------------------------------------------------------------------------
# Controls — inline in the main UI (no sidebar)
# ----------------------------------------------------------------------------
st.markdown("### Controls")

ctrl_col1, ctrl_col2, ctrl_col_spacer, ctrl_col3 = st.columns([1, 1, 0.6, 1.2])

with ctrl_col1:
    bengali_toggle = st.toggle("Translate to Bengali", value=True)

with ctrl_col2:
    autocorrect_toggle = st.toggle("Auto-correct spelling", value=True)

with ctrl_col3:
    speech_lang = st.radio(
        "Speak output in:",
        options=["English", "Bengali"] if bengali_toggle else ["English"],
        horizontal=True,
    )

# ----------------------------------------------------------------------------
# Editable buffer — lets the user add or remove any letter, at any
# position, before generating the caption/speech. This text field IS the
# buffer that gets fed into the pipeline: click anywhere in it and type,
# backspace, or paste like any normal text box (Space marks a word break,
# same as when the camera detects a pause in signing).
#
# `_sync_edit_buffer` is applied here, *before* the `st.text_input(key=
# "edit_buffer", ...)` widget below is instantiated, because Streamlit
# forbids writing to `st.session_state[key]` once a widget with that key
# has already been created during the current run.
# ----------------------------------------------------------------------------
if "edit_buffer" not in st.session_state:
    st.session_state.edit_buffer = ""
if "_sync_edit_buffer" not in st.session_state:
    st.session_state._sync_edit_buffer = False

if st.session_state._sync_edit_buffer:
    if ctx.video_processor:
        st.session_state.edit_buffer = "".join(ctx.video_processor.get_buffer_copy())
    st.session_state._sync_edit_buffer = False

st.markdown("### Edit Buffer")
st.caption(
    "This is exactly what becomes your caption. Click anywhere in the box "
    "to add or remove letters — e.g. detected \u201cA CAB\u201d? Edit it to "
    "\u201cA CAT\u201d or \u201cA BAT\u201d before generating."
)

edit_col1, edit_col2 = st.columns([4, 1])

with edit_col1:
    st.text_input(
        "Detected letters (editable)",
        key="edit_buffer",
        label_visibility="collapsed",
        placeholder="Sign to fill this in, or type/paste letters directly...",
    )

with edit_col2:
    sync_clicked = st.button("⟳ Load from Camera", use_container_width=True)

if sync_clicked:
    if ctx.video_processor:
        st.session_state._sync_edit_buffer = True
        st.rerun()
    else:
        st.warning("Start the camera stream first.")

# ----------------------------------------------------------------------------
# Action buttons
# ----------------------------------------------------------------------------
btn_col1, btn_col2, _ = st.columns([1, 1, 2])

with btn_col1:
    generate_clicked = st.button("Generate Speech & Caption", use_container_width=True)

with btn_col2:
    clear_clicked = st.button("Clear Buffer", use_container_width=True)

if clear_clicked:
    if ctx.video_processor:
        ctx.video_processor.clear_buffer()
    st.session_state.english_text = ""
    st.session_state.bengali_text = ""
    st.session_state.raw_text = ""
    st.session_state.audio_bytes = None
    st.session_state.detection_log = []
    st.session_state.edit_buffer = ""
    st.rerun()

if generate_clicked:
    # The editable buffer is the primary source of truth (it's what the
    # user sees and can freely add/remove letters from). If it's still
    # empty — e.g. they haven't clicked "Load from Camera" yet — fall
    # back to whatever the camera has detected live, same as before.
    source_text = st.session_state.edit_buffer
    if not source_text.strip() and ctx.video_processor:
        source_text = "".join(ctx.video_processor.get_buffer_copy())

    if not source_text.strip():
        st.warning(
            "No letters to work with yet. Sign something and click "
            "**⟳ Load from Camera**, or type letters directly into the "
            "editable buffer above."
        )
    else:
        st.session_state.detection_log = (
            ctx.video_processor.get_detection_log_copy() if ctx.video_processor else []
        )

        edited_buffer = list(source_text)

        with st.spinner("Processing sign language into text..."):
            result = run_pipeline(
                edited_buffer,
                translate=bengali_toggle,
                autocorrect=autocorrect_toggle,
            )

        st.session_state.raw_text = result["raw"]
        st.session_state.english_text = result["english"]
        st.session_state.bengali_text = result["bengali"] or ""

        # TTS
        tts_lang = "bn" if speech_lang == "Bengali" and st.session_state.bengali_text else "en"
        tts_text = (
            st.session_state.bengali_text
            if tts_lang == "bn"
            else st.session_state.english_text
        )
        with st.spinner("Synthesizing speech..."):
            st.session_state.audio_bytes = synthesize_speech(tts_text, lang=tts_lang)

# ----------------------------------------------------------------------------
# Output: Detected Caption card (english + bengali + raw table + speech)
# ----------------------------------------------------------------------------
if st.session_state.english_text:
    with st.container(border=True):
        st.markdown('<div class="caption-label">Detected Caption</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="caption-text-en">{st.session_state.english_text}</div>',
                    unsafe_allow_html=True)

        if st.session_state.bengali_text:
            st.markdown(f'<div class="caption-text-bn">{st.session_state.bengali_text}</div>',
                         unsafe_allow_html=True)

        with st.expander("Show raw detected letters"):
            if st.session_state.detection_log:
                df = pd.DataFrame(st.session_state.detection_log)
                df = df.rename(columns={
                    "letter": "Sign",
                    "timestamp": "Timestamp",
                    "confidence": "Confidence",
                })
                df["Confidence"] = df["Confidence"].apply(
                    lambda c: f"{c:.2f}" if isinstance(c, (int, float)) else "—"
                )
                st.dataframe(df, hide_index=True, use_container_width=True)
            else:
                st.code(st.session_state.raw_text or "", language=None)

        if st.session_state.audio_bytes:
            st.markdown("**Speech Output**")
            components.html(
                custom_audio_player_html(st.session_state.audio_bytes),
                height=70,
            )
else:
    st.info("Your generated caption will appear here after you click **Generate Speech & Caption**.")
