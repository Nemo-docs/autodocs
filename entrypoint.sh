#!/bin/sh
set -e

echo "GITHUB_WORKSPACE: $GITHUB_WORKSPACE"
cd "$GITHUB_WORKSPACE" || {
  echo "Failed to cd to GITHUB_WORKSPACE: $GITHUB_WORKSPACE" >&2
  exit 1
}
echo "Changed to workspace: $(pwd)"

exec python /action/main.py "$@"
