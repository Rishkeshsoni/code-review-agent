import os
import subprocess
import sys
import tempfile

from langchain_core.tools import tool


@tool
def run_linter_tool(code_string: str) -> str:
    """Writes python code to a temporary file and runs flake8 analysis."""
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "code_to_check.py")
        with open(path, "w", encoding="utf-8") as f:
            f.write(code_string)
        try:
            result = subprocess.run(
                [sys.executable, "-m", "flake8", path],
                capture_output=True,
                text=True,
                timeout=30,
            )
        except subprocess.TimeoutExpired:
            return "ERROR: linter timed out"
        output = (result.stdout + result.stderr).strip()
        output = output.replace(path, "code_to_check.py")
        return output or "NO_LINT_ERRORS"