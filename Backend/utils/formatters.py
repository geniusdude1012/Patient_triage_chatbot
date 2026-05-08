"""
utils/formatters.py
────────────────────
All response formatting functions.

Builds the structured output blocks shown to the patient:
- Emergency / urgent instant responses
- Department routing info block
- Urgency icons mapping
"""

# ── Urgency level display labels ──────────────────────────────────────────────
URGENCY_ICONS = {
    "emergency": "🔴 Emergency",
    "urgent":    "🟠 Urgent",
    "routine":   "🟡 Routine",
    "low":       "🟢 Routine"
}


def format_emergency_response(priority: str, categorized: dict) -> str | None:
    """
    Returns instant structured response for emergency/urgent cases.
    Returns None for routine/low — LLM handles those conversationally.
    """
    if priority == "emergency":
        found = ", ".join(categorized["emergency"])
        return (
            "\n🔴 EMERGENCY DETECTED\n"
            "─────────────────────────────────────\n"
            f"Detected:   {found}\n"
            "Urgency:    CRITICAL\n"
            "Department: Emergency / Immediate Care\n"
            "Action:     Call emergency services NOW\n"
            "            or go to the ER immediately.\n"
            "─────────────────────────────────────\n"
            "⚠️  This is AI-assisted triage, not a medical diagnosis.\n"
        )

    if priority == "urgent":
        found = ", ".join(categorized["urgent"])
        return (
            "\n🟠 URGENT — SAME DAY CARE NEEDED\n"
            "─────────────────────────────────────\n"
            f"Detected:   {found}\n"
            "Urgency:    HIGH\n"
            "Department: Urgent Care / Emergency Room\n"
            "Action:     Seek medical attention today.\n"
            "            Do not wait — visit urgent care now.\n"
            "─────────────────────────────────────\n"
            "⚠️  This is AI-assisted triage, not a medical diagnosis.\n"
        )

    return None


def format_department_block(dept_match: dict, priority: str) -> str:
    """
    Formats a matched department from department_info.json
    into a clean display block for the patient.
    """
    source_label = (
        "🏥 DEPARTMENT ROUTING"
        if dept_match.get("source") == "json"
        else "🏥 DEPARTMENT ROUTING (AI Suggested)"
    )

    return (
        f"\n─────────────────────────────────────\n"
        f"{source_label}\n"
        f"─────────────────────────────────────\n"
        f"Department:     {dept_match['department']}\n"
        f"Handles:        {dept_match.get('handles', 'N/A')}\n"
        f"Available:      {dept_match.get('available', 'N/A')}\n"
        f"Urgency:        {URGENCY_ICONS.get(priority, '🟢 Routine')}\n"
        f"Recommendation: {dept_match.get('recommendation', 'Please visit this department.')}\n"
        f"─────────────────────────────────────\n"
        f"⚠️  This is AI-assisted triage, not a medical diagnosis.\n"
    )