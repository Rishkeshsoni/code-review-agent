

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

        return {
            "passed": result.returncode == 0,
            "output": output or "NO ISSUES FOUND",
        }

    except subprocess.TimeoutExpired:
        return {
            "passed": False,
            "output": "ERROR: Check timed out",
        }

    except Exception as error:
        return {
            "passed": False,
            "output": f"ERROR: {type(error).__name__}: {error}",
        }


def validate_python_code(code_string: str) -> dict:
    if not code_string.strip():
        return {
            "passed": False,
            "output": "ERROR: Empty Python code",
        }

    if len(code_string.encode("utf-8")) > 100000:
        return {
            "passed": False,
            "output": "ERROR: Code exceeds the 100 KB limit",
        }

    results = []
    all_passed = True

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
            result = _run_check(command, path)

            results.append(
                f"--- {name} ---\n{result['output']}"
            )

            if not result["passed"]:
                all_passed = False

    return {
        "passed": all_passed,
        "output": "\n\n".join(results),
    }


@tool
def run_linter_tool(code_string: str) -> str:
    """Check Python code using Flake8, Black and Pylint."""
    result = validate_python_code(code_string)
    return result["output"]
