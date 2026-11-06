import json
import re
from pydantic import ValidationError
from . import llm
from .prompts import REPAIR_PROMPT, SYSTEM_PROMPT, build_user_prompt
from .schema import Extraction
from .validators import (
    check_completeness,
    check_owners,
    check_quotes,
    flag_vague_words,
)


def clean(text: str) -> str:
    """
    Preprocess raw transcript:
    1. Strip timestamps like [10:32] or 10:32:05.
    2. Strip verbal fillers (um, uh).
    3. Normalize spaces and excessive newlines.
    Preserves speaker names so attribution and owner guardrails work properly.
    """
    text = re.sub(r"\[?\d{1,2}:\d{2}(:\d{2})?\]?", "", text)  # timestamps
    text = re.sub(r"\b(um+|uh+)\b,?\s*", "", text, flags=re.IGNORECASE)  # filler
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_json(raw: str) -> dict:
    """
    Defensively extract the JSON object from LLM response.
    Uses regex search as the primary extractor, with json.JSONDecoder.raw_decode
    as a safe fallback in case the model outputs trailing explanations containing braces.
    """
    # First attempt: find first '{' and use raw_decode
    first_brace = raw.find("{")
    if first_brace != -1:
        try:
            obj, _ = json.JSONDecoder().raw_decode(raw[first_brace:])
            if isinstance(obj, dict):
                return obj
        except json.JSONDecodeError:
            pass

    # Secondary attempt: DOTALL regex match across outer braces
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not match:
        raise ValueError("No JSON object found in the model output")
    return json.loads(match.group(0))


def run(transcript: str, max_retries: int = 2) -> tuple[Extraction, dict]:
    """
    Execute the core 8-step pipeline:
    1. Preprocess & clean input.
    2. Call LLM with strict system prompt & schema hint.
    3. Validate JSON against Pydantic schema.
    4. Execute bounded repair loop (max 2 retries) on ValidationError/ValueError.
    5. Run deterministic post-generation quality guardrails (quotes, vague words, completeness, unknown owners).
    6. Return validated Extraction model and guardrail report.
    """
    text = clean(transcript)  # the model AND the checks see the same text
    raw = llm.call_llm(SYSTEM_PROMPT, build_user_prompt(text))

    data: Extraction = None
    last_err = None

    for attempt in range(max_retries + 1):
        try:
            data = Extraction.model_validate(extract_json(raw))
            break
        except (ValueError, ValidationError) as err:
            last_err = err
            if attempt == max_retries:
                raise RuntimeError(
                    f"Output still invalid after {max_retries} repairs: {err}"
                )
            raw = llm.call_llm(
                SYSTEM_PROMPT,
                REPAIR_PROMPT.format(error=str(err)[:1500], previous=raw),
            )

    report = {
        "unsupported_quotes": check_quotes(data, text),
        "vague_words": flag_vague_words(data),
        "gaps": check_completeness(data),
        "unknown_owners": check_owners(data, text),
    }

    return data, report

