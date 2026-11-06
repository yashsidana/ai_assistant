import json
import pytest
from core.pipeline import clean, extract_json, run
from core import llm


def test_clean_transcript():
    """Verify regex cleaning strips timestamps and fillers while preserving speaker names."""
    dirty = (
        "[10:32] Priya (Sales Head): Um, the app should be, uh, fast. \n\n\n\n"
        "[10:32:45] Arjun: Understood.   Let's check sync."
    )
    cleaned = clean(dirty)
    assert "[10:32]" not in cleaned
    assert "[10:32:45]" not in cleaned
    assert "um" not in cleaned.lower()
    assert "uh" not in cleaned.lower()
    assert "Priya (Sales Head):" in cleaned
    assert "Arjun:" in cleaned
    assert "\n\n\n" not in cleaned


def test_extract_json_with_surrounding_prose():
    """Verify JSON extractor correctly isolates JSON object when LLM returns conversational markdown prose."""
    raw_response = (
        "Here is the structured documentation you requested:\n```json\n"
        '{"summary": "Test", "requirements": [], "user_stories": [], "action_items": [], "status_update": "Done"}\n'
        "```\nHope this helps!"
    )
    extracted = extract_json(raw_response)
    assert isinstance(extracted, dict)
    assert extracted["summary"] == "Test"
    assert extracted["status_update"] == "Done"


def test_repair_loop_recovers_from_invalid_json(monkeypatch):
    """
    Simulate LLM outputting malformed JSON on attempt 1,
    and recovering with valid Pydantic Extraction JSON on attempt 2 via REPAIR_PROMPT.
    """
    call_count = 0

    valid_json = json.dumps({
        "summary": "Recovered valid summary",
        "requirements": [
            {
                "id": "R1",
                "title": "Offline Sync",
                "type": "non_functional",
                "description": "App must work offline",
                "priority": "must",
                "stakeholder": "Priya",
                "source_quote": "App must work offline",
                "ambiguity_flags": [],
            }
        ],
        "user_stories": [
            {
                "id": "US1",
                "requirement_id": "R1",
                "as_a": "rep",
                "i_want": "offline order taking",
                "so_that": "visits are not blocked",
                "acceptance_criteria": [
                    "Given offline state, When order created, Then saved locally",
                    "Given online state, When synced, Then uploaded to ERP",
                ],
            }
        ],
        "action_items": [],
        "risks": [],
        "open_questions": [],
        "status_update": "Requirements captured successfully",
    })

    def fake_call_llm(system: str, user: str, temperature: float = 0.0) -> str:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            # First call returns invalid JSON
            return "Sure! { malformed json : unquoted value"
        else:
            # Second call (after repair prompt) returns valid JSON
            return valid_json

    monkeypatch.setattr(llm, "call_llm", fake_call_llm)

    transcript = "Priya: App must work offline."
    data, report = run(transcript, max_retries=2)

    assert call_count == 2
    assert data.summary == "Recovered valid summary"
    assert len(data.requirements) == 1
    assert data.requirements[0].id == "R1"


def test_repair_loop_raises_on_persistent_failure(monkeypatch):
    """Verify runtime error is raised if model fails to produce valid output within max_retries."""
    def always_invalid(system: str, user: str, temperature: float = 0.0) -> str:
        return "{ broken : true "

    monkeypatch.setattr(llm, "call_llm", always_invalid)

    with pytest.raises(RuntimeError, match="Output still invalid after 2 repairs"):
        run("Sample transcript", max_retries=2)

