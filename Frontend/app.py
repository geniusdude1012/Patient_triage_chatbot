"""
Frontend/app.py
────────────────
Main Streamlit entry point.

Flow:
- If not started → show welcome page (name input)
- If started     → show chat interface with username greeting
- End Session    → saves history, resets to welcome page
"""

import streamlit as st
import uuid
from api_client import send_message, clear_session, start_session, end_session
from components.chat_ui import render_message
from components.welcome_page import show_welcome_page

st.set_page_config(page_title="Patient Triage Assistant", page_icon="🏥")

# ── Session state initialisation ──────────────────────────────────────────────
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

# ══════════════════════════════════════════════════════════════════════════════
# WELCOME PAGE — shown until patient enters name and clicks Start
# ══════════════════════════════════════════════════════════════════════════════
if not st.session_state.started:
    show_welcome_page()

    # After show_welcome_page sets started=True and calls rerun(),
    # register the session with FastAPI
    if st.session_state.started:
        start_session(st.session_state.session_id, st.session_state.username)

# ══════════════════════════════════════════════════════════════════════════════
# CHAT PAGE — shown after patient enters name
# ══════════════════════════════════════════════════════════════════════════════
else:
    st.title("🏥 Patient Triage Assistant")

    # ── Sidebar ────────────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown(f"### 👤 {st.session_state.username}")
        st.caption(f"Session: {st.session_state.session_id[:8]}...")
        st.divider()

        # End Session button — saves history and returns to welcome page
        if st.button("🔚 End Session", use_container_width=True, type="primary"):
            end_session(st.session_state.session_id)

            # Reset all session state → go back to welcome page
            st.session_state.started    = False
            st.session_state.username   = ""
            st.session_state.messages   = []
            st.session_state.greeted    = False
            st.session_state.session_id = str(uuid.uuid4())  # fresh ID
            st.rerun()

        st.divider()

        # Clear conversation (keeps username, resets chat only)
        if st.button("🔄 Clear conversation", use_container_width=True):
            clear_session(st.session_state.session_id)
            st.session_state.messages = []
            st.session_state.greeted  = False
            st.rerun()

    # ── Greeting message — shown once at session start ─────────────────────────
    if not st.session_state.greeted:
        greeting = f"Hi **{st.session_state.username}**! 👋 What can I help you with today?"
        st.session_state.messages.append({
            "role":     "assistant",
            "content":  greeting,
            "priority": "low"
        })
        st.session_state.greeted = True

    # ── Display full message history ───────────────────────────────────────────
    for msg in st.session_state.messages:
        render_message(msg["role"], msg["content"], msg.get("priority", "low"))

    # ── Chat input ─────────────────────────────────────────────────────────────
    if user_input := st.chat_input("Describe your symptoms..."):
        # Show and store user message
        st.session_state.messages.append({
            "role":    "user",
            "content": user_input
        })
        render_message("user", user_input)

        # Call FastAPI triage pipeline
        with st.spinner("Analyzing..."):
            result = send_message(
                user_input,
                st.session_state.session_id,
                st.session_state.username
            )

        response = result.get("response", "Sorry, something went wrong.")
        priority = result.get("priority", "low")

        # Show and store bot response
        st.session_state.messages.append({
            "role":     "assistant",
            "content":  response,
            "priority": priority
        })
        render_message("assistant", response, priority)