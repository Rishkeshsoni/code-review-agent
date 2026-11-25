
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
    status = (
        "awaiting_approval"
        if "apply_changes_node" in snap.next
        else "completed"
    )

    values = snap.values

    logger.info("Thread %s status: %s", thread_id, status)

    return {
        "thread_id": thread_id,
        "status": status,
        "next": list(snap.next),
        "lint_errors": values.get("lint_errors"),
        "refactored_code": values.get("refactored_code"),
        "history": values.get("history", []),
    }


@app.post("/api/webhooks/github")
def github_webhook(payload: dict):
    repo = payload.get("repository") or {}
    pr = payload.get("pull_request") or {}

    repo_url = repo.get("html_url") or payload.get("repo_url")
    branch = (pr.get("head") or {}).get("ref") or payload.get("branch")

    if not repo_url or not branch:
        raise HTTPException(
            status_code=400,
            detail="repo_url and branch are required",
        )

    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    try:
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
    except Exception as error:
        logger.exception("GitHub webhook processing failed")
        raise HTTPException(
            status_code=500,
            detail=f"Review processing failed: {type(error).__name__}",
        ) from error

    return _summary(thread_id, config)


@app.post("/api/reviews/{thread_id}/approve")
def approve_review(thread_id: str, body: ApprovalPayload):
    config = {"configurable": {"thread_id": thread_id}}
    snap = graph.get_state(config)

    if not snap.values:
        raise HTTPException(
            status_code=404,
            detail="Review thread not found",
        )

    if "apply_changes_node" not in snap.next:
        raise HTTPException(
            status_code=409,
            detail="Review is not waiting for approval",
        )

    if body.approved:
        graph.update_state(
            config,
            {
                "is_approved": True,
            },
        )
    else:
        feedback = (
            body.feedback.strip()
            if body.feedback and body.feedback.strip()
            else "Please improve the refactored code"
        )

        graph.update_state(
            config,
            {
                "is_approved": False,
                "reviewer_feedback": feedback,
            },
            as_node="lint_code_node",
        )

    try:
        graph.invoke(None, config)
    except Exception as error:
        logger.exception("Review resume failed")
        raise HTTPException(
            status_code=500,
            detail=f"Review resume failed: {type(error).__name__}",
        ) from error

    return _summary(thread_id, config)
