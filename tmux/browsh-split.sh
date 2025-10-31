#!/bin/bash

# Browsh terminal web browser launcher
# Since browsh has TTY issues, let's use lynx as a fallback

echo " Starting terminal web browser..."
echo ""

# Check if lynx is available as a simpler alternative
if command -v lynx &> /dev/null; then
    echo "Using Lynx (text-based web browser)"
    echo ""
    echo "Lynx Controls:"
    echo "• g - Go to URL"
    echo "• q - Quit"
    echo "• Up/Down arrows - Navigate"
    echo "• Enter - Follow link"
    echo "• b - Back"
    echo "• / - Search"
    echo ""
    echo "Starting lynx..."
    sleep 2
    lynx
else
    echo "Installing lynx (lightweight terminal browser)..."
    sudo apt update && sudo apt install -y lynx
    if [ $? -eq 0 ]; then
        echo "Lynx installed successfully! Starting..."
        lynx
    else
        echo "Failed to install lynx. Please install manually: sudo apt install lynx"
        read -p "Press Enter to continue..."
    fi
fi