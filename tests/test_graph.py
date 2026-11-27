
import hashlib
import hmac
from types import SimpleNamespace
from unittest.mock import patch

from fastapi.testclient import TestClient
from langgraph.checkpoint.memory import MemorySaver

import main
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


def test_automatic_refactor_retry():
    validation_results = [
        {"passed": True, "output": "Initial check"},
        {"passed": False, "output": "First validation failed"},
        {"passed": True, "output": "Second validation passed"},
    ]

    with (
        patch.dict("os.environ", {"GITHUB_TOKEN": "test-token"}),
        patch(
            "app.nodes.fetch_python_file",
            return_value=("a.py", "x=1\n"),
        ),
        patch(
            "app.nodes.validate_python_code",
            side_effect=validation_results,
        ),
    ):
        graph = build_graph(MemorySaver())
        config = _cfg("t3")

        graph.invoke(INIT, config)

        snapshot = graph.get_state(config)

        assert snapshot.next == ("apply_changes_node",)
        assert snapshot.values["refactor_attempts"] == 2
        assert snapshot.values["validation_passed"] is True


def test_refactor_stops_after_three_attempts():
    validation_results = [
        {"passed": True, "output": "Initial check"},
        {"passed": False, "output": "Validation failed"},
        {"passed": False, "output": "Validation failed"},
        {"passed": False, "output": "Validation failed"},
    ]

    with (
        patch.dict("os.environ", {"GITHUB_TOKEN": "test-token"}),
        patch(
            "app.nodes.fetch_python_file",
            return_value=("a.py", "x=1\n"),
        ),
        patch(
            "app.nodes.validate_python_code",
            side_effect=validation_results,
        ),
    ):
        graph = build_graph(MemorySaver())
        config = _cfg("t4")

        graph.invoke(INIT, config)

        snapshot = graph.get_state(config)

        assert snapshot.next == ()
        assert snapshot.values["refactor_attempts"] == 3
        assert snapshot.values["validation_passed"] is False


def test_webhook_rejects_missing_signature():
    client = TestClient(main.app)

    with patch.dict(
        "os.environ",
        {"GITHUB_WEBHOOK_SECRET": "test-secret"},
    ):
        response = client.post(
            "/api/webhooks/github",
            json={
                "repo_url": "https://github.com/test/repo",
                "branch": "main",
            },
        )

    assert response.status_code == 401
    assert response.json()["detail"] == (
        "Missing GitHub webhook signature"
    )


def test_webhook_rejects_invalid_signature():
    client = TestClient(main.app)

    with patch.dict(
        "os.environ",
        {"GITHUB_WEBHOOK_SECRET": "test-secret"},
    ):
        response = client.post(
            "/api/webhooks/github",
            json={
                "repo_url": "https://github.com/test/repo",
                "branch": "main",
            },
            headers={
                "X-Hub-Signature-256": "sha256=invalid",
            },
        )

    assert response.status_code == 401
    assert response.json()["detail"] == (
        "Invalid GitHub webhook signature"
    )


def test_webhook_accepts_valid_signature():
    client = TestClient(main.app)

    secret = "test-secret"
    body = (
        b'{"repo_url":"https://github.com/test/repo",'
        b'"branch":"main"}'
    )

    signature = "sha256=" + hmac.new(
        secret.encode("utf-8"),
        body,
        hashlib.sha256,
    ).hexdigest()

    snapshot = SimpleNamespace(
        values={
            "history": ["Webhook accepted"],
            "validation_passed": True,
            "refactor_attempts": 1,
            "refactored_code": "x = 1\n",
            "lint_errors": "NO ISSUES FOUND",
        },
        next=("apply_changes_node",),
    )

    with (
        patch.dict(
            "os.environ",
            {"GITHUB_WEBHOOK_SECRET": secret},
        ),
        patch.object(main.graph, "invoke") as invoke,
        patch.object(
            main.graph,
            "get_state",
            return_value=snapshot,
        ),
    ):
        response = client.post(
            "/api/webhooks/github",
            content=body,
            headers={
                "Content-Type": "application/json",
                "X-Hub-Signature-256": signature,
            },
        )

    assert response.status_code == 200
    assert response.json()["status"] == "awaiting_approval"
    invoke.assert_called_once()


def test_approval_rejects_missing_key():
    client = TestClient(main.app)

    with patch.dict(
        "os.environ",
        {"APPROVAL_API_KEY": "correct-test-key"},
    ):
        response = client.post(
            "/api/reviews/test-thread/approve",
            json={"approved": True},
        )

    assert response.status_code == 401
    assert response.json()["detail"] == (
        "Invalid or missing approval key"
    )


def test_approval_rejects_invalid_key():
    client = TestClient(main.app)

    with patch.dict(
        "os.environ",
        {"APPROVAL_API_KEY": "correct-test-key"},
    ):
        response = client.post(
            "/api/reviews/test-thread/approve",
            json={"approved": True},
            headers={"X-Approval-Key": "wrong-test-key"},
        )

    assert response.status_code == 401
    assert response.json()["detail"] == (
        "Invalid or missing approval key"
    )


def test_approval_accepts_valid_key():
    client = TestClient(main.app)

    snapshot = SimpleNamespace(
        values={
            "history": ["Review completed"],
            "validation_passed": True,
            "refactor_attempts": 1,
            "refactored_code": "x = 1\n",
            "lint_errors": "NO ISSUES FOUND",
        },
        next=("apply_changes_node",),
    )

    with (
        patch.dict(
            "os.environ",
            {"APPROVAL_API_KEY": "correct-test-key"},
        ),
        patch.object(
            main.graph,
            "get_state",
            return_value=snapshot,
        ),
        patch.object(main.graph, "update_state") as update_state,
        patch.object(main.graph, "invoke") as invoke,
    ):
        response = client.post(
            "/api/reviews/test-thread/approve",
            json={"approved": True},
            headers={"X-Approval-Key": "correct-test-key"},
        )

    assert response.status_code == 200
    assert response.json()["status"] == "awaiting_approval"

    update_state.assert_called_once_with(
        {"configurable": {"thread_id": "test-thread"}},
        {"is_approved": True},
    )

    invoke.assert_called_once_with(
        None,
        {"configurable": {"thread_id": "test-thread"}},
    )


def test_approval_returns_503_when_key_not_configured():
    client = TestClient(main.app)

    with patch.dict(
        "os.environ",
        {"APPROVAL_API_KEY": ""},
    ):
        response = client.post(
            "/api/reviews/test-thread/approve",
            json={"approved": True},
            headers={"X-Approval-Key": "some-test-key"},
        )

    assert response.status_code == 503
    assert response.json()["detail"] == (
        "Approval API security is not configured"
    )
