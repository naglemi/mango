#!/usr/bin/env bash
# Visual Pane Mover - Intuitive pane rearrangement
# Navigate windows visually, pick panes by what you see, move them where you want

set -euo pipefail

# Source library functions for layouts
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/pane-layout.sh"

# Function: show_window_list
# Display simple list of windows for selection
show_window_list() {
    local session_name="$1"

    echo ""
    echo "═══════════════════════════════════════════"
    echo "   Available Windows"
    echo "═══════════════════════════════════════════"
    echo ""

    tmux list-windows -t "$session_name" -F "  [#{window_index}] #{window_name} (#{window_panes} panes)"
    echo ""
}

# Function: pick_source_pane
# Let user visually select a pane from a window
pick_source_pane() {
    local session_name="$1"

    show_window_list "$session_name"

    local source_window
    read -p "Which window contains the pane you want to move? " source_window </dev/tty

    # Validate window exists
    if ! tmux list-windows -t "$session_name" -F "#{window_index}" | grep -q "^${source_window}$"; then
        echo "Error: Window $source_window does not exist" >&2
        return 1
    fi

    # Switch to that window so user can see it
    tmux select-window -t "$session_name:$source_window"

    echo ""
    echo "Switched to window $source_window"
    echo "Look at your tmux window - you'll see pane numbers displayed..."
    echo ""
    sleep 1

    # Display panes visually in the actual tmux window
    tmux display-panes -t "$session_name:$source_window" -d 5000

    echo "Pane numbers are now visible on each pane in the window."
    echo ""

    local pane_index
    read -p "Which pane number do you want to move? " pane_index </dev/tty

    # Validate pane exists
    if ! tmux list-panes -t "$session_name:$source_window" -F "#{pane_index}" | grep -q "^${pane_index}$"; then
        echo "Error: Pane $pane_index does not exist in window $source_window" >&2
        return 1
    fi

    echo "${source_window}.${pane_index}"
    return 0
}

# Function: pick_destination
# Let user choose where to move the pane
pick_destination() {
    local session_name="$1"
    local source_pane="$2"

    echo ""
    echo "─────────────────────────────────────────"
    echo "Where do you want to move pane $source_pane?"
    echo "─────────────────────────────────────────"
    echo ""
    echo "  [n] New window (create a new window for this pane)"
    echo "  [e] Existing window (join to an existing window)"
    echo ""

    local dest_choice
    read -n 1 -p "Destination [n/e]: " dest_choice </dev/tty
    echo ""
    echo ""

    case "$dest_choice" in
        n|N)
            # Create new window
            local new_window
            new_window=$(tmux new-window -P -F "#{window_index}" -n "Moved")
            echo "$new_window"
            return 0
            ;;
        e|E)
            # Pick existing window
            show_window_list "$session_name"

            local dest_window
            read -p "Which window to join to? " dest_window </dev/tty

            # Validate window exists
            if ! tmux list-windows -t "$session_name" -F "#{window_index}" | grep -q "^${dest_window}$"; then
                echo "Error: Window $dest_window does not exist" >&2
                return 1
            fi

            # Switch to destination window so user can see it
            tmux select-window -t "$session_name:$dest_window"

            echo ""
            echo "Switched to destination window $dest_window"
            echo "Look at your tmux window to see the current layout..."
            echo ""
            sleep 1

            # Show panes in destination
            tmux display-panes -t "$session_name:$dest_window" -d 5000

            echo "$dest_window"
            return 0
            ;;
        *)
            echo "Invalid choice" >&2
            return 1
            ;;
    esac
}

# Function: execute_move
# Move the pane to the destination
execute_move() {
    local session_name="$1"
    local source_pane="$2"  # format: window.pane
    local dest_window="$3"

    local source_window="${source_pane%.*}"
    local pane_index="${source_pane#*.}"

    echo ""
    echo "Moving pane $source_pane to window $dest_window..."

    # Get pane info for logging
    local pane_info
    pane_info=$(tmux list-panes -t "$session_name:$source_window" \
        -F "#{pane_index}:#{pane_current_command}" | grep "^${pane_index}:")
    local command=$(echo "$pane_info" | cut -d: -f2)

    # Execute the move
    if tmux join-pane -s "$session_name:${source_pane}" -t "$session_name:$dest_window" 2>&1; then
        echo " Moved pane successfully"

        # Check if source window is now empty
        local remaining_panes
        remaining_panes=$(tmux list-panes -t "$session_name:$source_window" 2>/dev/null | wc -l)

        if [ "$remaining_panes" -eq 0 ]; then
            echo " Source window $source_window was empty, removed it"
        fi

        # Switch to destination to see result
        tmux select-window -t "$session_name:$dest_window"

        echo ""
        echo "Moved: $command (pane $source_pane) → window $dest_window"

        return 0
    else
        echo "Error: Failed to move pane" >&2
        return 1
    fi
}

# Function: visual_pane_mover
# Main interactive loop
visual_pane_mover() {
    local session_name
    session_name=$(tmux display-message -p '#S')

    # Check we're in tmux
    if [ -z "$TMUX" ]; then
        echo "Error: This script must be run from within a tmux session" >&2
        exit 1
    fi

    echo ""
    echo "═══════════════════════════════════════════"
    echo "   Visual Pane Mover"
    echo "═══════════════════════════════════════════"
    echo ""
    echo "Move panes by seeing and selecting them visually."
    echo "You'll navigate to windows and see pane numbers displayed."
    echo ""

    while true; do
        # Pick source pane
        local source_pane
        source_pane=$(pick_source_pane "$session_name")

        if [ $? -ne 0 ]; then
            echo ""
            read -p "Try again? [y/n]: " retry </dev/tty
            if [[ "$retry" =~ ^[Yy] ]]; then
                continue
            else
                echo "Cancelled"
                exit 0
            fi
        fi

        # Pick destination
        local dest_window
        dest_window=$(pick_destination "$session_name" "$source_pane")

        if [ $? -ne 0 ]; then
            echo ""
            read -p "Try again? [y/n]: " retry </dev/tty
            if [[ "$retry" =~ ^[Yy] ]]; then
                continue
            else
                echo "Cancelled"
                exit 0
            fi
        fi

        # Execute the move
        execute_move "$session_name" "$source_pane" "$dest_window"

        echo ""
        echo "─────────────────────────────────────────"

        # Ask if user wants to move more panes
        local continue_choice
        read -n 1 -p "Move another pane? [y/n]: " continue_choice </dev/tty
        echo ""

        if [[ ! "$continue_choice" =~ ^[Yy] ]]; then
            break
        fi

        echo ""
    done

    echo ""
    echo "═══════════════════════════════════════════"
    echo "   Done!"
    echo "═══════════════════════════════════════════"
    echo ""

    exit 0
}

# Main entry point
visual_pane_mover
