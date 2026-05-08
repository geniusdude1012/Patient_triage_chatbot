# Stores per-session state (chat history + accumulated symptoms)
# In production replace with Redis

sessions: dict = {}

def get_session(session_id: str) -> dict:
    if session_id not in sessions:
        sessions[session_id] = {
            "chat_history": [],
            "accumulated_symptoms": []
        }
    return sessions[session_id]

def clear_session(session_id: str):
    sessions.pop(session_id, None)