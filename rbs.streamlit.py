import json
import operator
from typing import Any, Dict, List, Tuple
import streamlit as st

# ---------------------------------------------------------
# 1) Rule Engine Core Logic
# ---------------------------------------------------------

OPS = {
    "==": operator.eq,
    "!=": operator.ne,
    ">": operator.gt,
    ">=": operator.ge,
    "<": operator.lt,
    "<=": operator.le,
    "in": lambda a, b: a in b,
    "not_in": lambda a, b: a not in b,
}

# Pre-loaded default JSON rules matching exact lab requirements
DEFAULT_SCHOLARSHIP_RULES: List[Dict[str, Any]] = [
    {
        "name": "Top merit candidate",
        "priority": 100,
        "conditions": [
            ["cgpa", ">=", 3.7],
            ["co_curricular_score", ">=", 80],
            ["family_income", "<=", 8000],
            ["disciplinary_actions", "==", 0],
        ],
        "action": {
            "decision": "AWARD FULL",
            "reason": "Excellent academic & co-curricular performance, with acceptable need",
        },
    },
    {
        "name": "Serious disciplinary record",
        "priority": 90,
        "conditions": [["disciplinary_actions", ">=", 2]],
        "action": {
            "decision": "REJECT",
            "reason": "Too many disciplinary records",
        },
    },
    {
        "name": "Low CGPA not eligible",
        "priority": 95,
        "conditions": [["cgpa", "<", 2.5]],
        "action": {
            "decision": "REJECT",
            "reason": "CGPA below minimum scholarship requirement",
        },
    },
    {
        "name": "Good candidate partial scholarship",
        "priority": 80,
        "conditions": [
            ["cgpa", ">=", 3.3],
            ["co_curricular_score", ">=", 60],
            ["family_income", "<=", 12000],
            ["disciplinary_actions", "<=", 1],
        ],
        "action": {
            "decision": "AWARD PARTIAL",
            "reason": "Good academic & involvement record with moderate need",
        },
    },
    {
        "name": "Need-based review",
        "priority": 70,
        "conditions": [
            ["cgpa", ">=", 2.5],
            ["family_income", "<=", 4000],
        ],
        "action": {
            "decision": "REVIEW",
            "reason": "High need but borderline academic score",
        },
    },
]


def evaluate_condition(facts: Dict[str, Any], cond: List[Any]) -> bool:
    """Evaluate a single rule condition tuple [field, operator, target_value]."""
    if len(cond) != 3:
        return False
    field, op, value = cond
    if field not in facts or op not in OPS:
        return False
    try:
        return OPS[op](facts[field], value)
    except Exception:
        return False


def rule_matches(facts: Dict[str, Any], rule: Dict[str, Any]) -> bool:
    """All conditions within a rule must evaluate to True (AND logic)."""
    return all(evaluate_condition(facts, c) for c in rule.get("conditions", []))


def run_rules(
    facts: Dict[str, Any], rules: List[Dict[str, Any]]
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """Evaluates facts against the rule set and returns the highest priority outcome."""
    fired = [r for r in rules if rule_matches(facts, r)]
    if not fired:
        return (
            {
                "decision": "REVIEW",
                "reason": "No matching evaluation criteria met. Requires manual screening.",
            },
            [],
        )

    # Conflict Resolution Strategy: Sort by priority descending
    fired_sorted = sorted(
        fired, key=lambda r: r.get("priority", 0), reverse=True
    )
    best_action = fired_sorted[0].get(
        "action", {"decision": "REVIEW", "reason": "No action specified."}
    )
    return best_action, fired_sorted


# ---------------------------------------------------------
# 2) Streamlit Interactive User Interface
# ---------------------------------------------------------

st.set_page_config(
    page_title="Scholarship Advisory Rule-Based System",
    page_icon="🎓",
    layout="wide",
)

st.title("🎓 University Scholarship Advisory System")
st.caption(
    "A transparent knowledge representation system designed for scholarship committee evaluation."
)

# Sidebar: Applicant Data Inputs
with st.sidebar:
    st.header("📋 Applicant Facts")
    cgpa = st.number_input(
        "Cumulative GPA (CGPA)",
        min_value=0.0,
        max_value=4.0,
        step=0.01,
        value=3.75,
    )
    family_income = st.number_input(
        "Monthly Family Income (MYR)", min_value=0, step=100, value=5000
    )
    co_curricular_score = st.number_input(
        "Co-curricular Score (0-100)", min_value=0, max_value=100, step=1, value=85
    )
    community_service_hours = st.number_input(
        "Community Service Hours", min_value=0, step=1, value=20
    )
    current_semester = st.number_input(
        "Current Semester of Study", min_value=1, max_value=12, step=1, value=3
    )
    disciplinary_actions = st.number_input(
        "Disciplinary Actions on Record", min_value=0, max_value=10, step=1, value=0
    )

    st.divider()
    st.header("⚙️ Rule Base (JSON Config)")
    default_json = json.dumps(DEFAULT_SCHOLARSHIP_RULES, indent=2)
    rules_text = st.text_area(
        "Edit rule definitions dynamically:", value=default_json, height=280
    )

    run_btn = st.button("Evaluate Eligibility", type="primary")

# Construct fact dictionary matching rule condition names
facts = {
    "cgpa": float(cgpa),
    "family_income": float(family_income),
    "co_curricular_score": int(co_curricular_score),
    "community_service_hours": int(community_service_hours),
    "current_semester": int(current_semester),
    "disciplinary_actions": int(disciplinary_actions),
}

st.subheader("Submitted Fact Vector")
st.json(facts)

# Parse rule inputs cleanly
try:
    rules = json.loads(rules_text)
    assert isinstance(rules, list), "Rule base must be a structured JSON array."
except Exception as e:
    st.error(
        f"Malformed JSON configuration. Falling back to default rules. Exception: {e}"
    )
    rules = DEFAULT_SCHOLARSHIP_RULES

st.subheader("Active Knowledge Base")
with st.expander("Inspect JSON Rule Definitions", expanded=False):
    st.code(json.dumps(rules, indent=2), language="json")

st.divider()

# Execution and Results Display
if run_btn:
    action, fired_rules = run_rules(facts, rules)

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("Final Decision")
        badge = action.get("decision", "REVIEW")
        reason = action.get("reason", "-")

        if badge == "AWARD FULL":
            st.success(f"🏆 **FULL SCHOLARSHIP AWARDED**\n\n*Reason:* {reason}")
        elif badge == "AWARD PARTIAL":
            st.info(f"🥇 **PARTIAL SCHOLARSHIP AWARDED**\n\n*Reason:* {reason}")
        elif badge == "REJECT":
            st.error(f"❌ **APPLICATION REJECTED**\n\n*Reason:* {reason}")
        else:
            st.warning(f"⚠️ **MANUAL COMMITTEE REVIEW REQUIRED**\n\n*Reason:* {reason}")

    with col2:
        st.subheader("Fired Rules Execution Chain")
        if not fired_rules:
            st.info("No rule conditions were met.")
        else:
            for i, r in enumerate(fired_rules, start=1):
                st.write(
                    f"**{i}. {r.get('name','(unnamed)')}** — *Priority Level:* `{r.get('priority',0)}`"
                )
                st.caption(f"Triggered Action: {r.get('action',{})}")
                with st.expander("Matched Conditions"):
                    for cond in r.get("conditions", []):
                        st.code(str(cond))
else:
    st.info("Adjust applicant parameters on the sidebar and click **Evaluate Eligibility**.")