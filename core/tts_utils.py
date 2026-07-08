"""
tts_utils.py
------------
Free, open-source Text-to-Speech using gTTS, returned as in-memory audio
bytes. Includes a helper to build an autoplaying HTML <audio> tag via a
base64 data URI, since Streamlit's native st.audio does not autoplay.
"""

import base64
from io import BytesIO
from gtts import gTTS


def synthesize_speech(text, lang="en"):
    """
    Returns raw MP3 bytes for the given text using gTTS.
    lang: 'en' for English, 'bn' for Bengali.
    """
    if not text or not text.strip():
        return None
    try:
        tts = gTTS(text=text, lang=lang)
        buf = BytesIO()
        tts.write_to_fp(buf)
        buf.seek(0)
        return buf.read()
    except Exception:
        return None


def autoplay_audio_html(audio_bytes):
    """
    Builds an HTML <audio> tag with base64-embedded MP3 data and the
    `autoplay` attribute set, so the caption is spoken automatically
    the moment it's generated (Streamlit's st.audio alone won't autoplay).
    """
    if not audio_bytes:
        return ""
    b64 = base64.b64encode(audio_bytes).decode("utf-8")
    return f"""
        <audio autoplay="true" style="display:none;">
            <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
        </audio>
    """
