from __future__ import annotations

from decisiondrift.github.client import GitHubClient

MARKER = "<!-- decisiondrift-review -->"


def upsert_comment(
    client: GitHubClient,
    owner: str,
    repo: str,
    pr_number: int,
    body: str,
) -> int:
    existing_comments = client.list_comments(owner, repo, pr_number)
    for comment in existing_comments:
        if MARKER in (comment.get("body") or ""):
            client.update_comment(owner, repo, comment["id"], body)
            return comment["id"]
    comment = client.create_comment(owner, repo, pr_number, body)
    return comment["id"]
