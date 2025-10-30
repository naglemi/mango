#!/usr/bin/env python3
"""
Training Menu - Interactive interface for starting training with config selection
Only works in finetune project directories with main.py and configs/ folder
"""

import os
import sys
import termios
import tty
import subprocess
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Tuple

class TrainingMenu:
    """Interactive menu for training configuration selection."""

    def __init__(self):
        self.current_dir = Path.cwd()
        self.configs = []
        self.current_selection = 0
        self.selected_training_dir = None

        # Check if we're already in a valid training directory
        if self._is_training_directory():
            self.selected_training_dir = self.current_dir
        else:
            # Look for available training directories
            training_dirs = self._find_training_directories()
            if not training_dirs:
                print(" No finetune project directories found.")
                print("Searched in /home/ubuntu/ for directories containing:")
                print("  - 'finetune' in name")
                print("  - main.py file")
                print("  - configs/ directory")
                input("Press Enter to close...")
                sys.exit(1)
            elif len(training_dirs) == 1:
                self.selected_training_dir = training_dirs[0]
            else:
                # Let user choose from multiple directories
                self.selected_training_dir = self._select_training_directory(training_dirs)
                if not self.selected_training_dir:
                    sys.exit(0)

        # Load configs from selected directory
        self.configs = self._get_config_files()
        if not self.configs:
            print(f" No config files found in {self.selected_training_dir}/configs/ directory")
            input("Press Enter to close...")
            sys.exit(1)

    def _is_training_directory(self) -> bool:
        """Check if current directory is a valid training directory."""
        # Must contain 'finetune' in path
        if 'finetune' not in str(self.current_dir).lower():
            return False

        # Must have main.py
        if not (self.current_dir / 'main.py').exists():
            return False

        # Must have configs directory
        if not (self.current_dir / 'configs').exists():
            return False

        return True

    def _find_training_directories(self) -> List[Path]:
        """Find all valid training directories."""
        home_dir = Path.home()
        training_dirs = []

        # Look for directories containing 'finetune'
        for item in home_dir.iterdir():
            if item.is_dir() and 'finetune' in item.name.lower():
                # Check if it has required files
                if (item / 'main.py').exists() and (item / 'configs').exists():
                    training_dirs.append(item)

        return sorted(training_dirs)

    def _select_training_directory(self, training_dirs: List[Path]) -> Optional[Path]:
        """Interactive selection of training directory."""
        selection = 0

        try:
            while True:
                self._clear_screen()
                print(" Select Training Directory")
                print("=" * 50)
                print("Controls: ↑↓/WS navigate, ENTER select, q quit")
                print("=" * 50)
                print()

                for i, dir_path in enumerate(training_dirs):
                    marker = ">" if i == selection else " "
                    print(f"{marker} {dir_path.name}")

                print()
                key = self._get_char()

                if key in ['q', 'Q']:
                    return None
                elif key in ['\033[A', 'w', 'W']:  # Up
                    selection = max(0, selection - 1)
                elif key in ['\033[B', 's', 'S']:  # Down
                    selection = min(len(training_dirs) - 1, selection + 1)
                elif key in ['\r', '\n']:  # Enter
                    return training_dirs[selection]

        except KeyboardInterrupt:
            return None

    def _get_config_files(self) -> List[str]:
        """Get list of config files from configs/ directory."""
        configs_dir = self.selected_training_dir / 'configs'
        config_files = []

        for file_path in configs_dir.glob('*.yaml'):
            if file_path.is_file():
                config_files.append(file_path.name)

        for file_path in configs_dir.glob('*.yml'):
            if file_path.is_file():
                config_files.append(file_path.name)

        return sorted(config_files)

    def _clear_screen(self):
        """Clear terminal screen."""
        print('\033[2J\033[H', end='')

    def _display_menu(self):
        """Display the training menu."""
        self._clear_screen()

        print(" Training Menu")
        print("=" * 50)
        print("Controls: ↑↓ navigate, ENTER start training, q quit")
        print("=" * 50)
        print()

        print(f" Project: {self.selected_training_dir.name}")
        print(f" Found {len(self.configs)} config files")
        print()

        for i, config in enumerate(self.configs):
            prefix = "> " if i == self.current_selection else "  "
            print(f"{prefix}{config}")

        print()
        print("=" * 50)
        print(f"Selected: {self.configs[self.current_selection] if self.configs else 'None'}")

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
        if key == 'q':
            return False

        elif key == '\033[A':  # Up arrow
            self.current_selection = max(0, self.current_selection - 1)

        elif key == '\033[B':  # Down arrow
            self.current_selection = min(len(self.configs) - 1, self.current_selection + 1)

        elif key == '\r' or key == '\n':  # Enter - start training
            return self._start_training()

        return True

    def _generate_log_filename(self, config_name: str) -> str:
        """Generate log filename following existing naming scheme."""
        # Remove .yaml/.yml extension
        config_base = config_name.replace('.yaml', '').replace('.yml', '')

        # Get timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Create log filename
        log_filename = f"{config_base}_{timestamp}_tmux.log"

        return log_filename

    def _start_training(self) -> bool:
        """Start training with selected config."""
        config_name = self.configs[self.current_selection]
        config_path = f"configs/{config_name}"

        print(f"\n Starting training with config: {config_name}")

        # Generate log filename
        log_filename = self._generate_log_filename(config_name)
        log_path = self.current_dir / "logs" / log_filename

        # Ensure logs directory exists
        log_path.parent.mkdir(exist_ok=True)

        print(f" Log file: {log_path}")
        print(f" Command: python main.py --objective-config {config_path}")
        print()

        # Confirm before starting
        confirm = input("Start training? [Y/n]: ").strip().lower()
        if confirm and confirm != 'y' and confirm != 'yes':
            print(" Training cancelled")
            return True

        # Start training with logging
        cmd = f"python main.py --objective-config {config_path} 2>&1 | tee {log_path}"

        print(" Starting training...")
        print("=" * 50)

        # Execute training command
        try:
            subprocess.run(cmd, shell=True, cwd=self.selected_training_dir)
        except KeyboardInterrupt:
            print("\n  Training interrupted by user")
        except Exception as e:
            print(f"\n Training failed: {e}")

        return False  # Exit menu after training

    def run_menu(self):
        """Run the interactive training menu."""
        try:
            while True:
                self._display_menu()
                key = self._get_char()

                if not self._handle_input(key):
                    break

        except KeyboardInterrupt:
            print("\n Training menu cancelled.")
            return

        print("\n Training menu closed.")

def main():
    """Main entry point."""
    try:
        menu = TrainingMenu()
        menu.run_menu()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()