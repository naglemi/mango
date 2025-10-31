#!/bin/bash
# Checkbox-based file grabber matching hooks interface pattern

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Initialize state
SELECTED_FILES=()
CURRENT_INDEX=0
declare -a FILE_LIST
declare -a SELECTED_STATE

# Terminal control functions
clear_screen() {
    printf '\033[2J\033[H'
}

get_char() {
    local char
    read -rsn1 char

    # Handle arrow keys (escape sequences)
    if [[ $char == $'\033' ]]; then
        read -rsn2 char
        case $char in
            '[A') echo "UP" ;;
            '[B') echo "DOWN" ;;
            *) echo "$char" ;;
        esac
    else
        echo "$char"
    fi
}

# Find script files using shell globbing (same as before)
discover_files() {
    local files=()

    # Current directory
    shopt -s nullglob
    for ext in sh py js pl rb php go rs; do
        for file in *.$ext; do
            [[ -f "$file" ]] && files+=("./$file")
        done
    done

    # One level deep
    for dir in */; do
        [[ -d "$dir" ]] || continue
        for ext in sh py js pl rb php go rs; do
            for file in "$dir"*.$ext; do
                [[ -f "$file" ]] && files+=("$file")
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
                    [[ -f "$file" ]] && files+=("$file")
                done
            done
        done
    done
    shopt -u nullglob

    # Sort the files
    if [ ${#files[@]} -gt 0 ]; then
        IFS=$'\n' files=($(sort <<<"${files[*]}"))
    fi

    FILE_LIST=("${files[@]}")
    SELECTED_STATE=()
    for ((i=0; i<${#FILE_LIST[@]}; i++)); do
        SELECTED_STATE[i]=false
    done
}

display_menu() {
    clear_screen

    echo "File Grab - Checkbox Selection"
    echo "============================================"
    echo "SANITY CHECK: Running grab-files-checkbox.sh v3.0 ($(date '+%Y-%m-%d %H:%M:%S'))"
    echo "Working directory: $(pwd)"
    echo ""

    if [ ${#FILE_LIST[@]} -eq 0 ]; then
        echo "NO FILES FOUND"
        echo "================================="
        echo "Current directory: $(pwd)"
        echo "Files checked:"
        echo "   - Current dir: $(ls -la *.*  2>/dev/null | wc -l) total files"
        echo "   - Subdirs: $(ls -d */ 2>/dev/null | wc -l) directories"
        echo "   - Script files: 0 matching extensions"
        echo ""
        echo "PROOF CHECK - All files in current directory:"
        ls -la 2>/dev/null || echo "   (directory empty or no access)"
        echo ""
        echo "Press any key to exit..."
        get_char > /dev/null
        exit 0
    fi

    echo "Controls: ↑↓ navigate, SPACE toggle, ENTER confirm, q quit"
    echo "================================="
    echo ""

    # Display files with checkboxes
    for i in "${!FILE_LIST[@]}"; do
        local prefix=""
        local checkbox=""

        if [[ $i -eq $CURRENT_INDEX ]]; then
            prefix="> "
        else
            prefix="  "
        fi

        if [[ "${SELECTED_STATE[$i]}" == "true" ]]; then
            checkbox="[X]"
        else
            checkbox="[ ]"
        fi

        printf "%s%s %s\n" "$prefix" "$checkbox" "${FILE_LIST[$i]}"
    done

    echo ""
    echo "================================="
    local selected_count=0
    for state in "${SELECTED_STATE[@]}"; do
        [[ "$state" == "true" ]] && ((selected_count++))
    done
    echo "Selected: $selected_count files"
}

handle_input() {
    local key="$1"

    case $key in
        "UP")
            if [ $CURRENT_INDEX -gt 0 ]; then
                ((CURRENT_INDEX--))
            fi
            ;;
        "DOWN")
            if [ $CURRENT_INDEX -lt $((${#FILE_LIST[@]} - 1)) ]; then
                ((CURRENT_INDEX++))
            fi
            ;;
        " ")  # Spacebar - toggle selection
            if [[ "${SELECTED_STATE[$CURRENT_INDEX]}" == "true" ]]; then
                SELECTED_STATE[$CURRENT_INDEX]=false
            else
                SELECTED_STATE[$CURRENT_INDEX]=true
            fi
            ;;
        $'\n'|$'\r')  # Enter - confirm selection
            return 1
            ;;
        "q"|"Q")
            echo ""
            echo "Cancelled."
            exit 0
            ;;
    esac

    return 0
}

process_selection() {
    local selected_files=()

    for i in "${!SELECTED_STATE[@]}"; do
        if [[ "${SELECTED_STATE[$i]}" == "true" ]]; then
            selected_files+=("${FILE_LIST[$i]}")
        fi
    done

    if [ ${#selected_files[@]} -eq 0 ]; then
        echo ""
        echo "No files selected. Exiting."
        exit 0
    fi

    clear_screen
    echo "Processing ${#selected_files[@]} selected files:"
    echo "================================="
    for file in "${selected_files[@]}"; do
        echo "  - $file"
    done
    echo ""

    # Create temporary files
    local temp_file="/tmp/grabbed-files-$(date +%s).txt"
    local temp_plain="/tmp/grabbed-files-plain-$(date +%s).txt"

    # Create content
    {
        echo "Grabbed Files - $(date)"
        echo "Directory: $(pwd)"
        echo "Files: ${#selected_files[@]}"
        echo
    } > "$temp_file"

    {
        echo "File Grab Report"
        echo "==============="
        echo
        echo "Directory: $(pwd)"
        echo "Timestamp: $(date)"
        echo "Files grabbed: ${#selected_files[@]}"
        echo
    } > "$temp_plain"

    for file in "${selected_files[@]}"; do
        if [[ -f "$file" ]]; then
            echo "===== $file =====" >> "$temp_file"
            cat "$file" >> "$temp_file"
            echo >> "$temp_file"

            echo "File: $file" >> "$temp_plain"
            echo "Size: $(wc -l < "$file") lines" >> "$temp_plain"
            echo >> "$temp_plain"
        else
            echo "[ERROR] $file not found" >> "$temp_file"
            echo "ERROR: $file not found" >> "$temp_plain"
        fi
    done

    echo "Files processed and saved:"
    echo "  Concatenated: $temp_file"
    echo "  Summary: $temp_plain"
    echo ""
    echo "File grab complete!"
    echo "Files processed: ${#selected_files[@]}"
    echo ""
    read -p "Press Enter to close..."
}

# Main execution
main() {
    echo "Discovering files..."
    discover_files

    if [ ${#FILE_LIST[@]} -eq 0 ]; then
        display_menu
        exit 0
    fi

    while true; do
        display_menu
        key=$(get_char)
        if ! handle_input "$key"; then
            break
        fi
    done

    process_selection
}

# Execute main function
main "$@"