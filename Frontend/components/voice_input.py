"""
Frontend/components/voice_input.py
────────────────────────────────────
Inline mic button styled to sit beside the chat input.
Uses st.audio_input with a unique key to avoid duplicate ID error.
Transcribes via OpenAI Whisper and returns text.
"""

import streamlit as st
import sys
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from Backend.services.transcriber import transcribe_audio


def show_voice_input(key: str = "voice_input_main") -> str | None:
    """
    Renders a compact mic recorder with unique key.
    Returns transcribed text or None.
    """
    # ── Inject CSS to make audio_input look like a mic icon ───────────────────
    st.markdown("""
        <style>
        /* Hide the default audio_input label */
        div[data-testid="stAudioInput"] > label {
            display: none !important;
        }
        /* Make the recorder compact and icon-like */
        div[data-testid="stAudioInput"] {
            margin: 0 !important;
            padding: 0 !important;
        }
        div[data-testid="stAudioInput"] > div {
            border: none !important;
            background: transparent !important;
            padding: 0 !important;
        }
        </style>
    """, unsafe_allow_html=True)

    audio = st.audio_input(
        label="voice",
        key=key,
        label_visibility="collapsed"
    )

    if audio is not None:
        with st.spinner("Transcribing..."):
            audio_bytes = audio.read()
            text = transcribe_audio(audio_bytes)

        if text:
            return text
        else:
            st.toast("Could not transcribe. Please try again.", icon="⚠️")

    return None