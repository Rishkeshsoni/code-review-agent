import logging
import os

import black

from app.github_client import SAMPLE_CODE, commit_file, fetch_python_file
from app.tools import run_linter_tool

logger = logging.getLogger("agent")


def _strip_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines)
    return text


def fetch_pr_node(state):
    history = list(state.get("history", []))
    try:
        path, content = fetch_python_file(
            state["repo_url"], state["branch"], state.get("pr_number")
        )
        history.append(f"Fetched {path} from GitHub")
    except Exception as e:
        path, content = "sample.py", SAMPLE_CODE
        history.append(f"GitHub fetch failed ({e}); using sample code (demo mode)")
    logger.info("fetch_pr_node done: %s", path)
    return {"file_path": path, "code_contents": content, "history": history}


def lint_code_node(state):
    history = list(state.get("history", []))
    errors = run_linter_tool.invoke({"code_string": state["code_contents"]})
    history.append("Linter ran")
    logger.info("lint_code_node done")
    return {"lint_errors": errors, "history": history}


def propose_refactor_node(state):
    history = list(state.get("history", []))
    code = state["code_contents"]
    errors = state.get("lint_errors", "")
    feedback = state.get("reviewer_feedback", "")
    attempt = len([h for h in history if h.startswith("Refactor proposed")]) + 1

    if os.getenv("OPENAI_API_KEY"):
        from langchain_openai import ChatOpenAI

        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        prompt = (
            "Refactor this Python code to fix the lint errors. "
            "Keep the functionality exactly the same. "
            "Return ONLY the code, no explanation.\n\n"
            f"LINT ERRORS:\n{errors}\n\n"
            f"REVIEWER FEEDBACK:\n{feedback or 'none'}\n\n"
            f"CODE:\n{code}"
        )
        new_code = _strip_fences(llm.invoke(prompt).content)
    else:
        # demo mode: no OpenAI key, so use black formatter
        try:
            new_code = black.format_str(code, mode=black.Mode())
        except Exception:
            new_code = code
        if feedback:
            new_code += f"\n# Reviewer feedback applied (demo): {feedback}\n"

    history.append(f"Refactor proposed (attempt {attempt})")
    logger.info("propose_refactor_node done, attempt %s", attempt)
    return {"refactored_code": new_code, "history": history}


def apply_changes_node(state):
    history = list(state.get("history", []))
    if not state.get("is_approved"):
        history.append("Not approved - nothing committed")
        return {"history": history}
    try:
        commit_file(
            state["repo_url"],
            state["branch"],
            state["file_path"],
            state["refactored_code"],
            "refactor: apply AI-reviewed changes",
        )
        history.append("Committed refactored code to branch")
    except Exception as e:
        history.append(f"Commit failed ({e}) - demo mode, nothing pushed")
    logger.info("apply_changes_node done")
    return {"history": history}
