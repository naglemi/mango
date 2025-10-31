#!/bin/bash
set -euo pipefail

# Generate mobile menu configuration from menu items
# Creates touch-friendly grid: 4 columns x 5 rows = 20 slots per page
# Includes NEXT/PREV navigation if more than 18 items

MENU_CONFIG="$HOME/.tmux-menu-config.txt"
OUTPUT_DIR="$HOME/.tmux-mobile-menus"

if [ ! -f "$MENU_CONFIG" ]; then
    echo "ERROR: Menu configuration not found at $MENU_CONFIG"
    exit 1
fi

# Parse menu config to extract items
declare -a NAMES
declare -a KEYS
declare -a COMMANDS

while IFS= read -r line; do
    # Skip empty lines and lines with just backslash
    [[ -z "$line" || "$line" == "\\" ]] && continue

    # Extract quoted strings and key
    if [[ $line =~ \"([^\"]+)\"[[:space:]]+([a-zA-Z0-9])[[:space:]]+\"([^\"]+)\" ]]; then
        name="${BASH_REMATCH[1]}"
        key="${BASH_REMATCH[2]}"
        cmd="${BASH_REMATCH[3]}"

        # Skip empty divider lines
        [[ -z "$name" ]] && continue

        NAMES+=("$name")
        KEYS+=("$key")
        COMMANDS+=("$cmd")
    fi
done < "$MENU_CONFIG"

TOTAL_ITEMS=${#NAMES[@]}
ITEMS_PER_PAGE=18  # Leave 2 slots for NEXT/PREV
TOTAL_PAGES=$(( (TOTAL_ITEMS + ITEMS_PER_PAGE - 1) / ITEMS_PER_PAGE ))

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Function to generate a single page menu
generate_page() {
    local page_num=$1
    local output_file="$OUTPUT_DIR/page-${page_num}.conf"

    local start_idx=$(( (page_num - 1) * ITEMS_PER_PAGE ))
    local end_idx=$(( start_idx + ITEMS_PER_PAGE ))
    [[ $end_idx -gt $TOTAL_ITEMS ]] && end_idx=$TOTAL_ITEMS

    # Calculate next and prev page numbers (with wrapping)
    local next_page=$(( page_num % TOTAL_PAGES + 1 ))
    local prev_page=$(( page_num == 1 ? TOTAL_PAGES : page_num - 1 ))

    # Start building the menu command
    echo "display-menu -x C -y C -T \"MOBILE MENU - PAGE $page_num/$TOTAL_PAGES\" \\" > "$output_file"

    local col=0
    local items_added=0

    # Add menu items for this page
    for (( i=start_idx; i<end_idx; i++ )); do
        local name="${NAMES[$i]}"
        local key="${KEYS[$i]}"
        local cmd="${COMMANDS[$i]}"

        # Truncate long names to fit grid
        name=$(echo "$name" | cut -c1-18)

        # Format: "Name" key "command" \
        echo "    \"$name\" $key \"$cmd\" \\" >> "$output_file"

        items_added=$((items_added + 1))
    done

    # Add navigation buttons if multiple pages
    if [ $TOTAL_PAGES -gt 1 ]; then
        echo "    \"\" \"\" \"\" \\" >> "$output_file"
        echo "    \"<< PREV PAGE\" p \"run-shell 'tmux display-menu -x C -y C -T \\\"MOBILE MENU\\\" \$(cat $OUTPUT_DIR/page-${prev_page}.conf)'\" \\" >> "$output_file"
        echo "    \"NEXT PAGE >>\" n \"run-shell 'tmux display-menu -x C -y C -T \\\"MOBILE MENU\\\" \$(cat $OUTPUT_DIR/page-${next_page}.conf)'\"" >> "$output_file"
    else
        # Remove trailing backslash on last item if only one page
        sed -i '$ s/ \\$//' "$output_file"
    fi
}

# Generate all pages
for (( page=1; page<=TOTAL_PAGES; page++ )); do
    generate_page $page
done

# Create main entry point (page 1)
cp "$OUTPUT_DIR/page-1.conf" "$OUTPUT_DIR/main.conf"

echo "Generated $TOTAL_PAGES mobile menu page(s) in $OUTPUT_DIR"
echo "Main entry point: $OUTPUT_DIR/main.conf"
