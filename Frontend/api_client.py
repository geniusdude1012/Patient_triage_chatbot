import httpx
import streamlit as st

API_URL = "http://localhost:8000/api"

def send_message(message: str, session_id: str) -> dict:
    try:
        r = httpx.post(
            f"{API_URL}/chat",
            json={"message": message, "session_id": session_id},
            timeout=60
        )
        return r.json()
    except Exception as e:
        return {"response": f"Error: {e}", "priority": "low"}

def clear_session(session_id: str):
    httpx.post(f"{API_URL}/clear/{session_id}")