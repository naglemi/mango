#!/usr/bin/env bash
# Spectator Mode File Selector - Live file monitoring with vim-gitgutter

# Check if we're in a git repository
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo "Error: Not in a git repository"
    read -p "Press any key to exit..."
    exit 1
fi

# Get list of modified files in working tree with modification times
# First get files with git status, then sort by modification time
mapfile -t FILES < <(
    git status --porcelain |
    grep -E '^( M|M |MM| A|A |AM|\?\?)' |
    cut -c4- |
    while IFS= read -r file; do
        if [[ -f "$file" ]]; then
            # Get modification time in seconds since epoch
            mtime=$(stat -c %Y "$file" 2>/dev/null || stat -f %m "$file" 2>/dev/null)
            if [[ -n "$mtime" ]]; then
                echo "$mtime:$file"
            fi
        fi
    done |
    sort -rn |
    cut -d: -f2-
)

# If no modified files found, show 10 most recently edited tracked files
if [[ ${#FILES[@]} -eq 0 ]]; then
    echo "No modified files found in working tree."
    echo "Showing 10 most recently edited tracked files..."
    sleep 1
    mapfile -t FILES < <(
        git ls-files |
        while IFS= read -r file; do
            if [[ -f "$file" ]]; then
                mtime=$(stat -c %Y "$file" 2>/dev/null || stat -f %m "$file" 2>/dev/null)
                if [[ -n "$mtime" ]]; then
                    echo "$mtime:$file"
                fi
            fi
        done |
        sort -rn |
        head -10 |
        cut -d: -f2-
    )
fi

if [[ ${#FILES[@]} -eq 0 ]]; then
    echo "No files found to spectate."
    read -p "Press any key to exit..."
    exit 1
fi

# Function to get relative time string
get_time_ago() {
    local file="$1"
    local now=$(date +%s)
    local mtime=$(stat -c %Y "$file" 2>/dev/null || stat -f %m "$file" 2>/dev/null)

    if [[ -z "$mtime" ]]; then
        echo "unknown"
        return
    fi

    local diff=$((now - mtime))

    if [[ $diff -lt 60 ]]; then
        echo "${diff}s ago"
    elif [[ $diff -lt 3600 ]]; then
        echo "$((diff / 60))m ago"
    elif [[ $diff -lt 86400 ]]; then
        echo "$((diff / 3600))h ago"
    else
        echo "$((diff / 86400))d ago"
    fi
}

# Create menu items with time information
MENU_ITEMS=()
for file in "${FILES[@]}"; do
    time_ago=$(get_time_ago "$file")
    # Truncate filename if too long
    display_name="$file"
    if [[ ${#display_name} -gt 50 ]]; then
        display_name="...${display_name: -47}"
    fi
    MENU_ITEMS+=("$(printf "%-50s %10s" "$display_name" "[$time_ago]")")
done

# Display menu
echo "═══════════════════════════════════════════════════════════════════"
echo "                      SPECTATOR MODE FILE SELECTOR                 "
echo "═══════════════════════════════════════════════════════════════════"
echo
echo "Select a file to watch (use ↑/↓ arrows, press SPACE to select, q to quit):"
echo

# Menu selection logic
selected=0
tput civis  # Hide cursor

# Function to display the menu
display_menu() {
    local idx=0
    for item in "${MENU_ITEMS[@]}"; do
        # Clear the line first
        tput el  # Clear to end of line
        if [[ $idx -eq $selected ]]; then
            echo -e "\033[7m> $item\033[0m"  # Highlighted
        else
            echo "  $item"
        fi
        ((idx++))
    done
}

# Save cursor position before initial display
tput sc

# Initial display
display_menu

# Handle keyboard input
while true; do
    read -rsn1 key

    # Check for escape sequences (arrow keys)
    if [[ $key == $'\x1b' ]]; then
        read -rsn2 key  # Read the rest of the escape sequence
        case "$key" in
            '[A')  # Up arrow
                if [[ $selected -gt 0 ]]; then
                    ((selected--))
                else
                    selected=$((${#MENU_ITEMS[@]} - 1))
                fi
                ;;
            '[B')  # Down arrow
                if [[ $selected -lt $((${#MENU_ITEMS[@]} - 1)) ]]; then
                    ((selected++))
                else
                    selected=0
                fi
                ;;
        esac
    else
        case "$key" in
            ' ')  # Space - select
                tput cnorm  # Show cursor
                chosen_file="${FILES[$selected]}"
                break
                ;;
            q|Q)  # Quit
                tput cnorm  # Show cursor
                # Move cursor below menu before exiting
                tput cud $((${#MENU_ITEMS[@]} - selected))
                echo
                echo "Cancelled."
                exit 0
                ;;
            '')  # Enter key
                tput cnorm  # Show cursor
                chosen_file="${FILES[$selected]}"
                break
                ;;
        esac
    fi

    # Restore cursor position and redraw
    tput rc  # Restore cursor position
    display_menu
done

# Launch spectator mode with the selected file
export SPECTATOR_INTERVAL=3000
exec "$HOME/bin/spectate" "$chosen_file"