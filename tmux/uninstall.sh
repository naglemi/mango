#!/bin/bash

# Tmux Toolkit Uninstall Script
# Cleanly removes all tmux-related configurations

echo " Tmux Toolkit Uninstall"
echo "========================="
echo ""

# 1. Remove tmux config
if [ -f ~/.tmux.conf ]; then
    echo "Removing ~/.tmux.conf..."
    rm -f ~/.tmux.conf
    echo " Tmux config removed"
else
    echo " No tmux config found"
fi

# 2. Remove tmux prompt flag file
if [ -f ~/.mango_tmux_prompt ]; then
    echo "Removing tmux prompt flag..."
    rm -f ~/.mango_tmux_prompt
    echo " Tmux prompt flag removed"
else
    echo " No tmux prompt flag found"
fi

# 3. Remove bashrc additions
SHELL_CONFIG=~/.bashrc
if [ -f "$SHELL_CONFIG" ]; then
    if grep -q "# Mango Toolkit Bashrc Additions" "$SHELL_CONFIG" 2>/dev/null; then
        echo "Removing tmux toolkit from $SHELL_CONFIG..."
        
        # Create backup
        cp "$SHELL_CONFIG" "$SHELL_CONFIG.backup.$(date +%Y%m%d_%H%M%S)"
        echo " Created backup: $SHELL_CONFIG.backup.*"
        
        # Remove everything between start and end markers
        sed -i '/^# Mango Toolkit Bashrc Additions$/,/^# End Mango Toolkit$/d' "$SHELL_CONFIG"
        
        echo " Removed tmux toolkit sections from bashrc"
    else
        echo " No tmux toolkit sections found in bashrc"
    fi
else
    echo "  No bashrc file found"
fi

# 4. Remove any tmux-related aliases that might be outside the toolkit section
if [ -f "$SHELL_CONFIG" ]; then
    # Remove standalone tm() function if it exists outside our section
    sed -i '/^tm() {$/,/^}$/d' "$SHELL_CONFIG" 2>/dev/null
    
    # Remove mobile alias if it references mango
    sed -i '/alias mobile.*mango\/mobile\.sh/d' "$SHELL_CONFIG" 2>/dev/null
    
    # Remove invoke-persona alias
    sed -i '/alias invoke-persona.*mango/d' "$SHELL_CONFIG" 2>/dev/null
    
    # Remove distribute-rules alias
    sed -i '/alias distribute-rules.*mango/d' "$SHELL_CONFIG" 2>/dev/null
fi

# 5. Remove tmux plugin manager (if installed)
if [ -d ~/.tmux/plugins/tpm ]; then
    echo "Removing tmux plugin manager..."
    rm -rf ~/.tmux/plugins
    echo " Tmux plugins removed"
fi

# 6. Kill any running tmux sessions (optional - ask user)
if command -v tmux &> /dev/null && tmux ls &> /dev/null 2>&1; then
    echo ""
    echo "  Active tmux sessions detected:"
    tmux ls
    echo ""
    echo -n "Kill all tmux sessions? [y/N]: "
    read -r response
    if [[ "$response" =~ ^[yY] ]]; then
        tmux kill-server 2>/dev/null
        echo " All tmux sessions killed"
    else
        echo " Tmux sessions left running"
    fi
fi

echo ""
echo " Tmux toolkit uninstall complete!"
echo ""
echo "To apply changes:"
echo "  source ~/.bashrc"
echo ""
echo "Or start a new terminal session."