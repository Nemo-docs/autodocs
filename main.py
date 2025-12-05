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
    ensure_git_repo,
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
    print("="*80)
    print("[Main] Starting automated file count workflow")
    print("="*80)
    
    workspace = Path.cwd()
    print(f"[Main] Detected workspace: {workspace}")
    print(f"[Main] Current working dir: {os.getcwd()}")
    
    # Log environment variables (masked)
    print(f"[Main] Environment variables:")
    print(f"[Main]   GITHUB_REPOSITORY: {os.getenv('GITHUB_REPOSITORY', 'NOT SET')}")
    print(f"[Main]   GITHUB_ACTOR: {os.getenv('GITHUB_ACTOR', 'NOT SET')}")
    print(f"[Main]   GITHUB_REF: {os.getenv('GITHUB_REF', 'NOT SET')}")
    print(f"[Main]   GITHUB_SHA: {os.getenv('GITHUB_SHA', 'NOT SET')}")
    print(f"[Main]   GITHUB_WORKFLOW: {os.getenv('GITHUB_WORKFLOW', 'NOT SET')}")
    
    token = require_env("INPUT_GITHUB_TOKEN")
    token_prefix = token[:7] if len(token) > 7 else "***"
    token_suffix = token[-4:] if len(token) > 4 else "***"
    print(f"[Main] Token: {token_prefix}...{token_suffix} (length: {len(token)})")
    
    repo = require_env("GITHUB_REPOSITORY")
    actor = os.getenv("GITHUB_ACTOR", "automation")
    print(f"[Main] Repository: {repo}")
    print(f"[Main] Actor: {actor}")

    if not workspace.exists():
        print(f"[Main] ERROR: Workspace not found: {workspace}", file=sys.stderr)
        sys.exit(1)
    else:
        print(f"[Main] Workspace exists: {workspace}")

    print("\n" + "="*80)
    print("[Main] Step 1: Initialize GitHub client")
    print("="*80)
    client = GitHubClient(token=token, repo=repo)
    
    print("\n" + "="*80)
    print("[Main] Step 2: Get default branch")
    print("="*80)
    default_branch = os.getenv("DEFAULT_BRANCH") or client.get_default_branch()
    print(f"[Main] Using default branch: {default_branch}")

    print("\n" + "="*80)
    print("[Main] Step 3: Ensure git repository")
    print("="*80)
    ensure_git_repo(str(workspace), token, repo, default_branch)

    print("\n" + "="*80)
    print("[Main] Step 4: Configure git")
    print("="*80)
    configure_git_user(str(workspace), actor)
    set_remote_with_token(str(workspace), token, repo)
    
    print("\n" + "="*80)
    print(f"[Main] Step 5: Checkout work branch '{WORK_BRANCH}'")
    print("="*80)
    checkout_work_branch(str(workspace), default_branch, WORK_BRANCH)

    print("\n" + "="*80)
    print("[Main] Step 6: Count files and write file_count")
    print("="*80)
    total = count_files(workspace)
    print(f"[Main] Total files counted: {total}")
    target_path = write_file_count_file(workspace, total)
    print(f"[Main] Wrote file count to: {target_path}")

    if not has_changes(str(workspace)):
        print("[Main] No changes detected after writing file_count; exiting.")
        return

    print("\n" + "="*80)
    print("[Main] Step 7: Commit changes")
    print("="*80)
    stage_and_commit(str(workspace), [str(target_path.relative_to(workspace))], COMMIT_MSG)
    
    print("\n" + "="*80)
    print("[Main] Step 8: Push branch")
    print("="*80)
    push_branch(str(workspace), WORK_BRANCH)

    print("\n" + "="*80)
    print("[Main] Step 9: Check for existing PR")
    print("="*80)
    existing = client.find_open_pr(WORK_BRANCH, default_branch)
    if existing:
        print(f"[Main] Reusing existing PR: {existing['html_url']}")
        print("="*80)
        return

    print("\n" + "="*80)
    print("[Main] Step 10: Create new PR")
    print("="*80)
    pr = client.create_pr(PR_TITLE, PR_BODY, WORK_BRANCH, default_branch)
    print(f"[Main] Successfully opened PR: {pr['html_url']}")
    print("="*80)


if __name__ == "__main__":
    main()

