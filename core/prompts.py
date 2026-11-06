import re

SYSTEM_PROMPT = """You are a senior business analyst assistant. You convert meeting transcripts and client emails into structured project documentation.

Rules:
1. Use ONLY information present in the input. Never invent requirements, names, dates or numbers.
2. For every requirement and every action item, copy the exact words from the input that support it into "source_quote". Copy word for word, do not rephrase.
3. If something is vague or missing (no owner, no date, no measurable target), do NOT fill it in. Use null for missing owner or date, add a note to "ambiguity_flags", and add a clarifying question to "open_questions". An owner must be a person named in the input.
4. Write each user story as: As a <role>, I want <goal>, so that <benefit>. Give at least two acceptance criteria per story, each in Given / When / Then form.
5. Set "priority" (must, should, could, wont) only if the speaker stated or clearly implied it. Otherwise use "unspecified".
6. Every user story must reference an existing requirement id in "requirement_id".
7. Return ONLY valid JSON that matches the schema. No prose, no markdown fences."""

SCHEMA_HINT = """{
  "summary": "2-3 sentence summary of the discussion",
  "requirements": [
    {
      "id": "R1",
      "title": "Short title",
      "type": "functional|non_functional|constraint|assumption",
      "description": "Clear statement of the requirement",
      "priority": "must|should|could|wont|unspecified",
      "stakeholder": null,
      "source_quote": "exact words copied verbatim from input",
      "ambiguity_flags": []
    }
  ],
  "user_stories": [
    {
      "id": "US1",
      "requirement_id": "R1",
      "as_a": "role",
      "i_want": "goal",
      "so_that": "benefit",
      "acceptance_criteria": [
        "Given ... When ... Then ...",
        "Given ... When ... Then ..."
      ]
    }
  ],
  "action_items": [
    {
      "task": "Specific task description",
      "owner": null,
      "due_date": null,
      "source_quote": "exact sentence where task was assigned or agreed"
    }
  ],
  "risks": [
    "Identified risk or technical dependency"
  ],
  "open_questions": [
    "Clarifying question to resolve vague or missing information"
  ],
  "status_update": "Short, factual update for stakeholders (under 120 words)"
}"""


def build_user_prompt(text: str) -> str:
    """Construct user prompt placing input safely within XML-like delimiters to mitigate prompt injection."""
    return (
        "Extract the project documentation from the input below.\n\n"
        f"Return JSON in exactly this shape:\n{SCHEMA_HINT}\n\n"
        f"<input>\n{text}\n</input>"
    )


REPAIR_PROMPT = """Your previous answer failed validation.

Validation error:
{error}

Previous answer:
{previous}

Return a corrected version. Fix ONLY what the error describes, keep everything else, and return ONLY valid JSON."""


TEST_SCENARIOS_PROMPT = """You are a QA analyst. For the user story and acceptance criteria below, generate a comprehensive set of test scenarios.
Return a JSON array of objects with keys: "id", "scenario", "steps", "expected_result", "type" ("positive" | "negative" | "edge").
Cover every acceptance criterion at least once, and include at least 2 negative and 2 edge cases.

<story>
{story_text}
</story>"""

