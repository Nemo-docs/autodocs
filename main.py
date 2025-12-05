"""Entrypoint for counting files and opening a PR."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from file_counter import count_files, write_file_count_file
from github_client import (
    GitHubClient,
    checkout_work_branch,
    configure_git_user,
    has_changes,
    push_branch,
    set_remote_with_token,
    stage_and_commit,
)


WORK_BRANCH = "chore/file-count-update"
COMMIT_MSG = "chore: update file_count"
PR_TITLE = "chore: Update file_count"
PR_BODY = "Automated update of file_count."


def require_env(name: str) -> str:
    """Return env value or exit with a helpful message."""
    value = os.getenv(name)
    if not value:
        print(f"Missing required env: {name}", file=sys.stderr)
        sys.exit(1)
    return value


def main() -> None:
    """Orchestrate count → write → commit → push → PR."""
    workspace = Path.cwd()
    print(f"Detected workspace: {workspace}")
    print(f"Current working dir: {os.getcwd()}")
    token = require_env("INPUT_GITHUB_TOKEN")
    repo = require_env("GITHUB_REPOSITORY")
    actor = os.getenv("GITHUB_ACTOR", "automation")

    if not workspace.exists():
        print(f"Workspace not found: {workspace}", file=sys.stderr)
        sys.exit(1)
    else:
        print(f"Workspace exists: {workspace}")

    client = GitHubClient(token=token, repo=repo)
    default_branch = os.getenv("DEFAULT_BRANCH") or client.get_default_branch()

    configure_git_user(str(workspace), actor)
    set_remote_with_token(str(workspace), token, repo)
    print(f"About to checkout branch in {str(workspace)}")
    checkout_work_branch(str(workspace), default_branch, WORK_BRANCH)

    total = count_files(workspace)
    target_path = write_file_count_file(workspace, total)

    if not has_changes(str(workspace)):
        print("No changes detected after writing file_count; exiting.")
        return

    stage_and_commit(str(workspace), [str(target_path.relative_to(workspace))], COMMIT_MSG)
    push_branch(str(workspace), WORK_BRANCH)

    existing = client.find_open_pr(WORK_BRANCH, default_branch)
    if existing:
        print(f"Reusing existing PR: {existing['html_url']}")
        return

    pr = client.create_pr(PR_TITLE, PR_BODY, WORK_BRANCH, default_branch)
    print(f"Opened PR: {pr['html_url']}")


if __name__ == "__main__":
    main()

