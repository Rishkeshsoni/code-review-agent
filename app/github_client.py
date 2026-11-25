
import os

from github import Auth, Github


def parse_repo_name(repo_url: str) -> str:
    return (
        repo_url.rstrip("/")
        .removesuffix(".git")
        .replace("https://github.com/", "")
    )


def _client() -> Github:
    token = os.getenv("GITHUB_TOKEN")

    if not token:
        raise RuntimeError("GITHUB_TOKEN missing")

    return Github(auth=Auth.Token(token))


def fetch_python_file(repo_url, branch, pr_number=None):
    client = _client()

    try:
        repo = client.get_repo(parse_repo_name(repo_url))

        if pr_number:
            pull = repo.get_pull(int(pr_number))
            files = pull.get_files()

            for file in files:
                if file.filename.endswith(".py"):
                    content = repo.get_contents(
                        file.filename,
                        ref=pull.head.sha,
                    )

                    return (
                        file.filename,
                        content.decoded_content.decode("utf-8"),
                    )

            raise FileNotFoundError(
                "No modified Python file found in the pull request"
            )

        contents = repo.get_contents("", ref=branch)

        for item in contents:
            if item.type == "file" and item.name.endswith(".py"):
                content = repo.get_contents(item.path, ref=branch)

                return (
                    item.path,
                    content.decoded_content.decode("utf-8"),
                )

        raise FileNotFoundError("No Python file found in repository")

    finally:
        client.close()


def commit_file(repo_url, branch, path, new_content, message):
    client = _client()

    try:
        repo = client.get_repo(parse_repo_name(repo_url))

        existing = repo.get_contents(path, ref=branch)

        repo.update_file(
            path=path,
            message=message,
            content=new_content,
            sha=existing.sha,
            branch=branch,
        )

    finally:
        client.close()
