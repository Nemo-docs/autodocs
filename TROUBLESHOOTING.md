# Troubleshooting Guide: 403 Forbidden Error

## Problem
The GitHub Action is failing with a **403 Forbidden** error when attempting to create a pull request:

```
requests.exceptions.HTTPError: 403 Client Error: Forbidden for url: https://api.github.com/repos/DevanshSaini18/test_small_repo_python/pulls
```

## Root Causes

The 403 error when creating a PR typically occurs due to one of these reasons:

### 1. **Insufficient Token Permissions** (Most Likely)
The GitHub token doesn't have the required scopes to create pull requests.

**Required Scopes:**
- For **public repositories**: `public_repo` scope
- For **private repositories**: `repo` scope (full control)

**How to Check:**
- Go to GitHub Settings → Developer settings → Personal access tokens
- Check the scopes assigned to your token
- The token should have at least `public_repo` or `repo` scope

**Fix:**
```yaml
# In your workflow file (.github/workflows/file-count.yml)
# Make sure you're using a token with proper permissions

# Option 1: Use a Personal Access Token (PAT)
env:
  INPUT_GITHUB_TOKEN: ${{ secrets.PAT_TOKEN }}  # Create a PAT with 'repo' scope

# Option 2: Use GITHUB_TOKEN with proper permissions
permissions:
  contents: write
  pull-requests: write
```

### 2. **Wrong Authorization Header Format**
GitHub Personal Access Tokens (PAT) should use `token` authentication, not `Bearer`.

**Fixed in the code:**
```python
# Old (incorrect for PATs):
"Authorization": f"Bearer {token}"

# New (correct):
if token.startswith('ghp_') or token.startswith('github_pat_'):
    auth_type = "token"
else:
    auth_type = "Bearer"
    
"Authorization": f"{auth_type} {token}"
```

### 3. **Repository Access Issues**
- The token owner doesn't have write access to the repository
- The repository is an organization repo and the token lacks organization permissions
- Branch protection rules are preventing the operation

### 4. **Token Expired or Revoked**
- The token has expired (check expiration date)
- The token has been revoked
- The token was regenerated but the secret wasn't updated

### 5. **Repository Settings**
- The repository has disabled pull requests
- Organization policies prevent PR creation
- Branch protection rules require specific conditions

## Changes Made

### 1. Enhanced Logging in `github_client.py`
Added comprehensive logging to track:
- Token validation and authentication
- Token type detection (PAT vs GitHub App)
- API request/response details
- Token scopes
- Detailed error messages with diagnostics

### 2. Enhanced Logging in `main.py`
Added step-by-step logging to track:
- Environment variables
- Each workflow step
- Git operations
- PR creation process

### 3. Fixed Authorization Header
- Automatically detects token type
- Uses correct authorization format (`token` for PATs, `Bearer` for GitHub Apps)
- Added GitHub API version header

## How to Use the New Logging

When you run the workflow again, you'll see detailed output like:

```
[GitHubClient] Initializing with token: ghp_abc...xyz
[GitHubClient] Repository: DevanshSaini18/test_small_repo_python
[GitHubClient] Token length: 40
[GitHubClient] Detected personal access token, using 'token' auth
[GitHubClient] Validating token...
[GitHubClient] Token validation status: 200
[GitHubClient] Authenticated as: DevanshSaini18
[GitHubClient] Account type: User
[GitHubClient] Token scopes: repo, workflow
```

This will help identify:
1. Whether the token is valid
2. What scopes the token has
3. Which specific API call is failing
4. The exact error message from GitHub

## Recommended Fix

### Option 1: Use Personal Access Token (Recommended)

1. **Create a new PAT:**
   - Go to GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
   - Click "Generate new token (classic)"
   - Select scopes:
     - ✅ `repo` (Full control of private repositories)
     - ✅ `workflow` (Update GitHub Action workflows)
   - Generate and copy the token

2. **Add to repository secrets:**
   - Go to your repository → Settings → Secrets and variables → Actions
   - Create a new secret named `PAT_TOKEN`
   - Paste your token

3. **Update workflow file:**
   ```yaml
   - name: Run autodocs
     uses: Nemo-docs/autodocs@main
     with:
       github_token: ${{ secrets.PAT_TOKEN }}
   ```

### Option 2: Use GITHUB_TOKEN with Permissions

Update your workflow file to grant proper permissions:

```yaml
name: File Count Workflow

on:
  push:
    branches: [main]

permissions:
  contents: write
  pull-requests: write

jobs:
  file-count:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Run autodocs
        uses: Nemo-docs/autodocs@main
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
```

## Testing the Fix

After implementing the fix, the logs will show:

```
[GitHubClient] Token scopes: repo, workflow
[GitHubClient] Creating PR: chore/file-count-update -> main
[GitHubClient] POST https://api.github.com/repos/DevanshSaini18/test_small_repo_python/pulls
[GitHubClient] Response status: 201
[GitHubClient] Successfully created PR: https://github.com/DevanshSaini18/test_small_repo_python/pull/1
```

## Debug Mode

To enable even more verbose logging, set the `DEBUG_MODE` environment variable:

```yaml
- name: Run autodocs
  uses: Nemo-docs/autodocs@main
  with:
    github_token: ${{ secrets.PAT_TOKEN }}
  env:
    DEBUG_MODE: "true"
```

This will show full request headers and additional diagnostic information.

## Additional Resources

- [GitHub API Authentication](https://docs.github.com/en/rest/authentication/authenticating-to-the-rest-api)
- [GitHub Token Scopes](https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/scopes-for-oauth-apps)
- [GitHub Actions Permissions](https://docs.github.com/en/actions/security-guides/automatic-token-authentication#permissions-for-the-github_token)
