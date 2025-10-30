#!/usr/bin/env python3
"""
Interactive Workflow and MCP Configurator
Allows users to select which workflows and MCP servers to install
"""

import json
import os
import sys
import termios
import tty
from pathlib import Path
from typing import List, Optional, Tuple

# MCP definitions with descriptions
# Format: (id, name, description, default_enabled, requires_env)
MCPS = [
    ("pushover", "Pushover Notifications", "Send push notifications to mobile devices", True, False),
    ("report", "Report System", "S3-based reports with email notifications and file attachments", True, False),
    ("ninjagrab", "File Collection", "Collect multiple files into single output for workflows", True, False),
    ("process-monitor", "Process Monitor", "Monitor long-running processes with timeout handling", True, False),
    ("sleep", "Process Wait", "Simple blocking wait until process completes", True, False),
    ("gpt5-proxy", "GPT-5 Proxy", "Proxy server for GPT-5 API access", False, False),
    ("grok-proxy", "Grok Proxy", "Proxy server for xAI Grok API access", False, False),
]

# Workflow categories
# Format: (workflow_id, section, default_enabled)
WORKFLOW_CATEGORIES = {
    # Basic workflows (enabled by default)
    "discuss": ("basic", True),
    "help": ("basic", True),
    "new": ("basic", True),
    "newtask": ("basic", True),
    "read": ("basic", True),
    "sync-workflows": ("basic", True),
    "debt-audit": ("basic", True),
    "nocode": ("basic", True),

    # LLM workflows (require API keys)
    "deepseek-plea": ("llm", False),
    "gpt5plea": ("llm", False),
    "plea": ("llm", False),

    # Advanced workflows (not enabled by default)
    "chill_until_it_finishes": ("advanced", False),
    "implementplan": ("advanced", False),
    "blog": ("advanced", False),
    "report": ("advanced", False),
}

WORKFLOW_SECTION_TITLES = {
    "basic": "Basic Workflows",
    "llm": "LLM Integration (requires API keys)",
    "advanced": "Advanced Workflows"
}

def get_available_workflows(workflows_dir: Path) -> List[Tuple]:
    """Get list of available workflow files with categorization"""
    workflows = []

    if not workflows_dir.exists():
        return workflows

    for wf_file in sorted(workflows_dir.glob("*.md")):
        name = wf_file.stem
        # Try to extract description from first line of file
        try:
            with open(wf_file, 'r') as f:
                first_line = f.readline().strip()
                if first_line.startswith('#'):
                    description = first_line.lstrip('#').strip()
                else:
                    description = "Claude Code workflow command"
        except:
            description = "Claude Code workflow command"

        # Get category and default from WORKFLOW_CATEGORIES
        section, default = WORKFLOW_CATEGORIES.get(name, ("basic", True))

        # Format: (id, name, description, default, section)
        workflows.append((name, name, description, default, section))

    return workflows

class ItemConfigurator:
    """Interactive configurator using custom TUI."""

    def __init__(self, items: List[Tuple], title: str, developer_mode: bool = False, has_sections: bool = False, section_titles: dict = None):
        self.items = items
        self.title = title
        self.developer_mode = developer_mode
        self.has_sections = has_sections
        self.section_titles = section_titles or {}

        # Group items by section if they have sections
        self.sections = {}
        if has_sections:
            # Items have format: (id, name, description, default, section)
            for i, item in enumerate(items):
                section = item[4] if len(item) > 4 else "default"
                if section not in self.sections:
                    self.sections[section] = []
                self.sections[section].append(i)

        # Initialize enabled state with defaults
        self.enabled = {}

        for i, item in enumerate(items):
            # item format varies: (id, name, description, default) or (id, name, description, default, section)
            default = item[3] if len(item) > 3 else True

            # In developer mode, enable all by default
            if developer_mode:
                self.enabled[i] = True
            else:
                self.enabled[i] = default

        self.selected_index = 0
        self.message = ""

    def _clear_screen(self):
        """Clear the terminal screen."""
        os.system('clear' if os.name != 'nt' else 'cls')

    def _display_menu(self):
        """Display the menu with checkboxes."""
        self._clear_screen()

        # Header
        print(self.title.upper())
        print("=" * 80)
        print("Use ↑/↓ or W/S to navigate | Space to toggle | A to select all | Enter to confirm | Q to cancel")
        print()

        current_item = 0

        if self.has_sections:
            # Display items grouped by section in order
            section_order = ["basic", "llm", "advanced"] if "basic" in self.sections else sorted(self.sections.keys())
            for section_name in section_order:
                if section_name not in self.sections:
                    continue
                section_title = self.section_titles.get(section_name, section_name.upper())
                print(f"=== {section_title.upper()} ===")
                print()

                for item_idx in self.sections[section_name]:
                    item = self.items[item_idx]
                    item_id = item[0]
                    name = item[1]

                    # Checkbox
                    checkbox = "[X]" if self.enabled[item_idx] else "[ ]"

                    # Selection indicator
                    indicator = ">" if current_item == self.selected_index else " "

                    # Display line
                    print(f"{indicator} {checkbox} {name:<30}")

                    current_item += 1

                print()
        else:
            # Display items without sections
            for i, item in enumerate(self.items):
                item_id = item[0]
                name = item[1]

                # Checkbox
                checkbox = "[X]" if self.enabled[i] else "[ ]"

                # Selection indicator
                indicator = ">" if i == self.selected_index else " "

                # Display line
                print(f"{indicator} {checkbox} {name:<30}")

            print()

        # Footer
        enabled_count = sum(1 for e in self.enabled.values() if e)
        print(f"Selected: {enabled_count}/{len(self.items)}")

        # Show description of currently selected item
        if self.selected_index < len(self.items):
            item_idx = self._get_item_at_index(self.selected_index) if self.has_sections else self.selected_index
            if item_idx is not None and item_idx < len(self.items):
                _, _, description = self.items[item_idx][:3]
                print()
                print(f"Description: {description}")

        if self.message:
            print()
            print(f">>> {self.message}")

    def _get_key(self):
        """Get a single keypress from the user."""
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)

        try:
            tty.setraw(sys.stdin.fileno())
            key = sys.stdin.read(1)

            # Handle arrow keys (they send escape sequences)
            if key == '\x1b':
                next_chars = sys.stdin.read(2)
                if next_chars == '[A':  # Up arrow
                    key = 'UP'
                elif next_chars == '[B':  # Down arrow
                    key = 'DOWN'

            return key
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

    def _get_item_at_index(self, idx):
        """Get the item index for the given selection index (handles sections)."""
        if not self.has_sections:
            return idx

        current = 0
        section_order = ["basic", "llm", "advanced"] if "basic" in self.sections else sorted(self.sections.keys())
        for section_name in section_order:
            if section_name not in self.sections:
                continue
            for item_idx in self.sections[section_name]:
                if current == idx:
                    return item_idx
                current += 1
        return None

    def run(self) -> Optional[List[str]]:
        """Main UI loop."""
        total_items = len(self.items)

        if total_items == 0:
            print(f"No items found for {self.title}")
            return []

        while True:
            self._display_menu()
            key = self._get_key()

            if key in ['q', 'Q', '\x03']:  # q or Ctrl+C
                print("\nConfiguration cancelled.")
                return None

            elif key in ['UP', 'w', 'W']:
                if self.selected_index > 0:
                    self.selected_index -= 1
                    self.message = ""

            elif key in ['DOWN', 's', 'S']:
                if self.selected_index < total_items - 1:
                    self.selected_index += 1
                    self.message = ""

            elif key == ' ':  # Space to toggle
                item_idx = self._get_item_at_index(self.selected_index) if self.has_sections else self.selected_index
                if item_idx is not None:
                    self.enabled[item_idx] = not self.enabled[item_idx]
                    item_id, name = self.items[item_idx][:2]
                    state = "enabled" if self.enabled[item_idx] else "disabled"
                    self.message = f"{name} {state}"

            elif key in ['a', 'A']:  # Select all
                for i in self.enabled:
                    self.enabled[i] = True
                self.message = "All items enabled"

            elif key in ['\r', '\n']:  # Enter to confirm
                self._clear_screen()
                return self._get_selected_items()

    def _get_selected_items(self) -> List[str]:
        """Get list of selected item IDs."""
        selected = []

        for i, item in enumerate(self.items):
            if self.enabled.get(i, False):
                item_id = item[0]
                selected.append(item_id)

        return selected

def save_configuration(workflows: List[str], mcps: List[str], config_dir: Path):
    """Save selected workflows and MCPs to configuration file"""
    config_file = config_dir / "workflows-installed.json"

    config = {
        "version": "1.0.0",
        "workflows": workflows,
        "mcps": mcps
    }

    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)

    return config_file

def main():
    # Check for developer mode flag
    developer_mode = "--developer" in sys.argv

    if developer_mode:
        print(" Developer Mode: Selecting all workflows and MCPs by default")
    else:
        print("  Configuring Claude Code workflows and MCPs...")
    print()

    # Get workflows directory
    workflows_dir = Path(__file__).parent

    # Get available workflows
    workflows_list = get_available_workflows(workflows_dir)

    # Select workflows
    print("Step 1: Select Workflows")
    print()

    workflow_configurator = ItemConfigurator(
        workflows_list,
        "Claude Code Workflows",
        developer_mode,
        has_sections=True,
        section_titles=WORKFLOW_SECTION_TITLES
    )
    selected_workflows = workflow_configurator.run()

    if selected_workflows is None:
        sys.exit(0)

    print()
    print(f" Selected {len(selected_workflows)} workflows")
    print()

    # Select MCPs
    print("Step 2: Select MCP Servers")
    print()

    mcp_configurator = ItemConfigurator(
        MCPS,
        "Claude Code MCP Servers",
        developer_mode
    )
    selected_mcps = mcp_configurator.run()

    if selected_mcps is None:
        sys.exit(0)

    print()
    print(f" Selected {len(selected_mcps)} MCP servers")
    print()

    # Save configuration
    config_file = save_configuration(selected_workflows, selected_mcps, workflows_dir)

    print(f" Configuration saved to {config_file}")
    print()
    print("Selected workflows:")
    for wf in selected_workflows:
        print(f"  • {wf}")
    print()
    print("Selected MCPs:")
    for mcp in selected_mcps:
        mcp_info = next((m for m in MCPS if m[0] == mcp), None)
        if mcp_info:
            print(f"  • {mcp_info[1]}")
    print()

    return 0

if __name__ == "__main__":
    sys.exit(main())
