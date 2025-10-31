#!/usr/bin/env bash
# Library: Pane Arrangement for Complex Rearrangement
# Provides grouping and rearrangement logic

# Function: assign_panes_to_groups
# Purpose: Interactively assign panes to window groups
# Inputs: $1 - Session name, $2... - Pane identifiers
# Outputs: Newline-separated groups, each group is space-separated pane IDs
#          Example output:
#            1.0 2.1
#            3.0 3.1 4.0
#            5.0
# Exit codes: 0 on success, 1 on cancellation, 2 on error
assign_panes_to_groups() {
    local session_name="$1"
    shift
    local pane_ids=("$@")

    echo "" >&2
    echo "═══════════════════════════════════════════" >&2
    echo "   Pane Grouping - Assign to Windows" >&2
    echo "═══════════════════════════════════════════" >&2
    echo "" >&2
    echo "You have selected ${#pane_ids[@]} panes to rearrange." >&2
    echo "" >&2

    # Ask how many windows
    local num_windows
    while true; do
        read -p "How many windows do you want to create? [1-${#pane_ids[@]}]: " num_windows </dev/tty

        if [[ "$num_windows" =~ ^[0-9]+$ ]] && [ "$num_windows" -ge 1 ] && [ "$num_windows" -le "${#pane_ids[@]}" ]; then
            break
        fi
        echo "Invalid input. Please enter a number between 1 and ${#pane_ids[@]}" >&2
    done

    echo "" >&2
    echo "Creating $num_windows window(s)..." >&2
    echo "" >&2

    # If only one window, put all panes there
    if [ "$num_windows" -eq 1 ]; then
        echo "${pane_ids[*]}"
        return 0
    fi

    # Initialize groups array
    local -a groups
    for ((i=0; i<num_windows; i++)); do
        groups[$i]=""
    done

    # Interactive assignment using fzf
    echo "Assigning panes to windows..." >&2
    echo "" >&2

    local remaining_panes=("${pane_ids[@]}")
    local current_pane_idx=0

    while [ ${#remaining_panes[@]} -gt 0 ]; do
        local pane_id="${remaining_panes[0]}"

        # Get pane info for display
        local window_idx="${pane_id%.*}"
        local pane_idx="${pane_id#*.}"
        local pane_info
        pane_info=$(tmux list-panes -t "$session_name:$window_idx" \
            -F "#{pane_index}:#{window_name}:#{pane_current_command}" | \
            grep "^${pane_idx}:")

        local window_name=$(echo "$pane_info" | cut -d: -f2)
        local command=$(echo "$pane_info" | cut -d: -f3)

        # Show preview of pane
        echo "─────────────────────────────────────────" >&2
        echo "Pane: $pane_id | $window_name | $command" >&2
        echo "Remaining: ${#remaining_panes[@]} pane(s)" >&2
        echo "" >&2

        # Create menu options for window assignment
        local menu_items=""
        for ((i=0; i<num_windows; i++)); do
            local window_num=$((i+1))
            local group_size=$(echo "${groups[$i]}" | wc -w)
            menu_items+="Window $window_num (currently $group_size pane(s))"$'\n'
        done

        # Use fzf to select window
        local selected_window
        selected_window=$(echo "$menu_items" | \
            fzf --prompt="Assign pane $pane_id to which window? " \
                --header="Preview shown below | ESC to cancel" \
                --preview="tmux capture-pane -t $session_name:$pane_id -p 2>/dev/null || echo 'Preview not available'" \
                --preview-window=down:10 \
                --height=40% \
                2>/dev/tty)

        if [ $? -ne 0 ] || [ -z "$selected_window" ]; then
            echo "" >&2
            echo "Assignment cancelled" >&2
            return 1
        fi

        # Extract window number
        local window_group_idx=$(echo "$selected_window" | grep -o 'Window [0-9]*' | grep -o '[0-9]*')
        window_group_idx=$((window_group_idx - 1))

        # Add pane to group
        if [ -z "${groups[$window_group_idx]}" ]; then
            groups[$window_group_idx]="$pane_id"
        else
            groups[$window_group_idx]="${groups[$window_group_idx]} $pane_id"
        fi

        # Remove from remaining
        remaining_panes=("${remaining_panes[@]:1}")

        echo "  -> Assigned to Window $((window_group_idx + 1))" >&2
        echo "" >&2
    done

    # Output groups (newline-separated)
    for group in "${groups[@]}"; do
        if [ -n "$group" ]; then
            echo "$group"
        fi
    done

    return 0
}

# Function: execute_rearrangement
# Purpose: Execute the pane rearrangement based on groups
# Inputs: $1 - Session name, $2 - Groups (newline-separated)
# Outputs: Array of created window indices
# Exit codes: 0 on success, 1 on error
execute_rearrangement() {
    local session_name="$1"
    local groups="$2"

    echo "" >&2
    echo "═══════════════════════════════════════════" >&2
    echo "   Executing Rearrangement" >&2
    echo "═══════════════════════════════════════════" >&2
    echo "" >&2

    # Parse groups into array
    local -a group_array
    while IFS= read -r line; do
        if [ -n "$line" ]; then
            group_array+=("$line")
        fi
    done <<< "$groups"

    local -a created_windows
    local group_num=1

    for group in "${group_array[@]}"; do
        # Parse panes in this group
        read -ra pane_ids <<< "$group"

        if [ ${#pane_ids[@]} -eq 0 ]; then
            continue
        fi

        echo "Creating window $group_num with ${#pane_ids[@]} pane(s)..." >&2

        # Use first pane's window as base, or create new window
        local first_pane="${pane_ids[0]}"
        local first_window="${first_pane%.*}"
        local first_pane_idx="${first_pane#*.}"

        # Check if this is already a single-pane window
        local pane_count_in_window
        pane_count_in_window=$(tmux list-panes -t "$session_name:$first_window" | wc -l)

        local target_window
        if [ "$pane_count_in_window" -eq 1 ]; then
            # Use existing window
            target_window="$first_window"
            tmux rename-window -t "$session_name:$target_window" "Arranged-$group_num"
            echo "  Using existing window $target_window" >&2
        else
            # Break out the pane to its own window
            target_window=$(tmux break-pane -s "$session_name:$first_pane" -P -F "#{window_index}")
            tmux rename-window -t "$session_name:$target_window" "Arranged-$group_num"
            echo "  Created new window $target_window from pane $first_pane" >&2
        fi

        # Join remaining panes
        for ((i=1; i<${#pane_ids[@]}; i++)); do
            local pane_id="${pane_ids[$i]}"
            echo "  -> Joining pane $pane_id..." >&2

            if tmux join-pane -s "$session_name:$pane_id" -t "$session_name:$target_window" 2>&1; then
                # Check if source window is now empty and kill it
                local src_window="${pane_id%.*}"
                local remaining_panes
                remaining_panes=$(tmux list-panes -t "$session_name:$src_window" 2>/dev/null | wc -l)
                if [ "$remaining_panes" -eq 0 ]; then
                    tmux kill-window -t "$session_name:$src_window" 2>/dev/null || true
                fi
            else
                echo "    Warning: Failed to join pane $pane_id" >&2
            fi
        done

        created_windows+=("$target_window")
        echo "" >&2
        ((group_num++))
    done

    # Output created windows
    echo "${created_windows[*]}"
    return 0
}

# Function: apply_layouts_to_windows
# Purpose: Apply layouts to all created windows
# Inputs: $1 - Session name, $2... - Window indices
# Outputs: Status messages
# Exit codes: 0 on success
apply_layouts_to_windows() {
    local session_name="$1"
    shift
    local windows=("$@")

    echo "═══════════════════════════════════════════" >&2
    echo "   Applying Layouts" >&2
    echo "═══════════════════════════════════════════" >&2
    echo "" >&2

    # Source layout library
    local script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    source "$script_dir/pane-layout.sh"

    for window_idx in "${windows[@]}"; do
        # Count panes in window
        local pane_count
        pane_count=$(tmux list-panes -t "$session_name:$window_idx" 2>/dev/null | wc -l)

        if [ "$pane_count" -gt 1 ]; then
            echo "Window $window_idx ($pane_count panes):" >&2
            local layout
            layout=$(apply_layout "$window_idx" "$pane_count")
            echo "  -> Applied layout: $layout" >&2
            echo "" >&2
        else
            echo "Window $window_idx (1 pane): No layout needed" >&2
            echo "" >&2
        fi
    done

    return 0
}
