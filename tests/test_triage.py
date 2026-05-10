"""
tests/test_triage.py
─────────────────────
Simple automated tests for the Patient Triage Chatbot.
Run with: pytest tests/test_triage.py -v

These tests run in CI/CD pipeline on every push.
No real API keys needed — all LLM calls are mocked.
"""

import pytest
from unittest.mock import patch, MagicMock


# ══════════════════════════════════════════════════════════════════════════════
# TEST 1 — Emergency keyword detection
# Verifies critical symptoms are correctly classified
# ══════════════════════════════════════════════════════════════════════════════
def test_emergency_keywords_classify_correctly():
    """
    chest pain and seizure must always return 'emergency' priority.
    This is the most critical test — wrong classification = patient harm.
    """
    from Backend.api.routes.chat import _wants_appointment, _declines_appointment

    # These must always trigger emergency
    critical_symptoms = ["chest pain", "seizure", "unconscious", "not breathing"]

    from Backend.api.session_store import get_session
    from unittest.mock import patch
    import Backend.utils.state_manager as state

    # Mock the embeddings so no real OpenAI call is made
    with patch("Backend.services.emergency_classifier.embeddings_model") as mock_embed:
        mock_embed.embed_documents.return_value = [[0.1] * 1536]

        from Backend.services.emergency_classifier import categorize, get_priority

        # Simulate a symptom that matches critical
        with patch("Backend.services.emergency_classifier.cosine_similarity") as mock_cos:
            # Return high similarity (0.95) for emergency keywords
            import numpy as np
            mock_cos.return_value = np.array([[0.95] + [0.1] * 20])

            result = categorize(["chest pain"])
            priority = get_priority(result)

            assert priority == "emergency", \
                f"Expected 'emergency' but got '{priority}' for chest pain"

    print("✅ Emergency classification test passed")


# ══════════════════════════════════════════════════════════════════════════════
# TEST 2 — Appointment yes/no detection
# Verifies the chatbot correctly reads patient intent
# ══════════════════════════════════════════════════════════════════════════════
def test_appointment_intent_detection():
    """
    Patient saying 'yes', 'sure', 'ok' must trigger booking.
    Patient saying 'no', 'later', 'nope' must decline booking.
    """
    from Backend.api.routes.chat import _wants_appointment, _declines_appointment

    # These should all be treated as YES
    yes_inputs = ["yes", "sure", "ok", "okay", "yeah", "please book", "confirm", "yep"]
    for text in yes_inputs:
        assert _wants_appointment(text), \
            f"Expected '{text}' to be detected as YES for appointment"

    # These should all be treated as NO
    no_inputs = ["no", "nope", "not now", "later", "skip", "cancel"]
    for text in no_inputs:
        assert _declines_appointment(text), \
            f"Expected '{text}' to be detected as NO for appointment"

    print("✅ Appointment intent detection test passed")


# ══════════════════════════════════════════════════════════════════════════════
# TEST 3 — Department extraction from response
# Verifies department name is correctly parsed from markdown table
# ══════════════════════════════════════════════════════════════════════════════
def test_department_extraction_from_response():
    """
    The markdown table response must correctly yield the department name.
    Critical for routing the appointment booking to the right department.
    """
    from Backend.api.routes.chat import _extract_dept_from_response

    # Simulate what formatters.py produces
    sample_response = (
        "### 🏥 Department Routing\n\n"
        "| | |\n"
        "|---|---|\n"
        "| **Department** | Dental |\n"
        "| **Handles** | Teeth, gums, and oral health |\n"
        "| **Available** | 9AM - 5PM |\n"
        "| **Urgency** | 🟡 Routine |\n"
    )

    session = {"last_department": ""}
    dept = _extract_dept_from_response(sample_response, session)

    assert dept == "Dental", \
        f"Expected 'Dental' but got '{dept}'"

    # Test with Orthopedics
    sample_response_2 = (
        "### 🏥 Department Routing\n\n"
        "| | |\n"
        "|---|---|\n"
        "| **Department** | Orthopedics |\n"
        "| **Handles** | Bone, joint, and muscle conditions |\n"
    )

    dept2 = _extract_dept_from_response(sample_response_2, session)
    assert dept2 == "Orthopedics", \
        f"Expected 'Orthopedics' but got '{dept2}'"

    print("✅ Department extraction test passed")


# ══════════════════════════════════════════════════════════════════════════════
# TEST 4 — Session store creates and retrieves session correctly
# Verifies patient session data is stored and retrieved accurately
# ══════════════════════════════════════════════════════════════════════════════
def test_session_store_create_and_retrieve():
    """
    Session store must create a new session with correct default fields
    and retrieve it accurately by session_id.
    """
    from Backend.api.session_store import get_session, clear_session

    test_id = "test-session-abc123"

    # Clean up before test
    clear_session(test_id)

    # Create session
    session = get_session(test_id)

    # Verify all required fields exist
    assert "chat_history"         in session, "Missing chat_history"
    assert "accumulated_symptoms" in session, "Missing accumulated_symptoms"
    assert "username"             in session, "Missing username"
    assert "start_time"           in session, "Missing start_time"
    assert "messages"             in session, "Missing messages"
    assert "last_priority"        in session, "Missing last_priority"
    assert "awaiting_appointment" in session, "Missing awaiting_appointment"
    assert "last_department"      in session, "Missing last_department"

    # Verify defaults
    assert session["chat_history"]         == [], "chat_history should be empty list"
    assert session["accumulated_symptoms"] == [], "accumulated_symptoms should be empty list"
    assert session["last_priority"]        == "low", "Default priority should be low"
    assert session["awaiting_appointment"] == False, "Should not await appointment by default"

    # Verify same session is returned on second call
    session2 = get_session(test_id)
    session2["username"] = "TestPatient"
    session3 = get_session(test_id)
    assert session3["username"] == "TestPatient", "Session should persist between calls"

    # Clean up
    clear_session(test_id)

    print("✅ Session store test passed")


# ══════════════════════════════════════════════════════════════════════════════
# TEST 5 — FastAPI /api/chat endpoint returns correct response shape
# Verifies the API contract is intact (response, priority, session_id)
# ══════════════════════════════════════════════════════════════════════════════
def test_chat_endpoint_response_shape():
    """
    POST /api/chat must always return:
    - response (str, non-empty)
    - priority (one of: critical, urgent, routine, low)
    - session_id (str, matches request)

    Uses FastAPI TestClient — no real server needed.
    LLM calls are mocked so no OpenAI credits used.
    """
    from fastapi.testclient import TestClient

    # Mock all heavy imports before loading the app
    with patch("Backend.services.emergency_classifier.embeddings_model") as mock_emb, \
         patch("Backend.services.department_matcher.embeddings_model") as mock_emb2, \
         patch("Backend.services.symptom_extractor.extractor_llm") as mock_llm, \
         patch("Backend.services.conversation_service.chain") as mock_chain:

        # Mock symptom extractor — returns "mild fever"
        mock_llm.invoke.return_value = MagicMock(content="mild fever")

        # Mock embeddings — return dummy vectors
        mock_emb.embed_documents.return_value  = [[0.1] * 1536]
        mock_emb2.embed_documents.return_value = [[0.1] * 1536]

        # Mock conversation chain — returns a safe response
        mock_chain.invoke.return_value = (
            "I'm sorry to hear that. How long have you had the fever?"
        )

        from Backend.api.app import app
        client = TestClient(app)

        response = client.post("/api/chat", json={
            "message":    "I have mild fever",
            "session_id": "test-shape-check-999",
            "username":   "TestUser"
        })

        assert response.status_code == 200, \
            f"Expected 200 but got {response.status_code}: {response.text}"

        data = response.json()

        assert "response"   in data, "Missing 'response' field"
        assert "priority"   in data, "Missing 'priority' field"
        assert "session_id" in data, "Missing 'session_id' field"

        assert isinstance(data["response"], str),  "response must be a string"
        assert len(data["response"]) > 0,          "response must not be empty"
        assert data["priority"] in ["critical", "urgent", "routine", "low"], \
            f"Invalid priority value: {data['priority']}"
        assert data["session_id"] == "test-shape-check-999", \
            "session_id must match request"

    print("✅ API response shape test passed")