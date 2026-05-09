"""
Frontend/api_client.py
───────────────────────
All HTTP calls from Streamlit to FastAPI.
Single place for all API communication.
"""

import httpx

API_URL = "http://localhost:8000/api"


def send_message(message: str, session_id: str, username: str = "") -> dict:
    """POST /api/chat — sends user message, returns triage response."""
    try:
        r = httpx.post(
            f"{API_URL}/chat",
            json={
                "message":    message,
                "session_id": session_id,
                "username":   username
            },
            timeout=60
        )
        return r.json()
    except Exception as e:
        return {"response": f"Connection error: {e}", "priority": "low"}


def start_session(session_id: str, username: str) -> dict:
    """POST /api/session/start — registers username with session."""
    try:
        r = httpx.post(
            f"{API_URL}/session/start",
            json={"session_id": session_id, "username": username},
            timeout=10
        )
        return r.json()
    except Exception as e:
        print(f"start_session error: {e}")
        return {}


def end_session(session_id: str) -> dict:
    """POST /api/session/end — saves history to JSON and clears session."""
    try:
        r = httpx.post(
            f"{API_URL}/session/end",
            json={"session_id": session_id},
            timeout=10
        )
        return r.json()
    except Exception as e:
        print(f"end_session error: {e}")
        return {}


def clear_session(session_id: str) -> dict:
    """POST /api/clear/{session_id} — clears session without saving."""
    try:
        r = httpx.post(f"{API_URL}/clear/{session_id}", timeout=10)
        return r.json()
    except Exception as e:
        print(f"clear_session error: {e}")
        return {}