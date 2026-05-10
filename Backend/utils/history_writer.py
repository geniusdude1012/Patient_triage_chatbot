import os
import json
from datetime import datetime


# ── Sessions folder 
SESSIONS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "sessions"
)


def save_session(session: dict) -> str:
    """
    Writes the session dict to a JSON file.

    Args:
        session: the full session dict from session_store.get_session()

    Returns:
        filepath of the saved file
    """
    os.makedirs(SESSIONS_DIR, exist_ok=True)

    username   = session.get("username", "unknown")
    session_id = session.get("session_id", "unknown")
    date_str   = datetime.now().strftime("%Y-%m-%d")
    end_time   = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # ── Build the output structure ─────────────────────────────────────────────
    output = {
        "username":            username,
        "session_id":          session_id,
        "start_time":          session.get("start_time", "unknown"),
        "end_time":            end_time,
        "final_priority":      session.get("last_priority", "low"),
        "symptoms_collected":  session.get("accumulated_symptoms", []),
        "messages":            session.get("messages", [])
    }

    # ── Build filename 
    safe_username = "".join(c for c in username if c.isalnum() or c in "_-")
    short_id      = session_id[:8]
    filename      = f"{safe_username}_{short_id}_{date_str}.json"
    filepath      = os.path.join(SESSIONS_DIR, filename)

    # ── Write to file 
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"✅ Session saved → {filepath}")
    return filepath