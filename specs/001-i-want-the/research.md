# Research: Grid Dimension Calculation

**Purpose**: Calculate exact character width and line height for the tmux popup to perfectly fit the 4×5 mobile menu grid.

## Grid Layout Analysis

From `mobile-menu.sh` (lines 50-54):
```bash
COLS=4
ROWS=5
BTN_WIDTH=12
BTN_HEIGHT=6
```

## Header Lines

From `mobile-menu.sh` (lines 59-61):
```bash
echo "PAGE $CURRENT_PAGE/$TOTAL_PAGES"  # Line 1
echo ""                                  # Line 2 (blank)
```

**Header total**: 2 lines

## Grid Rendering Logic

### Width Calculation

Each row renders borders as follows (lines 66-74):
```bash
for (( col=0; col<COLS; col++ )); do
    printf "+"                           # Left border
    for (( i=0; i<BTN_WIDTH; i++ )); do
        printf "-"                       # Button width (12 chars)
    done
    if [ $col -eq $((COLS - 1)) ]; then
        printf "+"                       # Right border (last column)
    else
        printf "+ "                      # Right border + space (between columns)
    fi
done
```

**Per column breakdown**:
- Column 0: `+` (1) + 12 dashes + `+` (1) + space (1) = 15 chars
- Column 1: `+` (1) + 12 dashes + `+` (1) + space (1) = 15 chars
- Column 2: `+` (1) + 12 dashes + `+` (1) + space (1) = 15 chars
- Column 3: `+` (1) + 12 dashes + `+` (1) = 14 chars (no trailing space)

**Total width**: 15 + 15 + 15 + 14 = **59 characters**

### Height Calculation

From `mobile-menu.sh` (lines 64-232):

Each row consists of:
1. Top border line (1 line) - the `+----+` pattern
2. Button content (6 lines) - from BTN_HEIGHT=6
3. No explicit spacing between rows - next row's top border immediately follows previous row's bottom border

Wait, looking more carefully at the loop structure:
- Lines 64-232 is a single loop `for (( row=0; row<ROWS; row++ ))`
- Line 65-75: Draw top border (1 line)
- Lines 77-218: Draw button content (6 lines via inner loop `for (( line=0; line<BTN_HEIGHT; line++ ))`)
- Lines 220-229: Draw bottom border (1 line)
- Line 231: Add newline between rows `[ $row -ne $((ROWS - 1)) ] && echo ""`

So each row is:
- Top border: 1 line
- Content: 6 lines (BTN_HEIGHT)
- Bottom border: 1 line
- Spacing: 1 blank line (except after last row)

**Per row breakdown**:
- Row 0: top (1) + content (6) + bottom (1) + spacing (1) = 9 lines
- Row 1: top (1) + content (6) + bottom (1) + spacing (1) = 9 lines
- Row 2: top (1) + content (6) + bottom (1) + spacing (1) = 9 lines
- Row 3: top (1) + content (6) + bottom (1) + spacing (1) = 9 lines
- Row 4: top (1) + content (6) + bottom (1) + no spacing = 8 lines

Wait, this doesn't look right. Let me re-read the code...

Actually, looking at lines 220-231:
```bash
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
```

The bottom border is drawn INSIDE each row iteration. So the structure is:
- FOR each row (0-4):
  - Print top border (1 line)
  - Print 6 lines of button content
  - Print bottom border (1 line) - BUT WAIT, this shares with the next row's top border!

Actually no, re-reading more carefully... The loop draws:
1. Top border of row
2. 6 lines of content
3. (next iteration draws top border again, which serves as bottom border of previous row)

Looking at line 64-75 (top border) and 220-231 (bottom border), they're both drawn in the same iteration. So each row draws its own complete box.

Let me trace through what gets printed:

**Row 0**:
- Line 65-75: Top border (1 line with echo at line 75)
- Lines 78-217: 6 iterations of button content (6 lines, each ending with echo at line 217)
- Lines 221-229: Bottom border (1 line printed)
- Line 231: Conditional newline (adds 1 line since row != 4)

So Row 0 prints: 1 + 6 + 1 + 1 = 9 lines
Rows 1-3 also print: 9 lines each
Row 4 prints: 1 + 6 + 1 + 0 = 8 lines (no trailing newline)

**Total height**: 2 (header) + 9 + 9 + 9 + 9 + 8 = **46 lines**

## Final Dimensions

**Width**: 59 characters
**Height**: 46 lines

## Implementation

Current line in `tmux/tmux.conf.template` (line 141):
```bash
bind -n MouseDown1StatusRight display-popup -E -x 0 -y 0 -w 100% -h 100% '$HOME/usability/tmux/mobile-menu.sh'
```

New line:
```bash
bind -n MouseDown1StatusRight display-popup -E -x 0 -y 0 -w 59 -h 46 '$HOME/usability/tmux/mobile-menu.sh'
```

## Verification Checklist

After implementation, verify:
1. ✓ Popup width is exactly 59 characters
2. ✓ Popup height is exactly 46 lines
3. ✓ No blank space visible on right edge
4. ✓ No blank space visible on bottom edge
5. ✓ Terminal content visible beyond popup edges
6. ✓ All 20 icon buttons remain clickable
7. ✓ Mouse coordinate calculations still work correctly
8. ✓ Top/left positioning unchanged
