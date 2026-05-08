import streamlit as st

PRIORITY_COLORS = {
    "critical": "#FF4B4B",
    "urgent":   "#FF8C00",
    "routine":  "#FFC300",
    "low":      "#00C853"
}

def render_message(role: str, content: str, priority: str = "low"):
    if role == "user":
        with st.chat_message("user"):
            st.markdown(content)
    else:
        color = PRIORITY_COLORS.get(priority, "#00C853")
        with st.chat_message("assistant"):
            if priority in ("critical", "urgent"):
                st.markdown(
                    f'<div style="border-left:4px solid {color};padding:8px 12px;'
                    f'border-radius:4px;background:{color}18">{content}</div>',
                    unsafe_allow_html=True
                )
            else:
                st.markdown(content)