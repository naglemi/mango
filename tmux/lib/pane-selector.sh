#!/usr/bin/env bash
# Library: Pane Selection for Complex Rearrangement
# Provides FZF-based pane selection across all windows

# Function: generate_window_hierarchy
# Purpose: Generate visual hierarchy of windows and their panes
# Inputs: $1 - Session name
# Outputs: Formatted hierarchy with visual tree structure
generate_window_hierarchy() {
    local session_name="$1"

    # Get all windows
    local windows
    windows=$(tmux list-windows -t "$session_name" -F "#{window_index}:#{window_name}:#{window_panes}" 2>/dev/null)

    local output=""
    local prev_window=""

    # Get all panes with details
    local all_panes
    all_panes=$(tmux list-panes -s -t "$session_name" \
        -F "#{window_index}|#{pane_index}|#{window_name}|#{pane_current_command}|#{pane_title}|#{pane_width}x#{pane_height}" 2>/dev/null)

    while IFS=':' read -r win_idx win_name pane_count; do
        # Window header
        output+="┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓"$'\n'
        output+=$(printf "┃ Window %-2s: %-30s (%s pane(s)) ┃\n" "$win_idx" "$win_name" "$pane_count")
        output+="┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛"$'\n'

        # Get panes for this window
        local window_panes
        window_panes=$(echo "$all_panes" | grep "^${win_idx}|")

        local pane_num=0
        local total_panes=$(echo "$window_panes" | wc -l)

        while IFS='|' read -r w_idx p_idx w_name command title size; do
            local pane_id="${w_idx}.${p_idx}"

            # Determine tree character
            local tree_char="├─"
            if [ $((pane_num + 1)) -eq "$total_panes" ]; then
                tree_char="└─"
            fi

            # Format pane line
            output+=$(printf "  %s %-6s %-12s | %-15s | %s\n" \
                "$tree_char" "$pane_id" "$command" "$title" "$size")

            ((pane_num++))
        done <<< "$window_panes"

        output+=$'\n'
    done <<< "$windows"

    echo "$output"
}

# Function: select_panes
# Purpose: Display fzf multi-select menu for choosing any panes
# Inputs: $1 - Session name (string)
# Outputs: Space-separated pane identifiers (e.g., "1.0 2.1 3.0")
# Exit codes: 0 on success, 1 on cancellation, 2 on error
select_panes() {
    local session_name="${1:-$(tmux display-message -p '#S')}"

    # Get all panes with their details
    local panes_data
    panes_data=$(tmux list-panes -s -t "$session_name" \
        -F "#{window_index}|#{pane_index}|#{window_name}|#{pane_current_command}|#{pane_title}" 2>/dev/null)

    if [ $? -ne 0 ]; then
        echo "Error: Could not access session '$session_name'" >&2
        return 2
    fi

    if [ -z "$panes_data" ]; then
        echo "Error: No panes available in session '$session_name'" >&2
        return 2
    fi

    # Count available panes
    local pane_count
    pane_count=$(echo "$panes_data" | wc -l)

    if [ "$pane_count" -lt 2 ]; then
        echo "Error: Need at least 2 panes for rearrangement" >&2
        echo "Current session has $pane_count pane(s)" >&2
        return 2
    fi

    # Generate hierarchical view
    local hierarchy
    hierarchy=$(generate_window_hierarchy "$session_name")

    # Display hierarchy before selection
    echo "" >&2
    echo "Current window structure:" >&2
    echo "" >&2
    echo "$hierarchy" >&2
    echo "" >&2
    read -p "Press ENTER to continue to pane selection..." >&2
    echo "" >&2

    # Create flat list for fzf selection (but with window context)
    local formatted_panes
    formatted_panes=$(echo "$panes_data" | awk -F'|' '{
        pane_id = $1 "." $2
        window_name = $3
        command = $4
        title = $5
        printf "%-6s [Win: %-15s] %-12s | %s\n", pane_id, window_name, command, title
    }')

    # Launch FZF multi-select
    local selected
    selected=$(echo "$formatted_panes" | \
        fzf --multi \
            --prompt="Select panes to rearrange (TAB=select, ENTER=confirm): " \
            --header="Window structure shown above | ESC to cancel" \
            --preview="tmux capture-pane -t $session_name:{1} -p 2>/dev/null || echo 'Preview unavailable'" \
            --preview-window=right:50% \
            --height=80% \
            --ansi \
            2>/dev/tty)

    # Check if user cancelled
    if [ $? -ne 0 ] || [ -z "$selected" ]; then
        echo "Rearrangement cancelled" >&2
        return 1
    fi

    # Extract pane identifiers (window.pane format)
    local pane_ids
    pane_ids=$(echo "$selected" | awk '{print $1}' | tr '\n' ' ' | sed 's/ $//')

    echo "$pane_ids"
    return 0
}

# Function: get_pane_info
# Purpose: Get detailed information about a specific pane
# Inputs: $1 - Session name, $2 - Pane identifier (window.pane)
# Outputs: JSON-like string with pane info
# Exit codes: 0 on success, 1 on error
get_pane_info() {
    local session_name="$1"
    local pane_id="$2"

    # Parse window.pane
    local window_index="${pane_id%.*}"
    local pane_index="${pane_id#*.}"

    # Get pane details
    local pane_info
    pane_info=$(tmux list-panes -t "$session_name:$window_index" \
        -F "#{pane_index}:#{window_index}:#{window_name}:#{pane_current_command}:#{pane_pid}" | \
        grep "^${pane_index}:")

    if [ -z "$pane_info" ]; then
        echo "Error: Pane $pane_id not found" >&2
        return 1
    fi

    echo "$pane_info"
    return 0
}

# Function: validate_panes
# Purpose: Validate that panes still exist and are accessible
# Inputs: $1 - Session name, $2... - Pane identifiers
# Outputs: Error messages to stderr
# Exit codes: 0 if valid, 1 if invalid
validate_panes() {
    local session_name="$1"
    shift
    local pane_ids=("$@")

    # Check minimum count
    if [ ${#pane_ids[@]} -lt 2 ]; then
        echo "Error: At least 2 panes required for rearrangement (got ${#pane_ids[@]})" >&2
        return 1
    fi

    # Verify each pane exists
    for pane_id in "${pane_ids[@]}"; do
        local window_index="${pane_id%.*}"
        local pane_index="${pane_id#*.}"

        # Check pane exists
        if ! tmux list-panes -t "$session_name:$window_index" -F "#{pane_index}" | grep -q "^${pane_index}$"; then
            echo "Error: Pane $pane_id no longer exists in session '$session_name'" >&2
            return 1
        fi
    done

    return 0
}
