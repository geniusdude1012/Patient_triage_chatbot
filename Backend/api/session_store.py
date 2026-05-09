"""
Backend/api/session_store.py
──────────────────────────────
In-memory session storage.
Each session_id maps to a dict holding:
- chat_history        : LangChain message objects
- accumulated_symptoms: symptoms across all turns
- username            : patient name from welcome page
- start_time          : when session started
- session_id          : stored for history_writer access
- messages            : full {role, content, time} log for JSON export
- last_priority       : final triage priority for history file

In production: replace with Redis.
"""

from datetime import datetime

sessions: dict = {}


def get_session(session_id: str) -> dict:
    """
    Returns existing session or creates a new empty one.
    New sessions are created without a username — username is
    set later by register_session() when patient submits the welcome form.
    """
    if session_id not in sessions:
        sessions[session_id] = {
            "chat_history":         [],
            "accumulated_symptoms": [],
            "username":             "",
            "start_time":           datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "session_id":           session_id,
            "messages":             [],
            "last_priority":        "low"
        }
    return sessions[session_id]


def register_session(session_id: str, username: str) -> dict:
    """
    Sets the username and resets start_time for a session.
    Called by POST /api/session/start when patient submits the welcome form.
    """
    session = get_session(session_id)
    session["username"]      = username
    session["start_time"]    = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    session["messages"]      = []
    session["last_priority"] = "low"
    return session


def append_message(session_id: str, role: str, content: str) -> None:
    """
    Appends a message to the session's full message log.
    Called from routes/chat.py for every user + bot message.
    Used by history_writer when saving the session.
    """
    session = get_session(session_id)
    session["messages"].append({
        "role":    role,
        "content": content,
        "time":    datetime.now().strftime("%H:%M:%S")
    })


def clear_session(session_id: str) -> None:
    """Removes session from memory entirely."""
    sessions.pop(session_id, None)