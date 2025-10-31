#!/bin/bash

# Glances system monitor launcher
# Glances is a cross-platform monitoring tool with web interface

# Check if glances is installed
if ! command -v glances &> /dev/null; then
    echo "ERROR: glances is not installed"
    echo ""
    echo "Install with:"
    echo "  pip3 install glances"
    echo "  or"
    echo "  brew install glances"
    echo ""
    echo "Press any key to exit..."
    read -n 1
    exit 1
fi

echo " Starting Glances system monitor..."
echo ""
echo "Glances Controls:"
echo "• q - Quit"
echo "• h - Help"
echo "• s - Sort processes"
echo "• c - Sort by CPU"
echo "• m - Sort by memory"
echo "• p - Sort by process name"
echo "• i - Sort by I/O"
echo "• d - Show/hide disk I/O"
echo "• n - Show/hide network"
echo "• Space - Pause/resume"
echo ""
echo "Starting glances..."
sleep 2

# Start glances
glances