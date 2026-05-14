from fastapi import APIRouter
from Backend.api.schemas import ChatRequest, ChatResponse
from Backend.api.session_store import get_session, clear_session, append_message
from Backend.services.triage_engine import process
import Backend.utils.state_manager as state
import httpx
from Backend.config.settings import MAX_MESSAGES_PER_SESSION, MAX_MESSAGE_LENGTH

router = APIRouter()

# ── Appointment confirmation keywords ──────────────────────────────────────────
YES_WORDS = ["yes", "yeah", "sure", "ok", "okay", "please", "book", "confirm", "yep", "y"]
NO_WORDS  = ["no", "nope", "don't", "not now", "later", "skip", "cancel", "n"]


def _wants_appointment(text: str) -> bool:
    return any(w in text.lower() for w in YES_WORDS)


def _declines_appointment(text: str) -> bool:
    return any(w in text.lower() for w in NO_WORDS)


def _extract_dept_from_response(response: str, session: dict) -> str:
    """Extracts department name from markdown table row."""
    for line in response.split("\n"):
        # Match lines like: | **Department** | Dental |
        if "**Department**" in line and "|" in line:
            # Split by | and get the last non-empty part
            parts = [p.strip() for p in line.split("|") if p.strip()]
            # parts[0] = "**Department**", parts[1] = "Dental"
            if len(parts) >= 2:
                return parts[-1]  # last part is always the dept name
    return session.get("last_department", "")


async def _book_hmis_appointment(session: dict) -> dict:
    """Calls the HMIS appointment endpoint with full session data."""
    payload = {
        "patient_name":   session.get("username", ""),
        "session_id":     session.get("session_id", ""),
        "department":     session.get("last_department", ""),
        "symptoms":       session.get("accumulated_symptoms", []),
        "priority":       session.get("last_priority", "low"),
        "preferred_time": None
    }
    try:
        async with httpx.AsyncClient() as client:
            r = await client.post(
                "http://localhost:8000/api/hmis/appointment",
                json=payload,
                timeout=10
            )
            return r.json()
    except Exception as e:
        print(f"[HMIS] Booking failed: {e}")
        return {"status": "failed"}



# SINGLE /chat endpoint

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Full pipeline per message:
    1. Load session state
    2. Log user message
    3. If awaiting_appointment → handle yes/no response
    4. Otherwise → run normal triage pipeline
    5. If department shown in response → ask about booking
    6. Save state and return ChatResponse
    """

    # ── Load session state ─────────────────────────────────────────────────────
    session = get_session(request.session_id)
    state.chat_history[:]         = session["chat_history"]
    state.accumulated_symptoms[:] = session["accumulated_symptoms"]

    user_msg = request.message.strip()
    
    # CHECK 1 — Message too long

    if len(user_msg) > MAX_MESSAGE_LENGTH:
        return ChatResponse(
            response=(
                f"⚠️ Your message is too long "
                f"(max {MAX_MESSAGE_LENGTH} characters). "
                f"Please describe your symptoms more briefly."
            ),
            priority=session.get("last_priority", "low"),
            session_id=request.session_id
        )

    # CHECK 2 — Session message limit reached

    session["message_count"] = session.get("message_count", 0) + 1

    if session["message_count"] > MAX_MESSAGES_PER_SESSION:
        dept = session.get("last_department", "the appropriate department")
        response = (
            f"⏱️ **Session limit reached.**\n\n"
            f"This triage session has reached its maximum of "
            f"**{MAX_MESSAGES_PER_SESSION} messages**.\n\n"
            f"Based on our conversation, please visit: **{dept}**\n\n"
            f"Click **End Session** to save your history "
            f"or **Clear conversation** to start a fresh session.\n\n"
            f"> ⚠️ *This is AI-assisted triage and not a medical diagnosis.*"
        )
        append_message(request.session_id, "bot", response)
        return ChatResponse(
            response=response,
            priority=session.get("last_priority", "low"),
            session_id=request.session_id
        )

    
    append_message(request.session_id, "user", user_msg)

    
    # APPOINTMENT FLOW — intercept yes/no when waiting for confirmation
    if session.get("awaiting_appointment"):

        if _wants_appointment(user_msg):
            result = await _book_hmis_appointment(session)
            session["awaiting_appointment"] = False

            if result.get("status") == "confirmed":
                response = (
                    f"✅ **Appointment Confirmed!**\n\n"
                    f"| | |\n"
                    f"|---|---|\n"
                    f"| **Patient** | {result.get('patient', '')} |\n"
                    f"| **Department** | {result.get('department', '')} |\n"
                    f"| **Slot** | {result.get('slot', 'Next available')} |\n"
                    f"| **Reference** | `{result.get('reference', '')}` |\n"
                    f"| **Booked at** | {result.get('booked_at', '')} |\n\n"
                    f"> 📋 Please keep your reference number for check-in.\n\n"
                    f"> ⚠️ *This is AI-assisted triage and not a medical diagnosis.*"
                )
            else:
                response = (
                    "❌ Sorry, I couldn't complete the booking right now. "
                    "Please visit the reception desk directly to book your appointment."
                )

        elif _declines_appointment(user_msg):
            session["awaiting_appointment"] = False
            response = (
                f"No problem! Please visit "
                f"**{session.get('last_department', 'the recommended department')}** "
                f"directly during working hours. Take care and feel better soon! 🙏\n\n"
                f"> ⚠️ *This is AI-assisted triage and not a medical diagnosis.*"
            )

        else:
            # Unclear — ask again
            response = (
                f"Would you like me to book an appointment with "
                f"**{session.get('last_department', 'the recommended department')}** "
                f"for you? Please reply **Yes** or **No**."
            )

        append_message(request.session_id, "bot", response)
        session["chat_history"]         = list(state.chat_history)
        session["accumulated_symptoms"] = list(state.accumulated_symptoms)

        return ChatResponse(
            response=response,
            priority=session.get("last_priority", "low"),
            session_id=request.session_id
        )

   
    # NORMAL TRIAGE FLOW
    response = process(request.message)

    # ── Safety check — process() must never return None 
    if not response:
        response = "I'm sorry, something went wrong. Please describe your symptoms again."

    append_message(request.session_id, "bot", response)
    session["chat_history"]         = list(state.chat_history)
    session["accumulated_symptoms"] = list(state.accumulated_symptoms)

    # ── Detect priority from response emojis 
    priority = "low"
    if   "🔴" in response: priority = "critical"
    elif "🟠" in response: priority = "urgent"
    elif "🟡" in response: priority = "routine"

    session["last_priority"] = priority

    # ── If department shown → ask about appointment 
    if "Department Routing" in response or "DEPARTMENT ROUTING" in response:
        dept = _extract_dept_from_response(response, session)
        if dept:
            session["last_department"]      = dept
            session["awaiting_appointment"] = True
            response += (
                f"\n\n---\n"
                f"📅 **Would you like me to book an appointment "
                f"with {dept} for you?** *(Yes / No)*"
            )

    return ChatResponse(
        response=response,
        priority=priority,
        session_id=request.session_id
    )


# ── Clear session 
@router.post("/clear/{session_id}")
async def clear(session_id: str):
    """Clears session from memory without saving history."""
    clear_session(session_id)
    return {"status": "cleared"}