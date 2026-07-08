"""
app.py
------
অলীকবচন (Olikbochon) — a monolithic Streamlit application that translates
real-time (fingerspelled) sign language into text captions and speech,
in both English and Bengali.

Run with:
    streamlit run app.py
"""

import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode, RTCConfiguration

from video_processor import SignLanguageProcessor
from nlp_pipeline import run_pipeline
from tts_utils import synthesize_speech, autoplay_audio_html
from style import CUSTOM_CSS

# ----------------------------------------------------------------------------
# Page config (must be first Streamlit call)
# ----------------------------------------------------------------------------
st.set_page_config(
    page_title="অলীকবচন | Olikbochon",
    page_icon="assets/logo.png",
    layout="wide",
    initial_sidebar_state="expanded",
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

# ----------------------------------------------------------------------------
# Sidebar — branding + controls
# ----------------------------------------------------------------------------
with st.sidebar:
    st.image("assets/logo.png", use_container_width=True)
    st.markdown("### Controls")

    bengali_toggle = st.toggle("Translate to Bengali", value=True)
    speech_lang = st.radio(
        "Speak output in:",
        options=["English", "Bengali"] if bengali_toggle else ["English"],
        horizontal=True,
    )

    st.markdown("---")
    st.markdown(
        "**How to use:**\n"
        "1. Click **Start** below the camera to begin.\n"
        "2. Fingerspell letters — hold each letter steady for a beat.\n"
        "3. Pause / drop your hand briefly between words.\n"
        "4. Click **Generate Speech & Caption** when done.\n"
    )
    st.markdown("---")
    st.caption("Free and open-source: MediaPipe, scikit-learn, "
               "pyspellchecker, deep-translator, gTTS")

# ----------------------------------------------------------------------------
# Camera-first video stream
# ----------------------------------------------------------------------------
RTC_CONFIGURATION = RTCConfiguration(
    {"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}
)

ctx = webrtc_streamer(
    key="olikbochon-sign-stream",
    mode=WebRtcMode.SENDRECV,
    rtc_configuration=RTC_CONFIGURATION,
    video_processor_factory=SignLanguageProcessor,
    media_stream_constraints={"video": True, "audio": False},
    async_processing=True,
)

st.write("")

# ----------------------------------------------------------------------------
# Action buttons
# ----------------------------------------------------------------------------
btn_col1, btn_col2, _ = st.columns([1, 1, 2])

with btn_col1:
    generate_clicked = st.button("Generate Speech & Caption", use_container_width=True)

with btn_col2:
    clear_clicked = st.button("Clear Buffer", use_container_width=True)

if clear_clicked and ctx.video_processor:
    ctx.video_processor.clear_buffer()
    st.session_state.english_text = ""
    st.session_state.bengali_text = ""
    st.session_state.raw_text = ""
    st.session_state.audio_bytes = None
    st.rerun()

if generate_clicked:
    if not ctx.video_processor:
        st.warning("Start the camera stream first, then sign a few letters before generating speech.")
    else:
        raw_buffer = ctx.video_processor.get_buffer_copy()
        if not raw_buffer:
            st.warning("No letters detected yet. Sign something first.")
        else:
            with st.spinner("Processing sign language into text..."):
                result = run_pipeline(raw_buffer, translate=bengali_toggle)

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
# Output: final caption + audio
# ----------------------------------------------------------------------------
if st.session_state.english_text:
    st.markdown('<div class="caption-box">', unsafe_allow_html=True)
    st.markdown('<div class="caption-label">Detected caption</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="caption-text-en">{st.session_state.english_text}</div>',
                unsafe_allow_html=True)

    if st.session_state.bengali_text:
        st.markdown(f'<div class="caption-text-bn">{st.session_state.bengali_text}</div>',
                     unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    if st.session_state.audio_bytes:
        st.write("")
        st.audio(st.session_state.audio_bytes, format="audio/mp3")
        st.markdown(autoplay_audio_html(st.session_state.audio_bytes), unsafe_allow_html=True)

    with st.expander("Show raw detected letters"):
        st.code(st.session_state.raw_text or "", language=None)
else:
    st.info("Your generated caption will appear here after you click **Generate Speech & Caption**.")
