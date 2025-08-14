import streamlit as st
import time
import json
import pandas as pd
import numpy as np
import altair as alt

# =============================
# Page Settings
# =============================
st.set_page_config(
    page_title="Agentic AI CEO — 10 Leadership Agents FMEA",
    page_icon="🤖",
    layout="wide",
)

# =============================
# Predefined classic cases (optional quick-start)
# =============================
CASES = {
    "Nokia": "Failed to adapt from feature phones to smartphone OS ecosystems (iOS/Android).",
    "Kodak": "Underestimated the shift to digital photography despite inventing it internally.",
    "Blockbuster": "Ignored/late to video streaming disruption and online subscription models.",
    "Sears": "Lost retail share to e-commerce and discounters due to slow digital pivot.",
    "Pan Am": "High fixed costs, deregulation shocks, and financial mismanagement led to collapse.",
}

# =============================
# Leadership styles & biases (10 agents)
# =============================
LEADER_STYLES = {
    "Autocratic Leader Agentic AI Agent CEO": "Decides alone, tight control, speed over consensus.",
    "Democratic Leader Agentic AI Agent CEO": "Seeks participation and consensus, inclusive decision-making.",
    "Laissez-Faire Leader Agentic AI Agent CEO": "Hands-off, relies on team autonomy and initiative.",
    "Transformational Leader Agentic AI Agent CEO": "Drives inspiring vision, change, and innovation.",
    "Transactional Leader Agentic AI Agent CEO": "Targets performance via incentives, KPIs, and compliance.",
    "Servant Leader Agentic AI Agent CEO": "Puts people first, grows teams, builds trust and community.",
    "Charismatic Leader Agentic AI Agent CEO": "Inspires via presence and storytelling; rallies followers.",
    "Situational Leader Agentic AI Agent CEO": "Adapts style to team maturity and task complexity.",
    "Visionary Leader Agentic AI Agent CEO": "Long-term strategic focus; bold bets and roadmaps.",
    "Bureaucratic Leader Agentic AI Agent CEO": "Follows rules and procedures; values consistency.",
}

STYLE_BIASES = {
    # Bias on 0–10 FMEA scale. Positive => higher risk on that axis; Negative => lower.
    "Autocratic":       {"severity": +1, "occurrence": +1, "detection": -1},
    "Democratic":       {"severity":  0, "occurrence": +1, "detection":  0},
    "Laissez-Faire":    {"severity": +1, "occurrence": +2, "detection": -1},
    "Transformational": {"severity": +2, "occurrence": +1, "detection": -1},
    "Transactional":    {"severity":  0, "occurrence":  0, "detection": +1},
    "Servant":          {"severity":  0, "occurrence":  0, "detection":  0},
    "Charismatic":      {"severity": +2, "occurrence": +1, "detection": -1},
    "Situational":      {"severity": -1, "occurrence": -1, "detection": +1},
    "Visionary":        {"severity": +2, "occurrence": +1, "detection": -1},
    "Bureaucratic":     {"severity": -1, "occurrence":  0, "detection": +2},
}

# =============================
# Lightweight heuristic FMEA helpers
# =============================
RISKY_KEYWORDS = {
    "merger": (+2, +1, -1), "acquisition": (+2, +1, -1), "layoff": (+2, +2, -1),
    "restructure": (+1, +1, -1), "pivot": (+2, +1, -1), "ai": (+1, +1, -1),
    "cloud": (+1, 0, 0), "shutdown": (+3, +2, -2), "outsourcing": (+1, +1, 0),
    "offshoring": (+1, +1, 0), "automation": (+1, +1, 0), "cybersecurity": (+2, +1, +1),
    "compliance": (+1, 0, +2), "regulation": (+1, 0, +2), "expansion": (+1, +1, -1),
}

def clamp(x: int, lo: int = 1, hi: int = 10) -> int:
    return max(lo, min(hi, int(round(x))))


def base_scores(problem: str, decision: str):
    """Start with moderate base scores and nudge by risky keywords and length complexity."""
    sev, occ, det = 6, 5, 5
    text = f"{problem} {decision}".lower()
    for kw, (ds, do, dd) in RISKY_KEYWORDS.items():
        if kw in text:
            sev += ds; occ += do; det += dd
    length_factor = min(len(text) // 200, 3)  # very simple complexity proxy
    sev += length_factor; occ += length_factor
    return clamp(sev), clamp(occ), clamp(det)


def style_adjusted_scores(sev: int, occ: int, det: int, leader_name: str):
    for key, bias in STYLE_BIASES.items():
        if key in leader_name:
            sev += bias["severity"]
            occ += bias["occurrence"]
            det += bias["detection"]
            break
    return clamp(sev), clamp(occ), clamp(det)


def mitigation_for_style(leader_name: str):
    if "Autocratic" in leader_name:
        return [
            "Create a fast weekly red‑team review.",
            "Nominate a devil’s advocate for critical decisions.",
        ]
    if "Democratic" in leader_name:
        return [
            "Timebox discussions and set a decision deadline.",
            "Designate a final decision owner to avoid stalemates.",
        ]
    if "Laissez-Faire" in leader_name:
        return [
            "Set minimal check‑ins (biweekly OKRs).",
            "Install simple dashboards for progress visibility.",
        ]
    if "Transformational" in leader_name:
        return [
            "Translate vision into 30‑60‑90 day milestones.",
            "Pair inspiration with risk & dependency registers.",
        ]
    if "Transactional" in leader_name:
        return [
            "Align incentives to long‑term value, not vanity metrics.",
            "Audit KPIs quarterly to prevent gaming.",
        ]
    if "Servant" in leader_name:
        return [
            "Balance empathy with clear performance gates.",
            "Escalate decisively when business risk rises.",
        ]
    if "Charismatic" in leader_name:
        return [
            "Triangulate narratives with data and experiments.",
            "Use pre‑mortems to counter optimism bias.",
        ]
    if "Situational" in leader_name:
        return [
            "Reassess team readiness every sprint.",
            "Adapt coaching/directing mix as competency changes.",
        ]
    if "Visionary" in leader_name:
        return [
            "Back‑cast the vision into quarterly deliverables.",
            "Run discovery sprints and kill‑switch gates.",
        ]
    if "Bureaucratic" in leader_name:
        return [
            "Allow policy exceptions for controlled experiments.",
            "Create a lightweight fast‑track for innovations.",
        ]
    return ["Establish controls, measure, iterate."]


def failure_modes_text(problem: str, decision: str, leader_name: str) -> str:
    return (
        f"Execution gaps, misalignment, and unintended consequences while applying the decision "
        f"through the lens of {leader_name}."
    )


def effects_text() -> str:
    return (
        "Delays, cost overruns, quality issues, compliance risks, or missed market opportunities."
    )


def eli5_block(leader_name: str, sev: int, occ: int, det: int) -> str:
    return (
        "ELI5: Severity = how big the ouch; Occurrence = how often it might happen; "
        "Detection = how quickly we can spot it. Higher RPN needs attention. "
        f"This style tilts risks like this → S={sev}, O={occ}, D={det}."
    )


def run_fmea(problem: str, decision: str, leader_name: str, want_eli5: bool):
    sev0, occ0, det0 = base_scores(problem, decision)
    sev, occ, det = style_adjusted_scores(sev0, occ0, det0, leader_name)
    rpn = sev * occ * det

    result = {
        "Leader": leader_name,
        "Failure Mode": failure_modes_text(problem, decision, leader_name),
        "Effects": effects_text(),
        "Severity": sev,
        "Occurrence": occ,
        "Detection": det,
        "RPN": rpn,
        "Mitigation": mitigation_for_style(leader_name),
    }
    if want_eli5:
        result["ELI5"] = eli5_block(leader_name, sev, occ, det)
    return result

# =============================
# UI
# =============================
st.title("🤖 Agentic AI CEO — 10 Leadership Agents FMEA")
st.caption("Type a Problem and the Decision taken by the CEO. Ten leadership agents will score FMEA and suggest mitigation.")

# Controls
col_top = st.columns([2, 1, 1, 1, 1])
with col_top[0]:
    chosen_case = st.selectbox("Pick a classic case (optional)", [""] + list(CASES.keys()))
with col_top[1]:
    use_case_btn = st.button("Use case text")
with col_top[2]:
    clear_btn = st.button("Clear inputs")
with col_top[3]:
    show_eli5 = st.checkbox("Show ELI5", value=True)
with col_top[4]:
    delay = st.slider("Thinking delay per agent (s)", 0.0, 1.0, 0.10, 0.05)

# Inputs
default_problem = CASES.get(chosen_case, "") if use_case_btn else ""
problem = st.text_area("Problem", value=default_problem, height=90, placeholder="Describe the business problem…")
decision = st.text_area("Decision taken by CEO", height=90, placeholder="Describe the decision that has been taken…")

if clear_btn:
    st.experimental_rerun()

run_btn = st.button("Run FMEA with 10 Leadership Agents")

# State storage for last run
if "last_results" not in st.session_state:
    st.session_state.last_results = []

if run_btn:
    if not problem.strip() or not decision.strip():
        st.warning("Please provide both Problem and Decision taken by CEO.")
    else:
        st.success("Running agents…")
        results = []
        prog = st.progress(0)
        total = len(LEADER_STYLES)
        for i, (leader, desc) in enumerate(LEADER_STYLES.items(), start=1):
            with st.container():
                with st.expander(leader, expanded=False):
                    st.caption(desc)
                    time.sleep(delay)
                    r = run_fmea(problem, decision, leader, want_eli5=show_eli5)
                    # Pretty print
                    st.markdown(f"**Failure Mode:** {r['Failure Mode']}")
                    st.markdown(f"**Effects:** {r['Effects']}")
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("Severity", r["Severity"])
                    c2.metric("Occurrence", r["Occurrence"])
                    c3.metric("Detection", r["Detection"])
                    c4.metric("RPN", r["RPN"])
                    st.markdown("**Mitigation Strategy:**")
                    for m in r["Mitigation"]:
                        st.markdown(f"- {m}")
                    if show_eli5 and "ELI5" in r:
                        st.info(r["ELI5"])
            results.append(r)
            prog.progress(int(i / total * 100))
        st.session_state.last_results = results
        st.success("All agents finished.")

# =============================
# Summary & Charts
# =============================
st.markdown("---")
st.subheader("Summary of Results")
if st.session_state.last_results:
    df = pd.DataFrame([
        {
            "Leader": r["Leader"],
            "Severity": r["Severity"],
            "Occurrence": r["Occurrence"],
            "Detection": r["Detection"],
            "RPN": r["RPN"],
        }
        for r in st.session_state.last_results
    ])
    st.dataframe(df, use_container_width=True)

    # Top risks table
    st.markdown("**Top 3 RPN (highest risk first)**")
    top3 = df.sort_values("RPN", ascending=False).head(3)
    st.table(top3[["Leader", "RPN", "Severity", "Occurrence", "Detection"]])

    # Altair bar chart of RPN
    chart = (
        alt.Chart(df)
        .mark_bar()
        .encode(
            x=alt.X("Leader:N", sort='-y'),
            y=alt.Y("RPN:Q"),
            tooltip=["Leader", "RPN", "Severity", "Occurrence", "Detection"],
        )
        .properties(height=280)
    )
    st.altair_chart(chart, use_container_width=True)

    # Collated mitigations for copy/paste
    st.markdown("**Mitigation suggestions (combined)**")
    all_mit = []
    for r in st.session_state.last_results:
        for m in r["Mitigation"]:
            all_mit.append({"Leader": r["Leader"], "Mitigation": m})
    mit_df = pd.DataFrame(all_mit)
    st.dataframe(mit_df, use_container_width=True)

    # Downloads
    colx, coly, colz = st.columns(3)
    with colx:
        csv_bytes = df.to_csv(index=False).encode()
        st.download_button("⬇️ Download FMEA Scores (CSV)", data=csv_bytes, file_name="fmea_scores.csv", mime="text/csv")
    with coly:
        mit_csv = mit_df.to_csv(index=False).encode()
        st.download_button("⬇️ Download Mitigations (CSV)", data=mit_csv, file_name="mitigations.csv", mime="text/csv")
    with colz:
        txt = json.dumps(st.session_state.last_results, indent=2).encode()
        st.download_button("⬇️ Download Full Results (JSON)", data=txt, file_name="fmea_results.json", mime="application/json")
else:
    st.info("Enter a Problem and Decision, then click ‘Run FMEA with 10 Leadership Agents’. Your analysis will appear above, and a consolidated summary will render here.")

# =============================
# Footer help
# =============================
st.markdown(
    """
---
**How to use**
1) (Optional) choose a classic case → click **Use case text** to prefill fields.
2) Describe your **Problem** and the **Decision taken by the CEO**.
3) Click **Run FMEA with 10 Leadership Agents**.
4) Expand each agent’s panel for detailed Failure Mode, Effects, scores and Mitigation.
5) Review the **Summary** below for top‑risk ranking and export buttons.

**Notes**
- Purely rule‑based (no external APIs), designed for Streamlit Free tier.
- You can later plug in an open‑source LLM to enrich the Failure Mode wording; the scoring logic will still work.
    """
)
