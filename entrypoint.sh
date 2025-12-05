#!/bin/sh
set -e

echo "GITHUB_WORKSPACE: $GITHUB_WORKSPACE"

# Configure git to trust the workspace directory
# This fixes the "dubious ownership" error in Docker containers
git config --global --add safe.directory "$GITHUB_WORKSPACE"

cd "$GITHUB_WORKSPACE" || {
  echo "Failed to cd to GITHUB_WORKSPACE: $GITHUB_WORKSPACE" >&2
  exit 1
}
echo "Changed to workspace: $(pwd)"

exec python /action/main.py "$@"
