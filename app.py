import streamlit as st
import time
import pandas as pd
import numpy as np
import altair as alt
from typing import Dict, List, Tuple

# =============================================================
# Agentic AI CEO — 10 Leadership Agents FMEA (Context-Aware)
# -------------------------------------------------------------
# What changed vs older version?
# - Mitigation strategies are now derived from:
#     (1) Problem text, (2) CEO decision text, and (3) each
#         agent's FMEA scores (S, O, D, RPN)
# - We extract risk THEMES from text and map them to targeted
#   ACTIONS with owners, KPIs and 30/60/90d timelines.
# - We also build a COMBINED ROADMAP weighted by RPN across
#   all 10 agents.
# - Still rule-based and Streamlit Free friendly (no extra deps).
# =============================================================

st.set_page_config(page_title="Agentic AI CEO — 10 Leadership Agents FMEA", page_icon="🤖", layout="wide")

# -----------------------------
# Classic cases to prefill
# -----------------------------
CASES = {
    "Nokia": "Failed to adapt from feature phones to smartphone OS ecosystems (iOS/Android).",
    "Kodak": "Underestimated the shift to digital photography despite inventing it internally.",
    "Blockbuster": "Ignored/late to video streaming disruption and online subscription models.",
    "Sears": "Lost retail share to e-commerce and discounters due to slow digital pivot.",
    "Pan Am": "High fixed costs, deregulation shocks, and financial mismanagement led to collapse.",
    "Suzuki (hypothetical)": "Should Suzuki Motor Corporation go into the food business?"
}

# -----------------------------
# 10 Leadership Agents
# -----------------------------
LEADER_STYLES: Dict[str, str] = {
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
    # Biases adjust FMEA S/O/D (0–10). + raises risk, - lowers risk.
    "Autocratic":        {"severity": +1, "occurrence": +1, "detection": -1},
    "Democratic":        {"severity":  0, "occurrence": +1, "detection":  0},
    "Laissez-Faire":     {"severity": +1, "occurrence": +2, "detection": -1},
    "Transformational":  {"severity": +2, "occurrence": +1, "detection": -1},
    "Transactional":     {"severity":  0, "occurrence":  0, "detection": +1},
    "Servant":           {"severity":  0, "occurrence":  0, "detection":  0},
    "Charismatic":       {"severity": +2, "occurrence": +1, "detection": -1},
    "Situational":       {"severity": -1, "occurrence": -1, "detection": +1},
    "Visionary":         {"severity": +2, "occurrence": +1, "detection": -1},
    "Bureaucratic":      {"severity": -1, "occurrence":  0, "detection": +2},
}

# -----------------------------
# Text-driven risk themes → targeted actions
# -----------------------------
# Each theme has trigger keywords and a small library of actions.
THEMES: Dict[str, Dict] = {
    "Market & Customer": {
        "triggers": ["market", "customer", "demand", "pricing", "price", "churn", "subscription", "share", "competition", "competitor", "adoption", "go-to-market", "launch", "segment"],
        "actions": [
            {"action": "Run discovery sprints (10 interviews/segment)", "owner": "CPO", "kpi": "Validated needs / segment fit"},
            {"action": "A/B price tests in 2 pilot markets", "owner": "CRO", "kpi": "Conversion uplift"},
            {"action": "Spin up lightweight GTM squad (PMM+Sales)", "owner": "COO", "kpi": "Qualified pipeline"},
        ],
    },
    "Product & Tech": {
        "triggers": ["product", "feature", "roadmap", "sdk", "api", "quality", "defect", "latency", "ux", "performance", "scalability", "integration", "mvp"],
        "actions": [
            {"action": "Build MVP with kill-switch gates", "owner": "CTO", "kpi": "MVP readiness / P0 bugs"},
            {"action": "Create dependency register", "owner": "PMO", "kpi": "Critical path coverage"},
            {"action": "Hardening sprint (reliability/QA)", "owner": "CTO", "kpi": "Incident rate"},
        ],
    },
    "Operations & Supply": {
        "triggers": ["supply", "logistics", "inventory", "warehouse", "vendor", "supplier", "manufacturing", "capacity", "lead time", "production", "operations"],
        "actions": [
            {"action": "Dual-source critical inputs", "owner": "COO", "kpi": "Supply continuity"},
            {"action": "S&OP weekly with red/amber gates", "owner": "COO", "kpi": "On-time fulfillment"},
            {"action": "CO2-optimized routing + buffer stock", "owner": "COO", "kpi": "OTIF / Emissions"},
        ],
    },
    "Cyber & Data": {
        "triggers": ["cyber", "ransomware", "breach", "data", "pii", "security", "infosec", "ciso", "phishing", "encryption"],
        "actions": [
            {"action": "Patch & backup playbook (3-2-1)", "owner": "CISO", "kpi": "RTO/RPO compliance"},
            {"action": "Tabletop incident drill", "owner": "CISO", "kpi": "MTTR drill score"},
            {"action": "Zero-trust access review", "owner": "CISO", "kpi": "Least-privilege coverage"},
        ],
    },
    "Legal & Compliance": {
        "triggers": ["regulation", "regulatory", "compliance", "license", "privacy", "gdpr", "hipaa", "antitrust", "esg", "sox"],
        "actions": [
            {"action": "Create compliance matrix & owners", "owner": "GC", "kpi": "Control coverage"},
            {"action": "Pre-clear regulator engagement", "owner": "GC", "kpi": "Issues pre-cleared"},
            {"action": "Privacy impact assessment", "owner": "DPO", "kpi": "PIA completion"},
        ],
    },
    "Finance": {
        "triggers": ["revenue", "margin", "capex", "opex", "cash", "burn", "budget", "cost", "profit", "pricing"],
        "actions": [
            {"action": "Zero-based budget on new bet", "owner": "CFO", "kpi": "Runway / ROI"},
            {"action": "Stage-gate investment (30/60/90)", "owner": "CFO", "kpi": "Spend vs gates"},
            {"action": "Unit economics stress-test", "owner": "FP&A", "kpi": "CAC/LTV health"},
        ],
    },
    "People & Culture": {
        "triggers": ["layoff", "attrition", "hiring", "talent", "skills", "training", "culture", "union", "morale", "org"],
        "actions": [
            {"action": "Critical roles heatmap & backfills", "owner": "CHRO", "kpi": "Role coverage"},
            {"action": "Upskill program (OKRs/quarter)", "owner": "CHRO", "kpi": "Completion / proficiency"},
            {"action": "Change comms & listening posts", "owner": "CHRO", "kpi": "Engagement index"},
        ],
    },
    "Brand & Comms": {
        "triggers": ["brand", "pr", "reputation", "trust", "media", "investor", "stakeholder", "narrative"],
        "actions": [
            {"action": "Issue transparent narrative & FAQ", "owner": "CMO", "kpi": "Sentiment / coverage"},
            {"action": "Localized comms per market", "owner": "CMO", "kpi": "Share of voice"},
            {"action": "Investor brief with risk/mitigation", "owner": "IR", "kpi": "Investor feedback"},
        ],
    },
    "AI & Ethics": {
        "triggers": ["ai", "ml", "model", "bias", "explainability", "safety", "hallucination", "dataset"],
        "actions": [
            {"action": "Bias & safety checklist", "owner": "CTO", "kpi": "Checklist pass rate"},
            {"action": "Human-in-loop for high-risk flows", "owner": "CTO", "kpi": "Override events"},
            {"action": "Model eval suite (accuracy/robust)", "owner": "CTO", "kpi": "Eval scores"},
        ],
    },
    "International & Geo": {
        "triggers": ["tariff", "sanction", "export", "geo", "cross-border", "fx", "customs"],
        "actions": [
            {"action": "Tariff-mitigated routing & pricing", "owner": "COO", "kpi": "Delivered margin"},
            {"action": "Local partners/co-dev MOUs", "owner": "CorpDev", "kpi": "Signed MOUs"},
            {"action": "FX hedging policy review", "owner": "Treasury", "kpi": "Hedge coverage"},
        ],
    },
}

# FMEA keyword heuristics (impacting base S/O/D)
RISKY_KEYWORDS = {
    "merger": (+2, +1, -1), "acquisition": (+2, +1, -1), "layoff": (+2, +2, -1),
    "restructure": (+1, +1, -1), "pivot": (+2, +1, -1), "ai": (+1, +1, -1),
    "cloud": (+1, 0, 0), "shutdown": (+3, +2, -2), "outsourcing": (+1, +1, 0),
    "offshoring": (+1, +1, 0), "automation": (+1, +1, 0), "cybersecurity": (+2, +1, +1),
    "compliance": (+1, 0, +2), "regulation": (+1, 0, +2), "expansion": (+1, +1, -1),
}

# -----------------------------
# Small utilities
# -----------------------------

def clamp(x: int, lo: int = 1, hi: int = 10) -> int:
    return max(lo, min(hi, int(round(x))))


def tokenize(text: str) -> List[str]:
    t = text.lower()
    for ch in ",.;:!?()[]{}|\n\t\r-/_":
        t = t.replace(ch, " ")
    return [w for w in t.split() if w]


def detect_themes(problem: str, decision: str) -> Dict[str, float]:
    """Return weighted theme scores based on keyword hits in problem+decision text."""
    text = f"{problem} {decision}".lower()
    tokens = tokenize(text)
    scores: Dict[str, float] = {k: 0.0 for k in THEMES}
    length_bonus = min(len(tokens) / 200.0, 3.0)  # complexity bonus
    for theme, spec in THEMES.items():
        hits = 0
        for trig in spec["triggers"]:
            if trig in text:
                hits += text.count(trig)
        # score = hits + small complexity bonus
        scores[theme] = hits + length_bonus
    # guarantee some mass even when no keywords match
    if sum(scores.values()) == 0:
        for k in scores:
            scores[k] = 0.5
    return scores


def base_scores(problem: str, decision: str) -> Tuple[int, int, int]:
    sev, occ, det = 6, 5, 5
    text = f"{problem} {decision}".lower()
    for kw, (ds, do, dd) in RISKY_KEYWORDS.items():
        if kw in text:
            sev += ds; occ += do; det += dd
    length_factor = min(len(text) // 200, 3)
    sev += length_factor; occ += length_factor
    return clamp(sev), clamp(occ), clamp(det)


def style_adjusted_scores(sev: int, occ: int, det: int, leader_name: str) -> Tuple[int, int, int]:
    for key, bias in STYLE_BIASES.items():
        if key in leader_name:
            sev += bias["severity"]
            occ += bias["occurrence"]
            det += bias["detection"]
            break
    return clamp(sev), clamp(occ), clamp(det)


def rpn_bucket(rpn: int) -> str:
    if rpn >= 180:
        return "0–30d"
    if rpn >= 120:
        return "30–60d"
    return "60–90d"


def pick_actions_for_theme(theme: str, n: int = 2) -> List[Dict[str, str]]:
    lib = THEMES[theme]["actions"]
    # rotate to avoid duplicates when many agents pick same theme
    # (simple deterministic shuffle by theme hash)
    idx = abs(hash(theme)) % len(lib)
    ordered = lib[idx:] + lib[:idx]
    return ordered[:n]


def build_mitigations(problem: str, decision: str, leader: str, sev: int, occ: int, det: int, theme_scores: Dict[str, float]):
    """Return a list of mitigation action dicts tailored to text + scores."""
    rpn = sev * occ * det
    # emphasize themes by (text score) * (severity + occurrence), lower detection => earlier timeline
    weights = {k: v * (sev + occ) for k, v in theme_scores.items()}
    ranked = sorted(weights.items(), key=lambda x: x[1], reverse=True)
    top_themes = [t for t, _ in ranked[:3]]

    actions = []
    for theme in top_themes:
        for a in pick_actions_for_theme(theme, n=2):
            actions.append({
                "Leader": leader,
                "Theme": theme,
                "Action": a["action"],
                "Owner": a["owner"],
                "KPI": a["kpi"],
                "StartBy": rpn_bucket(rpn),
                "Why": f"Elevated {theme} risk signaled by text and S={sev}, O={occ}, D={det}",
                "RPN": rpn,
            })
    # add one style-specific guardrail per leader
    style_guardrails = {
        "Autocratic": "Create a weekly red-team review & devil's advocate gate.",
        "Democratic": "Timebox debates and appoint a single decision owner.",
        "Laissez-Faire": "Set biweekly OKRs and visibility dashboards.",
        "Transformational": "Back-cast vision into 30/60/90-day deliverables.",
        "Transactional": "Audit KPIs quarterly to prevent metric gaming.",
        "Servant": "Balance empathy with crisp performance gates.",
        "Charismatic": "Run pre-mortems to counter optimism bias.",
        "Situational": "Reassess team readiness each sprint and adapt coaching.",
        "Visionary": "Run discovery sprints; add kill-switch gates.",
        "Bureaucratic": "Enable policy exceptions for controlled experiments.",
    }
    for key, tip in style_guardrails.items():
        if key in leader:
            actions.append({
                "Leader": leader,
                "Theme": "Governance",
                "Action": tip,
                "Owner": "CEO/PMO",
                "KPI": "Decision latency / risk review cadence",
                "StartBy": rpn_bucket(rpn),
                "Why": f"Style-specific guardrail for {key} leadership.",
                "RPN": rpn,
            })
            break
    return actions


# -----------------------------
# App UI — Inputs
# -----------------------------
st.title("🤖 Agentic AI CEO — 10 Leadership Agents FMEA (with text-driven mitigations)")
st.caption("Type a Problem and the Decision taken by the CEO. Ten leadership agents will score FMEA and propose targeted mitigations. The combined roadmap is weighted by risk (RPN).")

cols = st.columns([2, 1.1, 1.1, 1.1, 1.3])
with cols[0]:
    chosen_case = st.selectbox("Pick a classic case (optional)", [""] + list(CASES.keys()))
with cols[1]:
    pref_fill = st.button("Use case text")
with cols[2]:
    clear_btn = st.button("Clear inputs")
with cols[3]:
    run_btn_top = st.button("Run FMEA (Top)")
with cols[4]:
    delay = st.slider("Thinking delay per agent (s)", 0.0, 1.0, 0.0, 0.05, help="Just for visual pacing on free tier.")

# Inputs
pref_problem = CASES.get(chosen_case, "") if pref_fill else ""
problem = st.text_area("Problem", value=pref_problem, height=90, placeholder="Describe the business problem…")
decision = st.text_area("Decision taken by CEO", height=90, placeholder="Describe the decision that has been taken…")

if clear_btn:
    st.experimental_rerun()

run_btn = st.button("Run FMEA with 10 Leadership Agents") or run_btn_top

# -----------------------------
# Engine
# -----------------------------
results_rows = []
all_actions: List[Dict] = []

if run_btn:
    if not problem.strip() or not decision.strip():
        st.warning("Please provide both Problem and Decision taken by CEO.")
    else:
        st.info("Running agents…")
        st.markdown("---")

        theme_scores = detect_themes(problem, decision)
        sev0, occ0, det0 = base_scores(problem, decision)

        for leader, desc in LEADER_STYLES.items():
            # Visual thinking placeholder
            ph = st.empty()
            ph.info(f"Thinking… ({leader})")
            time.sleep(delay)
            ph.empty()

            sev, occ, det = style_adjusted_scores(sev0, occ0, det0, leader)
            rpn = sev * occ * det

            # Build context-aware mitigations
            mitig = build_mitigations(problem, decision, leader, sev, occ, det, theme_scores)
            all_actions.extend(mitig)

            with st.expander(leader, expanded=False):
                st.caption(desc)
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Severity", sev)
                c2.metric("Occurrence", occ)
                c3.metric("Detection", det)
                c4.metric("RPN", rpn)
                st.markdown("**Failure Mode**: Execution gaps, misalignment, and unintended consequences while applying the decision through the lens of this leadership style.")
                st.markdown("**Effects**: Delays, cost overruns, quality issues, compliance risks, or missed market opportunities.")
                actions_df = pd.DataFrame(mitig)[["Theme", "Action", "Owner", "KPI", "StartBy", "Why"]]
                st.markdown("**Mitigation Strategy (tailored)**")
                st.dataframe(actions_df, use_container_width=True)

            results_rows.append({
                "Leader": leader,
                "Severity": sev,
                "Occurrence": occ,
                "Detection": det,
                "RPN": rpn,
            })

        st.success("All agents finished.")

        # -----------------------------
        # Summary & Combined Roadmap
        # -----------------------------
        st.subheader("Summary of Results")
        res_df = pd.DataFrame(results_rows).sort_values("RPN", ascending=False)
        st.dataframe(res_df, use_container_width=True)

        # Top 3 bar chart
        top3 = res_df.head(3)
        chart = (
            alt.Chart(top3)
            .mark_bar()
            .encode(x=alt.X("Leader:N"), y=alt.Y("RPN:Q"), tooltip=["Leader", "RPN", "Severity", "Occurrence", "Detection"])
            .properties(height=220)
        )
        st.altair_chart(chart, use_container_width=True)

        # Combined roadmap: aggregate actions by (Action, Owner, Theme, StartBy)
        act_df = pd.DataFrame(all_actions)
        # weight = sum of contributing RPNs (higher -> earlier priority)
        grouped = (
            act_df
            .groupby(["Action", "Owner", "Theme", "KPI", "StartBy"], as_index=False)
            .agg({"RPN": "sum", "Leader": lambda s: ", ".join(sorted(set(s))), "Why": lambda s: "; ".join(sorted(set(s)))})
            .rename(columns={"RPN": "Weight", "Leader": "SupportedBy", "Why": "Rationale"})
            .sort_values(["StartBy", "Weight"], ascending=[True, False])
        )

        st.subheader("Mitigation suggestions (combined) — Risk-weighted roadmap")
        st.caption("Actions are derived from your text + each leader's FMEA. Timeline buckets reflect RPN (0–30d / 30–60d / 60–90d).")
        st.dataframe(grouped, use_container_width=True)

        # Downloads
        c1, c2, c3 = st.columns(3)
        with c1:
            st.download_button("Download FMEA Scores (CSV)", res_df.to_csv(index=False).encode(), "fmea_scores.csv", "text/csv")
        with c2:
            st.download_button("Download Mitigations (CSV)", grouped.to_csv(index=False).encode(), "mitigation_roadmap.csv", "text/csv")
        with c3:
            payload = {
                "problem": problem,
                "decision": decision,
                "theme_scores": theme_scores,
                "fmea": results_rows,
                "actions": grouped.to_dict(orient="records"),
            }
            st.download_button("Download Full Results (JSON)", pd.io.json.dumps(payload, indent=2).encode(), "results.json", "application/json")

# -----------------------------
# Help / Notes
# -----------------------------
st.markdown("""
---
**How to use**
1. (Optional) choose a classic case → click **Use case text** to prefill.
2. Describe your **Problem** and the **Decision taken by the CEO**.
3. Click **Run FMEA with 10 Leadership Agents**.
4. Expand each agent panel for tailored mitigations. Review the **Summary** for a risk‑weighted combined roadmap.

**Notes**
- Purely rule-based, no external APIs — safe for Streamlit Free.
- When you later add an open-source LLM endpoint, you can enrich the "Failure Mode" text or generate more actions per theme; the scoring/roadmap logic will remain compatible.
""")
