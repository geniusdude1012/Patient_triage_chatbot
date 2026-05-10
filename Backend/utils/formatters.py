
# ── Urgency level display labels 
URGENCY_ICONS = {
    "emergency": "🔴 Emergency",
    "urgent":    "🟠 Urgent",
    "routine":   "🟡 Routine",
    "low":       "🟢 Routine"
}

def format_emergency_response(priority: str, categorized: dict) -> str | None:
    """
    Returns markdown-formatted instant response for emergency/urgent cases.
    Returns None for routine/low — LLM handles those conversationally.
    """
    if priority == "emergency":
        found = ", ".join(categorized["emergency"])
        return (
            "### 🔴 Emergency Detected\n\n"
            "| | |\n"
            "|---|---|\n"
            f"| **Symptoms** | {found} |\n"
            "| **Urgency** | CRITICAL |\n"
            "| **Department** | Emergency / Immediate Care |\n\n"
            "> 🚨 **Action:** Call emergency services (911) NOW "
            "or go to the ER immediately.\n\n"
            "> ⚠️ *This is AI-assisted triage, not a medical diagnosis.*\n"
            f"> \n *Please press the New Chat Button to end and start new session*\n"
            f"> \n *Please press the Clear Conversation Button to clear the conversation*\n"
        )

    if priority == "urgent":
        found = ", ".join(categorized["urgent"])
        return (
            "### 🟠 Urgent — Same Day Care Needed\n\n"
            "| | |\n"
            "|---|---|\n"
            f"| **Symptoms** | {found} |\n"
            "| **Urgency** | HIGH |\n"
            "| **Department** | Urgent Care / Emergency Room |\n\n"
            "> ⚡ **Action:** Seek medical attention today. "
            "Do not wait — visit urgent care now.\n\n"
            "> ⚠️ *This is AI-assisted triage, not a medical diagnosis.*\n"
            f"> \n *Please press the New Chat Button to end and start new session*\n"
            f"> \n *Please press the Clear Conversation Button to clear the conversation*\n"
        )

    return None


def format_department_block(dept_match: dict, priority: str) -> str:
    """
    Formats matched department into a clean markdown table block.
    Renders as a proper table inside Streamlit chat bubbles.
    """
    source = dept_match.get("source", "json")
    title  = "🏥 Department Routing" if source == "json" else "🏥 Department Routing (AI Suggested)"

    return (
        f"\n\n---\n"
        f"### {title}\n\n"
        "| | |\n"
        "|---|---|\n"
        f"| **Department** | {dept_match['department']} |\n"
        f"| **Handles** | {dept_match.get('handles', 'N/A')} |\n"
        f"| **Available** | {dept_match.get('available', 'N/A')} |\n"
        f"| **Urgency** | {URGENCY_ICONS.get(priority, '🟢 Routine')} |\n\n"
        f"> 📋 **Recommendation:** {dept_match.get('recommendation', 'Please visit this department.')}\n\n"
        f"> ⚠️ *This is AI-assisted triage, not a medical diagnosis.*\n"
        f"> \n *Please press the New Chat Button to end and start new session*\n"
        f"> \n *Please press the Clear Conversation Button to clear the conversation*\n"
    )


def format_llm_department_block(dept: dict, priority: str) -> str:
    """
    Same as format_department_block but for LLM-suggested departments
    (used in department_fallback.py instead of building the string there).
    """
    return (
        f"\n\n---\n"
        f"### 🏥 Department Routing (AI Suggested)\n\n"
        "| | |\n"
        "|---|---|\n"
        f"| **Department** | {dept['department']} |\n"
        f"| **Handles** | {dept.get('handles', 'N/A')} |\n"
        f"| **Available** | {dept.get('available', 'N/A')} |\n"
        f"| **Urgency** | {URGENCY_ICONS.get(priority, '🟢 Routine')} |\n\n"
        f"> 📋 **Recommendation:** {dept.get('recommendation', 'Please visit this department.')}\n\n"
        f"> ⚠️ *This is AI-assisted triage, not a medical diagnosis.*\n"
        f"> \n *Please press the New Chat Button to end and start new session*\n"
        f"> \n *Please press the Clear Conversation Button to clear the conversation*\n"
    )