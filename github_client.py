"""Helpers for git operations and GitHub API calls."""

from __future__ import annotations

import os
import sys
import subprocess
import json
from typing import Optional

import requests

API_ROOT = "https://api.github.com"

# Enable detailed logging
DEBUG_MODE = os.getenv("DEBUG_MODE", "true").lower() == "true"


class GitHubClient:
    """Minimal GitHub REST client for repo operations."""

    def __init__(self, token: str, repo: str):
        self.repo = repo
        self.session = requests.Session()
        
        # Log token info (masked)
        token_prefix = token[:7] if len(token) > 7 else "***"
        token_suffix = token[-4:] if len(token) > 4 else "***"
        print(f"[GitHubClient] Initializing with token: {token_prefix}...{token_suffix}")
        print(f"[GitHubClient] Repository: {repo}")
        print(f"[GitHubClient] Token length: {len(token)}")
        
        # GitHub tokens starting with 'ghp_' should use 'token' auth, not 'Bearer'
        # GitHub App tokens use 'Bearer'
        if token.startswith('ghp_') or token.startswith('github_pat_'):
            auth_type = "token"
            print(f"[GitHubClient] Detected personal access token, using 'token' auth")
        else:
            auth_type = "Bearer"
            print(f"[GitHubClient] Using 'Bearer' auth")
        
        self.session.headers.update(
            {
                "Authorization": f"{auth_type} {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28"
            }
        )
        
        if DEBUG_MODE:
            print(f"[GitHubClient] Request headers: {dict(self.session.headers)}")
        
        # Validate token by checking authentication
        self._validate_token()

    def _validate_token(self) -> None:
        """Validate the token by checking user/app authentication."""
        try:
            print("[GitHubClient] Validating token...")
            resp = self.session.get(f"{API_ROOT}/user", timeout=15)
            
            print(f"[GitHubClient] Token validation status: {resp.status_code}")
            
            if resp.status_code == 200:
                user_data = resp.json()
                print(f"[GitHubClient] Authenticated as: {user_data.get('login', 'unknown')}")
                print(f"[GitHubClient] Account type: {user_data.get('type', 'unknown')}")
            else:
                print(f"[GitHubClient] WARNING: Token validation failed with status {resp.status_code}")
                print(f"[GitHubClient] Response: {resp.text}")
                
            # Check scopes
            scopes = resp.headers.get('X-OAuth-Scopes', '')
            print(f"[GitHubClient] Token scopes: {scopes if scopes else 'No scopes header (might be fine for GitHub Apps)'}")
            
        except Exception as e:
            print(f"[GitHubClient] ERROR during token validation: {e}")
            print(f"[GitHubClient] This might indicate an authentication issue")
    
    def get_default_branch(self) -> str:
        """Return the default branch name for the repo."""
        print(f"[GitHubClient] Fetching default branch for {self.repo}")
        url = f"{API_ROOT}/repos/{self.repo}"
        print(f"[GitHubClient] GET {url}")
        
        resp = self.session.get(url, timeout=15)
        print(f"[GitHubClient] Response status: {resp.status_code}")
        
        if resp.status_code != 200:
            print(f"[GitHubClient] ERROR: Failed to get repository info")
            print(f"[GitHubClient] Response: {resp.text}")
        
        resp.raise_for_status()
        data = resp.json()
        default_branch = data["default_branch"]
        print(f"[GitHubClient] Default branch: {default_branch}")
        return default_branch

    def find_open_pr(self, head_branch: str, base_branch: str) -> Optional[dict]:
        """Return an open PR matching head/base if present."""
        print(f"[GitHubClient] Searching for open PR: {head_branch} -> {base_branch}")
        
        owner = self.repo.split("/")[0]
        params = {"state": "open", "head": f"{owner}:{head_branch}", "base": base_branch}
        url = f"{API_ROOT}/repos/{self.repo}/pulls"
        
        print(f"[GitHubClient] GET {url}")
        print(f"[GitHubClient] Params: {params}")
        
        resp = self.session.get(url, params=params, timeout=15)
        print(f"[GitHubClient] Response status: {resp.status_code}")
        
        if resp.status_code != 200:
            print(f"[GitHubClient] ERROR: Failed to search for PRs")
            print(f"[GitHubClient] Response: {resp.text}")
        
        resp.raise_for_status()
        data = resp.json()
        
        if data:
            print(f"[GitHubClient] Found existing PR: {data[0].get('html_url')}")
            return data[0]
        else:
            print(f"[GitHubClient] No existing PR found")
            return None

    def create_pr(self, title: str, body: str, head_branch: str, base_branch: str) -> dict:
        """Create a pull request."""
        print(f"[GitHubClient] Creating PR: {head_branch} -> {base_branch}")
        print(f"[GitHubClient] Title: {title}")
        
        payload = {
            "title": title,
            "body": body,
            "head": head_branch,
            "base": base_branch,
        }
        
        url = f"{API_ROOT}/repos/{self.repo}/pulls"
        print(f"[GitHubClient] POST {url}")
        print(f"[GitHubClient] Payload: {json.dumps(payload, indent=2)}")
        
        if DEBUG_MODE:
            print(f"[GitHubClient] Request headers: {dict(self.session.headers)}")
        
        resp = self.session.post(url, json=payload, timeout=15)
        print(f"[GitHubClient] Response status: {resp.status_code}")
        print(f"[GitHubClient] Response headers: {dict(resp.headers)}")
        
        if resp.status_code != 201:
            print(f"[GitHubClient] ERROR: Failed to create PR")
            print(f"[GitHubClient] Response body: {resp.text}")
            
            # Try to parse error message
            try:
                error_data = resp.json()
                print(f"[GitHubClient] Error details: {json.dumps(error_data, indent=2)}")
                
                if 'message' in error_data:
                    print(f"[GitHubClient] Error message: {error_data['message']}")
                if 'documentation_url' in error_data:
                    print(f"[GitHubClient] Documentation: {error_data['documentation_url']}")
            except:
                pass
            
            # Additional diagnostics for 403
            if resp.status_code == 403:
                print(f"[GitHubClient] 403 Forbidden - Possible causes:")
                print(f"[GitHubClient]   1. Token lacks 'repo' or 'public_repo' scope")
                print(f"[GitHubClient]   2. Token doesn't have write access to the repository")
                print(f"[GitHubClient]   3. Repository settings prevent PR creation")
                print(f"[GitHubClient]   4. Branch protection rules are blocking the operation")
                print(f"[GitHubClient]   5. Token has expired or been revoked")
        
        resp.raise_for_status()
        pr_data = resp.json()
        print(f"[GitHubClient] Successfully created PR: {pr_data.get('html_url')}")
        return pr_data


def run_git(args: list[str], cwd: str) -> str:
    """Run a git command and raise on failure. Returns stdout."""
    cmd = ["git"] + args
    print(f"Running: {' '.join(cmd)} in {cwd}")
    result = subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        print(f"Git error (exit {result.returncode}): {cmd}", file=sys.stderr)
        print(result.stdout, file=sys.stderr)
        print(result.stderr, file=sys.stderr)
        # Create an exception with the error message for better error handling
        error = subprocess.CalledProcessError(result.returncode, cmd)
        error.output = result.stdout
        error.stderr = result.stderr
        raise error
    return result.stdout


def is_git_repo(cwd: str) -> bool:
    """Check if the current directory is inside a Git repository."""
    try:
        run_git(["rev-parse", "--is-inside-work-tree"], cwd)
        return True
    except subprocess.CalledProcessError as e:
        # Check if it's a dubious ownership error
        stderr = getattr(e, 'stderr', '')
        if "dubious ownership" in stderr:
            print(f"Configuring safe.directory for {cwd}")
            try:
                subprocess.run(
                    ["git", "config", "--global", "--add", "safe.directory", cwd],
                    check=True,
                    capture_output=True,
                    text=True
                )
                # Try again after configuring
                run_git(["rev-parse", "--is-inside-work-tree"], cwd)
                return True
            except subprocess.CalledProcessError:
                return False
        return False


def ensure_git_repo(cwd: str, token: str, repo: str, default_branch: str) -> None:
    """Initialize a Git repository in the workspace if it doesn't exist."""
    if is_git_repo(cwd):
        return

    print(f"Initializing Git repository in {cwd}...")
    run_git(["init"], cwd)

    authed_url = f"https://x-access-token:{token}@github.com/{repo}"
    run_git(["remote", "add", "origin", authed_url], cwd)

    run_git(["fetch", "--depth=1", "origin", default_branch], cwd)
    run_git(["checkout", "-B", default_branch, f"origin/{default_branch}"], cwd)
    run_git(["pull", "origin", default_branch], cwd)


def configure_git_user(cwd: str, actor: str) -> None:
    """Configure git user for commits."""
    run_git(["config", "--local", "user.name", actor], cwd)
    run_git(["config", "--local", "user.email", f"{actor}@users.noreply.github.com"], cwd)


def set_remote_with_token(cwd: str, token: str, repo: str) -> None:
    """Rewrite origin to include token for push."""
    authed = f"https://x-access-token:{token}@github.com/{repo}"
    run_git(["remote", "set-url", "origin", authed], cwd)


def checkout_work_branch(cwd: str, base_branch: str, work_branch: str) -> None:
    """Fetch base, sync, and create/update the work branch."""
    run_git(["fetch", "origin", base_branch], cwd)
    run_git(["checkout", base_branch], cwd)
    run_git(["reset", "--hard", f"origin/{base_branch}"], cwd)
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
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    return bool(result.stdout.strip())


def push_branch(cwd: str, branch: str) -> None:
    """Push the work branch."""
    # Fetch the remote branch first to check if it exists
    branch_exists_remotely = True
    try:
        run_git(["fetch", "origin", branch], cwd)
    except subprocess.CalledProcessError:
        # Branch doesn't exist remotely yet
        branch_exists_remotely = False
        print(f"Branch {branch} doesn't exist remotely yet, will create it")
    
    if branch_exists_remotely:
        # Use --force-with-lease for existing branches (safer)
        run_git(["push", "-u", "origin", branch, "--force-with-lease"], cwd)
    else:
        # Use --force for new branches (--force-with-lease fails when no remote ref exists)
        run_git(["push", "-u", "origin", branch, "--force"], cwd)

