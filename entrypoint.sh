#!/bin/sh
set -e

cd "$GITHUB_WORKSPACE" || {
  echo "Failed to cd to GITHUB_WORKSPACE: $GITHUB_WORKSPACE" >&2
  exit 1
}

exec python /action/main.py "$@"
