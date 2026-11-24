import logging
import uuid
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

load_dotenv()

from app.graph import graph  # noqa: E402

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("agent")

app = FastAPI(title="Autonomous Code Review & Refactoring Agent")


class ApprovalPayload(BaseModel):
    approved: bool
    feedback: Optional[str] = None


def _summary(thread_id, config):
    snap = graph.get_state(config)
    status = "awaiting_approval" if snap.next else "completed"
    v = snap.values
    logger.info("Thread %s status: %s", thread_id, status)
    return {
        "thread_id": thread_id,
        "status": status,
        "next": list(snap.next),
        "lint_errors": v.get("lint_errors"),
        "refactored_code": v.get("refactored_code"),
        "history": v.get("history"),
    }


@app.post("/api/webhooks/github")
def github_webhook(payload: dict):
    repo = payload.get("repository") or {}
    pr = payload.get("pull_request") or {}
    repo_url = repo.get("html_url") or payload.get("repo_url")
    branch = (pr.get("head") or {}).get("ref") or payload.get("branch")
    if not repo_url or not branch:
        raise HTTPException(400, "repo_url and branch are required")

    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    graph.invoke(
        {
            "pr_url": pr.get("html_url") or repo_url,
            "repo_url": repo_url,
            "branch": branch,
            "pr_number": pr.get("number") or payload.get("pr_number"),
            "history": [],
            "is_approved": False,
            "reviewer_feedback": "",
        },
        config,
    )
    return _summary(thread_id, config)


@app.post("/api/reviews/{thread_id}/approve")
def approve_review(thread_id: str, body: ApprovalPayload):
    config = {"configurable": {"thread_id": thread_id}}
    snap = graph.get_state(config)
    if not snap.next:
        raise HTTPException(404, "Thread not found or already completed")

    if body.approved:
        graph.update_state(config, {"is_approved": True})
    else:
        # rollback: pretend lint just finished, so graph re-runs propose_refactor_node
        graph.update_state(
            config,
            {
                "is_approved": False,
                "reviewer_feedback": body.feedback or "Please improve the refactor",
            },
            as_node="lint_code_node",
        )
    graph.invoke(None, config)
    return _summary(thread_id, config)