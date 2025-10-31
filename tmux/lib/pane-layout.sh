#!/usr/bin/env bash
# Library: Pane Layout Management
# Provides smart layout defaults and application

# Function: apply_layout
# Purpose: Prompt for and apply pane layout to consolidated window
# Inputs: $1 - Window index, $2 - Pane count
# Outputs: Applied layout name to stdout
# Exit codes: 0 on success, 1 on failure
apply_layout() {
    local window_index="$1"
    local pane_count="$2"

    # Calculate smart default based on pane count
    local default_layout
    if [ "$pane_count" -le 3 ]; then
        default_layout="main-vertical"
    else
        default_layout="tiled"
    fi

    # Prompt user for layout choice
    echo "Available layouts:" >&2
    echo "  main-vertical   : One large left pane, others stacked right (default for ≤3 panes)" >&2
    echo "  main-horizontal : One large top pane, others stacked below" >&2
    echo "  tiled          : Grid arrangement (default for ≥4 panes)" >&2
    echo "  even-vertical  : Equal-height vertical splits" >&2
    echo "  even-horizontal: Equal-width horizontal splits" >&2
    echo "  <custom>       : Custom layout string" >&2
    echo "" >&2

    read -p "Layout [$default_layout]: " user_layout </dev/tty

    # Use default if user pressed Enter
    local layout="${user_layout:-$default_layout}"

    # Apply the layout
    if tmux select-layout -t ":$window_index" "$layout" 2>/dev/null; then
        echo "$layout"
        return 0
    else
        echo "Error: Failed to apply layout '$layout'" >&2
        echo "Falling back to default: $default_layout" >&2

        if tmux select-layout -t ":$window_index" "$default_layout" 2>/dev/null; then
            echo "$default_layout"
            return 0
        else
            echo "Error: Failed to apply fallback layout" >&2
            return 1
        fi
    fi
}

# Function: get_smart_default_layout
# Purpose: Calculate smart default layout based on pane count
# Inputs: $1 - Pane count
# Outputs: Layout name to stdout
# Exit codes: 0 always
get_smart_default_layout() {
    local pane_count="$1"

    if [ "$pane_count" -le 3 ]; then
        echo "main-vertical"
    else
        echo "tiled"
    fi

    return 0
}

# Function: validate_layout
# Purpose: Check if a layout name/string is valid
# Inputs: $1 - Layout name or string
# Outputs: Error message to stderr if invalid
# Exit codes: 0 if valid, 1 if invalid
validate_layout() {
    local layout="$1"

    # List of valid tmux layout names
    local valid_layouts="even-horizontal even-vertical main-horizontal main-vertical tiled"

    # Check if it's a named layout
    if echo "$valid_layouts" | grep -qw "$layout"; then
        return 0
    fi

    # Check if it's a custom layout string (starts with a layout ID pattern)
    if [[ "$layout" =~ ^[0-9a-f]+, ]]; then
        return 0
    fi

    echo "Error: Invalid layout '$layout'" >&2
    echo "Valid layouts: $valid_layouts" >&2
    echo "Or provide a custom layout string" >&2
    return 1
}
