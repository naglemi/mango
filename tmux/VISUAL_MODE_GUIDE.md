# Visual Pane Mover - Simple & Intuitive Guide

## The Problem with Lists and Hierarchies

Traditional approaches show you panes in lists or trees. But that's not how you think about your tmux workspace - you think **visually**. You don't think "pane 0.1 in the vim window", you think "THAT pane" (pointing at your screen).

## Visual Mode: How It Works

Visual Mode lets you work the way you naturally think:

1. **Pick a window** from a simple list
2. **See the actual layout** - script switches to that window
3. **tmux displays pane numbers** visually on each pane (using `display-panes`)
4. **Type the number you see** - that's your source pane
5. **Choose destination** - new window or existing window
6. **If existing, see that layout too** - pick where it goes
7. **Pane moves** - you see the result immediately
8. **Repeat** or finish

## Example Session

```
Available Windows:
  [0] vim (3 panes)
  [1] monitoring (2 panes)
  [2] logs (1 pane)

Which window contains the pane you want to move? 0

[Script switches to window 0]
[Your screen shows pane numbers overlaid on actual panes]

┌─────────────────────┬──────────────┐
│                     │      1       │
│         0           │    (bash)    │
│       (vim)         ├──────────────┤
│                     │      2       │
└─────────────────────┴──────────────┘

Which pane number do you want to move? 1

Where do you want to move pane 0.1?
  [n] New window
  [e] Existing window
Destination: e

Which window to join to? 2

[Script switches to window 2]
[You see the destination layout]

┌────────────────────────────────────┐
│               0                    │
│           (tail -f)                │
└────────────────────────────────────┘

 Moved: bash (pane 0.1) → window 2

[Window 2 now has both panes]

Move another pane? [y/n]: n

Done!
```

## Why This Is Better

### You See What You're Doing
- Actual layouts visible, not abstract lists
- Pane numbers appear on the panes themselves
- Navigate to windows to see them as they actually are

### Natural Mental Model
- "I want to move THAT pane" (point at screen)
- "To THAT window" (point at window list)
- No need to remember window.pane notation
- No confusion about hierarchy

### One at a Time
- Move one pane, see result, decide next move
- Clear cause and effect
- Easy to undo (just move it back)
- No overwhelming batch operations

### Leverages tmux Built-ins
- Uses `display-panes` - feature you already know
- Same pane numbers tmux shows normally
- Familiar navigation (script switches windows for you)

## Usage

Run from tmux:
```bash
./consolidate-windows.sh
```

Press `v` for Visual Mode (recommended)

## Tips

- **Take your time**: The script waits for you to look and decide
- **Pane numbers stay visible**: 5 seconds by default (configurable)
- **Empty windows auto-removed**: If you move the last pane, source window disappears
- **Works with any layout**: Doesn't matter how complex your window is
- **Safe to experiment**: Move panes around, see what works, move them again

## Comparison to Other Modes

### Simple Mode (ENTER)
- Quick consolidation of single-pane windows
- All-in-one operation
- Limited to single-pane windows only

### Visual Mode (v) - RECOMMENDED
- Move any pane to any window
- See layouts before and during selection
- One pane at a time, fully controlled
- Works with multi-pane windows

### Complex Mode (c)
- Batch operations - select many panes at once
- Assign to multiple window groups
- More powerful but more complex
- Good for major reorganizations

## When to Use Visual Mode

- Moving a few panes around
- Reorganizing your workspace
- You want to see what you're doing
- You prefer step-by-step control
- You're rearranging multi-pane windows

**In short: Use Visual Mode when you want to work naturally and visually with your panes.**
