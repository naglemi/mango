# Tmux Interactive Installation Guide

## Overview

The tmux installation system now supports two modes:
1. **Developer Mode** - Full configuration with ALL menu items (use `--developer` flag)
2. **Public Mode** - Interactive configuration with reasonable defaults for general users (default)

## Installation Modes

### Developer Mode (Explicit)

When you run the installer with `--developer` flag:
- Installs the **complete** tmux configuration
- Includes ALL menu items (training, GPU monitoring, EC2, SLURM, etc.)
- No interactive configuration
- Full feature set enabled immediately

**Usage:** `./setup-tmux.sh --developer`

### Public Mode (Interactive - Default)

When you run the installer without flags:
- Shows an interactive fzf menu
- Lets users select which features they want
- Provides reasonable defaults (excludes ML/server-specific items)
- Generates a customized tmux.conf based on selections

**Usage:** `./setup-tmux.sh`

## Menu Items

### Core Items (Always Included)
These are fundamental tmux operations, always enabled:
- New Window
- Next Window
- Break to Window
- Consolidate Windows
- Close Pane
- Rename Pane
- Split Horizontal
- Split Vertical

### General Tools (Default: ON)
Basic productivity tools useful for everyone:
- Edit File (vim/nvim file selector)
- Grab Files (interactive file collector)
- Copy Buffer (buffer management)
- Lazygit (git GUI)
- Settings (configuration menu)
- Plugin Manager (TPM management)

### Claude AI Tools (Default: ON)
For Claude Code users:
- Fork Claude (start new conversation pane)
- Hook Manager (manage Claude Code hooks)
- CLAUDE.md (edit project instructions)
- Ask LLM (interactive LLM chat)

### System Monitoring (Default: ON for htop, OFF for glances)
- System Monitor (htop)
- Glances Monitor (alternative system monitor)

### Remote Access (Default: ON)
- SSH to Host (interactive SSH host selector)

### Machine Learning / GPU (Default: OFF)
For deep learning and GPU work:
- Train Model (training launcher)
- W&B Monitor (Weights & Biases dashboard)
- NVTOP Monitor (GPU monitoring)
- GPUstat Compact (compact GPU stats)

### Server Management (Default: OFF)
For HPC and cloud infrastructure:
- EC2 SSH (AWS EC2 instance selector)
- SLURM Jobs (HPC job management)
- Spectator (session spectator)

## How to Run Installation

### Fresh Installation

```bash
cd ~/mango
./setup.sh
```

This will:
1. Install hooks system
2. Install tmux with interactive configuration (or full config if developer mode)

### Just Tmux

```bash
cd ~/mango/tmux
./setup-tmux.sh
```

### Reconfigure Menu

If you want to change your menu selections later:

```bash
cd ~/mango/tmux
python3 configure-menu.py
bash generate-tmux-conf.sh
tmux source-file ~/.tmux.conf
```

## Using the Interactive Menu

When you run the installation in public mode:

1. **fzf menu appears** with all optional items
2. Items with `[x]` are selected by default
3. Items with `[ ]` are not selected

**Keys:**
- `Tab` - Toggle selection (select/deselect)
- `Arrow keys` / `j/k` - Navigate
- `Enter` - Confirm selections
- `Ctrl+C` or `Esc` - Cancel

**Default Selections:**
-  General tools (editing, git, files, buffers)
-  Claude AI tools
-  Basic system monitoring
-  SSH access
-  ML/GPU tools
-  Server management tools
-  Training workflows

## Files Created

- `~/.tmux.conf` - Final tmux configuration
- `~/.tmux-menu-config.txt` - Your menu selections (can be regenerated)
- `~/.tmux-cheatsheet.txt` - Quick reference guide
- `~/.tmux/resurrect/` - Session persistence data

## Dependencies

### Required
- **fzf** - For interactive menu (auto-installed)
- **xclip** - For clipboard integration (auto-installed)
- **git** - For TPM plugin manager

### Optional
- **gpustat** - GPU monitoring (pip install, optional)
- **nvtop** - GPU monitoring (AppImage, optional)
- **lazygit** - Git TUI (optional but recommended)
- **htop** - System monitor (usually pre-installed)
- **glances** - Alternative system monitor (optional)

## Keyboard Shortcuts

Once installed, tmux menu is accessible via:
- **Ctrl+G** - Show menu (iOS/mobile friendly)
- **Right-click** on pane - Show menu (desktop)
- **Right-click** on status bar - Window management menu

Core shortcuts:
- **Ctrl+B, |** - Split vertical
- **Ctrl+B, -** - Split horizontal
- **Ctrl+B, f** - Fork Claude conversation
- **Alt+Arrow** - Navigate panes
- **Ctrl+Shift+Arrow** - Resize panes
- **Ctrl+Shift+C/V** - Copy/paste with system clipboard

## Customization

### Manual Menu Editing

If you want to manually edit which items appear:

1. Edit `~/.tmux-menu-config.txt`
2. Run `bash ~/mango/tmux/generate-tmux-conf.sh`
3. Reload tmux: `tmux source-file ~/.tmux.conf`

### Adding Custom Items

To add your own menu items:

1. Edit `~/mango/tmux/configure-menu.py`
2. Add entries to the `MENU_ITEMS` list
3. Re-run the configuration

### Template Modification

The base template is at `~/mango/tmux/tmux.conf.template`
- Contains all non-menu configuration
- `{{MENU_ITEMS}}` placeholder is replaced with your selections

## Auto-Start on Login

The installer offers an optional **tmux auto-launcher** that runs when you open a new terminal.

### Features

When enabled, every time you open a terminal you'll see a menu:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
           TMUX SESSION MANAGER
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Options:
  [1] Start new tmux session
  [2] Resume/attach to existing session
  [3] Skip (use normal shell)
  [4] Uninstall auto-launcher

Choice [1-4]:
```

### Installation

During `./setup-tmux.sh`, you'll be asked:
```
Enable tmux auto-start? [y/N]:
```

- **y** - Install auto-launcher
- **N** - Skip (default)

### Behavior

- **Smart detection**: Won't run if already in tmux
- **IDE-friendly**: Skips in VS Code, Claude Code, and other integrated terminals
- **Shell support**: Works with bash and zsh

### Uninstalling

Three ways to remove:
1. **From launcher menu**: Choose option 4 when the menu appears
2. **Manual removal**: Edit `~/.bashrc` and remove the `tmux-auto-launcher.sh` line
3. **Re-run installer**: Run `./setup-tmux.sh` again and choose No

### Re-enabling

Simply run `./setup-tmux.sh` again and choose Yes when prompted.

## Troubleshooting

### fzf not found
```bash
sudo apt-get install fzf
# or
git clone --depth 1 https://github.com/junegunn/fzf.git ~/.fzf
~/.fzf/install
```

### xclip not working (SSH)
Ensure X11 forwarding is enabled:
```bash
ssh -X user@host
# or in ~/.ssh/config:
ForwardX11 yes
```

### Menu items not appearing
Check that the helper scripts exist:
```bash
ls ~/mango/tmux/*.sh
ls ~/mango/tmux/*.py
```

### GPU tools failing
These are optional and only work with NVIDIA GPUs:
- Skip GPU monitoring if you don't have GPUs
- They're disabled by default in public mode

## Developer vs Public Mode

**Developer Mode** (`--developer` flag):
- Zero configuration
- ALL features enabled
- Perfect for power users who already know the system
- Full feature set including training, ML, and server tools

**Public Mode** (default, no flag):
- Interactive configuration
- Reasonable defaults for general users
- Excludes server/ML-specific items by default
- Clean experience for new users

## Migration from Old Installation

If you previously installed tmux with full configuration:
1. Your existing `~/.tmux.conf` is backed up automatically
2. Run `./setup-tmux.sh --developer` to get the full configuration again
3. Or run `./setup-tmux.sh` (without flag) to interactively select features

Your previous configuration is never lost - it's backed up with a timestamp.
