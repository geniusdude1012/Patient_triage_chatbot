from fastapi import APIRouter
from Backend.api.schemas import ChatRequest, ChatResponse
from Backend.api.session_store import get_session
from Backend.services.triage_engine import process
import Backend.utils.state_manager as state

router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    # Load this session's state
    session = get_session(request.session_id)
    state.chat_history[:] = session["chat_history"]
    state.accumulated_symptoms[:] = session["accumulated_symptoms"]

    # Run the triage pipeline
    response = process(request.message)

    # Save state back to session
    session["chat_history"]        = list(state.chat_history)
    session["accumulated_symptoms"] = list(state.accumulated_symptoms)

    # Detect priority from response text
    priority = "low"
    if "🔴" in response:   priority = "critical"
    elif "🟠" in response: priority = "urgent"
    elif "🟡" in response: priority = "routine"

    return ChatResponse(
        response=response,
        priority=priority,
        session_id=request.session_id
    )

@router.post("/clear/{session_id}")
async def clear(session_id: str):
    from Backend.api.session_store import clear_session
    clear_session(session_id)
    return {"status": "cleared"}