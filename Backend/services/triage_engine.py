"""
services/triage_engine.py
──────────────────────────
Master pipeline orchestrator.

Coordinates all services in the correct order:
1. Extract symptoms from user input
2. Accumulate symptoms across conversation turns
3. Classify symptoms against emergency.json
4. Match department from department_info.json
5. Return instant response for emergency/urgent cases
6. Route to LLM conversation for routine/low cases
7. Append department block when LLM concludes
"""

from services.symptom_extractor   import extract_symptoms
from services.emergency_classifier import categorize, get_priority
from services.department_matcher   import match_department
from services.department_fallback  import get_llm_department
from services.conversation_service import chat
from utils.formatters              import format_emergency_response, format_department_block
from utils.state_manager           import accumulated_symptoms


def process(user_input: str) -> str:
    """
    Full triage pipeline — called for every user message.

    Flow:
    ┌─────────────────────────────────────────┐
    │  User input                              │
    │       ↓                                  │
    │  1. Extract symptoms (LLM)               │
    │       ↓                                  │
    │  2. Accumulate across turns              │
    │       ↓                                  │
    │  3. Classify → emergency / urgent /      │
    │                routine / unknown         │
    │       ↓                                  │
    │  4. Match department (embeddings)        │
    │       ↓                                  │
    │  Emergency/Urgent                        │
    │    → instant structured response        │
    │    → + department block                 │
    │                                          │
    │  Routine/Low                             │
    │    → LLM conversation                   │
    │    → + department block (after final)   │
    └─────────────────────────────────────────┘
    """
    print("\n" + "─" * 45)

    # ── Step 1: Extract symptoms from current message ──────────────────────────
    symptoms = extract_symptoms(user_input)
    print(f"   [Extracted]   {symptoms if symptoms else 'none detected'}")

    # ── Step 2: Accumulate symptoms across conversation turns ──────────────────
    for s in symptoms:
        if s not in accumulated_symptoms:
            accumulated_symptoms.append(s)
    print(f"   [Accumulated] {accumulated_symptoms}")

    # ── Step 3: Classify against emergency.json ────────────────────────────────
    categorized = categorize(accumulated_symptoms)
    print(
        f"   [Classified]  "
        f"emergency={categorized['emergency']} | "
        f"urgent={categorized['urgent']} | "
        f"routine={categorized['routine']} | "
        f"unknown={categorized['unknown']}"
    )

    # ── Step 4: Get highest priority level ─────────────────────────────────────
    priority = get_priority(categorized)
    print(f"   [Priority]    {priority.upper()}")

    # ── Step 5: Match department via embeddings ────────────────────────────────
    dept_match = match_department(accumulated_symptoms)
    print(f"   [Department]  {dept_match['department'] if dept_match else 'none matched'}")

    # ── Step 6: Instant response for emergency / urgent ────────────────────────
    instant = format_emergency_response(priority, categorized)
    if instant:
        dept_block = _get_dept_block(dept_match, accumulated_symptoms, priority)
        return instant + dept_block

    # ── Step 7: LLM conversation for routine / low ─────────────────────────────
    print(f"   [Routing]     LLM conversation")
    llm_response = chat(user_input, dept_match)

    # Show department block only when LLM stops asking questions
    # (i.e. response has no "?" — LLM has concluded triage)
    if "?" in llm_response or not accumulated_symptoms:
        print(f"   [Dept Block]  Suppressed — LLM still gathering info")
        return llm_response

    print(f"   [Dept Block]  Appending — LLM concluded")
    dept_block = _get_dept_block(dept_match, accumulated_symptoms, priority)
    return llm_response + dept_block


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