"""
Backend/api/routes/chat.py
────────────────────────────
POST /api/chat  — main triage endpoint
POST /api/clear — clears session without saving
"""

from fastapi import APIRouter
from Backend.api.schemas import ChatRequest, ChatResponse
from Backend.api.session_store import get_session, clear_session, append_message
from Backend.services.triage_engine import process
import Backend.utils.state_manager as state

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Full triage pipeline per message:
    1. Load session state into state_manager
    2. Log user message to session history
    3. Run triage_engine.process()
    4. Log bot response to session history
    5. Save state back to session
    6. Detect priority from response emojis
    7. Return ChatResponse
    """
    # ── Load session state ─────────────────────────────────────────────────────
    session = get_session(request.session_id)
    state.chat_history[:]        = session["chat_history"]
    state.accumulated_symptoms[:] = session["accumulated_symptoms"]

    # ── Log user message to full history ──────────────────────────────────────
    append_message(request.session_id, "user", request.message)

    # ── Run triage pipeline ────────────────────────────────────────────────────
    response = process(request.message)

    # ── Log bot response to full history ──────────────────────────────────────
    append_message(request.session_id, "bot", response)

    # ── Save updated state back to session ────────────────────────────────────
    session["chat_history"]        = list(state.chat_history)
    session["accumulated_symptoms"] = list(state.accumulated_symptoms)

    # ── Detect priority from response emojis ──────────────────────────────────
    priority = "low"
    if   "🔴" in response: priority = "critical"
    elif "🟠" in response: priority = "urgent"
    elif "🟡" in response: priority = "routine"

    # ── Track last priority for history file ──────────────────────────────────
    session["last_priority"] = priority

    return ChatResponse(
        response=response,
        priority=priority,
        session_id=request.session_id
    )


@router.post("/clear/{session_id}")
async def clear(session_id: str):
    """Clears session from memory without saving history."""
    clear_session(session_id)
    return {"status": "cleared"}