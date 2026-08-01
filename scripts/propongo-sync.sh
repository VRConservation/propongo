#!/usr/bin/env bash
# propongo-sync.sh - run Propongo against a git-tracked data folder and
# push changes back to the shared repository when the session ends.
#
# Usage:
#   scripts/propongo-sync.sh [branch]
#
#   branch   optional git branch to work on (e.g. proposal/grant-2026)
#
# Environment:
#   PROPONGO_REPO_DIR   git repository to sync (default: current directory)
set -euo pipefail

REPO_DIR="${PROPONGO_REPO_DIR:-$(pwd)}"
DATA_DIR="${REPO_DIR}/data"
BRANCH="${1:-}"

usage() {
    echo "Usage: $0 [branch]"
    echo ""
    echo "  branch   optional git branch to work on (e.g. proposal/grant-2026)"
}

case "${1:-}" in
    -h|--help) usage; exit 0 ;;
esac

if ! command -v propongo >/dev/null 2>&1; then
    echo "error: 'propongo' command not found on PATH" >&2
    echo "       install it first (see docs/installation.md)" >&2
    exit 1
fi

if [ ! -d "$REPO_DIR/.git" ]; then
    echo "error: $REPO_DIR is not a git repository" >&2
    exit 1
fi

# Switch to (or create) the requested branch.
if [ -n "$BRANCH" ]; then
    git -C "$REPO_DIR" switch "$BRANCH" 2>/dev/null \
        || git -C "$REPO_DIR" switch -c "$BRANCH"
fi

# Pull the latest work from teammates before starting.
git -C "$REPO_DIR" pull --rebase \
    || echo "warning: could not pull (remote may not be configured yet)"

echo "Starting Propongo (data: $DATA_DIR). Press Ctrl+C to stop."
export PROPONGO_DATA_DIR="$DATA_DIR"
propongo

# Commit and push whatever changed during the session.
git -C "$REPO_DIR" add -A
if git -C "$REPO_DIR" diff --cached --quiet; then
    echo "No changes to commit."
else
    git -C "$REPO_DIR" commit -m "Update proposals ($(date '+%Y-%m-%d %H:%M'))"
fi
git -C "$REPO_DIR" push \
    || echo "warning: push failed (check your remote and credentials)"
