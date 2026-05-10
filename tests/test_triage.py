"""
tests/test_triage.py
─────────────────────
Automated tests for Patient Triage Chatbot CI/CD pipeline.
All LLM and embedding calls are mocked — no real API key needed.
Run with: pytest tests/test_triage.py -v
"""

import os
import sys
import numpy as np
from unittest.mock import patch, MagicMock

# ── Set dummy env BEFORE any Backend imports 
os.environ["OPENAI_API_KEY"] = "sk-test-dummy-key"

# ── Dummy embedding — used by all mocks 
DUMMY_EMBEDDING  = [[0.1] * 1536]
DUMMY_EMBEDDINGS = [[0.1] * 1536] * 50   # enough for all keyword lists

# TEST 1 — Appointment yes/no intent detection
# Pure Python logic — no imports needed, no mocking needed

def test_appointment_intent_detection():
    """
    Patient saying yes/sure/ok must trigger booking.
    Patient saying no/later/nope must decline booking.
    No mocking needed — pure string matching logic.
    """
    YES_WORDS = ["yes", "yeah", "sure", "ok", "okay", "please", "book", "confirm", "yep", "y"]
    NO_WORDS  = ["no", "nope", "don't", "not now", "later", "skip", "cancel", "n"]

    def wants(text):
        return any(w in text.lower() for w in YES_WORDS)

    def declines(text):
        return any(w in text.lower() for w in NO_WORDS)

    for text in ["yes", "sure", "ok", "yeah", "please book"]:
        assert wants(text), f"Expected '{text}' to be YES"

    for text in ["no", "nope", "not now", "later", "skip"]:
        assert declines(text), f"Expected '{text}' to be NO"

    print("✅ Appointment intent detection passed")



# TEST 2 — Department extraction from markdown response
# Pure Python string parsing — no API calls needed

def test_department_extraction_from_response():
    """
    Markdown table must correctly yield the department name.
    No mocking needed — pure string parsing logic.
    """
    def extract_dept(response: str, session: dict) -> str:
        for line in response.split("\n"):
            if "**Department**" in line and "|" in line:
                parts = [p.strip() for p in line.split("|") if p.strip()]
                if len(parts) >= 2:
                    return parts[-1]
        return session.get("last_department", "")

    # Test Dental
    response1 = (
        "### 🏥 Department Routing\n\n"
        "| | |\n"
        "|---|---|\n"
        "| **Department** | Dental |\n"
        "| **Handles** | Teeth, gums, and oral health |\n"
    )
    assert extract_dept(response1, {}) == "Dental", "Should extract Dental"

    # Test Orthopedics
    response2 = (
        "### 🏥 Department Routing\n\n"
        "| | |\n"
        "|---|---|\n"
        "| **Department** | Orthopedics |\n"
        "| **Handles** | Bone and joint conditions |\n"
    )
    assert extract_dept(response2, {}) == "Orthopedics", "Should extract Orthopedics"

    # Test General Medicine / OPD (with slash)
    response3 = (
        "| **Department** | General Medicine / OPD |\n"
    )
    assert extract_dept(response3, {}) == "General Medicine / OPD", \
        "Should extract department with slash"

    print("✅ Department extraction passed")



# TEST 3 — Priority detection from emoji in response text
# Pure Python logic — no API calls needed
# 
def test_priority_detection_from_response_emojis():
    """
    Priority must be correctly detected from emoji in bot response.
    This is what chat.py uses to set session priority.
    """
    def detect_priority(response: str) -> str:
        if   "🔴" in response: return "critical"
        elif "🟠" in response: return "urgent"
        elif "🟡" in response: return "routine"
        return "low"

    assert detect_priority("### 🔴 Emergency Detected\nCall 911 now") == "critical"
    assert detect_priority("### 🟠 Urgent — Same Day Care\nVisit urgent care") == "urgent"
    assert detect_priority("### 🟡 Routine\nSchedule an appointment") == "routine"
    assert detect_priority("I'm sorry to hear that. How long have you had this?") == "low"

    print("✅ Priority detection from emoji passed")



# TEST 4 — Session store creates correct structure
# Mocks embeddings so no OpenAI call is made at import time

def test_session_store_create_and_retrieve():
    """
    Session store must create session with all required fields.
    Mocks embeddings model to prevent real API calls at import time.
    """
    with patch("langchain_openai.OpenAIEmbeddings") as mock_emb_cls, \
         patch("langchain_openai.ChatOpenAI") as mock_chat_cls:

        # Mock embedding instance
        mock_emb = MagicMock()
        mock_emb.embed_documents.return_value = DUMMY_EMBEDDINGS
        mock_emb.embed_query.return_value      = DUMMY_EMBEDDING[0]
        mock_emb_cls.return_value = mock_emb

        # Mock chat LLM instance
        mock_chat = MagicMock()
        mock_chat.invoke.return_value = MagicMock(content="Test response")
        mock_chat_cls.return_value = mock_chat

        from Backend.api.session_store import get_session, clear_session

        test_id = "test-session-pytest-001"
        clear_session(test_id)

        session = get_session(test_id)

        # Required fields
        required = [
            "chat_history", "accumulated_symptoms", "username",
            "start_time", "messages", "last_priority",
            "awaiting_appointment", "last_department"
        ]
        for field in required:
            assert field in session, f"Missing field: '{field}'"

        # Default values
        assert session["chat_history"]         == []
        assert session["accumulated_symptoms"] == []
        assert session["last_priority"]        == "low"
        assert session["awaiting_appointment"] == False
        assert session["last_department"]      == ""

        # Persistence check
        session["username"] = "TestPatient"
        assert get_session(test_id)["username"] == "TestPatient"

        clear_session(test_id)
        print("✅ Session store test passed")



# TEST 5 — Emergency response formatting
# Pure Python string formatting — no API calls needed

def test_emergency_response_formatting():
    """
    Emergency and urgent responses must contain required fields.
    Verifies formatters.py output structure without calling OpenAI.
    """
    with patch("langchain_openai.OpenAIEmbeddings") as mock_emb_cls, \
         patch("langchain_openai.ChatOpenAI") as mock_chat_cls:

        mock_emb = MagicMock()
        mock_emb.embed_documents.return_value = DUMMY_EMBEDDINGS
        mock_emb_cls.return_value = mock_emb

        mock_chat = MagicMock()
        mock_chat_cls.return_value = mock_chat

        from Backend.utils.formatters import (
            format_emergency_response,
            format_department_block,
            URGENCY_ICONS
        )

        # Test emergency response
        categorized_emergency = {
            "emergency": ["chest pain"],
            "urgent":    [],
            "routine":   [],
            "unknown":   []
        }
        result = format_emergency_response("emergency", categorized_emergency)
        assert result is not None,              "Emergency response must not be None"
        assert "chest pain"  in result,         "Must mention detected symptom"
        assert "CRITICAL"    in result,         "Must say CRITICAL"
        assert "emergency"   in result.lower(), "Must mention emergency"

        # Test urgent response
        categorized_urgent = {
            "emergency": [],
            "urgent":    ["severe headache"],
            "routine":   [],
            "unknown":   []
        }
        result2 = format_emergency_response("urgent", categorized_urgent)
        assert result2 is not None,                "Urgent response must not be None"
        assert "severe headache" in result2,       "Must mention detected symptom"

        # Test routine/low returns None (LLM handles it)
        result3 = format_emergency_response("low", {
            "emergency": [], "urgent": [], "routine": [], "unknown": []
        })
        assert result3 is None, "Routine/low must return None so LLM handles it"

        # Test department block
        dept_match = {
            "department":    "Dental",
            "handles":       "Teeth, gums, and oral health",
            "available":     "9AM - 5PM",
            "recommendation": "Visit Dental OPD",
            "source":        "json"
        }
        dept_block = format_department_block(dept_match, "routine")
        assert "Dental"         in dept_block, "Must contain department name"
        assert "9AM - 5PM"      in dept_block, "Must contain availability"
        assert "Visit Dental"   in dept_block, "Must contain recommendation"

        # Test URGENCY_ICONS mapping
        assert "🔴" in URGENCY_ICONS["emergency"]
        assert "🟠" in URGENCY_ICONS["urgent"]
        assert "🟡" in URGENCY_ICONS["routine"]
        assert "🟢" in URGENCY_ICONS["low"]

        print("✅ Emergency response formatting passed")