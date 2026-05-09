"""
Frontend/components/welcome_page.py
─────────────────────────────────────
Welcome landing page shown before the chatbot starts.
Patient enters their name and clicks Start.
Sets session_state.username and session_state.started = True.
"""

import streamlit as st
from api_client import start_session  


def show_welcome_page():
    """
    Renders the full welcome page.
    Called from app.py when st.session_state.started is False.
    """

    # ── Centered layout ────────────────────────────────────────────────────────
    st.markdown("<br><br>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown(
            """
            <div style="text-align:center;">
                <h1>🏥</h1>
                <h2>Welcome to Patient Triage Assistant</h2>
                <p style="color:gray;font-size:15px;">
                    I'll help you find the right care quickly.<br>
                    Please enter your name to get started.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Name input form ────────────────────────────────────────────────────
        with st.form("welcome_form", clear_on_submit=False):
            name = st.text_input(
                "Your name",
                placeholder="Enter your name...",
                label_visibility="collapsed"
            )
            submitted = st.form_submit_button(
                "Start Consultation →",
                use_container_width=True,
                type="primary"
            )

            if submitted:
                 if not name.strip():
                    st.error("Please enter your name to continue.")
                 else:
                    st.session_state.username = name.strip()
                    st.session_state.started  = True
                    # ✅ Call API BEFORE rerun — not after
                    start_session(st.session_state.session_id, name.strip())
                    st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(
            "<p style='text-align:center;color:gray;font-size:12px;'>"
            "⚠️ This is AI-assisted triage and not a medical diagnosis.</p>",
            unsafe_allow_html=True
        )