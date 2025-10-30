#!/usr/bin/env bash
# Library: Window Selection for Consolidation
# Provides FZF-based window selection with validation

# Function: select_windows
# Purpose: Display fzf multi-select menu for choosing single-pane windows
# Inputs: $1 - Session name (string)
# Outputs: Space-separated window indices (e.g., "0 2 5")
# Exit codes: 0 on success, 1 on cancellation, 2 on error
select_windows() {
    local session_name="${1:-$(tmux display-message -p '#S')}"

    # Get all single-pane windows with their details
    local windows_data
    windows_data=$(tmux list-windows -t "$session_name" -F "#{window_index}:#{window_panes}:#{window_name}" 2>/dev/null)

    if [ $? -ne 0 ]; then
        echo "Error: Could not access session '$session_name'" >&2
        return 2
    fi

    # Filter for single-pane windows only
    local single_pane_windows
    single_pane_windows=$(echo "$windows_data" | awk -F: '$2 == 1 {print $1 ": " $3}')

    if [ -z "$single_pane_windows" ]; then
        echo "Error: No single-pane windows available in session '$session_name'" >&2
        echo "Tip: Only single-pane windows can be consolidated" >&2
        return 2
    fi

    # Count available windows
    local window_count
    window_count=$(echo "$single_pane_windows" | wc -l)

    if [ "$window_count" -lt 2 ]; then
        echo "Error: Need at least 2 single-pane windows for consolidation" >&2
        echo "Current session has $window_count single-pane window(s)" >&2
        return 2
    fi

    # Launch FZF multi-select
    local selected
    selected=$(echo "$single_pane_windows" | \
        fzf --multi \
            --prompt="Select windows to consolidate (TAB to select, ENTER to confirm): " \
            --header="Only single-pane windows shown | ESC to cancel" \
            --preview="tmux capture-pane -t $session_name:{1} -p" \
            --preview-window=right:60% \
            --height=80% \
            2>/dev/tty)

    # Check if user cancelled (ESC or Ctrl+C)
    if [ $? -ne 0 ] || [ -z "$selected" ]; then
        echo "Consolidation cancelled" >&2
        return 1
    fi

    # Extract window indices from selection
    local indices
    indices=$(echo "$selected" | awk '{print $1}' | tr -d ':' | tr '\n' ' ' | sed 's/ $//')

    echo "$indices"
    return 0
}

# Function: validate_windows
# Purpose: Validate selected windows are eligible for consolidation
# Inputs: $1 - Session name, $2... - Window indices
# Outputs: Error messages to stderr
# Exit codes: 0 if valid, 1 if invalid
validate_windows() {
    local session_name="$1"
    shift
    local window_indices=("$@")

    # Check minimum count
    if [ ${#window_indices[@]} -lt 2 ]; then
        echo "Error: At least 2 windows required for consolidation (got ${#window_indices[@]})" >&2
        return 1
    fi

    # Verify each window exists and is single-pane
    for idx in "${window_indices[@]}"; do
        # Check window exists
        if ! tmux list-windows -t "$session_name" -F "#{window_index}" | grep -q "^${idx}$"; then
            echo "Error: Window $idx no longer exists in session '$session_name'" >&2
            return 1
        fi

        # Check window is single-pane
        local pane_count
        pane_count=$(tmux list-panes -t "$session_name:$idx" 2>/dev/null | wc -l)

        if [ "$pane_count" -ne 1 ]; then
            echo "Error: Window $idx has $pane_count panes (only single-pane windows allowed)" >&2
            return 1
        fi
    done

    return 0
}

# Function: check_single_pane_availability
# Purpose: Check if session has enough single-pane windows for consolidation
# Inputs: $1 - Session name
# Outputs: Count of single-pane windows to stdout
# Exit codes: 0 always
check_single_pane_availability() {
    local session_name="${1:-$(tmux display-message -p '#S')}"

    local count
    count=$(tmux list-windows -t "$session_name" -F "#{window_index}:#{window_panes}" 2>/dev/null | \
            awk -F: '$2 == 1' | wc -l)

    echo "$count"
    return 0
}
