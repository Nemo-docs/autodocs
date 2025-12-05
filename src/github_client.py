"""Helpers for git operations and GitHub API calls."""

from __future__ import annotations

import os
import subprocess
from typing import Optional

import requests

API_ROOT = "https://api.github.com"


class GitHubClient:
    """Minimal GitHub REST client for repo operations."""

    def __init__(self, token: str, repo: str):
        self.repo = repo
        self.session = requests.Session()
        self.session.headers.update(
            {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}
        )

    def get_default_branch(self) -> str:
        """Return the default branch name for the repo."""
        resp = self.session.get(f"{API_ROOT}/repos/{self.repo}", timeout=15)
        resp.raise_for_status()
        return resp.json()["default_branch"]

    def find_open_pr(self, head_branch: str, base_branch: str) -> Optional[dict]:
        """Return an open PR matching head/base if present."""
        owner = self.repo.split("/")[0]
        params = {"state": "open", "head": f"{owner}:{head_branch}", "base": base_branch}
        resp = self.session.get(f"{API_ROOT}/repos/{self.repo}/pulls", params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        return data[0] if data else None

    def create_pr(self, title: str, body: str, head_branch: str, base_branch: str) -> dict:
        """Create a pull request."""
        payload = {
            "title": title,
            "body": body,
            "head": head_branch,
            "base": base_branch,
        }
        resp = self.session.post(f"{API_ROOT}/repos/{self.repo}/pulls", json=payload, timeout=15)
        resp.raise_for_status()
        return resp.json()


def run_git(args: list[str], cwd: str) -> None:
    """Run a git command and raise on failure."""
    subprocess.run(["git", *args], cwd=cwd, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)


def configure_git_user(cwd: str, actor: str) -> None:
    """Configure git user for commits."""
    run_git(["config", "user.name", actor], cwd)
    run_git(["config", "user.email", f"{actor}@users.noreply.github.com"], cwd)


def set_remote_with_token(cwd: str, token: str, repo: str) -> None:
    """Rewrite origin to include token for push."""
    authed = f"https://x-access-token:{token}@github.com/{repo}"
    run_git(["remote", "set-url", "origin", authed], cwd)


def checkout_work_branch(cwd: str, base_branch: str, work_branch: str) -> None:
    """Fetch base, sync, and create/update the work branch."""
    run_git(["fetch", "origin", base_branch], cwd)
    run_git(["checkout", base_branch], cwd)
    run_git(["pull", "origin", base_branch], cwd)
    run_git(["checkout", "-B", work_branch, f"origin/{base_branch}"], cwd)


def stage_and_commit(cwd: str, paths: list[str], message: str) -> None:
    """Stage given paths and create a commit."""
    run_git(["add", *paths], cwd)
    run_git(["commit", "-m", message], cwd)


def has_changes(cwd: str) -> bool:
    """Return True if the repo has staged or unstaged changes."""
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=cwd,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    return bool(result.stdout.strip())


def push_branch(cwd: str, branch: str) -> None:
    """Push the work branch."""
    run_git(["push", "-u", "origin", branch, "--force-with-lease"], cwd)

