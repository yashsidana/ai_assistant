import os
from pathlib import Path
import pandas as pd
import streamlit as st

from core.export import to_jira_csv, to_markdown
from core.llm import get_provider
from core.pipeline import run

# Define root paths
ROOT_DIR = Path(__file__).resolve().parent
SAMPLES_DIR = ROOT_DIR / "samples"


def blank(x):
    """Normalize empty string or NaN to None."""
    return None if pd.isna(x) or x == "" else x


st.set_page_config(
    page_title="AI Requirements Assistant",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom header styling
st.title("📋 AI Requirements Assistant")
st.caption(
    "Human-in-the-Loop AI workflow: Converts messy meeting transcripts & client emails into structured, "
    "traceable requirements, INVEST user stories, and action items. A person must review and approve before export."
)

# Sidebar: Configuration, Provider Info, & Sample Loader
with st.sidebar:
    st.header("⚙️ Configuration")
    provider = get_provider()
    model_name = os.getenv("LLM_MODEL", "default")
    
    provider_labels = {
        "anthropic": f"🟣 Anthropic ({model_name})",
        "openai": f"🟢 OpenAI ({model_name})",
        "gemini": f"🔵 Google Gemini ({model_name})",
        "mock": "🟡 Offline / Demo Mode (Mock Engine)",
    }
    st.info(f"**Active LLM Engine:**\n\n{provider_labels.get(provider, provider)}")
    
    st.divider()
    st.subheader("📂 Load Sample Transcript")
    sample_files = list(SAMPLES_DIR.glob("*.txt")) if SAMPLES_DIR.exists() else []
    sample_options = ["-- None (Paste manually or upload) --"] + [f.name for f in sample_files]
    
    selected_sample = st.selectbox("Choose a fictional CPG sales scenario:", sample_options)
    
    sample_content = ""
    if selected_sample and selected_sample != "-- None (Paste manually or upload) --":
        sample_path = SAMPLES_DIR / selected_sample
        if sample_path.exists():
            sample_content = sample_path.read_text(encoding="utf-8")

    st.markdown("""
    ---
    ### 🛡️ Guardrails In Action
    - **Traceability:** Verbatim quotes checked via difflib window matching.
    - **Anti-Hallucination:** Missing owners/dates are preserved as `null`.
    - **Anti-Ambiguity:** Vague adjectives ('fast', 'seamless') are flagged.
    - **Speaker Grounding:** Action owners cross-checked with speakers.
    - **Export Gate:** Export locked until human verification checkbox.
    """)

# Input section
col_upload, col_hint = st.columns([2, 1])
with col_upload:
    uploaded = st.file_uploader("Upload transcript (.txt file)", type=["txt"])
    
if uploaded:
    default_text = uploaded.read().decode("utf-8")
elif sample_content:
    default_text = sample_content
else:
    default_text = ""

text = st.text_area(
    "Paste a meeting transcript or client email below:",
    value=default_text,
    height=240,
    placeholder="Priya (Client, Sales Head): The reps in the field need to see an outlet's last three orders...",
)

# Action button
if st.button("🚀 Analyse Transcript", type="primary", disabled=not text.strip()):
    try:
        with st.spinner("Extracting requirements, stories & running guardrail checks..."):
            data, report = run(text)
            st.session_state["result"] = (data.model_dump(), report)
            st.success("Extraction completed successfully!")
    except Exception as err:
        st.error(f"Execution Error: {err}")

# Results display & Human-in-the-Loop review
if "result" in st.session_state:
    d, report = st.session_state["result"]

    st.divider()
    st.subheader("📌 Executive Summary")
    st.info(d.get("summary", ""))

    tab_req, tab_us, tab_act, tab_checks = st.tabs([
        "📋 Requirements",
        "📖 User Stories",
        "✅ Action Items",
        "🛡️ Quality & Guardrail Checks"
    ])

    with tab_req:
        st.markdown("**Editable Requirements Table** *(Double-click any cell to adjust title, priority, or details)*")
        req = pd.DataFrame(d.get("requirements", []))
        if not req.empty:
            if "ambiguity_flags" in req.columns:
                req["ambiguity_flags"] = req["ambiguity_flags"].apply(
                    lambda x: "; ".join(x) if isinstance(x, list) else str(x)
                )
            req_edit = st.data_editor(req, num_rows="dynamic", use_container_width=True, key="req_editor")
        else:
            st.write("No requirements extracted.")
            req_edit = req

    with tab_us:
        st.markdown("**Editable User Stories (INVEST & Given/When/Then)**")
        us = pd.DataFrame(d.get("user_stories", []))
        if not us.empty:
            if "acceptance_criteria" in us.columns:
                us["acceptance_criteria"] = us["acceptance_criteria"].apply(
                    lambda x: "\n".join(x) if isinstance(x, list) else str(x)
                )
            us_edit = st.data_editor(us, num_rows="dynamic", use_container_width=True, key="us_editor")
        else:
            st.write("No user stories generated.")
            us_edit = us

    with tab_act:
        st.markdown("**Action Items & Follow-ups**")
        act = pd.DataFrame(d.get("action_items", []))
        act_edit = st.data_editor(act, num_rows="dynamic", use_container_width=True, key="act_editor")

    with tab_checks:
        st.subheader("🛡️ Automated Guardrails Report")
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### 🔍 Source Quote Verification")
            unsupported = report.get("unsupported_quotes") or []
            if unsupported:
                st.error(f"⚠️ **Quotes not found in input (possible hallucination):** {', '.join(unsupported)}")
            else:
                st.success("✅ All requirement and action quotes verified against source text.")

            st.markdown("#### 🗣️ Owner Attribution Check")
            unknown_owners = report.get("unknown_owners") or []
            if unknown_owners:
                st.warning(f"⚠️ **Unrecognized Action Owners:**\n" + "\n".join([f"- {o}" for o in unknown_owners]))
            else:
                st.success("✅ All action owners verified against recognized speakers or mentions.")

        with c2:
            st.markdown("#### ⚠️ Vague Wording Flags")
            vague = report.get("vague_words") or {}
            if vague:
                for rid, words in vague.items():
                    st.warning(f"**{rid}:** contains unmeasurable terms: *{', '.join(words)}*")
            else:
                st.success("✅ No unmeasurable vague wording flagged.")

            st.markdown("#### 🧩 Structural Completeness & Gaps")
            gaps = report.get("gaps") or []
            if gaps:
                for g in gaps:
                    st.info(f"ℹ️ {g}")
            else:
                st.success("✅ No structural gaps identified.")

        st.markdown("#### ❓ Clarifying Questions for the Client")
        open_questions = d.get("open_questions", [])
        if open_questions:
            for q in open_questions:
                st.markdown(f"- ❓ {q}")
        else:
            st.write("None.")

    st.divider()

    # Human-in-the-Loop Approval Gate (Section 7.4)
    st.subheader("✍️ Human Sign-Off & Export Gate")
    reviewed = st.checkbox("✅ I have reviewed and edited these outputs against the source transcript")

    if reviewed:
        # Re-pack reviewer's edits from data editors
        d["requirements"] = req_edit.to_dict("records")
        d["user_stories"] = [
            {
                **s,
                "acceptance_criteria": [line.strip() for line in str(s.get("acceptance_criteria", "")).split("\n") if line.strip()]
            }
            for s in us_edit.to_dict("records")
        ]
        d["action_items"] = [
            {**a, "owner": blank(a.get("owner")), "due_date": blank(a.get("due_date"))}
            for a in act_edit.to_dict("records")
        ]

        markdown_doc = to_markdown(d)
        jira_csv = to_jira_csv(d)

        col_dl1, col_dl2 = st.columns(2)
        with col_dl1:
            st.download_button(
                label="📥 Download Markdown Notes (project_notes.md)",
                data=markdown_doc,
                file_name="project_notes.md",
                mime="text/markdown",
                use_container_width=True
            )
        with col_dl2:
            st.download_button(
                label="📥 Download Jira-Ready Backlog (jira_backlog.csv)",
                data=jira_csv,
                file_name="jira_backlog.csv",
                mime="text/csv",
                use_container_width=True
            )

        with st.expander("📄 Preview Final Approved Markdown Document", expanded=False):
            st.code(markdown_doc, language="markdown")
    else:
        st.warning("🔒 Export is locked until you review the tables and confirm accuracy using the checkbox above.")

