import csv
import io


def to_markdown(d: dict) -> str:
    """
    Format validated extraction into clean, executive-ready Markdown notes.
    Reflects all human edits made during the Streamlit review step.
    """
    out = ["# Project notes", "", "## Summary", d.get("summary", ""), "", "## Requirements"]
    for r in d.get("requirements", []):
        prio = r.get("priority", "unspecified")
        rtype = r.get("type", "functional")
        out.append(f"- **{r.get('id', '')} {r.get('title', '')}** ({rtype}, {prio}): {r.get('description', '')}")

    out += ["", "## User stories"]
    for s in d.get("user_stories", []):
        out.append(
            f"- **{s.get('id', '')}** ({s.get('requirement_id', '')}) As a {s.get('as_a', '')}, "
            f"I want {s.get('i_want', '')}, so that {s.get('so_that', '')}."
        )
        for ac in s.get("acceptance_criteria", []):
            out.append(f"  - {ac}")

    out += ["", "## Action items"]
    for a in d.get("action_items", []):
        owner = a.get("owner") or "TBD"
        due = a.get("due_date") or "TBD"
        out.append(f"- {a.get('task', '')} (owner: {owner}, due: {due})")

    out += ["", "## Risks"] + [f"- {x}" for x in d.get("risks", [])]
    out += ["", "## Open questions"] + [f"- {x}" for x in d.get("open_questions", [])]
    out += ["", "## Status update", d.get("status_update", "")]

    return "\n".join(out)


def to_jira_csv(d: dict) -> str:
    """
    Export backlog formatted directly for standard Jira CSV Issue Import.
    (Stretch Goal 5.12)
    Maps Requirements, User Stories, and Action Items into Jira Epics, Stories, and Sub-tasks.
    """
    output = io.StringIO()
    writer = csv.writer(output)

    # Jira CSV Standard Headers
    writer.writerow([
        "Issue Key",
        "Issue Type",
        "Summary",
        "Description",
        "Priority",
        "Assignee",
        "Due Date",
        "Acceptance Criteria",
        "Linked Requirement"
    ])

    priority_map = {
        "must": "Highest",
        "should": "High",
        "could": "Medium",
        "wont": "Low",
        "unspecified": "Medium"
    }

    # Write Requirements
    for r in d.get("requirements", []):
        writer.writerow([
            r.get("id", ""),
            "Requirement",
            r.get("title", ""),
            r.get("description", ""),
            priority_map.get(r.get("priority", "unspecified"), "Medium"),
            r.get("stakeholder") or "",
            "",
            "",
            ""
        ])

    # Write User Stories
    for s in d.get("user_stories", []):
        ac_text = "\n".join(s.get("acceptance_criteria", []))
        story_summary = f"As a {s.get('as_a', '')}, I want {s.get('i_want', '')}"
        story_desc = f"So that: {s.get('so_that', '')}\n\nAcceptance Criteria:\n{ac_text}"
        writer.writerow([
            s.get("id", ""),
            "Story",
            story_summary,
            story_desc,
            "Medium",
            "",
            "",
            ac_text,
            s.get("requirement_id", "")
        ])

    # Write Action Items
    for i, a in enumerate(d.get("action_items", []), start=1):
        writer.writerow([
            f"ACT-{i}",
            "Task",
            a.get("task", ""),
            f"Source quote: {a.get('source_quote', '')}",
            "High",
            a.get("owner") or "",
            a.get("due_date") or "",
            "",
            ""
        ])

    return output.getvalue()

