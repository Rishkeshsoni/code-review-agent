
import os
import subprocess
import sys
import tempfile

from langchain_core.tools import tool


def _run_check(command, filename, timeout=30):
    try:
        result = subprocess.run(
            command + [filename],
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=False,
        )

        output = (result.stdout + result.stderr).strip()
        output = output.replace(filename, "code_to_check.py")

        return output

    except subprocess.TimeoutExpired:
        return "ERROR: Check timed out"

    except Exception as error:
        return f"ERROR: {type(error).__name__}: {error}"


@tool
def run_linter_tool(code_string: str) -> str:
    """Check Python code using Flake8, Black and Pylint."""

    if not code_string.strip():
        return "ERROR: Empty Python code"

    if len(code_string) > 100000:
        return "ERROR: Code exceeds the 100 KB limit"

    results = []

    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "code_to_check.py")

        with open(path, "w", encoding="utf-8") as file:
            file.write(code_string)

        checks = [
            ("FLAKE8", [sys.executable, "-m", "flake8"]),
            ("BLACK", [sys.executable, "-m", "black", "--check"]),
            (
                "PYLINT",
                [
                    sys.executable,
                    "-m",
                    "pylint",
                    "--score=n",
                    "--reports=n",
                    "--disable=all",
                    "--enable=E,F",
                ],
            ),
        ]

        for name, command in checks:
            output = _run_check(command, path)
            results.append(f"--- {name} ---\n{output or 'NO ISSUES FOUND'}")

    return "\n\n".join(results)

