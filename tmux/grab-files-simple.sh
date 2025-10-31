#!/bin/bash
# Simple file grabber using shell-based selection

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo " File Grab - Select files to grab and email"
echo "============================================"
echo " SANITY CHECK: Running grab-files-simple.sh v2.0 ($(date '+%Y-%m-%d %H:%M:%S'))"
echo " Working directory: $(pwd)"
echo

# Find script files up to 2 levels deep (using shell globbing)
FILES=()

# Current directory
shopt -s nullglob
for ext in sh py js pl rb php go rs; do
    for file in *.$ext; do
        [[ -f "$file" ]] && FILES+=("./$file")
    done
done

# One level deep
for dir in */; do
    [[ -d "$dir" ]] || continue
    for ext in sh py js pl rb php go rs; do
        for file in "$dir"*.$ext; do
            [[ -f "$file" ]] && FILES+=("$file")
        done
    done
done

# Two levels deep
for dir in */; do
    [[ -d "$dir" ]] || continue
    for subdir in "$dir"*/; do
        [[ -d "$subdir" ]] || continue
        for ext in sh py js pl rb php go rs; do
            for file in "$subdir"*.$ext; do
                [[ -f "$file" ]] && FILES+=("$file")
            done
        done
    done
done
shopt -u nullglob

# Sort the files
if [ ${#FILES[@]} -gt 0 ]; then
    IFS=$'\n' FILES=($(sort <<<"${FILES[*]}"))
fi

echo " SANITY CHECK: Searched for extensions: sh py js pl rb php go rs"
echo " Search scope: current directory, 1 level deep, 2 levels deep"
echo

if [ ${#FILES[@]} -eq 0 ]; then
    echo " NO FILES FOUND"
    echo "================================="
    echo " Current directory: $(pwd)"
    echo " Files checked:"
    echo "   - Current dir: $(ls -la *.*  2>/dev/null | wc -l) total files"
    echo "   - Subdirs: $(ls -d */ 2>/dev/null | wc -l) directories"
    echo "   - Script files: 0 matching extensions"
    echo
    echo " PROOF CHECK - All files in current directory:"
    ls -la 2>/dev/null || echo "   (directory empty or no access)"
    echo
    read -p "Press Enter to exit..."
    exit 0
fi

echo " FOUND ${#FILES[@]} SCRIPT FILES:"
echo "================================="
echo

# Show files with numbers
for i in "${!FILES[@]}"; do
    printf "%3d) %s\n" $((i+1)) "${FILES[$i]}"
done

echo
echo "Enter file numbers to select (space-separated, e.g., '1 3 5'):"
echo "Or press Enter to cancel"
read -r SELECTION

if [[ -z "$SELECTION" ]]; then
    echo "No files selected. Exiting."
    exit 0
fi

# Convert selection to array
IFS=' ' read -ra INDICES <<< "$SELECTION"
SELECTED_FILES=()

for i in "${!INDICES[@]}"; do
    idx="${INDICES[i]}"
    if [[ "$idx" =~ ^[0-9]+$ ]] && [ "$idx" -ge 1 ] && [ "$idx" -le ${#FILES[@]} ]; then
        SELECTED_FILES+=("${FILES[$((idx-1))]}")
    else
        echo "  Invalid selection: '$idx' (ignoring)"
    fi
done

if [ ${#SELECTED_FILES[@]} -eq 0 ]; then
    echo "No valid files selected. Exiting."
    exit 0
fi

echo
echo "Selected files:"
for file in "${SELECTED_FILES[@]}"; do
    echo "  - $file"
done

# Create temporary files
TEMP_FILE="/tmp/grabbed-files-$(date +%s).txt"
TEMP_PLAIN="/tmp/grabbed-files-plain-$(date +%s).txt"

# Create content
{
    echo "Grabbed Files - $(date)"
    echo "Directory: $(pwd)"
    echo "Files: ${#SELECTED_FILES[@]}"
    echo
} > "$TEMP_FILE"

{
    echo "File Grab Report"
    echo "==============="
    echo
    echo "Directory: $(pwd)"
    echo "Timestamp: $(date)"
    echo "Files grabbed: ${#SELECTED_FILES[@]}"
    echo
} > "$TEMP_PLAIN"

for file in "${SELECTED_FILES[@]}"; do
    if [[ -f "$file" ]]; then
        echo "===== $file =====" >> "$TEMP_FILE"
        cat "$file" >> "$TEMP_FILE"
        echo >> "$TEMP_FILE"

        echo "File: $file" >> "$TEMP_PLAIN"
        echo "Size: $(wc -l < "$file") lines" >> "$TEMP_PLAIN"
        echo >> "$TEMP_PLAIN"
    else
        echo "[ERROR] $file not found" >> "$TEMP_FILE"
        echo "ERROR: $file not found" >> "$TEMP_PLAIN"
    fi
done

REL_DIR="$(basename "$(pwd)")"

echo
echo " Files processed and saved:"
echo "  Concatenated: $TEMP_FILE"
echo "  Summary: $TEMP_PLAIN"
echo
echo " File grab complete!"
echo "Files processed: ${#SELECTED_FILES[@]}"

read -p "Press Enter to close..."