from unittest.mock import patch

from langgraph.checkpoint.memory import MemorySaver

from app.graph import build_graph
from app.tools import run_linter_tool

INIT = {
    "pr_url": "https://github.com/test/repo",
    "repo_url": "https://github.com/test/repo",
    "branch": "main",
    "history": [],
    "is_approved": False,
    "reviewer_feedback": "",
}


def _cfg(tid):
    return {"configurable": {"thread_id": tid}}


def test_lint_tool_finds_syntax_error():
    result = run_linter_tool.invoke({"code_string": "def foo(:\n    pass\n"})
    assert result != "NO_LINT_ERRORS"
    assert "E9" in result


def test_lint_tool_clean_code():
    result = run_linter_tool.invoke({"code_string": "x = 1\n"})
    assert result == "NO_LINT_ERRORS"


def test_rejection_rolls_back_to_refactor():
    with patch("app.nodes.fetch_python_file", return_value=("a.py", "x=1\n")), patch(
        "app.nodes.commit_file"
    ) as commit:
        g = build_graph(MemorySaver())
        cfg = _cfg("t1")
        g.invoke(INIT, cfg)
        snap = g.get_state(cfg)
        assert snap.next == ("apply_changes_node",)
        before = len(snap.values["history"])

        g.update_state(
            cfg,
            {"is_approved": False, "reviewer_feedback": "Use list comprehensions"},
            as_node="lint_code_node",
        )
        g.invoke(None, cfg)

        snap = g.get_state(cfg)
        assert snap.next == ("apply_changes_node",)
        assert snap.values["reviewer_feedback"] == "Use list comprehensions"
        assert len(snap.values["history"]) > before
        commit.assert_not_called()


def test_approval_commits_and_finishes():
    with patch("app.nodes.fetch_python_file", return_value=("a.py", "x=1\n")), patch(
        "app.nodes.commit_file"
    ) as commit:
        g = build_graph(MemorySaver())
        cfg = _cfg("t2")
        g.invoke(INIT, cfg)
        g.update_state(cfg, {"is_approved": True})
        g.invoke(None, cfg)
        assert g.get_state(cfg).next == ()
        commit.assert_called_once()
