import os

from github import Auth, Github

SAMPLE_CODE = """import os,sys
def add(a,b):
    result=a+b
    return result
x=[]
for i in range(5):
    x.append(i*2)
print(x)
"""


def parse_repo_name(repo_url: str) -> str:
    return (
        repo_url.replace("https://github.com/", "")
        .replace(".git", "")
        .strip("/")
    )


def _client() -> Github:
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise RuntimeError("GITHUB_TOKEN missing")
    return Github(auth=Auth.Token(token))


def fetch_python_file(repo_url, branch, pr_number=None):
    repo = _client().get_repo(parse_repo_name(repo_url))
    path = None
    if pr_number:
        for f in repo.get_pull(int(pr_number)).get_files():
            if f.filename.endswith(".py"):
                path = f.filename
                break
    if path is None:
        for item in repo.get_contents("", ref=branch):
            if item.name.endswith(".py"):
                path = item.path
                break
    if path is None:
        raise FileNotFoundError("No .py file found")
    content = repo.get_contents(path, ref=branch).decoded_content.decode("utf-8")
    return path, content


def commit_file(repo_url, branch, path, new_content, message):
    repo = _client().get_repo(parse_repo_name(repo_url))
    existing = repo.get_contents(path, ref=branch)
    repo.update_file(path, message, new_content, existing.sha, branch=branch)