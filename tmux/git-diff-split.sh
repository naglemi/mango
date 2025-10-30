#!/bin/bash

# Git diff viewer for staged changes
# Shows diffs for all staged files in the working tree

# We're already in the correct directory thanks to tmux -c option

# Check if we're in a git repo
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "Not in a git repository"
    read -p "Press Enter to exit..."
    exit 1
fi

# Check for staged changes
if ! git diff --cached --name-only | grep -q .; then
    echo "No staged changes found"
    echo "Use 'git add <file>' to stage changes first"
    read -p "Press Enter to exit..."
    exit 1
fi

clear
echo "=== Git Diff - Staged Changes ==="
echo
git diff --cached --stat
echo
echo "────────────────────────────────────────"
echo
git diff --cached --color=always | less -R