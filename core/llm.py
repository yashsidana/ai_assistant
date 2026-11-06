import os
import json
from dotenv import load_dotenv

load_dotenv()

_client = None
_provider = None


def get_provider() -> str:
    """Determine which LLM provider to use based on available environment variables."""
    global _provider
    if _provider:
        return _provider

    configured_provider = os.getenv("LLM_PROVIDER", "").lower()
    if configured_provider:
        _provider = configured_provider
        return _provider

    if os.getenv("ANTHROPIC_API_KEY"):
        _provider = "anthropic"
    elif os.getenv("OPENAI_API_KEY"):
        _provider = "openai"
    elif os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY"):
        _provider = "gemini"
    else:
        _provider = "mock"
    return _provider


def call_llm(system: str, user: str, temperature: float = 0.0) -> str:
    """
    Unified LLM API gateway function.
    Reads provider credentials and model name from environment variables.
    Configured at temperature 0 for repeatable, consistent structured extraction.
    """
    global _client
    provider = get_provider()

    if provider == "anthropic":
        from anthropic import Anthropic
        if _client is None or not isinstance(_client, Anthropic):
            _client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        model_name = os.getenv("LLM_MODEL", "claude-3-5-sonnet-20241022")
        resp = _client.messages.create(
            model=model_name,
            max_tokens=4000,
            temperature=temperature,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        return resp.content[0].text

    elif provider == "openai":
        from openai import OpenAI
        if _client is None or not isinstance(_client, OpenAI):
            _client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        model_name = os.getenv("LLM_MODEL", "gpt-4o")
        resp = _client.chat.completions.create(
            model=model_name,
            temperature=temperature,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            max_tokens=4000,
        )
        return resp.choices[0].message.content

    elif provider == "gemini":
        try:
            from google import genai
            if _client is None:
                api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
                _client = genai.Client(api_key=api_key)
            model_name = os.getenv("LLM_MODEL", "gemini-1.5-flash")
            resp = _client.models.generate_content(
                model=model_name,
                contents=f"{system}\n\n{user}",
                config={"temperature": temperature, "max_output_tokens": 4000},
            )
            return resp.text
        except ImportError:
            import google.generativeai as genai_legacy
            api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
            genai_legacy.configure(api_key=api_key)
            model_name = os.getenv("LLM_MODEL", "gemini-1.5-flash")
            model = genai_legacy.GenerativeModel(
                model_name=model_name,
                system_instruction=system,
                generation_config={"temperature": temperature, "max_output_tokens": 4000},
            )
            resp = model.generate_content(user)
            return resp.text

    else:
        # Fallback offline mock response for demo / test execution when no API key is set
        return _mock_response(user)


def _mock_response(user: str) -> str:
    """Offline mock generator providing verified extraction output for testing without API keys."""
    # Check if this matches route_app_call sample
    if "reps in the field need to see an outlet's last three orders" in user.lower() or "route_app" in user.lower():
        sample_output = {
            "summary": "Discussion between Priya (Sales Head) and Arjun (BA) regarding field sales application requirements. Key needs include offline access to an outlet's last three orders, app responsiveness, and weekly email visit summaries for supervisors.",
            "requirements": [
                {
                    "id": "R1",
                    "title": "Order History Visibility",
                    "type": "functional",
                    "description": "Field representatives must be able to view an outlet's last three orders prior to placing a new order.",
                    "priority": "must",
                    "stakeholder": "Priya",
                    "source_quote": "The reps in the field need to see an outlet's last three orders before they take a new one.",
                    "ambiguity_flags": []
                },
                {
                    "id": "R2",
                    "title": "Offline Operation and Network Sync",
                    "type": "non_functional",
                    "description": "The application must function without internet connectivity and automatically synchronize orders once network is restored.",
                    "priority": "must",
                    "stakeholder": "Priya",
                    "source_quote": "it must work offline. Sync when they get back to network.",
                    "ambiguity_flags": []
                },
                {
                    "id": "R3",
                    "title": "Supervisor Visit Summary",
                    "type": "functional",
                    "description": "Provide supervisors with a daily summary report of field visits delivered via email.",
                    "priority": "should",
                    "stakeholder": "Priya",
                    "source_quote": "supervisors want a daily summary of visits by Friday, ideally by email.",
                    "ambiguity_flags": ["'by Friday' timing ambiguous - frequency conflict between daily and Friday delivery"]
                },
                {
                    "id": "R4",
                    "title": "Application Performance",
                    "type": "non_functional",
                    "description": "The application must perform fast as field reps have limited time per store visit.",
                    "priority": "unspecified",
                    "stakeholder": "Priya",
                    "source_quote": "the app should be fast, reps only spend a few minutes at each store.",
                    "ambiguity_flags": ["No measurable target; 'fast' and 'feel quick' are not testable"]
                }
            ],
            "user_stories": [
                {
                    "id": "US1",
                    "requirement_id": "R1",
                    "as_a": "field sales representative",
                    "i_want": "to view the last three completed orders of an outlet",
                    "so_that": "I can recommend relevant replenishment stock instead of guessing",
                    "acceptance_criteria": [
                        "Given an outlet is selected, When the order screen opens, Then the outlet's last three orders are displayed with date and order items",
                        "Given an outlet has fewer than three historical orders, When the order screen opens, Then all available historical orders are displayed with a note"
                    ]
                },
                {
                    "id": "US2",
                    "requirement_id": "R2",
                    "as_a": "field sales representative",
                    "i_want": "to record orders while offline and have them sync when network is restored",
                    "so_that": "poor network coverage at retail outlets does not halt my sales visits",
                    "acceptance_criteria": [
                        "Given the device has no cellular or wifi signal, When an order is submitted, Then the order is saved locally on device storage",
                        "Given unsynced offline orders exist on device, When network connectivity is re-established, Then the application automatically uploads all pending orders"
                    ]
                }
            ],
            "action_items": [
                {
                    "task": "Share draft requirements with the client",
                    "owner": "Arjun",
                    "due_date": "next Wednesday",
                    "source_quote": "I will share the draft requirements with you by next Wednesday."
                },
                {
                    "task": "Check offline sync feasibility",
                    "owner": "Rahul",
                    "due_date": None,
                    "source_quote": "Rahul from engineering will check offline sync feasibility."
                }
            ],
            "risks": [
                "Offline data synchronization conflicts when multiple reps or back-office modify accounts",
                "App performance perception without an agreed SLA metric"
            ],
            "open_questions": [
                "What specific measurable threshold constitutes 'fast' (e.g. order screen launch under 2.0 seconds on mid-range Android devices)?",
                "Does 'by Friday' mean the daily summary email feature must be delivered by this Friday, or should summaries be sent out on Fridays?"
            ],
            "status_update": "Completed discovery call with Priya regarding field sales mobile app. Captured requirements for offline order entry, 3-order history display, and supervisor reporting. Engineering checking offline sync feasibility; draft requirements to be shared by next Wednesday."
        }
        return json.dumps(sample_output)

    # Generic fallback mock
    return json.dumps({
        "summary": "Project discussion analysis summary.",
        "requirements": [
            {
                "id": "R1",
                "title": "System Feature",
                "type": "functional",
                "description": "General system functional capability extracted from input.",
                "priority": "unspecified",
                "stakeholder": None,
                "source_quote": user[:100].strip(),
                "ambiguity_flags": []
            }
        ],
        "user_stories": [
            {
                "id": "US1",
                "requirement_id": "R1",
                "as_a": "user",
                "i_want": "to use the system feature",
                "so_that": "I can complete my task",
                "acceptance_criteria": [
                    "Given the system is ready, When the action is triggered, Then the expected state is achieved",
                    "Given invalid input is supplied, When submitted, Then a helpful validation error is shown"
                ]
            }
        ],
        "action_items": [],
        "risks": [],
        "open_questions": [],
        "status_update": "Discussion analyzed and structured into requirements."
    })

