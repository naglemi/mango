#!/bin/bash

# File selector for vim editing
# Shows numbered list of modified files (scripts and docs)

cd "$(pwd)" || exit 1

# Check if we're in a git repo
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "Not in a git repository"
    read -p "Press Enter to exit..."
    exit 1
fi

# Get staged files with specific extensions
staged_files=$(git diff --cached --name-only | grep -E '\.(py|R|sh|json|yaml|yml|txt|md)$' | sort)

if [ -z "$staged_files" ]; then
    echo "No staged files found with extensions: .py, .R, .sh, .json, .yaml, .txt, .md"
    echo "Use 'git add <file>' to stage changes first"
    read -p "Press Enter to exit..."
    exit 1
fi

# Create numbered list
echo "=== File Selector for Vim ==="
echo
i=1
file_array=()
while IFS= read -r file; do
    # Show file with its extension highlighted
    ext="${file##*.}"
    basename="${file%.*}"
    printf "  %2d) %-40s [%s]\n" "$i" "$file" "$ext"
    file_array+=("$file")
    ((i++))
done <<< "$staged_files"

echo
echo -n "Select file (1-$((i-1))) or q to quit: "
read -r selection

if [[ "$selection" == "q" ]]; then
    exit 0
fi

if [[ "$selection" =~ ^[0-9]+$ ]] && [ "$selection" -ge 1 ] && [ "$selection" -lt "$i" ]; then
    selected_file="${file_array[$((selection-1))]}"
    clear
    vim "$selected_file"
else
    echo "Invalid selection"
    sleep 1
fi