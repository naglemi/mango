# Tmux Module

Terminal multiplexer configuration for productive development environments.

## Overview

This module provides:
- Optimized tmux configuration with mouse support
- Bash integration for automatic session management
- Quick aliases for common operations
- Visual indicators for active sessions

## What is tmux?

tmux is a terminal multiplexer that lets you:
- Run multiple terminal sessions in one window
- Detach and reattach sessions (they keep running!)
- Split panes horizontally and vertically  
- Switch between multiple projects easily
- Survive SSH disconnections

## Setup

### Quick Install
```bash
# Install tmux config and bash integration
cd tmux/
./setup-tmux.sh      # Installs tmux.conf
./setup-bashrc.sh    # Adds bash helpers (optional)
```

### Manual Install
```bash
# Just want the tmux config?
cp tmux/tmux.conf ~/.tmux.conf

# Just want the bash integration?
cat tmux/bashrc_additions >> ~/.bashrc
source ~/.bashrc
```

## Features

### Mouse Support
- Click to select panes
- Drag pane borders to resize
- Scroll with mouse wheel
- Select text for copying

### Status Bar
- Shows all sessions
- Current session highlighted
- Window list with activity indicators
- Clean, minimal design

### Key Bindings
Default prefix is `Ctrl-b`, then:

| Key | Action |
|-----|--------|
| `c` | Create new window |
| `n` | Next window |
| `p` | Previous window |
| `d` | Detach session |
| `s` | List sessions |
| `%` | Split vertically |
| `"` | Split horizontally |
| `arrow` | Navigate panes |
| `z` | Zoom pane (toggle) |

### Bash Integration

The bashrc additions provide:

1. **Auto-attach on SSH login** (optional)
   ```bash
   # When you SSH in, you'll see:
   # You have active tmux sessions:
   #   main: 2 windows (created Mon Dec 18 10:30:15 2023)
   #   dev: 1 windows (created Mon Dec 18 09:15:22 2023)
   # 
   # Attach to a session? [y/N]:
   ```

2. **Quick aliases**
   ```bash
   tm          # Attach to 'main' or create it
   tm work     # Attach to 'work' or create it
   tls         # List all sessions with details
   ```

## Usage Examples

### Example 1: Basic Development
```bash
# Start a new session for your project
tmux new -s myproject

# Split window for editor and terminal
Ctrl-b %                    # Split vertically
vim myfile.py              # Editor in left pane
Ctrl-b arrow-right         # Move to right pane
python myfile.py           # Run code in right pane

# Detach and come back later
Ctrl-b d                   # Detach
tmux attach -t myproject   # Reattach
```

### Example 2: Multiple Projects
```bash
# Project 1
tm project1
# ... work on project 1 ...
Ctrl-b d

# Project 2  
tm project2
# ... work on project 2 ...
Ctrl-b d

# See all sessions
tls
# main: 1 windows (created Mon Dec 18 10:30:15 2023) (attached)
# project1: 3 windows (created Mon Dec 18 11:45:00 2023)
# project2: 2 windows (created Mon Dec 18 14:20:33 2023)

# Quick switch
tm project1    # Back to project 1
```

### Example 3: Remote Development
```bash
# SSH to server
ssh myserver

# Auto-attach prompt appears
# Attach to a session? [y/N]: y
# Which session? main

# Or create new session
tm development

# Work normally - survives disconnection!
# If SSH drops, just reconnect and tm development
```

### Example 4: Pane Layouts
```bash
# Create a 4-pane development layout
tmux new -s dev

# Split into 4 panes
Ctrl-b %           # Split vertically
Ctrl-b "           # Split horizontally  
Ctrl-b arrow-left  # Go to left pane
Ctrl-b "           # Split horizontally again

# Now you have:
# | vim  | logs |
# | test | git  |

# Save this layout
Ctrl-b d
# Your layout persists!
```

## Tips & Tricks

### Copy Mode
1. Enter copy mode: `Ctrl-b [`
2. Navigate with arrow keys
3. Start selection: `Space`
4. Copy selection: `Enter`
5. Paste: `Ctrl-b ]`

### Window Management
```bash
# Rename current window
Ctrl-b ,

# Kill current pane
Ctrl-b x

# Kill current window
Ctrl-b &
```

### Session Management
```bash
# Create session in background
tmux new -s background -d

# Send commands to session
tmux send-keys -t background "npm run build" Enter

# Kill session
tmux kill-session -t background
```

## Configuration Details

The included `tmux.conf` provides:

```bash
# Mouse support
set -g mouse on

# Start windows at 1 (easier to reach)
set -g base-index 1

# Faster command sequences
set -s escape-time 0

# More history
set -g history-limit 10000

# Better colors
set -g default-terminal "screen-256color"

# Status bar styling
set -g status-bg black
set -g status-fg white
# ... and more
```

## Troubleshooting

**Q: Claude Code (or tqdm/ora) progress indicators creating cascading lines?**
A: This happens when TERM is incorrectly set inside tmux. The fix is already included in our tmux.conf with `set -g default-terminal "tmux-256color"`. If you're still seeing the issue:
1. Restart tmux completely: `tmux kill-server` then start a new session
2. Check inside tmux: `echo $TERM` should show `tmux-256color`, not `xterm-256color`
3. If using an older system without tmux terminfo, change the line to `set -g default-terminal "screen-256color"`

**Q: Mouse not working?**
A: Make sure you have tmux 2.1+. Check with `tmux -V`.

**Q: Copy/paste not working?**
A: Hold `Shift` while selecting for terminal copy (bypasses tmux).

**Q: Sessions lost after reboot?**
A: tmux sessions don't persist across reboots. Consider `tmux-resurrect` plugin.

**Q: Weird characters/colors?**
A: Make sure your terminal supports 256 colors. Our config sets this automatically.

## Advanced Usage

### Synchronized Panes
```bash
# Type in all panes simultaneously
Ctrl-b :
setw synchronize-panes on
```

### Session Scripts
```bash
#!/bin/bash
# dev-session.sh
tmux new-session -d -s dev
tmux send-keys -t dev "cd ~/project" Enter
tmux split-window -h -t dev
tmux send-keys -t dev "npm run watch" Enter
tmux select-pane -t dev:0.0
tmux attach -t dev
```

## Files in This Module

- `tmux.conf` - Main tmux configuration
- `bashrc_additions` - Bash integration helpers
- `setup-tmux.sh` - Installs tmux config
- `setup-bashrc.sh` - Installs bash helpers
- `README.md` - This file