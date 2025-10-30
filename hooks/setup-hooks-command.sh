#!/bin/bash

# Setup script to add hooks command to PATH
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Create symlink in /usr/local/bin (which is typically in PATH)
if [ -w /usr/local/bin ]; then
    sudo ln -sf "$SCRIPT_DIR/hooks" /usr/local/bin/hooks
    echo " Created symlink /usr/local/bin/hooks"
else
    # Alternative: add to ~/bin if it exists
    if [ -d ~/bin ]; then
        ln -sf "$SCRIPT_DIR/hooks" ~/bin/hooks
        echo " Created symlink ~/bin/hooks"
    else
        mkdir -p ~/bin
        ln -sf "$SCRIPT_DIR/hooks" ~/bin/hooks
        echo " Created ~/bin directory and symlink"
        echo ""
        echo "Add the following to your ~/.bashrc or ~/.profile:"
        echo 'export PATH="$HOME/bin:$PATH"'
    fi
fi

echo ""
echo "Setup complete! You can now run 'hooks' from anywhere."
echo "You may need to restart your shell or run: source ~/.bashrc"