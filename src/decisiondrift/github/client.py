from __future__ import annotations

import os

import httpx


class GitHubClient:
    def __init__(self, token: str | None = None):
        self.token = token or os.environ.get("GITHUB_TOKEN") or os.environ.get("INPUT_GITHUB_TOKEN")
        self.api_url = os.environ.get("GITHUB_API_URL", "https://api.github.com")
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "decisiondrift-action",
        }
        if self.token:
            self.headers["Authorization"] = f"token {self.token}"

    def _repo_api(self, owner: str, repo: str, path: str) -> str:
        return f"{self.api_url}/repos/{owner}/{repo}/{path.lstrip('/')}"

    def get_pr_diff(self, owner: str, repo: str, pr_number: int) -> str:
        url = self._repo_api(owner, repo, f"pulls/{pr_number}")
        resp = httpx.get(url, headers={**self.headers, "Accept": "application/vnd.github.v3.diff"}, timeout=30)
        resp.raise_for_status()
        return resp.text

    def list_comments(self, owner: str, repo: str, pr_number: int) -> list[dict]:
        url = self._repo_api(owner, repo, f"issues/{pr_number}/comments")
        resp = httpx.get(url, headers=self.headers, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def create_comment(self, owner: str, repo: str, pr_number: int, body: str) -> dict:
        url = self._repo_api(owner, repo, f"issues/{pr_number}/comments")
        resp = httpx.post(url, headers=self.headers, json={"body": body}, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def update_comment(self, owner: str, repo: str, comment_id: int, body: str) -> dict:
        url = self._repo_api(owner, repo, f"issues/comments/{comment_id}")
        resp = httpx.patch(url, headers=self.headers, json={"body": body}, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def create_status(self, owner: str, repo: str, sha: str, state: str, description: str, context: str, target_url: str = "") -> dict:
        url = self._repo_api(owner, repo, f"statuses/{sha}")
        payload: dict[str, str | None] = {
            "state": state,
            "description": description,
            "context": context,
        }
        if target_url:
            payload["target_url"] = target_url
        resp = httpx.post(url, headers=self.headers, json=payload, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def submit_review(self, owner: str, repo: str, pr_number: int, body: str, event: str = "COMMENT") -> dict:
        url = self._repo_api(owner, repo, f"pulls/{pr_number}/reviews")
        payload = {
            "body": body,
            "event": event,
        }
        resp = httpx.post(url, headers=self.headers, json=payload, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def get_pr(self, owner: str, repo: str, pr_number: int) -> dict:
        url = self._repo_api(owner, repo, f"pulls/{pr_number}")
        resp = httpx.get(url, headers=self.headers, timeout=30)
        resp.raise_for_status()
        return resp.json()
