from core.export import to_jira_csv, to_markdown

SAMPLE_DATA = {
    "summary": "Meeting discussion notes",
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
            "i_want": "to take orders offline",
            "so_that": "poor signal does not block visits",
            "acceptance_criteria": [
                "Given no signal, When order submitted, Then saved on device",
                "Given signal restored, When app synced, Then orders uploaded",
            ],
        }
    ],
    "action_items": [
        {
            "task": "Check offline sync feasibility",
            "owner": "Rahul",
            "due_date": "next Wednesday",
            "source_quote": "Rahul will check offline sync feasibility",
        }
    ],
    "risks": ["Device storage limit on large catalogs"],
    "open_questions": ["What is the target sync frequency?"],
    "status_update": "Initial discovery call concluded.",
}


def test_markdown_export():
    """Verify markdown formatting includes all sections and content."""
    md = to_markdown(SAMPLE_DATA)
    assert "# Project notes" in md
    assert "## Summary" in md
    assert "Meeting discussion notes" in md
    assert "## Requirements" in md
    assert "- **R1 Offline Sync** (non_functional, must): App must work offline" in md
    assert "## User stories" in md
    assert "Given no signal" in md
    assert "## Action items" in md
    assert "(owner: Rahul, due: next Wednesday)" in md
    assert "## Risks" in md
    assert "## Open questions" in md
    assert "## Status update" in md


def test_jira_csv_export():
    """Verify Jira CSV output conforms to standard column headers and rows."""
    csv_str = to_jira_csv(SAMPLE_DATA)
    lines = csv_str.strip().splitlines()
    assert len(lines) >= 4  # Header + 1 Req + 1 Story + 1 Action
    header = lines[0]
    assert "Issue Key" in header
    assert "Issue Type" in header
    assert "Summary" in header
    assert "Acceptance Criteria" in header
    assert "Requirement" in csv_str
    assert "Story" in csv_str
    assert "Task" in csv_str

