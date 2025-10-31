#!/bin/bash

# Setup bashrc additions for mango toolkit

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo " Mango Toolkit Bashrc Setup"
echo "================================="
echo ""

# Detect which shell config file to use
if [ -n "$BASH_VERSION" ]; then
    if [ -f ~/.bashrc ]; then
        SHELL_CONFIG=~/.bashrc
    elif [ -f ~/.bash_profile ]; then
        SHELL_CONFIG=~/.bash_profile
    else
        SHELL_CONFIG=~/.bashrc
        touch "$SHELL_CONFIG"
    fi
else
    echo "  This script is designed for bash. Your shell might be different."
    echo "Continue anyway? [y/N]: "
    read -r response
    if [[ ! "$response" =~ ^[yY] ]]; then
        exit 1
    fi
    SHELL_CONFIG=~/.bashrc
fi

echo "Will modify: $SHELL_CONFIG"
echo ""

# Check if already installed
if grep -q "# Mango Toolkit Bashrc Additions" "$SHELL_CONFIG" 2>/dev/null; then
    echo "  Usability toolkit already configured in $SHELL_CONFIG"
    echo -n "Reinstall? [y/N]: "
    read -r response
    if [[ ! "$response" =~ ^[yY] ]]; then
        exit 0
    fi
    # Remove old installation
    sed -i.bak '/# Mango Toolkit Bashrc Additions/,/# End Mango Toolkit/d' "$SHELL_CONFIG"
fi

# Ask about tmux auto-attach feature
echo "  Tmux Session Management"
echo "Would you like to be prompted to resume tmux sessions on login?"
echo "(You'll see a list of sessions and can choose to attach or continue to shell)"
echo -n "Enable tmux session prompt? [Y/n]: "
read -r tmux_response

ENABLE_TMUX_PROMPT=true
if [[ "$tmux_response" =~ ^[nN] ]]; then
    ENABLE_TMUX_PROMPT=false
fi

# Create/remove the flag file
if [ "$ENABLE_TMUX_PROMPT" = true ]; then
    touch ~/.mango_tmux_prompt
    echo " Tmux session prompt enabled"
else
    rm -f ~/.mango_tmux_prompt
    echo " Tmux session prompt disabled"
fi

# Backup shell config
cp "$SHELL_CONFIG" "$SHELL_CONFIG.backup.$(date +%Y%m%d_%H%M%S)"
echo " Backed up $SHELL_CONFIG"

# Create the .mango_bashrc file with the new version
cat > ~/.mango_bashrc << 'EOF'
#!/bin/bash
# Mango Toolkit Bashrc Extensions
# This file is sourced by .bashrc - DO NOT EDIT MANUALLY
# Regenerate using: ~/mango/tmux/setup-bashrc.sh

# Add mango toolkit to PATH
export PATH="$PATH:$HOME/mango"

# Tmux session management (robust version with fzf and fallback)
if [ -f ~/.mango_tmux_prompt ]; then
    # ONLY run tmux menu if we're in an interactive session with a TTY
    if [ -t 0 ] && [ -t 1 ]; then
        # Source the robust menu script instead of fragile inline code
        if [ -f ~/mango/tmux/tmux-session-menu.sh ]; then
            source ~/mango/tmux/tmux-session-menu.sh
        fi
    fi
fi

# Aliases for quick access
alias mobile='~/mango/remote/mobile.sh'
alias invoke-persona='~/mango/personas/invoke-persona.sh'
alias distribute-rules='~/mango/personas/distribute-rules.sh'
alias spectator='~/mango/tmux/spectator.sh'
alias spec='~/mango/tmux/spectator.sh'

# Function to quickly create and attach to a tmux session
tm() {
    if [ -z "$1" ]; then
        # No argument - try to attach to 'mobile' or create it
        tmux attach -t mobile 2>/dev/null || tmux new -s mobile
    else
        # Session name provided
        tmux attach -t "$1" 2>/dev/null || tmux new -s "$1"
    fi
}
EOF

# Add sourcing of .mango_bashrc to shell config
echo "" >> "$SHELL_CONFIG"
echo "# Mango Toolkit Bashrc Additions" >> "$SHELL_CONFIG"
echo "if [ -f ~/.mango_bashrc ]; then" >> "$SHELL_CONFIG"
echo "    source ~/.mango_bashrc" >> "$SHELL_CONFIG"
echo "fi" >> "$SHELL_CONFIG"
echo "# End Mango Toolkit" >> "$SHELL_CONFIG"

echo " Added mango toolkit configuration"
echo ""

# Create symlink to usability directory if not in home
if [ "$SCRIPT_DIR" != "$HOME/mango" ]; then
    if [ -e "$HOME/mango" ]; then
        echo "  $HOME/mango already exists"
    else
        ln -s "$SCRIPT_DIR" "$HOME/mango"
        echo " Created symlink: ~/mango -> $SCRIPT_DIR"
    fi
fi

echo ""
echo " Bashrc setup complete!"
echo ""
echo "Features added:"
echo "  • Usability toolkit in PATH"
if [ "$ENABLE_TMUX_PROMPT" = true ]; then
    echo "  • Tmux session prompt on login"
fi
echo "  • Aliases: mobile, invoke-persona, distribute-rules"
echo "  • tm function for quick tmux access"
echo ""
echo "To apply changes:"
echo "  source $SHELL_CONFIG"
echo ""
echo "Or start a new terminal session."

# Offer to source now
echo ""
echo -n "Source now? [Y/n]: "
read -r source_response
if [[ ! "$source_response" =~ ^[nN] ]]; then
    source "$SHELL_CONFIG"
    echo " Configuration loaded!"
fi