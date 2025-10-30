# Claude Code Progress Indicator Fix for TMUX

## The Problem

When running Claude Code inside TMUX, progress indicators create cascading repeated lines instead of updating in-place. Each spinner update, percentage increment, or status message creates a new line, making the scrollback buffer nearly unusable.

### Example of the Issue:
```
Thinking... /
Thinking... -
Thinking... \
Thinking... |
Thinking... /
(repeated hundreds of times instead of a single spinning line)
```

## Why This Happens

TMUX sits between your terminal and applications, translating escape sequences between two different terminal emulation standards. When the `TERM` environment variable inside TMUX is incorrectly set (typically inheriting `xterm-256color` from your outer terminal), applications send carriage return (`\r`) sequences that TMUX doesn't properly recognize.

**The carriage return issue:**
- Applications expect `\r` to move the cursor to the start of the current line
- With wrong TERM type, TMUX treats each `\r` as a new line
- Result: cascading output instead of in-place updates

This affects:
- Claude Code's TUI framework
- Python's tqdm progress bars
- Node.js spinner libraries (ora, etc.)
- Any CLI tool using dynamic progress indicators

## The Solution

Set TMUX's `default-terminal` to `tmux-256color` (or `screen-256color` on older systems) so applications use TMUX-compatible escape sequences.

### What Was Changed

Added to `~/.tmux.conf` and `~/usability/tmux/tmux.conf`:

```bash
# Set proper terminal type to fix carriage return issues in TUI apps
# This prevents Claude Code, tqdm, ora, and other progress indicators from creating cascading lines
# tmux-256color tells apps to use tmux-compatible escape sequences instead of xterm
set -g default-terminal "tmux-256color"
```

Also added a convenient reload binding:
```bash
# Reload config with prefix+r
bind r source-file ~/.tmux.conf \; display-message "Config reloaded!"
```

## How to Apply the Fix

### For New Sessions (Recommended)
The fix is already in place! Just create a new tmux session or window:
```bash
# Start a new tmux session
tmux new -s test

# Inside tmux, verify TERM is correct
echo $TERM
# Should show: tmux-256color
```

### For Existing Panes
The TERM variable is set when a pane is created, so existing panes won't automatically update. Options:

**Option 1: Create a new pane** (Quick)
```bash
# Inside tmux: Ctrl+b then | (or -)
# New pane will have correct TERM
```

**Option 2: Restart TMUX entirely** (Complete)
```bash
# Exit all tmux sessions
exit  # repeat for each pane/window

# Or force kill (loses unsaved work!)
tmux kill-server

# Start fresh
tmux new -s main
```

**Option 3: Manual TERM override** (Temporary)
```bash
# Inside existing pane
export TERM=tmux-256color
# Only affects current shell session
```

### For Systems Without tmux-256color terminfo

Older systems might not have the `tmux-256color` terminfo entry. If you get errors about unknown terminal type:

1. Edit both config files:
   ```bash
   vim ~/.tmux.conf
   vim ~/usability/tmux/tmux.conf
   ```

2. Change the line to:
   ```bash
   set -g default-terminal "screen-256color"
   ```

3. Reload or restart tmux

## Verification

Check if the fix is working:

```bash
# 1. Check tmux configuration
tmux show-options -g default-terminal
# Should show: tmux-256color

# 2. Check TERM inside tmux
echo $TERM
# Should show: tmux-256color (or screen-256color)

# 3. Test with Claude Code
claude --continue
# Progress indicators should update in-place, not cascade
```

## Technical Details

### Why This Affects Claude Code More

Claude Code uses a sophisticated Terminal User Interface (TUI) framework with frequent status updates:
- "Thinking" indicators
- File listing operations
- Compilation progress
- Tool execution status

Every status update sends a `\r` (carriage return) to return to the start of the line and overwrite the previous text. With the wrong terminal type, each update becomes a new line, generating massive scrollback.

### The TMUX Connection Pattern

1. **Outer terminal** (your SSH client/terminal app) sets `TERM=xterm-256color`
2. **TMUX server** intercepts all terminal I/O
3. **Applications inside TMUX** check `TERM` to know which escape sequences to send
4. If `TERM=xterm-256color`, apps send xterm escape codes
5. TMUX's terminal emulator (screen/tmux) doesn't fully implement xterm codes
6. Result: `\r` doesn't work as expected

### The Fix Explained

Setting `default-terminal "tmux-256color"`:
- Tells apps: "You're running under tmux, use tmux escape codes"
- TMUX's terminal emulator correctly handles tmux/screen codes
- `\r` now properly returns cursor to line start
- In-place updates work correctly

## Related Issues

This is a well-known issue:
- TMUX GitHub issue #4004: CR fails in vertical splits
- Python tqdm issues #760, #1315: Progress bars create spam in tmux
- Node.js ora: Similar spinner issues documented

## Troubleshooting

**Still seeing cascading lines?**

1. Verify config loaded:
   ```bash
   tmux show-options -g default-terminal
   ```

2. Check you're in a NEW pane/session:
   ```bash
   echo $TERM
   # Should NOT be xterm-256color or screen
   ```

3. Try screen-256color instead if tmux-256color unavailable:
   ```bash
   # Edit config
   set -g default-terminal "screen-256color"
   # Restart tmux
   ```

4. Check for conflicting config:
   ```bash
   # Look for other default-terminal settings
   grep default-terminal ~/.tmux.conf
   ```

**Colors look wrong?**

The config includes proper terminal-overrides for true color (RGB) support, so colors should work correctly even with tmux-256color. If not:

```bash
# Verify RGB support
tmux show-options -gA terminal-overrides | grep -i rgb
# Should show multiple RGB entries
```

## References

- [TMUX Manual - default-terminal](https://man7.org/linux/man-pages/man1/tmux.1.html)
- [Terminal Type Database - tmux-256color](https://invisible-island.net/ncurses/terminfo.src.html)
- [TMUX Issue #4004 - Carriage Return in Vertical Splits](https://github.com/tmux/tmux/issues/4004)
- [tqdm Issue #760 - TMUX Progress Bar Issues](https://github.com/tqdm/tqdm/issues/760)

## Quick Reference

```bash
# Apply fix to new session
tmux new -s work

# Reload config in existing session
# (press: Ctrl+b then r)
# or:
tmux source-file ~/.tmux.conf

# Verify it worked
echo $TERM  # in NEW pane

# Full restart (if needed)
tmux kill-server && tmux new -s main
```
