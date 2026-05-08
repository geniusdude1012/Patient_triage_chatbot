import streamlit as st
import uuid
from api_client import send_message, clear_session
from components.chat_ui import render_message

st.set_page_config(page_title="Patient Triage Assistant", page_icon="🏥")
st.title("🏥 Patient Triage Assistant")

# Session ID — unique per browser tab
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = []

# Sidebar
with st.sidebar:
    st.header("Session")
    st.caption(f"ID: {st.session_state.session_id[:8]}...")
    if st.button("🔄 Clear conversation"):
        clear_session(st.session_state.session_id)
        st.session_state.messages = []
        st.rerun()

# Display history
for msg in st.session_state.messages:
    render_message(msg["role"], msg["content"], msg.get("priority", "low"))

# Input
if user_input := st.chat_input("Describe your symptoms..."):
    st.session_state.messages.append({"role": "user", "content": user_input})
    render_message("user", user_input)

    with st.spinner("Analyzing..."):
        result = send_message(user_input, st.session_state.session_id)

    response = result.get("response", "Sorry, something went wrong.")
    priority = result.get("priority", "low")

    st.session_state.messages.append({
        "role": "assistant",
        "content": response,
        "priority": priority
    })
    render_message("assistant", response, priority)