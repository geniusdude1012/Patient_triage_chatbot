
from Backend.services.symptom_extractor   import extract_symptoms
from Backend.services.emergency_classifier import categorize, get_priority
from Backend.services.department_matcher   import match_department
from Backend.services.department_fallback  import get_llm_department
from Backend.services.conversation_service import chat
from Backend.utils.formatters              import format_emergency_response, format_department_block
from Backend.utils.state_manager           import accumulated_symptoms


def process(user_input: str) -> str:
    """
    Full triage pipeline — called for every user message.
    
    """
    print("\n" + "─" * 45)

    symptoms = extract_symptoms(user_input)
    print(f"   [Extracted]   {symptoms if symptoms else 'none detected'}")

    for s in symptoms:
        if s not in accumulated_symptoms:
            accumulated_symptoms.append(s)
    print(f"   [Accumulated] {accumulated_symptoms}")

    categorized = categorize(accumulated_symptoms)
    priority    = get_priority(categorized)
    print(f"   [Priority]    {priority.upper()}")

    dept_match = match_department(accumulated_symptoms)
    print(f"   [Department]  {dept_match['department'] if dept_match else 'none matched'}")

    # Instant response for emergency/urgent
    instant = format_emergency_response(priority, categorized)
    if instant:
        dept_block = _get_dept_block(dept_match, accumulated_symptoms, priority)
        return instant + dept_block

    # ── Check if user is explicitly asking about department 
    dept_keywords = ["department", "where", "which department", "which doctor", "where to go"]
    user_asking_dept = any(kw in user_input.lower() for kw in dept_keywords)

    print(f"   [Routing]     LLM conversation")
    llm_response = chat(user_input, dept_match)

    # Show dept block if:
    # 1. LLM has stopped asking questions (no "?" in response), OR
    # 2. User explicitly asked about department
    if "?" not in llm_response or user_asking_dept:
        print(f"   [Dept Block]  Appending")
        dept_block = _get_dept_block(dept_match, accumulated_symptoms, priority)
        return llm_response + dept_block

    print(f"   [Dept Block]  Suppressed — LLM still asking questions")
    return llm_response


def _get_dept_block(dept_match: dict | None, symptoms: list, priority: str) -> str:
    """
    Returns formatted department block.
    Uses JSON match if available, falls back to LLM suggestion.
    """
    if dept_match:
        return format_department_block(dept_match, priority)
    elif symptoms:
        return get_llm_department(symptoms, priority)
    return ""