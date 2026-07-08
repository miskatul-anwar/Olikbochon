"""
style.py
--------
Custom CSS injected via st.markdown to hide default Streamlit chrome
(hamburger menu, footer, header) and give the app a minimal, modern,
sleek, camera-first look.
"""

CUSTOM_CSS = """
<style>
    /* ---- Hide default Streamlit chrome ---- */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    div[data-testid="stToolbar"] {visibility: hidden; height: 0;}
    div[data-testid="stDecoration"] {visibility: hidden; height: 0;}
    div[data-testid="stStatusWidget"] {visibility: hidden; height: 0;}

    /* ---- Global look & feel ---- */
    html, body, [class*="css"] {
        font-family: 'Poppins', 'Segoe UI', sans-serif;
    }

    .stApp {
        background: radial-gradient(circle at 20% 0%, #101826 0%, #05070c 60%);
        color: #f5f7fa;
    }

    section[data-testid="stSidebar"] {
        background: #0b1120;
        border-right: 1px solid rgba(255,255,255,0.06);
    }

    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
        max-width: 1200px;
    }

    /* ---- Camera container ---- */
    div[data-testid="stVideo"], .video-wrapper video {
        border-radius: 18px;
        overflow: hidden;
    }

    /* ---- Caption box (for the final processed text under the video) ---- */
    .caption-box {
        margin-top: 1rem;
        padding: 1.4rem 1.6rem;
        background: rgba(255, 255, 255, 0.04);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        text-align: center;
    }

    .caption-text-en {
        font-size: 2.0rem;
        font-weight: 600;
        color: #ffffff;
        line-height: 1.3;
    }

    .caption-text-bn {
        font-size: 1.9rem;
        font-weight: 600;
        color: #43e97b;
        margin-top: 0.4rem;
        line-height: 1.4;
    }

    .caption-label {
        text-transform: uppercase;
        letter-spacing: 1.5px;
        font-size: 0.7rem;
        color: #6c7a89;
        margin-bottom: 0.4rem;
    }

    /* ---- Buttons ---- */
    .stButton > button {
        border-radius: 10px;
        border: 1px solid rgba(255, 255, 255, 0.12);
        padding: 0.6rem 1.4rem;
        font-weight: 600;
        width: 100%;
        background: #1b2436;
        color: #f5f7fa;
        transition: background 0.15s ease, border-color 0.15s ease;
    }

    .stButton > button:hover {
        background: #232f45;
        border-color: rgba(255, 255, 255, 0.25);
        color: #f5f7fa;
    }

    hr {
        border-color: rgba(255,255,255,0.08);
    }
</style>
"""
