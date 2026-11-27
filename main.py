
import hashlib
import hmac
import logging
import os
import uuid
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException, Request
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
    values = snap.values

    if "apply_changes_node" in snap.next:
        status = "awaiting_approval"
    elif (
        values.get("validation_passed") is False
        and values.get("refactor_attempts", 0) >= 3
    ):
        status = "validation_failed"
    else:
        status = "completed"

    logger.info("Thread %s status: %s", thread_id, status)

    return {
        "thread_id": thread_id,
        "status": status,
        "next": list(snap.next),
        "lint_errors": values.get("lint_errors"),
        "refactored_code": values.get("refactored_code"),
        "validation_passed": values.get("validation_passed"),
        "refactor_attempts": values.get("refactor_attempts", 0),
        "history": values.get("history", []),
    }


@app.post("/api/webhooks/github")
async def github_webhook(
    request: Request,
    x_hub_signature_256: Optional[str] = Header(default=None),
):
    secret = os.getenv("GITHUB_WEBHOOK_SECRET")

    if not secret:
        logger.error("GitHub webhook secret is not configured")
        raise HTTPException(
            status_code=503,
            detail="Webhook security is not configured",
        )

    if not x_hub_signature_256:
        raise HTTPException(
            status_code=401,
            detail="Missing GitHub webhook signature",
        )

    body = await request.body()

    expected_signature = "sha256=" + hmac.new(
        secret.encode("utf-8"),
        body,
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(
        x_hub_signature_256,
        expected_signature,
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid GitHub webhook signature",
        )

    try:
        payload = await request.json()
    except Exception as error:
        raise HTTPException(
            status_code=400,
            detail="Invalid JSON payload",
        ) from error

    if not isinstance(payload, dict):
        raise HTTPException(
            status_code=400,
            detail="Webhook payload must be a JSON object",
        )

    repo = payload.get("repository") or {}
    pr = payload.get("pull_request") or {}

    if not isinstance(repo, dict) or not isinstance(pr, dict):
        raise HTTPException(
            status_code=400,
            detail="Invalid repository or pull_request format",
        )

    head = pr.get("head") or {}

    if not isinstance(head, dict):
        raise HTTPException(
            status_code=400,
            detail="Invalid pull_request head format",
        )

    repo_url = repo.get("html_url") or payload.get("repo_url")
    branch = head.get("ref") or payload.get("branch")

    if (
        not isinstance(repo_url, str)
        or not repo_url.strip()
        or not isinstance(branch, str)
        or not branch.strip()
    ):
        raise HTTPException(
            status_code=400,
            detail="repo_url and branch are required",
        )

    repo_url = repo_url.strip()
    branch = branch.strip()

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
def approve_review(
    thread_id: str,
    body: ApprovalPayload,
    approval_key: Optional[str] = Header(
        default=None,
        alias="X-Approval-Key",
    ),
):
    expected_key = os.getenv("APPROVAL_API_KEY")

    if not expected_key:
        raise HTTPException(
            status_code=503,
            detail="Approval API security is not configured",
        )

    if not approval_key or not hmac.compare_digest(
        approval_key,
        expected_key,
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing approval key",
        )

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
            {"is_approved": True},
        )
    else:
        if snap.values.get("refactor_attempts", 0) >= 3:
            raise HTTPException(
                status_code=409,
                detail="Maximum refactoring attempts reached",
            )

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
