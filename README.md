# File Count PR Tool

Containerized Python helper that counts non-hidden files in a repository, writes/updates a `file_count` file, commits the change, pushes a branch, and opens a pull request using `GITHUB_TOKEN`.

## Directory Layout
- `src/main.py` — entrypoint orchestrating count, commit, push, PR.
- `src/file_counter.py` — file counting utility with sensible excludes.
- `src/github_client.py` — minimal GitHub API + git helpers.
- `Dockerfile` — builds runnable image.

## Inputs (env)
- `GITHUB_TOKEN` (required) — repo-scoped token (Actions default).
- `GITHUB_REPOSITORY` (required) — `owner/repo`.
- `GITHUB_ACTOR` (optional) — used for git user; default `automation`.
- `DEFAULT_BRANCH` (optional) — branch to base from; falls back to repo default via API.
- `WORKSPACE_PATH` (optional) — path to repo checkout; default `/workspace` (works with `docker run -v ${{ github.workspace }}:/workspace`).

## Behavior
- Skips hidden files/dirs and common vendor/venv folders (`.git`, `node_modules`, `venv`, `.venv`, `__pycache__`).
- Writes the count as plain text to `file_count` at repo root.
- Creates/updates branch `chore/file-count-update`, pushes with `--force-with-lease`.
- Opens or reuses a PR titled `Update file_count` targeting the default branch.
- No PR is opened if there are no changes after writing `file_count`.

## Local Build/Run
```bash
docker build -t file-count-tool ./tool
docker run --rm \
  -e GITHUB_TOKEN=ghp_... \
  -e GITHUB_REPOSITORY=owner/repo \
  -e GITHUB_ACTOR="$(git config user.name)" \
  -v "$(pwd)":/workspace \
  file-count-tool
```

## Notes
- Git is installed in the image; remote is rewritten to include the token for push.
- Keep functions under ~60 lines for readability.

