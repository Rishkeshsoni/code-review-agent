
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


def _cfg(thread_id):
    return {"configurable": {"thread_id": thread_id}}


def test_lint_tool_finds_syntax_error():
    result = run_linter_tool.invoke(
        {"code_string": "def foo(:\n    pass\n"}
    )

    assert "FLAKE8" in result
    assert "E999" in result or "syntax" in result.lower()


def test_lint_tool_clean_code():
    result = run_linter_tool.invoke(
        {"code_string": "x = 1\n"}
    )

    assert "FLAKE8" in result
    assert "BLACK" in result
    assert "PYLINT" in result
    assert "NO ISSUES FOUND" in result


def test_rejection_rolls_back_to_refactor():
    with (
        patch.dict("os.environ", {"GITHUB_TOKEN": "test-token"}),
        patch(
            "app.nodes.fetch_python_file",
            return_value=("a.py", "x=1\n"),
        ),
        patch("app.nodes.commit_file") as commit,
    ):
        graph = build_graph(MemorySaver())
        config = _cfg("t1")

        graph.invoke(INIT, config)

        snapshot = graph.get_state(config)

        assert snapshot.next == ("apply_changes_node",)

        before = len(snapshot.values["history"])

        graph.update_state(
            config,
            {
                "is_approved": False,
                "reviewer_feedback": "Use list comprehensions",
            },
            as_node="lint_code_node",
        )

        graph.invoke(None, config)

        snapshot = graph.get_state(config)

        assert snapshot.next == ("apply_changes_node",)
        assert snapshot.values["reviewer_feedback"] == (
            "Use list comprehensions"
        )
        assert len(snapshot.values["history"]) > before

        commit.assert_not_called()


def test_approval_commits_and_finishes():
    with (
        patch.dict("os.environ", {"GITHUB_TOKEN": "test-token"}),
        patch(
            "app.nodes.fetch_python_file",
            return_value=("a.py", "x=1\n"),
        ),
        patch("app.nodes.commit_file") as commit,
    ):
        graph = build_graph(MemorySaver())
        config = _cfg("t2")

        graph.invoke(INIT, config)

        graph.update_state(
            config,
            {"is_approved": True},
        )

        graph.invoke(None, config)

        assert graph.get_state(config).next == ()

        commit.assert_called_once()
