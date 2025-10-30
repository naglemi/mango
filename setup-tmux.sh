#!/bin/bash

# Setup tmux configuration

# Base directory where this script lives
BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Tmux directory
TMUX_DIR="$BASE_DIR/tmux"

# Parse command line arguments
DEVELOPER_MODE=0
SHOW_HELP=0
UNINSTALL=0

for arg in "$@"; do
    case $arg in
        --developer)
            DEVELOPER_MODE=1
            shift
            ;;
        --help|-h)
            SHOW_HELP=1
            shift
            ;;
        --uninstall)
            UNINSTALL=1
            shift
            ;;
        *)
            ;;
    esac
done

if [ $SHOW_HELP -eq 1 ]; then
    echo "Usage: ./setup-tmux.sh [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --developer    Enable all tmux features (developer mode)"
    echo "  --uninstall    Remove tmux configuration (restore backup if available)"
    echo "  --help, -h     Show this help message"
    echo ""
    echo "Default: Interactive menu selection with recommended defaults"
    exit 0
fi

# Uninstall mode
if [ $UNINSTALL -eq 1 ]; then
    echo "Uninstalling tmux configuration..."
    echo ""

    # Find most recent backup
    LATEST_BACKUP=$(ls -t ~/.tmux.conf.backup.* 2>/dev/null | head -1)

    if [ -f ~/.tmux.conf ]; then
        if [ -n "$LATEST_BACKUP" ]; then
            echo "Found backup: $LATEST_BACKUP"
            read -p "Restore from backup? (y/n) " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                cp "$LATEST_BACKUP" ~/.tmux.conf
                echo "Restored tmux config from backup"
            else
                rm ~/.tmux.conf
                echo "Removed tmux config (no restore)"
            fi
        else
            rm ~/.tmux.conf
            echo "Removed tmux config (no backup available)"
        fi
    else
        echo "No tmux config found - nothing to uninstall"
    fi

    # Remove tmux configuration record
    if [ -f "$TMUX_DIR/.tmux-menu-config.txt" ]; then
        rm -f "$TMUX_DIR/.tmux-menu-config.txt"
        echo "Removed menu configuration record"
    fi

    echo ""
    echo "Uninstallation complete!"
    echo ""
    echo "Restart tmux for changes to take effect:"
    echo "  tmux kill-server && tmux"
    exit 0
fi

# Check if Claude Code is installed
if ! command -v claude &> /dev/null; then
    echo "ERROR: Claude Code is not installed"
    echo "The 'claude' command was not found in PATH"
    exit 1
fi

echo "Setting up tmux configuration..."

# Create symlink for $HOME/mango if it doesn't exist
if [ "$BASE_DIR" != "$HOME/mango" ]; then
    if [ -e "$HOME/mango" ] && [ ! -L "$HOME/mango" ]; then
        echo "WARNING: $HOME/mango exists but is not a symlink"
        echo "   All scripts expect mango repo at $HOME/mango"
        echo "   Please move or rename the existing directory"
        exit 1
    elif [ ! -e "$HOME/mango" ]; then
        ln -s "$BASE_DIR" "$HOME/mango"
        echo "Created symlink: $HOME/mango -> $BASE_DIR"
    fi
fi

# Backup existing tmux.conf if it exists
if [ -f ~/.tmux.conf ]; then
    backup_file=~/.tmux.conf.backup.$(date +%Y%m%d_%H%M%S)
    cp ~/.tmux.conf "$backup_file"
    echo "Backed up existing config to $backup_file"
fi

# Check core dependencies
echo "Checking core dependencies..."
echo ""

CORE_DEPS=()

# Check fzf (required for interactive menu)
if ! command -v fzf &> /dev/null; then
    CORE_DEPS+=("fzf (required for interactive menu configuration)")
fi

# Check nvim (required for Desktop and Mobile presets)
if ! command -v nvim &> /dev/null; then
    CORE_DEPS+=("nvim (required for Desktop and Mobile presets)")
fi

# Check lazygit (used in Desktop and Mobile presets)
if ! command -v lazygit &> /dev/null; then
    CORE_DEPS+=("lazygit (for git management in presets)")
fi

# Check xclip (for clipboard on Linux)
if ! command -v xclip &> /dev/null && command -v apt-get &> /dev/null; then
    CORE_DEPS+=("xclip (for clipboard support)")
fi

# Ask permission to install core dependencies
if [ ${#CORE_DEPS[@]} -gt 0 ]; then
    echo "The following core dependencies are missing:"
    for dep in "${CORE_DEPS[@]}"; do
        echo "  • $dep"
    done
    echo ""
    echo -n "Install missing dependencies? [y/N]: "
    read -r install_core_deps

    if [[ "$install_core_deps" =~ ^[Yy]$ ]]; then
        echo ""
        echo "Installing core dependencies..."

        # Install fzf
        if ! command -v fzf &> /dev/null; then
            if command -v apt-get &> /dev/null; then
                echo "Installing fzf..."
                sudo apt-get update && sudo apt-get install -y fzf
            elif command -v brew &> /dev/null; then
                echo "Installing fzf..."
                brew install fzf
            else
                echo "Installing fzf via git..."
                if command -v git &> /dev/null; then
                    git clone --depth 1 https://github.com/junegunn/fzf.git ~/.fzf
                    ~/.fzf/install --bin
                    echo "Installed fzf"
                else
                    echo "Cannot install fzf - git not available"
                fi
            fi
        fi

        # Install nvim
        if ! command -v nvim &> /dev/null; then
            if command -v apt-get &> /dev/null; then
                echo "Installing neovim..."
                sudo apt-get install -y neovim
            elif command -v brew &> /dev/null; then
                echo "Installing neovim..."
                brew install neovim
            else
                echo "Cannot install neovim - no package manager found"
                echo "    Please install manually: https://neovim.io/"
            fi
        fi

        # Install lazygit
        if ! command -v lazygit &> /dev/null; then
            if command -v brew &> /dev/null; then
                echo "Installing lazygit..."
                brew install lazygit
            elif command -v apt-get &> /dev/null; then
                echo "Installing lazygit..."
                LAZYGIT_VERSION=$(curl -s "https://api.github.com/repos/jesseduffield/lazygit/releases/latest" | grep -Po '"tag_name": "v\K[^"]*')
                curl -Lo lazygit.tar.gz "https://github.com/jesseduffield/lazygit/releases/latest/download/lazygit_${LAZYGIT_VERSION}_Linux_x86_64.tar.gz"
                tar xf lazygit.tar.gz lazygit
                sudo install lazygit /usr/local/bin
                rm lazygit lazygit.tar.gz
            else
                echo "Cannot install lazygit - no package manager found"
                echo "    Please install manually: https://github.com/jesseduffield/lazygit"
            fi
        fi

        # Install xclip
        if ! command -v xclip &> /dev/null && command -v apt-get &> /dev/null; then
            echo "Installing xclip..."
            sudo apt-get install -y xclip
        fi

        echo ""
        echo "Core dependencies installation complete"
    else
        echo ""
        echo "Skipping core dependency installation."
        echo "Some features may not work without these dependencies."
    fi
else
    echo "All core dependencies already installed"
fi

echo ""

# Setup NeoVim with file browser
echo "Setting up NeoVim with file browser..."
chmod +x "$TMUX_DIR/setup-nvim.sh"
bash "$TMUX_DIR/setup-nvim.sh"

echo ""

# Configure tmux.conf
chmod +x "$TMUX_DIR/configure-menu.py"
chmod +x "$TMUX_DIR/generate-tmux-conf.sh"
chmod +x "$TMUX_DIR/preset-desktop.sh"
chmod +x "$TMUX_DIR/preset-mobile.sh"
chmod +x "$TMUX_DIR/preset-battlestation.sh"
chmod +x "$TMUX_DIR/tmux-session-menu.sh"

# Check developer mode flag
if [ $DEVELOPER_MODE -eq 1 ]; then
    echo "Developer mode enabled (--developer flag)"
    echo "Installing FULL configuration with all menu items"
    # Use the original full configuration
    cp "$TMUX_DIR/tmux.conf" ~/.tmux.conf
else
    echo "Public mode - configuring menu items interactively..."
    if python3 "$TMUX_DIR/configure-menu.py"; then
        # Generate final tmux.conf from template with selected items
        bash "$TMUX_DIR/generate-tmux-conf.sh"
        echo "Installed customized tmux configuration"
    else
        echo "Menu configuration cancelled, using default configuration"
        cp "$TMUX_DIR/tmux.conf" ~/.tmux.conf
        echo "Installed default tmux configuration"
    fi
fi

# Check for feature-specific dependencies and ask permission
echo ""
echo "Checking for feature-specific dependencies..."

FEATURE_DEPS=()

# In developer mode, GPU tools are needed (full config includes them)
if [ $DEVELOPER_MODE -eq 1 ]; then
    if ! command -v gpustat &> /dev/null; then
        FEATURE_DEPS+=("gpustat (GPU monitoring - developer mode)")
    fi
    if ! command -v nvtop &> /dev/null; then
        FEATURE_DEPS+=("nvtop (interactive GPU monitor - developer mode)")
    fi
    if ! command -v glances &> /dev/null; then
        FEATURE_DEPS+=("glances (system monitor - developer mode)")
    fi
# In public mode, check what features were selected
elif [ -f ~/.tmux-menu-config.txt ]; then
    if grep -q "GPUstat" ~/.tmux-menu-config.txt; then
        if ! command -v gpustat &> /dev/null; then
            FEATURE_DEPS+=("gpustat (for GPUstat Compact feature)")
        fi
    fi

    if grep -q "NVTOP" ~/.tmux-menu-config.txt; then
        if ! command -v nvtop &> /dev/null; then
            FEATURE_DEPS+=("nvtop (for NVTOP Monitor feature)")
        fi
    fi

    if grep -q "Glances" ~/.tmux-menu-config.txt; then
        if ! command -v glances &> /dev/null; then
            FEATURE_DEPS+=("glances (for Glances Monitor feature)")
        fi
    fi
fi

# Ask permission to install feature dependencies
if [ ${#FEATURE_DEPS[@]} -gt 0 ]; then
    echo ""
    echo "The following feature-specific dependencies are missing:"
    for dep in "${FEATURE_DEPS[@]}"; do
        echo "  • $dep"
    done
    echo ""
    echo -n "Install these dependencies? [y/N]: "
    read -r install_feature_deps

    if [[ "$install_feature_deps" =~ ^[Yy]$ ]]; then
        echo ""
        echo "Installing feature dependencies..."

        # Install gpustat if needed
        if ! command -v gpustat &> /dev/null && [[ " ${FEATURE_DEPS[@]} " =~ "gpustat" ]]; then
            echo "Installing gpustat..."
            pip install --user gpustat
            echo "Installed gpustat"
        fi

        # Install nvtop if needed
        if ! command -v nvtop &> /dev/null && [[ " ${FEATURE_DEPS[@]} " =~ "nvtop" ]]; then
            echo "Installing nvtop..."
            NVTOP_DIR="$HOME/.local/bin"
            mkdir -p "$NVTOP_DIR"

            if command -v wget &> /dev/null; then
                wget -O "$NVTOP_DIR/nvtop" "https://github.com/Syllo/nvtop/releases/download/3.1.0/nvtop-3.1.0-x86_64.AppImage" 2>/dev/null
                chmod +x "$NVTOP_DIR/nvtop"
                if [ -x "$NVTOP_DIR/nvtop" ]; then
                    echo "Installed nvtop"
                else
                    echo "nvtop installation failed"
                fi
            else
                echo "wget not available - skipping nvtop"
            fi
        fi

        # Install glances if needed
        if ! command -v glances &> /dev/null && [[ " ${FEATURE_DEPS[@]} " =~ "glances" ]]; then
            echo "Installing glances..."
            if command -v brew &> /dev/null; then
                brew install glances
                echo "Installed glances"
            elif command -v pip3 &> /dev/null; then
                pip3 install --user glances
                echo "Installed glances"
            else
                echo "Cannot install glances - no package manager (brew/pip3) found"
                echo "    Please install manually: pip3 install glances"
            fi
        fi

        echo ""
        echo "Feature dependencies installation complete"
    else
        echo ""
        echo "Skipped feature dependency installation."
        echo "Some tmux features may not work without these dependencies."
    fi
else
    echo "All feature dependencies already installed"
fi

echo ""

# Install TPM (Tmux Plugin Manager)
echo "Installing TPM and plugins..."
if [ -d ~/.tmux/plugins/tpm ]; then
    echo "TPM already installed"
else
    git clone https://github.com/tmux-plugins/tpm ~/.tmux/plugins/tpm
    echo "Installed TPM"
fi

# Create resurrect directory
mkdir -p ~/.tmux/resurrect
echo "Created tmux-resurrect directory"

# Note about plugin installation
echo ""
echo "To install tmux plugins:"
echo "  1. Start or restart tmux: tmux new -s test"
echo "  2. Press Ctrl+B then Shift+I to install plugins"
echo "  Or plugins will auto-install on first tmux start"

# Install spectate script
echo "Installing spectate script..."
mkdir -p ~/bin
cp "$TMUX_DIR/spectate" ~/bin/spectate
chmod +x ~/bin/spectate
echo "Installed spectate to ~/bin"

# Create a quick reference card
cat > ~/.tmux-cheatsheet.txt << 'EOF'
TMUX QUICK REFERENCE
===================

BASICS:
  tmux new -s name     Create new session
  tmux attach -t name  Attach to session
  tmux ls              List sessions
  Ctrl+B, D            Detach from session

MOUSE/SCROLLING:
  Scroll up            Enters copy mode automatically
  Click & drag         Select text (auto-copies to clipboard)
  Drag pane border     Resize panes with mouse
  Click pane           Switch to that pane

PANES:
  Ctrl+B, |            Split vertical (side by side)
  Ctrl+B, -            Split horizontal (top/bottom)
  Ctrl+B, f            Fork Claude conversation to new pane
  Alt+Arrow keys       Navigate between panes (Option on Mac)
  Ctrl+Shift+Arrows    Resize panes
  Ctrl+Shift+X         Close current pane
  Ctrl+B, z            Zoom/unzoom pane

WINDOWS:
  Ctrl+B, c            New window
  Ctrl+B, n/p          Next/previous window
  Ctrl+B, 1-9          Go to window number
  Ctrl+B, ,            Rename window

COPY/PASTE:
  Ctrl+Shift+C         Copy from tmux to system clipboard
  Ctrl+Shift+V         Paste from system clipboard
  Ctrl+B, [            Enter copy mode manually
  v                    Start selection in copy mode
  y                    Copy selection and exit

SESSION MANAGEMENT:
  Ctrl+B, Ctrl+s       Save session (tmux-resurrect)
  Ctrl+B, Ctrl+r       Restore session (tmux-resurrect)
  Auto-save            Every 15 minutes (tmux-continuum)
  Auto-restore         On tmux start (tmux-continuum)

RIGHT-CLICK MENUS:
  Right-click on pane           Full menu (split, fork Claude, tools, etc.)
  Right-click on status bar     Window menu with options:
                                  • Press 'W' = Combine All Windows
                                  • Press 'e' = Even Layout (1 Row)
                                  • Press 'f' = Grid Layout (2+ Rows)

OTHER:
  Ctrl+B, r            Reload config
  Ctrl+B, ?            Show all keybindings
  Ctrl+B, I            Install/update tmux plugins (TPM)
  Ctrl+B, U            Update all tmux plugins (TPM)
EOF

echo "Created cheat sheet at ~/.tmux-cheatsheet.txt"

# If tmux is running, offer to reload
if pgrep -x "tmux" > /dev/null; then
    echo ""
    echo "Tmux is currently running. To apply new settings:"
    echo "  1. Inside tmux: Press Ctrl+B, then r"
    echo "  2. Or restart tmux sessions"
fi

echo ""
echo "Tmux setup complete!"
echo ""
echo "Key features enabled:"
echo "  • Mouse support with natural scrolling"
echo "  • 50,000 line scrollback buffer"
echo "  • Vim-style navigation and copy mode"
echo "  • Better status bar with session info"
echo "  • Intuitive pane splitting (| and -)"
echo "  • Session persistence with tmux-resurrect"
echo "  • Auto-save every 15 minutes with tmux-continuum"
echo "  • Auto-restore sessions on tmux start"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "QUICK TEST - Window Management Options:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1. Start tmux:  tmux new -s test"
echo "2. Split panes a few times (Ctrl+B, | or Ctrl+B, -)"
echo "3. Right-click on the STATUS BAR at the BOTTOM (where window tabs are)"
echo "4. You should see:"
echo "   • Press 'W' = Combine All Windows - merge multiple windows into one"
echo "   • Press 'e' = Even Layout (1 Row) - arranges panes side-by-side"
echo "   • Press 'f' = Grid Layout (2+ Rows) - arranges panes in a grid"
echo ""
echo "IMPORTANT: Right-click on STATUS BAR (bottom), NOT on a pane!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "See ~/.tmux-cheatsheet.txt for full reference"

# Ask about tmux auto-start
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TMUX AUTO-START ON LOGIN"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Would you like tmux to automatically start on login?"
echo ""
echo "When enabled, you'll see a menu on each login with options to:"
echo "  • Start new tmux session"
echo "  • Resume existing session"
echo "  • Skip and use normal shell"
echo "  • Uninstall auto-launcher"
echo ""
echo "WARNING: This will edit your shell configuration file:"
echo "   • Linux: ~/.bashrc"
echo "   • Mac: ~/.zshrc (or ~/.bashrc if you use bash)"
echo ""
echo "To undo manually: remove lines containing 'tmux-auto-launcher.sh' from your shell config"
echo "Or run the auto-launcher menu and select option 4 (Uninstall)"
echo ""
echo -n "Enable tmux auto-start? [y/N]: "
read -r enable_autostart

if [[ "$enable_autostart" =~ ^[Yy]$ ]]; then
    echo ""
    echo "Installing tmux auto-launcher..."

    # Copy launcher script
    chmod +x "$TMUX_DIR/tmux-auto-launcher.sh"

    # Detect which shell config file exists
    if [ -f ~/.zshrc ]; then
        # zsh (typically macOS)
        SHELL_RC="$HOME/.zshrc"
        SHELL_NAME="zsh"

        if ! grep -q "tmux-auto-launcher.sh" "$SHELL_RC" 2>/dev/null; then
            echo "" >> "$SHELL_RC"
            echo "# Tmux auto-launcher (installed by mango/tmux)" >> "$SHELL_RC"
            echo "source \"$TMUX_DIR/tmux-auto-launcher.sh\"" >> "$SHELL_RC"
            echo "Added to ~/.zshrc"
        else
            echo "Already in ~/.zshrc"
        fi
    elif [ -f ~/.bashrc ]; then
        # bash (typically Linux)
        SHELL_RC="$HOME/.bashrc"
        SHELL_NAME="bash"

        if ! grep -q "tmux-auto-launcher.sh" "$SHELL_RC" 2>/dev/null; then
            echo "" >> "$SHELL_RC"
            echo "# Tmux auto-launcher (installed by mango/tmux)" >> "$SHELL_RC"
            echo "source \"$TMUX_DIR/tmux-auto-launcher.sh\"" >> "$SHELL_RC"
            echo "Added to ~/.bashrc"
        else
            echo "Already in ~/.bashrc"
        fi
    else
        echo "Neither ~/.zshrc nor ~/.bashrc found. Cannot install auto-launcher."
        echo "Please create one of these files first."
        exit 1
    fi

    echo ""
    echo "Tmux auto-launcher installed!"
    echo ""
    echo "To test: open a new terminal or run: source $SHELL_RC"
    echo "To uninstall later: select option 4 from the launcher menu"
else
    echo ""
    echo "Skipped tmux auto-start installation."
    echo "You can run this setup again later to enable it."
fi

echo ""
echo "To uninstall, run: ./setup-tmux.sh --uninstall"
echo ""