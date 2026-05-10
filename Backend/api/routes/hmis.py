from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime
import uuid
import os
import json
import glob

router = APIRouter(prefix="/hmis", tags=["HMIS"])

#  existing model 
class AppointmentRequest(BaseModel):
    patient_name:   str
    session_id:     str
    department:     str
    symptoms:       list[str]
    priority:       str
    preferred_time: str | None = None

# existing endpoint 
@router.post("/appointment")
async def book_appointment(data: AppointmentRequest):
    ref = f"APT-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:6].upper()}"

    print(f"\n{'='*50}")
    print(f"[HMIS] NEW APPOINTMENT BOOKED")
    print(f"  Patient:    {data.patient_name}")
    print(f"  Department: {data.department}")
    print(f"  Symptoms:   {', '.join(data.symptoms)}")
    print(f"  Priority:   {data.priority}")
    print(f"  Time:       {data.preferred_time or 'Next available'}")
    print(f"  Reference:  {ref}")
    print(f"{'='*50}\n")

    return {
        "status":     "confirmed",
        "reference":  ref,
        "patient":    data.patient_name,
        "department": data.department,
        "slot":       data.preferred_time or "Next available slot",
        "booked_at":  datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }


# PATIENT HISTORY ENDPOINT

SESSIONS_DIR = "sessions"   

def _load_session_file(filepath: str) -> dict:
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)

def _search_by_username(username: str) -> list[dict]:
    """Find all session files where username matches (case-insensitive)."""
    matches = []
    pattern = os.path.join(SESSIONS_DIR, "*.json")

    for filepath in glob.glob(pattern):
        try:
            data = _load_session_file(filepath)
            if data.get("username", "").lower() == username.lower():
                matches.append(data)
        except (json.JSONDecodeError, KeyError):
            continue  # skip corrupted files silently

    return matches

def _search_by_session_id(session_id: str) -> dict | None:
    """Find a single session file by exact session_id."""
    pattern = os.path.join(SESSIONS_DIR, "*.json")

    for filepath in glob.glob(pattern):
        try:
            data = _load_session_file(filepath)
            if data.get("session_id") == session_id:
                return data
        except (json.JSONDecodeError, KeyError):
            continue

    return None


@router.get("/patient/history")
async def get_patient_history(
    username:   str | None = None,
    session_id: str | None = None
):
    """
    Retrieve all saved session records for a patient.

    Query by username  → returns ALL sessions for that patient
    Query by session_id → returns that single specific session
    Both provided      → session_id takes priority

    Examples:
      GET /api/hmis/patient/history?username=saujanya
      GET /api/hmis/patient/history?session_id=0aad5af8-22d6-499f-a4c6-62dd7fc7bcf7
    """

    # ── Validate at least one param provided 
    if not username and not session_id:
        raise HTTPException(
            status_code=400,
            detail="Provide at least one query parameter: 'username' or 'session_id'"
        )

    # ── sessions folder must exist 
    if not os.path.exists(SESSIONS_DIR):
        raise HTTPException(
            status_code=500,
            detail=f"Sessions directory '{SESSIONS_DIR}' not found on server."
        )

    # ── Search by session_id first (more specific) 
    if session_id:
        record = _search_by_session_id(session_id)

        if not record:
            raise HTTPException(
                status_code=404,
                detail=f"No session found with session_id: {session_id}"
            )

        return {
            "query":        {"session_id": session_id},
            "total_sessions": 1,
            "sessions":     [record]
        }

    # ── Search by username 
    records = _search_by_username(username)

    if not records:
        raise HTTPException(
            status_code=404,
            detail=f"No sessions found for username: '{username}'"
        )

    # Sort by start_time descending (most recent first)
    records.sort(
        key=lambda x: x.get("start_time", ""),
        reverse=True
    )

    return {
        "query":          {"username": username},
        "total_sessions": len(records),
        "sessions":       records
    }