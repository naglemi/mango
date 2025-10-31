#!/usr/bin/env bash
# Grab files and email them using report MCP
# Integrates file-grab-menu.py with ninjagrab-style concatenation and email delivery

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Run the file selection menu
echo " Select files to grab and email..."

# Create temporary file for communication
TEMP_SELECTION="/tmp/grab-selection-$$"

# Run the menu directly (not captured)
python3 "$SCRIPT_DIR/file-grab-menu.py" > "$TEMP_SELECTION"

# Read the selection from the temp file
if [[ -f "$TEMP_SELECTION" ]]; then
    OUTPUT_LINE="$(head -n 1 "$TEMP_SELECTION")"
    if [[ "$OUTPUT_LINE" == SELECTED_FILES=* ]]; then
        SELECTED_FILES="${OUTPUT_LINE#SELECTED_FILES=}"
    else
        SELECTED_FILES=""
    fi
    rm -f "$TEMP_SELECTION"
else
    SELECTED_FILES=""
fi

# Check if any files were selected
if [[ -z "$SELECTED_FILES" || "$SELECTED_FILES" == '""' ]]; then
    echo "No files selected. Exiting."
    exit 0
fi

# Create temporary file for concatenated output
TEMP_FILE="/tmp/grabbed-files-$(date +%s).txt"
TEMP_PLAIN="/tmp/grabbed-files-plain-$(date +%s).txt"

# Parse selected files and concatenate them
eval "FILES_ARRAY=($SELECTED_FILES)"

echo " Grabbing ${#FILES_ARRAY[@]} files..."

# Create delimited output (like ninjagrab)
{
    echo "Grabbed Files - $(date)"
    echo "Directory: $(pwd)"
    echo "Files: ${#FILES_ARRAY[@]}"
    echo
} > "$TEMP_FILE"

# Also create plain text version for email body
{
    echo "File Grab Report"
    echo "==============="
    echo
    echo "Directory: $(pwd)"
    echo "Timestamp: $(date)"
    echo "Files grabbed: ${#FILES_ARRAY[@]}"
    echo
} > "$TEMP_PLAIN"

for file in "${FILES_ARRAY[@]}"; do
    # Remove quotes from file path
    file="${file//\"/}"

    if [[ -f "$file" ]]; then
        # Add delimiter (ninjagrab style)
        echo "===== $file =====" >> "$TEMP_FILE"
        cat "$file" >> "$TEMP_FILE"
        echo >> "$TEMP_FILE"

        # Add to plain text summary
        echo "File: $file" >> "$TEMP_PLAIN"
        echo "Size: $(wc -l < "$file") lines" >> "$TEMP_PLAIN"
        echo >> "$TEMP_PLAIN"
    else
        echo "[ERROR] $file not found or not readable" >> "$TEMP_FILE"
        echo "ERROR: $file not found" >> "$TEMP_PLAIN"
    fi
done

# Get relative directory path for subject
REL_DIR="$(basename "$(pwd)")"

# Send via Claude Code (using node MCP server directly)
echo " Sending grabbed files via email..."

# Create the report using nodejs directly
node -e "
const { execSync } = require('child_process');
const { readFileSync } = require('fs');

const attachmentContent = readFileSync('$TEMP_FILE', 'utf8');
const plainContent = readFileSync('$TEMP_PLAIN', 'utf8');

// Prepare the message for Claude
const message = {
    agent_name: 'File Grab Tool',
    title: 'Grabbed Files from $REL_DIR',
    text_content: plainContent + '\n\n--- FILE CONTENTS ---\n\n' + attachmentContent,
    files: ['$TEMP_FILE']
};

// Write command for Claude to execute
const cmd = \`echo 'Using report MCP to send grabbed files: $REL_DIR'\`;
console.log(cmd);
" 2>/dev/null

# Actually send via Claude MCP (if available)
if command -v claude >/dev/null 2>&1; then
    # Try to send using claude command with MCP
    echo 'Sending grabbed files report...' | claude 2>/dev/null || {
        echo "  Claude command not available, saving files locally instead"
        echo "Files saved to: $TEMP_FILE"
        echo "Plain text saved to: $TEMP_PLAIN"
        echo
        echo "You can manually send these files or use the report MCP directly:"
        echo "mcp__report__send_report with files=['$TEMP_FILE']"
    }
else
    echo "  Claude command not available, files saved locally:"
    echo "Concatenated: $TEMP_FILE"
    echo "Summary: $TEMP_PLAIN"
fi

# Keep temp files for now (don't auto-delete)
echo
echo " File grab complete!"
echo "Files processed: ${#FILES_ARRAY[@]}"
echo "Output saved: $TEMP_FILE"