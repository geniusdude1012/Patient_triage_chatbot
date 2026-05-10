import streamlit as st
import uuid
from api_client import send_message, clear_session, start_session, end_session
from components.chat_ui import render_message
from components.welcome_page import show_welcome_page
from components.voice_input import show_voice_input

st.set_page_config(page_title="Patient Triage Assistant", page_icon="🏥")

st.markdown("""
    <style>
    /* Sidebar is ~244px wide — push input to start after it */
    .stChatInput {
        position: fixed !important;
        bottom: 0 !important;
        left: 244px !important;
        right: 0 !important;
        z-index: 999 !important;
        padding: 1rem !important;
        background: var(--background-color) !important;
    }

    .main .block-container {
        padding-bottom: 100px !important;
    }

    /* Make audio input compact */
    div[data-testid="stAudioInput"] {
        max-width: 60px !important;
    }
    </style>
""", unsafe_allow_html=True)

# Session state initialisation
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = []
if "started" not in st.session_state:
    st.session_state.started = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "greeted" not in st.session_state:
    st.session_state.greeted = False
if "voice_counter" not in st.session_state:
    st.session_state.voice_counter = 0


if not st.session_state.started:
    show_welcome_page()


# CHAT PAGE

else:
    st.title("🏥 Patient Triage Assistant")

    # Sidebar
    with st.sidebar:
        st.markdown(f"### 👤 {st.session_state.username}")
        st.caption(f"Session: {st.session_state.session_id[:8]}...")
        st.divider()

        if st.button("🔚 New Chat", use_container_width=True, type="primary"):
            end_session(st.session_state.session_id)
            st.session_state.started       = False
            st.session_state.username      = ""
            st.session_state.messages      = []
            st.session_state.greeted       = False
            st.session_state.session_id    = str(uuid.uuid4())
            st.session_state.voice_counter = 0
            st.rerun()

        st.divider()

        if st.button("🔄 Clear conversation", use_container_width=True):
            clear_session(st.session_state.session_id)
            st.session_state.messages      = []
            st.session_state.greeted       = False
            st.session_state.voice_counter = 0
            st.rerun()

    # Greeting — shown once
    if not st.session_state.greeted:
        greeting = f"Hi **{st.session_state.username}**! 👋 What can I help you with today?"
        st.session_state.messages.append({
            "role":     "assistant",
            "content":  greeting,
            "priority": "low"
        })
        st.session_state.greeted = True

    # Message history
    for msg in st.session_state.messages:
        render_message(msg["role"], msg["content"], msg.get("priority", "low"))

    # INPUT ROW — text input (left) + mic icon (right)
    
    # Chat input at top level — always sticks to bottom
    user_input = st.chat_input("Describe your symptoms...")

    # Mic recorder in a container above the input
    with st.container():
        voice_key  = f"mic_{st.session_state.voice_counter}"
    voice_text = show_voice_input(key=voice_key)
    
    # SHARED INPUT HANDLER
   
    def handle_input(text: str, is_voice: bool = False):
        display_text = f"🎙️ {text}" if is_voice else text

        st.session_state.messages.append({
            "role":    "user",
            "content": display_text
        })
        render_message("user", display_text)

        with st.spinner("Analyzing..."):
            result = send_message(
                text,
                st.session_state.session_id,
                st.session_state.username
            )

        response = result.get("response", "Sorry, something went wrong.")
        priority = result.get("priority", "low")

        st.session_state.messages.append({
            "role":     "assistant",
            "content":  response,
            "priority": priority
        })
        render_message("assistant", response, priority)

    # Handle typed input
    if user_input:
        handle_input(user_input, is_voice=False)

    # Handle voice input
    if voice_text:
        st.toast(f"🗣️ Heard: \"{voice_text}\"", icon="🎙️")
        handle_input(voice_text, is_voice=True)
        st.session_state.voice_counter += 1
        st.rerun()