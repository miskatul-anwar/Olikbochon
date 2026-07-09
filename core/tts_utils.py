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


def custom_audio_player_html(audio_bytes):
    """
    Builds a small, self-contained custom audio player (speaker toggle,
    play/pause button, seek bar) styled to match the app's dark theme.

    Streamlit's built-in st.audio() renders the browser's default media
    controls, which don't match the app's design. Plain <script> tags
    inside st.markdown() are not executed by the browser (Streamlit
    inserts markdown via innerHTML, which never runs embedded scripts) —
    so this returns a full HTML fragment meant to be rendered with
    `st.components.v1.html(...)`, which mounts it in a real iframe where
    the JavaScript actually runs and the controls are interactive.

    Returns "" if there's no audio to play.
    """
    if not audio_bytes:
        return ""
    b64 = base64.b64encode(audio_bytes).decode("utf-8")
    return f"""
    <div style="
        display:flex; align-items:center; gap:14px;
        background:#1b2436; border:1px solid rgba(255,255,255,0.08);
        border-radius:12px; padding:10px 18px;
        font-family:'Poppins','Segoe UI',sans-serif;
    ">
        <span id="olik-speaker" title="Mute/unmute" style="cursor:pointer; font-size:1.05rem; user-select:none;">🔊</span>
        <span id="olik-playpause" title="Play/pause" style="
            cursor:pointer; font-size:0.95rem; user-select:none;
            width:28px; height:28px; border-radius:50%;
            background:#43e97b; color:#05070c; font-weight:700;
            display:flex; align-items:center; justify-content:center;
            flex-shrink:0;
        ">▶</span>
        <input id="olik-seek" type="range" min="0" max="100" value="0" step="0.1" style="
            flex:1; accent-color:#43e97b; height:4px; cursor:pointer;
        ">
        <audio id="olik-audio" autoplay style="display:none;">
            <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
        </audio>
    </div>
    <script>
        const audio = document.getElementById('olik-audio');
        const playBtn = document.getElementById('olik-playpause');
        const seek = document.getElementById('olik-seek');
        const speaker = document.getElementById('olik-speaker');
        let seeking = false;

        playBtn.addEventListener('click', function () {{
            if (audio.paused) {{ audio.play(); }} else {{ audio.pause(); }}
        }});
        speaker.addEventListener('click', function () {{
            audio.muted = !audio.muted;
            speaker.textContent = audio.muted ? '🔇' : '🔊';
        }});
        audio.addEventListener('play', function () {{ playBtn.textContent = '⏸'; }});
        audio.addEventListener('pause', function () {{ playBtn.textContent = '▶'; }});
        audio.addEventListener('timeupdate', function () {{
            if (!seeking && audio.duration) {{
                seek.value = (audio.currentTime / audio.duration) * 100;
            }}
        }});
        seek.addEventListener('input', function () {{ seeking = true; }});
        seek.addEventListener('change', function () {{
            if (audio.duration) {{
                audio.currentTime = (seek.value / 100) * audio.duration;
            }}
            seeking = false;
        }});
    </script>
    """
