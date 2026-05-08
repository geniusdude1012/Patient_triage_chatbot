"""
services/department_fallback.py
─────────────────────────────────
When department_matcher finds no JSON match,
this service asks the LLM to suggest the best department.

Returns a formatted department block string.
"""

import json
from Backend.models.llm_models import extractor_llm
from Backend.models.prompts import build_department_fallback_prompt
from Backend.utils.formatters import URGENCY_ICONS


def get_llm_department(symptoms: list[str], priority: str) -> str:
    """
    Asks LLM to suggest the most appropriate department
    when JSON matching fails.

    Parses the LLM's JSON response and returns a formatted
    department block string. Falls back to a generic message
    if parsing fails — never crashes the chatbot.
    """
    prompt = build_department_fallback_prompt(symptoms, priority)

    try:
        response = extractor_llm.invoke(prompt)
        raw = response.content.strip()

        # Strip markdown code fences if LLM wraps in ```json
        if raw.startswith("```"):
            parts = raw.split("```")
            raw = parts[1] if len(parts) > 1 else raw
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()

        dept = json.loads(raw)

        # Validate all required keys exist
        required = ["department", "handles", "available", "recommendation"]
        missing  = [k for k in required if k not in dept]
        if missing:
            raise ValueError(f"Missing keys in LLM response: {missing}")

        print(f"   [Dept LLM]  Suggested → {dept['department']}")

        return (
            f"\n─────────────────────────────────────\n"
            f"🏥 DEPARTMENT ROUTING (AI Suggested)\n"
            f"─────────────────────────────────────\n"
            f"Department:     {dept['department']}\n"
            f"Handles:        {dept['handles']}\n"
            f"Available:      {dept['available']}\n"
            f"Urgency:        {URGENCY_ICONS.get(priority, '🟢 Routine')}\n"
            f"Recommendation: {dept['recommendation']}\n"
            f"─────────────────────────────────────\n"
        )

    except (json.JSONDecodeError, ValueError, Exception) as e:
        print(f"   [Dept LLM]  Parse failed: {e}")

        # Graceful fallback — always returns something useful
        return (
            f"\n─────────────────────────────────────\n"
            f"🏥 DEPARTMENT ROUTING\n"
            f"─────────────────────────────────────\n"
            f"Department:     Please consult reception\n"
            f"Handles:        General patient routing\n"
            f"Available:      8AM - 8PM\n"
            f"Urgency:        {URGENCY_ICONS.get(priority, '🟢 Routine')}\n"
            f"Recommendation: Please describe your symptoms at the\n"
            f"                front desk for proper department routing.\n"
            f"─────────────────────────────────────\n"
        )