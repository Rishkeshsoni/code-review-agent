from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from app.nodes import (
    apply_changes_node,
    fetch_pr_node,
    lint_code_node,
    propose_refactor_node,
)
from app.state import ReviewState


def build_graph(checkpointer=None):
    builder = StateGraph(ReviewState)
    builder.add_node("fetch_pr_node", fetch_pr_node)
    builder.add_node("lint_code_node", lint_code_node)
    builder.add_node("propose_refactor_node", propose_refactor_node)
    builder.add_node("apply_changes_node", apply_changes_node)

    builder.add_edge(START, "fetch_pr_node")
    builder.add_edge("fetch_pr_node", "lint_code_node")
    builder.add_edge("lint_code_node", "propose_refactor_node")
    builder.add_edge("propose_refactor_node", "apply_changes_node")
    builder.add_edge("apply_changes_node", END)

    return builder.compile(
        checkpointer=checkpointer or MemorySaver(),
        interrupt_before=["apply_changes_node"],
    )


graph = build_graph(MemorySaver())