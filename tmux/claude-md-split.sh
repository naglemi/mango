#!/bin/bash
# CLAUDE.md manager - Edit or append to CLAUDE.md (local or global)

LOCAL_CLAUDE="CLAUDE.md"
GLOBAL_CLAUDE="$HOME/CLAUDE.md"

# Display menu
echo ""
echo "═══════════════════════════════════════════"
echo "           CLAUDE.md MANAGER"
echo "═══════════════════════════════════════════"
echo "  Current directory: $(pwd)"
echo "  Local:  $LOCAL_CLAUDE"
echo "  Global: $GLOBAL_CLAUDE"
echo "───────────────────────────────────────────"
echo "  [1] Edit Local CLAUDE.md"
echo "  [2] Append to Local CLAUDE.md"
echo "  [3] Edit Global CLAUDE.md"
echo "  [4] Append to Global CLAUDE.md"
echo "  [Enter] Cancel"
echo "───────────────────────────────────────────"

read -r -e -p "  Enter choice: " choice

# Function to create local CLAUDE.md if it doesn't exist
create_local_claude() {
    if [ ! -f "$LOCAL_CLAUDE" ]; then
        echo " Creating new local CLAUDE.md with template"
        cat > "$LOCAL_CLAUDE" << 'EOF'
# CLAUDE.md - Project-specific instructions for Claude

## Project Overview
[Brief description of this project]

## Key Rules
1. [Project-specific rule 1]
2. [Project-specific rule 2]

## Technical Requirements
- [Requirement 1]
- [Requirement 2]

## Notes
- These instructions override global CLAUDE.md when working in this directory
- Be specific about what makes this project unique
EOF
    fi
}

# Function to append text to a file
append_to_file() {
    local file=$1
    local file_desc=$2

    echo ""
    echo "   Type your new rule/instruction (or press Enter to cancel):"
    echo "  ───────────────────────────────────────────"
    read -r -e -p "  > " new_rule

    if [ -n "$new_rule" ]; then
        # Append with proper formatting
        echo "" >> "$file"
        echo "$new_rule" >> "$file"
        echo "   Rule appended to $file_desc"
        echo ""
        echo "  Preview of last 5 lines:"
        echo "  ───────────────────────────────────────────"
        tail -5 "$file" | sed 's/^/  /'
    else
        echo "   Cancelled - no changes made"
    fi
}

case "$choice" in
    1)
        create_local_claude
        echo "   Opening local CLAUDE.md in Vim..."
        ${EDITOR:-vim} "$LOCAL_CLAUDE"
        ;;
    2)
        create_local_claude
        append_to_file "$LOCAL_CLAUDE" "local CLAUDE.md"
        ;;
    3)
        echo "   Opening global CLAUDE.md in Vim..."
        ${EDITOR:-vim} "$GLOBAL_CLAUDE"
        ;;
    4)
        append_to_file "$GLOBAL_CLAUDE" "global CLAUDE.md"
        ;;
    "")
        echo "   Cancelled"
        ;;
    *)
        echo "   Invalid choice: $choice"
        ;;
esac

echo "═══════════════════════════════════════════"
echo ""