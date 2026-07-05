"""
CareerPilot-AI LangGraph Workflow.

Flow:
    parse_jd + parse_resume (concurrent)
    → rule_match
    → llm_analysis
    → integrity_guard
       ├─ passed → compose → END
       ├─ failed + retries left → llm_analysis (retry)
       └─ failed + exhausted → compose (with warnings) → END
"""
import logging

from langgraph.graph import StateGraph, END
from sqlalchemy.orm import Session

from app.agents.nodes import (
    compose_report,
    fallback_rule,
    integrity_guard,
    llm_analysis,
    parse_jd,
    parse_resume,
    rule_match,
)
from app.agents.state import CareerPilotState

logger = logging.getLogger(__name__)


def should_continue(state: CareerPilotState) -> str:
    """Conditional edge after integrity_guard."""
    if state.get("degraded"):
        return "fallback"

    if state.get("error"):
        return "fallback"

    if state.get("guard_passed", False):
        return "compose"

    retries = state.get("guard_retry_count", 0)
    max_retries = state.get("max_guard_retries", 2)

    if retries < max_retries:
        logger.info(f"Guard failed, retrying ({retries}/{max_retries})")
        return "retry"

    logger.warning(f"Guard failed after {max_retries} retries, composing with warnings")
    return "compose"


def build_graph() -> StateGraph:
    workflow = StateGraph(CareerPilotState)

    # Add nodes
    workflow.add_node("parse_jd", parse_jd)
    workflow.add_node("parse_resume", parse_resume)
    workflow.add_node("rule_match", rule_match)
    workflow.add_node("llm_analysis", llm_analysis)
    workflow.add_node("integrity_guard", integrity_guard)
    workflow.add_node("fallback", lambda s: s)  # placeholder, handled by caller

    # We handle compose differently — it needs db access
    # So compose is a sentinel node, actual work is done by the caller
    workflow.add_node("compose", lambda s: s)

    # Edges
    workflow.set_entry_point("parse_jd")
    workflow.add_edge("parse_jd", "parse_resume")
    workflow.add_edge("parse_resume", "rule_match")
    workflow.add_edge("rule_match", "llm_analysis")
    workflow.add_edge("llm_analysis", "integrity_guard")

    # Conditional: guard → compose / retry / fallback
    workflow.add_conditional_edges(
        "integrity_guard",
        should_continue,
        {
            "compose": "compose",
            "retry": "llm_analysis",
            "fallback": "fallback",
        }
    )

    workflow.add_edge("compose", END)
    workflow.add_edge("fallback", END)

    return workflow.compile()
