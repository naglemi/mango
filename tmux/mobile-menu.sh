#!/bin/bash
# Touch-friendly mobile menu with 4x5 grid of SQUARE buttons
# Mouse/touch only - no keyboard shortcuts

MENU_CONFIG="$HOME/.tmux-menu-config.txt"

if [ ! -f "$MENU_CONFIG" ]; then
    clear
    echo "ERROR: Menu configuration not found"
    sleep 2
    exit 1
fi

# Parse menu items
declare -a NAMES
declare -a KEYS
declare -a COMMANDS

while IFS= read -r line; do
    [[ -z "$line" || "$line" == "\\" ]] && continue
    # Parse: "emoji name" key "command" \
    if [[ $line =~ ^[[:space:]]*\"([^\"]+)\"[[:space:]]+([a-zA-Z0-9])[[:space:]]+(.*)$ ]]; then
        name="${BASH_REMATCH[1]}"
        key="${BASH_REMATCH[2]}"
        cmd_part="${BASH_REMATCH[3]}"
        # Remove trailing backslash
        cmd_part="${cmd_part% \\\\}"
        cmd_part="${cmd_part% \\}"
        # Extract command
        if [[ $cmd_part =~ ^\"(.*)\"$ ]]; then
            cmd="${BASH_REMATCH[1]}"
            [[ -z "$name" ]] && continue
            NAMES+=("$name")
            KEYS+=("$key")
            COMMANDS+=("$cmd")
        fi
    fi
done < "$MENU_CONFIG"

TOTAL_ITEMS=${#NAMES[@]}
# Reserve last slot on each page for EXIT button
ITEMS_PER_PAGE=17
CURRENT_PAGE=${1:-1}
TOTAL_PAGES=$(( (TOTAL_ITEMS + ITEMS_PER_PAGE - 1) / ITEMS_PER_PAGE ))

START_IDX=$(( (CURRENT_PAGE - 1) * ITEMS_PER_PAGE ))
END_IDX=$(( START_IDX + ITEMS_PER_PAGE ))
[[ $END_IDX -gt $TOTAL_ITEMS ]] && END_IDX=$TOTAL_ITEMS

# SQUARE buttons: chars are 2x taller than wide, so 12 wide × 6 tall = square
COLS=4
ROWS=5
BTN_WIDTH=12
BTN_HEIGHT=6

# Reserve last slot for EXIT button
RESERVED_SLOTS=1

clear
echo "PAGE $CURRENT_PAGE/$TOTAL_PAGES"
echo ""

# Draw grid
for (( row=0; row<ROWS; row++ )); do
    # Top border
    for (( col=0; col<COLS; col++ )); do
        printf "+"
        for (( i=0; i<BTN_WIDTH; i++ )); do printf "-"; done
        if [ $col -eq $((COLS - 1)) ]; then
            printf "+"
        else
            printf "+ "
        fi
    done
    echo ""

    # Button content
    for (( line=0; line<BTN_HEIGHT; line++ )); do
        for (( col=0; col<COLS; col++ )); do
            slot=$(( row * COLS + col ))
            actual_idx=$(( START_IDX + slot ))

            # Navigation buttons on last row - dashed border: NO delimiters on lines 0,2,4
            if [ $TOTAL_PAGES -gt 1 ] && [ $row -eq 4 ]; then
                if [ $col -eq 0 ]; then
                    if [ $line -eq 0 ] || [ $line -eq 2 ] || [ $line -eq 4 ]; then
                        if [ $line -eq 2 ]; then
                            text="< PREV"
                            len=${#text}
                            pad=$(( (BTN_WIDTH - len) / 2 ))
                            printf " %*s%s%*s " $pad "" "$text" $(( BTN_WIDTH - len - pad )) ""
                        else
                            printf " %*s " $BTN_WIDTH ""
                        fi
                    else
                        printf "|            |"
                    fi
                    [ $col -ne $((COLS - 1)) ] && printf " "
                    continue
                elif [ $col -eq 3 ]; then
                    if [ $line -eq 0 ] || [ $line -eq 2 ] || [ $line -eq 4 ]; then
                        if [ $line -eq 2 ]; then
                            text="NEXT >"
                            len=${#text}
                            pad=$(( (BTN_WIDTH - len) / 2 ))
                            printf " %*s%s%*s " $pad "" "$text" $(( BTN_WIDTH - len - pad )) ""
                        else
                            printf " %*s " $BTN_WIDTH ""
                        fi
                    else
                        printf "|            |"
                    fi
                    [ $col -ne $((COLS - 1)) ] && printf " "
                    continue
                fi
            fi

            # Check if this is the EXIT button slot (last slot on page)
            if [ $slot -eq 17 ]; then
                # EXIT button - dashed border: NO delimiters on lines 0,2,4 (odd lines 1,3,5)
                if [ $line -eq 0 ]; then
                    emoji="🚪"
                    len=${#emoji}
                    pad=$(( (BTN_WIDTH - len) / 2 ))
                    printf " %*s%s%*s " $pad "" "$emoji" $(( BTN_WIDTH - len - pad )) ""
                elif [ $line -eq 1 ]; then
                    printf "|    EXIT    |"
                elif [ $line -eq 2 ]; then
                    # Empty dashed line: 1 space + 12 chars + 1 space = 14 chars
                    printf " %*s " $BTN_WIDTH ""
                elif [ $line -eq 3 ]; then
                    printf "|            |"
                elif [ $line -eq 4 ]; then
                    shortcut="(q)"
                    len=${#shortcut}
                    pad=$(( (BTN_WIDTH - len) / 2 ))
                    printf " %*s%s%*s " $pad "" "$shortcut" $(( BTN_WIDTH - len - pad )) ""
                else
                    printf "|            |"
                fi
                [ $col -ne $((COLS - 1)) ] && printf " "
            elif [ $actual_idx -lt $END_IDX ]; then
                # Regular item - name format is "emoji text"
                name="${NAMES[$actual_idx]}"
                key="${KEYS[$actual_idx]}"

                # Extract emoji (before first space) and text (after first space)
                # This handles emojis that are 1 char (🪟) vs 2 chars (➡️ with variation selector)
                emoji="${name%% *}"
                text="${name#* }"

                # Split text by spaces for multi-line display
                IFS=' ' read -ra words <<< "$text"

                # Dashed border: NO delimiters on lines 0,2,4 (odd lines 1,3,5)
                if [ $line -eq 0 ]; then
                    # Line 0: emoji (no delimiters, centered in BTN_WIDTH with 1 space padding on each side)
                    len=${#emoji}
                    pad=$(( (BTN_WIDTH - len) / 2 ))
                    printf " %*s%s%*s " $pad "" "$emoji" $(( BTN_WIDTH - len - pad )) ""
                elif [ $line -eq 1 ]; then
                    # Line 1: first title word (with delimiters)
                    if [ ${#words[@]} -gt 0 ]; then
                        word="${words[0]}"
                        word=$(echo "$word" | cut -c1-$BTN_WIDTH)
                        len=${#word}
                        pad=$(( (BTN_WIDTH - len) / 2 ))
                        printf "|%*s%s%*s|" $pad "" "$word" $(( BTN_WIDTH - len - pad )) ""
                    else
                        printf "|            |"
                    fi
                elif [ $line -eq 2 ]; then
                    # Line 2: second title word (no delimiters, centered in BTN_WIDTH with 1 space padding)
                    if [ ${#words[@]} -gt 1 ]; then
                        word="${words[1]}"
                        word=$(echo "$word" | cut -c1-$BTN_WIDTH)
                        len=${#word}
                        pad=$(( (BTN_WIDTH - len) / 2 ))
                        printf " %*s%s%*s " $pad "" "$word" $(( BTN_WIDTH - len - pad )) ""
                    else
                        # Empty line: 1 space + 12 chars + 1 space = 14 chars
                        printf " %*s " $BTN_WIDTH ""
                    fi
                elif [ $line -eq 3 ]; then
                    # Line 3: third title word (with delimiters)
                    if [ ${#words[@]} -gt 2 ]; then
                        word="${words[2]}"
                        word=$(echo "$word" | cut -c1-$BTN_WIDTH)
                        len=${#word}
                        pad=$(( (BTN_WIDTH - len) / 2 ))
                        printf "|%*s%s%*s|" $pad "" "$word" $(( BTN_WIDTH - len - pad )) ""
                    else
                        printf "|            |"
                    fi
                elif [ $line -eq 4 ]; then
                    # Line 4: keyboard shortcut (no delimiters, centered in BTN_WIDTH with 1 space padding)
                    shortcut="($key)"
                    len=${#shortcut}
                    pad=$(( (BTN_WIDTH - len) / 2 ))
                    printf " %*s%s%*s " $pad "" "$shortcut" $(( BTN_WIDTH - len - pad )) ""
                else
                    # Line 5: empty (with delimiters)
                    printf "|            |"
                fi
                [ $col -ne $((COLS - 1)) ] && printf " "
            else
                # Empty slot - dashed border: NO delimiters on lines 0,2,4
                if [ $line -eq 0 ] || [ $line -eq 2 ] || [ $line -eq 4 ]; then
                    # Empty dashed line: 1 space + 12 chars + 1 space = 14 chars
                    printf " %*s " $BTN_WIDTH ""
                else
                    printf "|            |"
                fi
                [ $col -ne $((COLS - 1)) ] && printf " "
            fi
        done
        echo ""
    done

    # Bottom border
    for (( col=0; col<COLS; col++ )); do
        printf "+"
        for (( i=0; i<BTN_WIDTH; i++ )); do printf "-"; done
        if [ $col -eq $((COLS - 1)) ]; then
            printf "+"
        else
            printf "+ "
        fi
    done
    # Add newline between rows, but not after the very last row
    [ $row -ne $((ROWS - 1)) ] && echo ""
done

# Disable echo to prevent mouse sequences from appearing
stty -echo 2>/dev/null

# Enable mouse - only button press events
printf '\033[?1000h\033[?1006h'
trap 'stty echo 2>/dev/null; printf "\033[?1000l\033[?1006l"; exit 0' EXIT INT TERM

# Read mouse and keyboard events
while true; do
    IFS= read -r -d '' -n 1 c

    # Handle keyboard shortcuts
    if [[ "$c" == "q" ]] || [[ "$c" == "Q" ]]; then
        exit 0
    fi

    # Check if pressed key matches any menu item
    for i in "${!KEYS[@]}"; do
        if [[ "$c" == "${KEYS[$i]}" ]]; then
            cmd="${COMMANDS[$i]}"
            cmd="${cmd//\$HOME/$HOME}"
            eval "tmux $cmd"
            exit 0
        fi
    done

    if [[ "$c" == $'\033' ]]; then
        IFS= read -r -d '' -n 1 c2
        if [[ "$c2" == "[" ]]; then
            IFS= read -r -d '' -n 1 c3
            if [[ "$c3" == "<" ]]; then
                # Read rest of mouse sequence until M or m
                seq=""
                while IFS= read -r -d '' -n 1 ch; do
                    seq+="$ch"
                    [[ "$ch" == "M" || "$ch" == "m" ]] && break
                done

                # Only process press (M), not release (m)
                [[ ! $seq =~ M$ ]] && continue

                if [[ $seq =~ ([0-9]+)\;([0-9]+)\;([0-9]+)M ]]; then
                    raw_x="${BASH_REMATCH[2]}"
                    raw_y="${BASH_REMATCH[3]}"

                    # Mouse coordinates are 1-indexed, convert to 0-indexed
                    x=$(( raw_x - 1 ))
                    y=$(( raw_y - 1 ))

                    # DEBUG
                    echo "Raw click: x=$raw_x y=$raw_y -> Adjusted: x=$x y=$y" > /tmp/mobile-menu-debug.log

                    # Calculate grid position
                    # Line 0: "PAGE x/y"
                    # Line 1: ""
                    # Line 2: starts grid (first + border)

                    # Subtract header lines (2)
                    adj_y=$(( y - 2 ))

                    # Each row is: 1 top border + 6 content + 1 bottom border = 8 lines
                    grid_row=$(( adj_y / 8 ))

                    # Each column: x=0-14 is col0, x=15-29 is col1, x=30-44 is col2, x=45-59 is col3
                    grid_col=$(( x / 15 ))

                    echo "Calculated: adj_y=$adj_y grid_row=$grid_row grid_col=$grid_col" >> /tmp/mobile-menu-debug.log

                    # Bounds check
                    if [ $grid_row -lt 0 ] || [ $grid_row -ge $ROWS ] || [ $grid_col -lt 0 ] || [ $grid_col -ge $COLS ]; then
                        echo "OUT OF BOUNDS" >> /tmp/mobile-menu-debug.log
                        continue
                    fi

                    # Check for navigation
                    echo "TOTAL_PAGES=$TOTAL_PAGES grid_row=$grid_row grid_col=$grid_col" >> /tmp/mobile-menu-debug.log
                    if [ $TOTAL_PAGES -gt 1 ] && [ $grid_row -eq 4 ]; then
                        echo "In navigation check" >> /tmp/mobile-menu-debug.log
                        if [ $grid_col -eq 0 ]; then
                            echo "PREV button clicked" >> /tmp/mobile-menu-debug.log
                            new_page=$(( CURRENT_PAGE == 1 ? TOTAL_PAGES : CURRENT_PAGE - 1 ))
                            exec "$0" $new_page
                        elif [ $grid_col -eq 3 ]; then
                            echo "NEXT button clicked" >> /tmp/mobile-menu-debug.log
                            new_page=$(( CURRENT_PAGE == TOTAL_PAGES ? 1 : CURRENT_PAGE + 1 ))
                            exec "$0" $new_page
                        fi
                    fi

                    # Calculate slot
                    slot=$(( grid_row * COLS + grid_col ))
                    echo "Calculated slot=$slot" >> /tmp/mobile-menu-debug.log

                    # Check if EXIT button clicked (slot 17)
                    if [ $slot -eq 17 ]; then
                        echo "EXIT button clicked, exiting..." >> /tmp/mobile-menu-debug.log
                        exit 0
                    fi

                    # Execute command for regular items
                    idx=$(( START_IDX + slot ))

                    if [ $idx -ge $START_IDX ] && [ $idx -lt $END_IDX ]; then
                        cmd="${COMMANDS[$idx]}"
                        # Expand $HOME but keep #{...} for tmux to evaluate
                        cmd="${cmd//\$HOME/$HOME}"

                        # Special case: Close Pane in mobile menu should close immediately without confirmation
                        if [[ "$cmd" == *"display-menu -T 'Close Pane?'"* ]]; then
                            cmd="kill-pane"
                        fi

                        # Special case: nvim, lazygit, and spectator open in new-window from icon menu
                        name="${NAMES[$idx]}"
                        if [[ "$name" == *"Neovim"* ]]; then
                            cmd="new-window -c '#{pane_current_path}' 'nvim'"
                        elif [[ "$name" == *"Lazygit"* ]]; then
                            cmd="new-window -c '#{pane_current_path}' 'lazygit'"
                        elif [[ "$name" == *"Spectator"* ]]; then
                            cmd="new-window -c '#{pane_current_path}' '$HOME/mango/tmux/spectator.sh #{pane_current_path}'"
                        fi

                        echo "Executing command for idx=$idx: tmux $cmd" >> /tmp/mobile-menu-debug.log
                        # Use eval to let tmux expand #{pane_current_path} etc
                        eval "tmux $cmd" 2>> /tmp/mobile-menu-debug.log
                        echo "Command exit code: $?" >> /tmp/mobile-menu-debug.log
                        exit 0
                    fi
                fi
            fi
        fi
    fi
done
