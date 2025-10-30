# iOS Termius Tmux Shortcuts

## Primary Shortcuts (Work on iOS)

These shortcuts work directly in Termius on iOS without any modifier key issues:

| Shortcut | Action | Notes |
|----------|--------|-------|
| **Ctrl-g** | Show Menu | Replaces right-click menu, shows all options |
| **Ctrl-z** | Kill Pane | Close current pane immediately (iOS) |
| **Ctrl-x** | Kill Pane | Close current pane immediately (regular keyboards) |

## Menu Options (After pressing Ctrl-g)

Once you press Ctrl-g, a menu appears. Press the letter to select:

| Key | Action |
|-----|--------|
| **h** | Split Horizontal |
| **v** | Split Vertical |
| **f** | Fork Claude |
| **s** | SSH to Host |
| **d** | Git Diffs |
| **e** | Edit File |
| **n** | GPU Monitor |
| **t** | System Monitor |
| **x** | Kill This Pane |
| **z** | Zoom Toggle |
| **c** | Copy Mode |
| **p** | Paste Buffer |

## Additional Available Control Keys

If you want more direct shortcuts, these control keys are available:

- **Ctrl-l** (^l) - Currently clears screen
- **Ctrl-s** (^s) - Currently stops output (can be disabled)
- **Ctrl-r** (^r) - Currently reverse search in bash
- **Ctrl-n** (^n) - Currently next in bash history
- **Ctrl-p** (^p) - Currently previous in bash history

## How to Use

1. **To open the menu**: Press `Ctrl-g` from anywhere in tmux
2. **To close a pane**: Press `Ctrl-z` on iOS or `Ctrl-x` on regular keyboards
3. **To select from menu**: After pressing `Ctrl-g`, just press the letter (no Enter needed)

## Navigation

- Click/tap on panes to switch between them (mouse support is enabled)
- Use the menu (`Ctrl-g` then `z`) to zoom/unzoom a pane

## Why These Choices?

- **Ctrl-g**: Minimal conflict (just terminal bell), perfect for menu
- **Ctrl-z**: Works on iOS where Ctrl-x doesn't, overrides suspend (rarely used in tmux)
- **Ctrl-x**: Natural choice for "exit/close" on regular keyboards
- **No Shift needed**: iOS Termius handles single control keys better
- **No Alt needed**: Alt key not available on iOS

## TEST CHANGE FOR GIT DIFF
This line was added to test that git diffs work from current pane directory.