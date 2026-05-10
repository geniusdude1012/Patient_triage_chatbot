from fastapi import APIRouter
from pydantic import BaseModel
from datetime import datetime
import uuid

router = APIRouter(prefix="/hmis", tags=["HMIS"])

class AppointmentRequest(BaseModel):
    patient_name: str
    session_id:   str
    department:   str
    symptoms:     list[str]
    priority:     str
    preferred_time: str | None = None

@router.post("/appointment")
async def book_appointment(data: AppointmentRequest):
    """
    Books appointment and sends full triage info to HMIS.
    Called when patient confirms they want an appointment.
    """
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

    # TODO: replace with real HMIS call when connecting to hospital system
    # requests.post("http://hmis-system/api/appointments", json=data.dict())

    return {
        "status":      "confirmed",
        "reference":   ref,
        "patient":     data.patient_name,
        "department":  data.department,
        "slot":        data.preferred_time or "Next available slot",
        "booked_at":   datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }