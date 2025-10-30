#!/bin/bash
# Ask LLM File Selector - Bash implementation based on working grab-files-checkbox.sh pattern
# Enhanced for broader file type support with size filtering

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Initialize state
SELECTED_FILES=()
CURRENT_INDEX=0
declare -a FILE_LIST
declare -a SELECTED_STATE
declare -a FILE_SIZES
MAX_FILE_SIZE=1048576  # 1MB default

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

# Format file size in human-readable format
format_size() {
    local size=$1
    if [ $size -lt 1024 ]; then
        echo "${size}B"
    elif [ $size -lt 1048576 ]; then
        echo "$((size/1024))KB"
    else
        echo "$((size/1048576))MB"
    fi
}

# Discover all relevant files with enhanced patterns
discover_files() {
    local files=()
    local sizes=()

    # Enhanced file extensions for Ask LLM
    local extensions=(
        "py" "js" "ts" "jsx" "tsx" "go" "rs" "java" "c" "cpp" "h" "hpp"
        "sh" "bash" "zsh" "fish" "pl" "rb" "php" "lua" "r" "scala" "kt"
        "swift" "m" "mm" "cs" "vb" "fs" "clj" "hs" "elm" "erl" "ex" "jl"
        "md" "rst" "txt" "json" "yaml" "yml" "toml" "ini" "cfg" "conf"
        "xml" "html" "htm" "css" "scss" "sass" "less" "sql" "graphql"
        "dockerfile" "env" "mk" "ipynb" "rmd" "qmd" "tex" "bib" "csv" "tsv" "log"
    )

    shopt -s nullglob dotglob

    # Function to check if file should be included
    should_include_file() {
        local file="$1"
        local filename=$(basename "$file")

        # Skip hidden files (except special ones)
        if [[ "$filename" == .* ]] && [[ ! "$filename" =~ \.(env|envrc|gitignore|dockerignore)$ ]]; then
            return 1
        fi

        # Skip directories
        [[ -d "$file" ]] && return 1

        # Get file size
        local size=$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null || echo 0)

        # Skip files that are too large
        [ $size -gt $MAX_FILE_SIZE ] && return 1

        # Check extensions
        local ext="${filename##*.}"
        ext="${ext,,}"  # lowercase

        # Check if extension matches or if it's a special filename
        for valid_ext in "${extensions[@]}"; do
            if [[ "$ext" == "$valid_ext" ]]; then
                return 0
            fi
        done

        # Check special filenames without extensions
        case "$filename" in
            "makefile"|"Makefile"|"dockerfile"|"Dockerfile"|"readme"|"README"|"license"|"LICENSE"|"changelog"|"CHANGELOG"|"todo"|"TODO")
                return 0
                ;;
        esac

        return 1
    }

    # Scan current directory
    for file in *; do
        if should_include_file "$file"; then
            local size=$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null || echo 0)
            files+=("$file")
            sizes+=("$size")
        fi
    done

    # Scan one level deep
    for dir in */; do
        [[ -d "$dir" ]] || continue
        # Skip common ignore patterns
        case "$(basename "$dir")" in
            "node_modules"|"__pycache__"|".git"|".venv"|"venv"|"env"|"build"|"dist"|"target"|"bin"|"obj"|".next"|".nuxt")
                continue
                ;;
        esac

        for file in "$dir"*; do
            if should_include_file "$file"; then
                local size=$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null || echo 0)
                files+=("$file")
                sizes+=("$size")
            fi
        done
    done

    # Scan two levels deep
    for dir in */; do
        [[ -d "$dir" ]] || continue
        case "$(basename "$dir")" in
            "node_modules"|"__pycache__"|".git"|".venv"|"venv"|"env"|"build"|"dist"|"target"|"bin"|"obj"|".next"|".nuxt")
                continue
                ;;
        esac

        for subdir in "$dir"*/; do
            [[ -d "$subdir" ]] || continue
            case "$(basename "$subdir")" in
                "node_modules"|"__pycache__"|".git"|".venv"|"venv"|"env"|"build"|"dist"|"target"|"bin"|"obj"|".next"|".nuxt")
                    continue
                    ;;
            esac

            for file in "$subdir"*; do
                if should_include_file "$file"; then
                    local size=$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null || echo 0)
                    files+=("$file")
                    sizes+=("$size")
                fi
            done
        done
    done

    shopt -u nullglob dotglob

    # Sort files by path
    if [ ${#files[@]} -gt 0 ]; then
        # Create indexed array for sorting
        local indexed=()
        for i in "${!files[@]}"; do
            indexed+=("$i:${files[i]}")
        done

        # Sort by filename part
        IFS=$'\n' sorted=($(printf '%s\n' "${indexed[@]}" | sort -t: -k2))

        # Rebuild arrays
        files=()
        sizes=()
        for item in "${sorted[@]}"; do
            local idx="${item%%:*}"
            files+=("${FILE_LIST[idx]:-${item#*:}}")
            sizes+=("${FILE_SIZES[idx]:-0}")
        done
    fi

    FILE_LIST=("${files[@]}")
    FILE_SIZES=("${sizes[@]}")
    SELECTED_STATE=()
    for ((i=0; i<${#FILE_LIST[@]}; i++)); do
        SELECTED_STATE[i]=false
    done
}

display_menu() {
    clear_screen

    echo " Ask LLM - File Selection"
    echo "============================================"
    echo " Directory: $(pwd)"
    echo " Found ${#FILE_LIST[@]} relevant files"
    echo " Max file size: $(format_size $MAX_FILE_SIZE)"
    echo ""

    if [ ${#FILE_LIST[@]} -eq 0 ]; then
        echo " NO RELEVANT FILES FOUND"
        echo "================================="
        echo " Current directory: $(pwd)"
        echo " Search criteria:"
        echo "   - File types: code, config, docs, data files"
        echo "   - Max size: $(format_size $MAX_FILE_SIZE)"
        echo "   - Depth: up to 2 subdirectories"
        echo "   - Excludes: hidden files, build dirs, node_modules, etc."
        echo ""
        echo "Press any key to exit..."
        get_char > /dev/null
        return 1
    fi

    echo "Controls: ↑↓ navigate, SPACE toggle, ENTER confirm, q quit, s toggle size limit"
    echo "================================="
    echo ""

    # Calculate display window
    local display_start=$((CURRENT_INDEX > 15 ? CURRENT_INDEX - 15 : 0))
    local display_end=$((display_start + 30))
    [ $display_end -gt ${#FILE_LIST[@]} ] && display_end=${#FILE_LIST[@]}

    # Show truncation indicator
    [ $display_start -gt 0 ] && echo "  ..."

    # Display files with checkboxes
    for ((i=display_start; i<display_end; i++)); do
        local prefix=""
        local checkbox=""

        if [[ $i -eq $CURRENT_INDEX ]]; then
            prefix="> "
        else
            prefix="  "
        fi

        if [[ "${SELECTED_STATE[$i]}" == "true" ]]; then
            checkbox=""
        else
            checkbox=""
        fi

        local size_str=$(format_size ${FILE_SIZES[$i]})
        printf "%s%s %s (%s)\n" "$prefix" "$checkbox" "${FILE_LIST[$i]}" "$size_str"
    done

    # Show truncation indicator
    [ $display_end -lt ${#FILE_LIST[@]} ] && echo "  ..."

    echo ""
    echo "================================="
    local selected_count=0
    local total_size=0
    for i in "${!SELECTED_STATE[@]}"; do
        if [[ "${SELECTED_STATE[$i]}" == "true" ]]; then
            ((selected_count++))
            ((total_size += ${FILE_SIZES[$i]}))
        fi
    done
    echo "Selected: $selected_count files"
    [ $selected_count -gt 0 ] && echo "Total size: $(format_size $total_size)"
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
            if [ ${#FILE_LIST[@]} -gt 0 ]; then
                if [[ "${SELECTED_STATE[$CURRENT_INDEX]}" == "true" ]]; then
                    SELECTED_STATE[$CURRENT_INDEX]=false
                else
                    SELECTED_STATE[$CURRENT_INDEX]=true
                fi
            fi
            ;;
        "s"|"S")  # Toggle size limit
            if [ $MAX_FILE_SIZE -eq 1048576 ]; then
                MAX_FILE_SIZE=10485760  # 10MB
            else
                MAX_FILE_SIZE=1048576   # 1MB
            fi
            echo " Rescanning with new size limit..."
            discover_files
            CURRENT_INDEX=0
            ;;
        $'\n'|$'\r')  # Enter - confirm selection
            return 1
            ;;
        "q"|"Q")
            echo ""
            echo "Cancelled."
            return 2
            ;;
    esac

    return 0
}

# Output selected files in format expected by ask-llm.sh
output_selection() {
    local selected_files=()

    for i in "${!SELECTED_STATE[@]}"; do
        if [[ "${SELECTED_STATE[$i]}" == "true" ]]; then
            selected_files+=("${FILE_LIST[$i]}")
        fi
    done

    clear_screen
    echo " Ask LLM - File Selection Complete"
    echo "================================="

    if [ ${#selected_files[@]} -eq 0 ]; then
        echo "No files selected."
        echo "SELECTED_FILES="
        return
    fi

    echo "Selected ${#selected_files[@]} files:"
    local total_size=0
    for file in "${selected_files[@]}"; do
        # Find the size for this file
        for i in "${!FILE_LIST[@]}"; do
            if [[ "${FILE_LIST[$i]}" == "$file" ]]; then
                local size=${FILE_SIZES[$i]}
                ((total_size += size))
                echo "   $file ($(format_size $size))"
                break
            fi
        done
    done
    echo ""
    echo "Total: $(format_size $total_size)"
    echo ""

    # Output in format expected by shell script
    printf "SELECTED_FILES="
    printf '"%s" ' "${selected_files[@]}"
    echo ""
}

# Main execution
main() {
    # Set working directory if provided
    if [ $# -gt 0 ] && [ -d "$1" ]; then
        cd "$1"
    fi

    echo " Discovering files..."
    discover_files

    if [ ${#FILE_LIST[@]} -eq 0 ]; then
        display_menu
        echo "SELECTED_FILES="
        exit 0
    fi

    while true; do
        display_menu
        key=$(get_char)
        result=$(handle_input "$key")
        case $? in
            1) break ;;      # Enter pressed
            2) echo "SELECTED_FILES="; exit 0 ;;  # Quit pressed
        esac
    done

    output_selection
}

# Execute main function
main "$@"