from core.schema import Extraction
from core.validators import (
    check_completeness,
    check_owners,
    check_quotes,
    flag_vague_words,
    speakers_in,
)

SOURCE = (
    "Priya (Client, Sales Head): Reps must see the last three orders. The app should be fast. "
    "Arjun (BA): Arjun will send drafts by Wednesday. Rahul from engineering will check offline sync."
)


def make(quote="The app should be fast", owner=None, due_date=None, req_id="R1", story_req_id="R1"):
    return Extraction.model_validate({
        "summary": "Sample summary",
        "requirements": [
            {
                "id": req_id,
                "title": "Speed",
                "type": "non_functional",
                "description": "App should be fast",
                "source_quote": quote,
            }
        ],
        "user_stories": [
            {
                "id": "US1",
                "requirement_id": story_req_id,
                "as_a": "rep",
                "i_want": "quick access",
                "so_that": "time is saved",
                "acceptance_criteria": [
                    "Given screen open, When clicked, Then loaded",
                    "Given slow network, When cached, Then instant",
                ],
            }
        ],
        "action_items": [
            {
                "task": "send drafts",
                "owner": owner,
                "due_date": due_date,
                "source_quote": "Arjun will send drafts by Wednesday",
            }
        ],
        "status_update": "In progress",
    })


def test_quote_found():
    """Valid verbatim quote is accepted without flags."""
    assert check_quotes(make(), SOURCE) == []


def test_invented_quote_is_flagged():
    """Invented quote not in source text is detected as a potential hallucination."""
    assert "R1" in check_quotes(make(quote="The app must support 10,000 concurrent users"), SOURCE)


def test_vague_word_flagged():
    """Unmeasurable adjective ('fast') is flagged for BA review."""
    assert flag_vague_words(make())["R1"] == ["fast"]


def test_missing_owner_and_date():
    """Missing action item owners and due dates are flagged as completeness gaps."""
    warnings = check_completeness(make(owner=None, due_date=None))
    assert "Action 1 has no owner" in warnings
    assert "Action 1 has no due date" in warnings


def test_broken_story_link():
    """User story referencing a non-existent requirement ID is flagged."""
    warnings = check_completeness(make(req_id="R1", story_req_id="R99"))
    assert "US1 points to unknown requirement R99" in warnings


def test_speakers_and_owner_attribution():
    """Action owner not mentioned in meeting transcript or speaker list is flagged for misattribution."""
    speakers = speakers_in(SOURCE)
    assert "priya" in speakers
    assert "arjun" in speakers

    # Arjun is a known speaker -> valid
    data_valid = make(owner="Arjun")
    assert check_owners(data_valid, SOURCE) == []

    # Rahul is mentioned in text -> valid
    data_mentioned = make(owner="Rahul")
    assert check_owners(data_mentioned, SOURCE) == []

    # Michael was never in transcript -> flagged
    data_invalid = make(owner="Michael Scott")
    assert "Action 1: owner 'Michael Scott' not found in the input" in check_owners(data_invalid, SOURCE)

