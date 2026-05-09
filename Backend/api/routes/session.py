"""
Backend/api/routes/session.py
───────────────────────────────
FastAPI routes for session lifecycle management.

POST /api/session/start  → registers username with session
POST /api/session/end    → saves history to JSON, clears session
"""

from fastapi import APIRouter
from pydantic import BaseModel
from Backend.api.session_store import get_session, clear_session
from Backend.utils.history_writer import save_session

router = APIRouter()


# ── Request models ─────────────────────────────────────────────────────────────
class SessionStartRequest(BaseModel):
    session_id: str
    username:   str


class SessionEndRequest(BaseModel):
    session_id: str


# ── POST /api/session/start ────────────────────────────────────────────────────
@router.post("/session/start")
async def start_session(request: SessionStartRequest):
    """
    Registers a username with a session.
    Called from Streamlit when patient clicks Start on welcome page.
    Creates session in session_store with username + start_time.
    """
    from datetime import datetime

    session = get_session(request.session_id)
    session["username"]   = request.username
    session["start_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    session["session_id"] = request.session_id
    session["messages"]   = []      # full message log for history
    session["last_priority"] = "low"

    print(f"✅ Session started — user: {request.username} | id: {request.session_id[:8]}")

    return {
        "status":     "started",
        "username":   request.username,
        "session_id": request.session_id
    }


# ── POST /api/session/end ──────────────────────────────────────────────────────
@router.post("/session/end")
async def end_session(request: SessionEndRequest):
    """
    Ends a session:
    1. Saves full session history to JSON file
    2. Clears session from memory
    Called from Streamlit when patient clicks End Session.
    """
    session = get_session(request.session_id)

    # Save to JSON file
    filepath = save_session(session)

    # Clear from memory
    clear_session(request.session_id)

    print(f"✅ Session ended — saved to {filepath}")

    return {
        "status":   "ended",
        "saved_to": filepath
    }