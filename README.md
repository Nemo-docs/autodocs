# Automated File Count PR Tool

This is an open-source GitHub Action that counts the number of non-hidden files in your repository (excluding common directories like `.git`, `node_modules`, `venv`), creates or updates a `file_count` file at the root with the total count, commits the change to a dedicated branch, and opens (or updates) a pull request.

## Why Use This?
- Automated documentation of repo size.
- Reduces manual setup with Docker containerization.
- Runs entirely within GitHub Actions.

## As a GitHub Action

### Prerequisites
- Your repository must have a `GITHUB_TOKEN` (automatically available in workflows).
- Workflow permissions: `contents: write` and `pull-requests: write`.

### Usage in Your Repository's Workflow

Create a file like `.github/workflows/update-file-count.yml` in your host repository:

```yaml
name: Update File Count

on:
  workflow_dispatch:  # Manual trigger

permissions:
  contents: write
  pull-requests: write

jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run File Count Action
        uses: devan/automated_docs@main  # Replace with your username/repo and tag/branch
```

This will:
1. Checkout your repository.
2. Run the action in a Docker container, mounting your workspace.
3. Count files, update `file_count`.
4. Push to branch `chore/file-count-update`.
5. Create or reuse PR titled `chore: Update file_count`.

### Customization
- The action uses environment variables from the GitHub context.
- To customize branch/PR details, fork and edit `src/main.py`.

## Previous Example Issue
The old example workflow built the Docker image in your host repo, which could accidentally build your repo's image if a `Dockerfile` exists there, leading to unwanted installations (e.g., Poetry/pip from your `requirements.txt`). The new usage avoids this by using the pre-defined action.

## Local Development/Testing
If you want to test locally:

```bash
# Build
docker build -t file-count-tool .

# Run (mount your repo)
docker run --rm \
  -e GITHUB_TOKEN=ghp_... \
  -e GITHUB_REPOSITORY=owner/repo \
  -e GITHUB_ACTOR="Your Name" \
  -v "$(pwd)":/github/workspace \
  file-count-tool
```

## Exclusions
- Hidden files/directories (starting with `.`).
- Common dirs: `.git`, `node_modules`, `venv`, `.venv`, `__pycache__`.

## License
See [LICENSE](LICENSE).

