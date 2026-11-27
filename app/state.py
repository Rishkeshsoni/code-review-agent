from typing import TypedDict, List


class ReviewState(TypedDict, total=False):
    pr_url: str
    code_contents: str
    lint_errors: str
    refactored_code: str
    is_approved: bool
    reviewer_feedback: str
    history: List[str]
    validation_passed: bool
    refactor_attempts: int
    repo_url: str
    branch: str
    pr_number: int
    file_path: str