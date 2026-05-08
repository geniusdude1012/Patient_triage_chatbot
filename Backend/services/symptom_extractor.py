"""
services/symptom_extractor.py
──────────────────────────────
Uses LLM to extract standardized medical symptoms
from any natural language input — slang, informal, multilingual.
"""

from models.llm_models import extractor_llm
from models.prompts import build_symptom_extraction_prompt


def extract_symptoms(user_input: str) -> list[str]:
    """
    Extracts all medical symptoms from raw user input.

    Returns a clean list of symptom strings with qualifiers preserved.
    Example:
        "my chest is killing me and i cant breathe"
        → ["chest pain", "difficulty breathing"]
    """
    prompt   = build_symptom_extraction_prompt(user_input)
    response = extractor_llm.invoke(prompt)
    raw      = response.content.lower().strip()

    if raw == "none" or not raw:
        return []

    return [s.strip() for s in raw.split(",") if s.strip()]