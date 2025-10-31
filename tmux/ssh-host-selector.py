#!/usr/bin/env python3
"""
SSH Host Selector - Interactive menu for selecting SSH hosts from config
Uses arrow keys and WASD navigation like other menus
"""

import os
import sys
import termios
import tty
import subprocess
import re
from pathlib import Path
from typing import List, Tuple, Optional

class SSHHostSelector:
    """Interactive SSH host selector."""

    def __init__(self):
        self.hosts = self._load_ssh_hosts()
        self.current_selection = 0

        if not self.hosts:
            print(" No SSH hosts found in ~/.ssh/config")
            print("Add hosts to your SSH config file:")
            print("  Host hostname")
            print("    HostName server.example.com")
            print("    User username")
            input("Press Enter to close...")
            sys.exit(1)

    def _load_ssh_hosts(self) -> List[Tuple[str, str]]:
        """Load SSH hosts from SSH config."""
        ssh_config = Path.home() / '.ssh' / 'config'
        hosts = []

        if not ssh_config.exists():
            return hosts

        try:
            with open(ssh_config, 'r') as f:
                content = f.read()

            # Parse SSH config for Host entries
            current_host = None
            current_hostname = None
            current_user = None

            for line in content.split('\n'):
                line = line.strip()

                if line.startswith('Host ') and not '*' in line:
                    # Save previous host if we have one
                    if current_host:
                        display_name = current_host
                        if current_hostname and current_hostname != current_host:
                            display_name += f" ({current_hostname})"
                        if current_user:
                            display_name += f" [{current_user}]"
                        hosts.append((current_host, display_name))

                    # Start new host
                    current_host = line.split()[1]
                    current_hostname = None
                    current_user = None

                elif line.startswith('HostName '):
                    current_hostname = line.split()[1]

                elif line.startswith('User '):
                    current_user = line.split()[1]

            # Don't forget the last host
            if current_host:
                display_name = current_host
                if current_hostname and current_hostname != current_host:
                    display_name += f" ({current_hostname})"
                if current_user:
                    display_name += f" [{current_user}]"
                hosts.append((current_host, display_name))

        except Exception as e:
            print(f"Error reading SSH config: {e}")
            return []

        return sorted(hosts, key=lambda x: x[0].lower())

    def _clear_screen(self):
        """Clear terminal screen."""
        print('\033[2J\033[H', end='', flush=True)

    def _display_menu(self):
        """Display the SSH host selection menu."""
        self._clear_screen()

        print(" SSH Host Selector")
        print("=" * 50)
        print("Controls: ↑↓/WS navigate, ENTER connect, q quit")
        print("=" * 50)
        print()

        # Display hosts
        display_start = max(0, self.current_selection - 10)
        display_end = min(len(self.hosts), display_start + 20)

        if display_start > 0:
            print("  ...")

        for i in range(display_start, display_end):
            host_id, display_name = self.hosts[i]
            if i == self.current_selection:
                print(f"> {display_name}")
            else:
                print(f"  {display_name}")

        if display_end < len(self.hosts):
            print("  ...")

        print()
        print(f"Found {len(self.hosts)} SSH hosts")

    def _get_char(self) -> str:
        """Get a single character from stdin."""
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)

            # Handle arrow keys (escape sequences)
            if ch == '\033':
                ch += sys.stdin.read(1)  # [
                if ch == '\033[':
                    ch += sys.stdin.read(1)  # A, B, C, or D

            return ch
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

    def _handle_input(self, key: str) -> bool:
        """Handle keyboard input. Returns False to exit."""
        if key in ['q', 'Q']:
            return False

        elif key == '\033[A' or key == 'w' or key == 'W':  # Up arrow or W
            self.current_selection = max(0, self.current_selection - 1)

        elif key == '\033[B' or key == 's' or key == 'S':  # Down arrow or S
            self.current_selection = min(len(self.hosts) - 1, self.current_selection + 1)

        elif key == '\r' or key == '\n':  # Enter - connect to host
            return self._connect_to_host()

        return True

    def _connect_to_host(self) -> bool:
        """Connect to the selected SSH host."""
        if 0 <= self.current_selection < len(self.hosts):
            host_id, display_name = self.hosts[self.current_selection]
            print(f"\n Connecting to {host_id}...")

            try:
                # Use the SSH wrapper to handle TOTP automation
                ssh_wrapper = Path.home() / 'mango' / 'auth' / 'ssh-wrapper'
                if ssh_wrapper.exists():
                    subprocess.run([str(ssh_wrapper), host_id])
                else:
                    # Fallback to regular ssh
                    subprocess.run(['ssh', host_id])
            except KeyboardInterrupt:
                print("\n  Connection interrupted")
            except Exception as e:
                print(f"\n SSH connection failed: {e}")
                input("Press Enter to continue...")
                return True  # Stay in menu

        return False  # Exit menu after connection attempt

    def run_menu(self):
        """Run the interactive SSH host selection menu."""
        try:
            while True:
                self._display_menu()
                key = self._get_char()
                if not self._handle_input(key):
                    break
        except KeyboardInterrupt:
            print("\n SSH host selector closed.")

def main():
    """Main entry point."""
    # Check if we're in tmux
    if not os.environ.get('TMUX'):
        print("  This tool works best inside tmux but can run standalone.")

    try:
        selector = SSHHostSelector()
        selector.run_menu()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()