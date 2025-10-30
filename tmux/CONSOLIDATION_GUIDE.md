# Tmux Window/Pane Consolidation and Rearrangement Guide

## Overview

The consolidation system provides two modes for organizing your tmux workspace:

- **Simple Mode** (default): Consolidate multiple single-pane windows into one multi-pane window
- **Complex Mode** (press 'c'): Rearrange any combination of panes into any window configuration

## Usage

Run the script from within tmux:
```bash
./consolidate-windows.sh
```

You'll be prompted to choose a mode:
- Press ENTER for Simple Mode
- Press 'c' for Complex Mode

## Simple Mode

### What it does
Consolidates multiple single-pane windows into a single window with multiple panes.

### Workflow
1. Select 2+ single-pane windows using fzf (TAB to multi-select)
2. First selected window becomes the target
3. Other windows are joined as panes to the target
4. Choose a layout (or use smart default)
5. Original windows are removed

### Example
```
Before:  Window 0 (vim)  |  Window 1 (shell)  |  Window 2 (logs)

After:   Window 0 (Consolidated)
         ┌─────────────┬──────┐
         │             │shell │
         │     vim     ├──────┤
         │             │logs  │
         └─────────────┴──────┘
```

### Limitations
- Only works with single-pane windows
- All panes consolidated into one window

## Complex Mode

### What it does
Allows you to select ANY panes from ANY windows and rearrange them into ANY window configuration.

### Workflow
1. View visual hierarchy of all windows and panes
   - See window structure with tree display
   - Pane counts, sizes, and commands shown
   - Press ENTER to proceed to selection
2. Select any panes using fzf (TAB to multi-select)
   - Works with panes from multi-pane windows
   - Can select panes from different windows
   - Window context shown for each pane
3. Specify how many windows you want to create
4. Assign each pane to a window group (interactive fzf)
5. Layouts are applied automatically
6. Empty windows are cleaned up

### Example 1: Split multi-pane window
```
Before:  Window 0
         ┌──────┬──────┐
         │pane 0│pane 1│
         ├──────┼──────┤
         │pane 2│pane 3│
         └──────┴──────┘

Select:  Panes 0, 1, 2, 3
Group:   Window 1: [0, 1]  |  Window 2: [2, 3]

After:   Window 0 (Arranged-1)  |  Window 1 (Arranged-2)
         ┌──────┬──────┐        ┌──────┬──────┐
         │pane 0│pane 1│        │pane 2│pane 3│
         └──────┴──────┘        └──────┴──────┘
```

### Example 2: Consolidate across windows
```
Before:  Window 0 (vim, htop, logs)  |  Window 1 (shell1, shell2)

Select:  Panes vim, shell1, shell2
Group:   Window 1: [vim, shell1, shell2]

After:   Window 0 (htop, logs)  |  Window 1 (Arranged-1)
                                   ┌─────────────┬────────┐
                                   │     vim     │shell1  │
                                   │             ├────────┤
                                   │             │shell2  │
                                   └─────────────┴────────┘
```

### Example 3: Complete reorganization
```
Before:  3 windows with various panes

Select:  8 panes across all windows
Group:   Window 1: [pane1, pane2]
         Window 2: [pane3, pane4, pane5]
         Window 3: [pane6, pane7, pane8]

After:   3 organized windows with custom groupings
```

## Features

### Selection
- **Visual hierarchy**: Tree view of all windows and their panes before selection
- **Window grouping**: Clear display of which panes belong to which windows
- **Pane details**: Size, command, title shown for each pane
- **fzf multi-select**: TAB to select, ENTER to confirm, ESC to cancel
- **Live preview**: See pane contents while selecting
- **Window context**: Each pane labeled with its source window

### Layout Options
- `main-vertical`: One large left pane, others stacked right (default ≤3 panes)
- `main-horizontal`: One large top pane, others stacked below
- `tiled`: Grid arrangement (default ≥4 panes)
- `even-vertical`: Equal-height vertical splits
- `even-horizontal`: Equal-width horizontal splits
- Custom layout strings supported

### Smart Defaults
- Automatically suggests best layout based on pane count
- Validates all selections before execution
- Cleans up empty windows automatically
- Preserves pane content and working directories

## Architecture

### Libraries
- `lib/window-selector.sh`: Simple mode window selection
- `lib/pane-selector.sh`: Complex mode pane selection
- `lib/pane-arranger.sh`: Complex mode grouping and execution
- `lib/pane-layout.sh`: Layout management (shared)

### Design Principles
- **Progressive disclosure**: Simple by default, complex when needed
- **Fail-fast validation**: Catch errors before execution
- **No data loss**: Validate everything, clean up safely
- **Intuitive UX**: Clear prompts, helpful previews, smart defaults

## Tips

### Simple Mode
- Create single-pane windows first if you need to consolidate multi-pane windows
- Or use Complex Mode to handle multi-pane windows directly

### Complex Mode
- Select panes from anywhere - different windows, multi-pane windows, etc.
- You can leave some panes behind (they stay in original window)
- Empty windows are automatically removed
- First pane in each group determines the base window

### General
- Use live preview to verify you're selecting the right panes
- Smart defaults usually work well for layouts
- You can always rearrange again if needed
- Press ESC at any selection to cancel safely

## Troubleshooting

### "Not enough single-pane windows"
In Simple Mode, you need at least 2 single-pane windows. Use Complex Mode to work with multi-pane windows.

### "Pane no longer exists"
The pane was closed or moved between selection and execution. Try again.

### Layout looks wrong
You can run the script again to rearrange, or use `tmux select-layout <name>` to change layout manually.

### Empty windows left behind
This shouldn't happen - empty windows are automatically cleaned up. Report as a bug if seen.
