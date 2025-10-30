#!/usr/bin/env bash
# Synchronize local workflow definitions to Cascade runtime directories.
# Copies (force overwrite) all markdown workflow files from ./workflows/
# into the standard runtime locations used by Cascade.
# Use --developer flag to also install workflows from ~/mango-dev/workflows/

set -euo pipefail

# Parse command line arguments
DEVELOPER_MODE=0

for arg in "$@"; do
    case $arg in
        --developer)
            DEVELOPER_MODE=1
            shift
            ;;
        --help|-h)
            echo "Usage: sync-workflows.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --developer    Also install workflows from ~/mango-dev/workflows/"
            echo "  --help, -h     Show this help message"
            echo ""
            echo "Default: Install public workflows only"
            exit 0
            ;;
        *)
            ;;
    esac
done

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Ensure destination folders exist
mkdir -p ~/.windsurf/workflows
mkdir -p ~/.claude/commands

# Copy *.md (case-insensitive) to both targets from public workflows
shopt -s nocaseglob nullglob
echo "Installing public workflows..."
for wf in "$SCRIPT_DIR"/*.md; do
  cp -f "$wf" ~/.windsurf/workflows/
  cp -f "$wf" ~/.claude/commands/
done

# If developer mode enabled, also install workflows from ~/mango-dev/workflows/
if [ $DEVELOPER_MODE -eq 1 ]; then
  if [ -d ~/mango-dev/workflows/ ]; then
    echo "Developer mode: Installing private workflows from ~/mango-dev/workflows/..."
    for wf in ~/mango-dev/workflows/*.md; do
      [ -f "$wf" ] || continue
      cp -f "$wf" ~/.windsurf/workflows/
      cp -f "$wf" ~/.claude/commands/
    done
  else
    echo "Warning: --developer flag used but ~/mango-dev/workflows/ not found"
  fi
fi

shopt -u nocaseglob

echo " Workflow sync complete"
