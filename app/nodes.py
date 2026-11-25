
import ast
import logging
import os

import black

from app.github_client import commit_file, fetch_python_file
from app.tools import run_linter_tool

logger = logging.getLogger("agent")

SAMPLE_CODE = """import os,sys

def add(a,b):
    result=a+b
    return result

x=[]
for i in range(5):
    x.append(i*2)

print(x)
"""


def _strip_fences(text: str) -> str:
    text = text.strip()

    if text.startswith("```"):
        lines = text.splitlines()[1:]

        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]

        text = "\n".join(lines)

    return text.strip()


def fetch_pr_node(state):
    history = list(state.get("history", []))

    if not os.getenv("GITHUB_TOKEN"):
        path = "sample.py"
        content = SAMPLE_CODE
        history.append("Demo mode: GITHUB_TOKEN missing; using sample code")
    else:
        path, content = fetch_python_file(
            state["repo_url"],
            state["branch"],
            state.get("pr_number"),
        )
        history.append(f"Fetched {path} from GitHub")

    logger.info("fetch_pr_node completed: %s", path)

    return {
        "file_path": path,
        "code_contents": content,
        "history": history,
    }


def lint_code_node(state):
    history = list(state.get("history", []))

    code = state.get("refactored_code") or state["code_contents"]

    errors = run_linter_tool.invoke(
        {"code_string": code}
    )

    history.append("Flake8, Black and Pylint checks completed")

    return {
        "lint_errors": errors,
        "history": history,
    }


def propose_refactor_node(state):
    history = list(state.get("history", []))

    original_code = state["code_contents"]
    feedback = state.get("reviewer_feedback", "")
    previous_draft = state.get("refactored_code", "")

    if feedback and previous_draft:
        code = previous_draft
    else:
        code = original_code

    attempt = (
        len([
            item for item in history
            if item.startswith("Refactor proposed")
        ]) + 1
    )

    if os.getenv("OPENAI_API_KEY"):
        from langchain_openai import ChatOpenAI

        llm = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0,
        )

        prompt = f"""
You are an expert Python code reviewer.

Improve the current Python code.

Requirements:
1. Fix all reported lint errors.
2. Follow the reviewer feedback carefully.
3. Preserve the original program functionality.
4. Do not remove important functionality.
5. Return complete Python source code only.
6. Do not include Markdown code fences or explanations.

REVIEWER FEEDBACK:
{feedback or "No additional feedback"}

LINT RESULTS:
{state.get("lint_errors", "")}

ORIGINAL CODE FOR REFERENCE:
{original_code}

CURRENT CODE TO IMPROVE:
{code}
"""

        response = llm.invoke(prompt)
        new_code = _strip_fences(response.content)

        if not new_code:
            raise ValueError("AI returned empty refactored code")

        ast.parse(new_code)

        history.append(
            f"Refactor proposed (attempt {attempt}) using OpenAI"
        )

    else:
        try:
            new_code = black.format_str(
                code,
                mode=black.Mode(),
            )
        except black.InvalidInput as error:
            raise ValueError(
                "Demo code could not be formatted. "
                "Check the Python syntax."
            ) from error

        ast.parse(new_code)

        history.append(
            f"Refactor proposed (attempt {attempt}) using Black demo mode"
        )

        if feedback:
            history.append(
                "Reviewer feedback recorded; demo mode cannot apply "
                "semantic AI changes"
            )

    logger.info("Refactor proposed: attempt %s", attempt)

    return {
        "refactored_code": new_code,
        "history": history,
    }


def apply_changes_node(state):
    history = list(state.get("history", []))

    if not state.get("is_approved"):
        history.append("Not approved: no changes committed")
        return {"history": history}

    if not os.getenv("GITHUB_TOKEN"):
        history.append(
            "Demo mode: GITHUB_TOKEN missing; no GitHub commit performed"
        )
        return {"history": history}

    try:
        commit_file(
            state["repo_url"],
            state["branch"],
            state["file_path"],
            state["refactored_code"],
            "refactor: apply AI-reviewed changes",
        )

        history.append("Successfully committed refactored code to GitHub")

    except Exception as error:
        logger.exception("GitHub commit failed")

        history.append(
            f"GitHub commit failed: {type(error).__name__}: {error}"
        )

        raise

    return {"history": history}
