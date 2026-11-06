import re
from difflib import SequenceMatcher
from .schema import Extraction

VAGUE_WORDS = [
    "fast", "quick", "quickly", "user-friendly", "easy", "simple",
    "intuitive", "robust", "scalable", "flexible", "soon", "asap",
    "etc", "appropriate", "as needed", "seamless", "efficient",
    "real-time", "large", "many", "some",
]


def _norm(s: str) -> str:
    """Lowercase and normalize all whitespace sequences to a single space."""
    return re.sub(r"\s+", " ", s.lower()).strip()


def quote_in_source(quote: str, source: str, threshold: float = 0.85) -> bool:
    """
    Verify whether quote exists in source text.
    1. Checks exact substring after normalization.
    2. Slides a window across the source using difflib.SequenceMatcher (accepts similarity >= 0.85)
       to tolerate minor transcription variances, dropped punctuation, or minor token differences.
    """
    q, t = _norm(quote), _norm(source)
    if not q:
        return False
    if q in t:
        return True

    w = len(q)
    step = max(1, w // 4)
    best = 0.0
    for i in range(0, max(1, len(t) - w + 1), step):
        best = max(best, SequenceMatcher(None, q, t[i:i + w]).ratio())
        if best >= threshold:
            return True
    return best >= threshold


def check_quotes(data: Extraction, source: str) -> list[str]:
    """Return ids of items whose source_quote is not grounded in the input text."""
    bad = []
    for r in data.requirements:
        if not quote_in_source(r.source_quote, source):
            bad.append(r.id)
    for i, a in enumerate(data.action_items, start=1):
        if not quote_in_source(a.source_quote, source):
            bad.append(f"Action {i}")
    return bad


def flag_vague_words(data: Extraction) -> dict[str, list[str]]:
    """Return {requirement id: [vague words found in its description or title]}."""
    flags = {}
    for r in data.requirements:
        text = _norm(r.title + " " + r.description)
        found = [w for w in VAGUE_WORDS if re.search(rf"\b{re.escape(w)}\b", text)]
        if found:
            flags[r.id] = found
    return flags


def check_completeness(data: Extraction) -> list[str]:
    """Return human-readable warnings about structural gaps, missing links, and unassigned tasks."""
    warnings = []
    req_ids = {r.id for r in data.requirements}
    linked = {s.requirement_id for s in data.user_stories}

    # Broken user story links
    for s in data.user_stories:
        if s.requirement_id not in req_ids:
            warnings.append(f"{s.id} points to unknown requirement {s.requirement_id}")

    # Requirements without user stories (e.g., untestable or non-functional needs)
    for rid in sorted(req_ids - linked):
        warnings.append(f"{rid} has no user story")

    # Action items missing accountability
    for i, a in enumerate(data.action_items, start=1):
        if not a.owner:
            warnings.append(f"Action {i} has no owner")
        if not a.due_date:
            warnings.append(f"Action {i} has no due date")

    return warnings


def speakers_in(text: str) -> set[str]:
    """
    Extract speaker names appearing before a colon at the start of lines,
    ignoring parenthetical role notes like 'Priya (Client, Sales Head):'.
    """
    pattern = r"^([A-Z][\w.'-]*(?: [A-Z][\w.'-]*)*)(?: \([^)]*\))?:"
    return {m.group(1).lower() for m in re.finditer(pattern, text, re.MULTILINE)}


def check_owners(data: Extraction, text: str) -> list[str]:
    """
    Anti-misattribution check:
    Flag action item owners who are neither identified speakers nor mentioned in the input text.
    """
    known = speakers_in(text)
    low = text.lower()
    bad = []
    for i, a in enumerate(data.action_items, start=1):
        if a.owner and a.owner.lower() not in known and a.owner.lower() not in low:
            bad.append(f"Action {i}: owner '{a.owner}' not found in the input")
    return bad

