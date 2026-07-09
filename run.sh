#!/bin/bash
# ABOUTME: Runs the collector and pushes updated data to GitHub.
# ABOUTME: Designed to be called by launchd on macOS.

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "$(date): Starting collector run"

python3 collector.py

# Commit and push if data changed
if git diff --quiet data.json seen_posts.json last_run.json latest_post.json 2>/dev/null; then
    echo "No data changes to commit"
else
    git add data.json
    [ -f latest_post.json ] && git add latest_post.json
    [ -f seen_posts.json ] && git add seen_posts.json
    [ -f last_run.json ] && git add last_run.json
    git commit -m "update pulse data"
    git push
    echo "Data pushed to GitHub"
fi

echo "$(date): Done"
