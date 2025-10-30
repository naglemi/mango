#!/usr/bin/env python3
"""
Install selected workflows and MCP servers
Reads workflows-installed.json and configures Claude Code
"""

import json
import os
import sys
import subprocess
import shutil
from pathlib import Path
from typing import Dict, List

# MCP configuration details
MCP_CONFIGS = {
    "pushover": {
        "name": "pushover",
        "command": ["npx", "-y", "pushover-mcp", "start"],
        "env_vars": {
            "PUSHOVER_APP_TOKEN": os.environ.get("PUSHOVER_APP_TOKEN", ""),
            "PUSHOVER_USER_KEY": os.environ.get("PUSHOVER_USER_KEY", "")
        },
        "requires_npm_global": "pushover-mcp"
    },
    "report": {
        "name": "report",
        "command": ["node", "{script_path}"],
        "script": "mcp/report/index.js",
        "env_vars": {
            "REPORT_BUCKET": "usability-reports",
            "AWS_REGION": "us-east-1",
            "REPORT_EMAIL_FROM": "your-email@example.com",
            "REPORT_EMAIL_TO": "your-email@example.com",
            "REPORT_URL_EXPIRATION": "604800"
        }
    },
    "ninjagrab": {
        "name": "ninjagrab",
        "command": ["{python_cmd}", "{script_path}"],
        "script": "mcp/ninjagrab/ninjagrab_mcp_server.py",
        "env_vars": {
            "NINJAGRAB_SCRIPT_PATH": "{workflows_dir}/ninjagrab.sh"
        }
    },
    "process-monitor": {
        "name": "process-monitor",
        "command": ["{python_cmd}", "{script_path}"],
        "script": "mcp/process-monitor/process_monitor_mcp_server.py"
    },
    "sleep": {
        "name": "sleep",
        "command": ["{python_cmd}", "{script_path}"],
        "script": "mcp/sleep/sleep_mcp_server.py"
    },
    "gpt5-proxy": {
        "name": "gpt5-proxy",
        "command": ["{python_cmd}", "{script_path}"],
        "script": "mcp/gpt5-proxy/gpt5_proxy_mcp_server.py",
        "env_vars": {
            "OPENAI_API_KEY": os.environ.get("OPENAI_API_KEY", "")
        }
    },
    "grok-proxy": {
        "name": "grok-proxy",
        "command": ["{python_cmd}", "{script_path}"],
        "script": "mcp/grok-proxy/grok_proxy_mcp_server.py",
        "env_vars": {
            "XAI_API_KEY": os.environ.get("XAI_API_KEY", "")
        }
    }
}

def load_installed_config(workflows_dir: Path) -> Dict:
    """Load the workflows-installed.json configuration"""
    config_file = workflows_dir / "workflows-installed.json"

    if not config_file.exists():
        print(f"ERROR: {config_file} not found")
        print("Run configure-workflows.py first to select workflows and MCPs")
        sys.exit(1)

    with open(config_file, 'r') as f:
        return json.load(f)

def install_workflows(workflow_ids: List[str], workflows_dir: Path, developer_mode: bool = False) -> int:
    """Install selected workflows to Claude commands directory"""
    claude_commands = Path.home() / ".claude" / "commands"
    claude_commands.mkdir(parents=True, exist_ok=True)

    installed_count = 0

    # Install public workflows
    for wf_id in workflow_ids:
        wf_file = workflows_dir / f"{wf_id}.md"
        if wf_file.exists():
            shutil.copy(wf_file, claude_commands / f"{wf_id}.md")
            installed_count += 1
        else:
            print(f"Warning: Workflow file not found: {wf_file}")

    # If developer mode, also install private workflows
    if developer_mode:
        private_workflows_dir = Path.home() / "mango-dev" / "workflows"
        if private_workflows_dir.exists():
            for wf_file in private_workflows_dir.glob("*.md"):
                shutil.copy(wf_file, claude_commands / wf_file.name)
                installed_count += 1

    return installed_count

def detect_python_command() -> str:
    """Detect available Python command"""
    if shutil.which("python3"):
        return "python3"
    elif shutil.which("python"):
        return "python"
    else:
        print("ERROR: Python not found")
        sys.exit(1)

def install_mcp(mcp_id: str, base_dir: Path) -> bool:
    """Install a single MCP server using claude mcp add"""
    if mcp_id not in MCP_CONFIGS:
        print(f"Warning: Unknown MCP '{mcp_id}', skipping")
        return False

    config = MCP_CONFIGS[mcp_id]
    python_cmd = detect_python_command()

    # Build command
    command = []
    for part in config["command"]:
        if "{script_path}" in part:
            script_path = base_dir / config["script"]
            command.append(part.replace("{script_path}", str(script_path.resolve())))
        elif "{python_cmd}" in part:
            command.append(part.replace("{python_cmd}", python_cmd))
        elif "{workflows_dir}" in part:
            workflows_dir = base_dir / "workflows"
            command.append(part.replace("{workflows_dir}", str(workflows_dir.resolve())))
        else:
            command.append(part)

    # Remove existing MCP first
    subprocess.run(["claude", "mcp", "remove", config["name"], "--scope", "user"],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Build claude mcp add command
    claude_cmd = ["claude", "mcp", "add", config["name"], "--scope", "user"]

    # Add environment variables
    if "env_vars" in config:
        for env_key, env_value in config["env_vars"].items():
            # Load from bashrc if available
            if env_key in os.environ:
                env_value = os.environ[env_key]
            claude_cmd.extend(["-e", f"{env_key}={env_value}"])

    # Add separator and command
    claude_cmd.append("--")
    claude_cmd.extend(command)

    # Run installation
    try:
        result = subprocess.run(claude_cmd, check=True, capture_output=True, text=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"  Error installing {config['name']}: {e.stderr}")
        return False

def install_npm_package(package: str) -> bool:
    """Install npm package globally if needed"""
    # Check if already installed
    try:
        result = subprocess.run(["npm", "list", "-g", package],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if result.returncode == 0:
            return True
    except:
        pass

    # Install it
    print(f"  Installing {package} globally...")
    try:
        subprocess.run(["npm", "install", "-g", package], check=True)
        return True
    except subprocess.CalledProcessError:
        print(f"  Failed to install {package}")
        print(f"  You may need to use sudo: sudo npm install -g {package}")
        return False

def main():
    print(" Installing selected workflows and MCPs...")
    print()

    # Get directories
    workflows_dir = Path(__file__).parent
    base_dir = workflows_dir.parent

    # Check for developer mode (for private workflows)
    developer_mode = "--developer" in sys.argv

    # Load configuration
    try:
        config = load_installed_config(workflows_dir)
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    selected_workflows = config.get("workflows", [])
    selected_mcps = config.get("mcps", [])

    # Install workflows
    if selected_workflows:
        print("Installing workflows...")
        count = install_workflows(selected_workflows, workflows_dir, developer_mode)
        print(f" Installed {count} workflows to ~/.claude/commands/")
        print()

    # Install MCPs
    if selected_mcps:
        print("Installing MCP servers...")

        # Check for required npm packages
        for mcp_id in selected_mcps:
            if mcp_id in MCP_CONFIGS:
                config = MCP_CONFIGS[mcp_id]
                if "requires_npm_global" in config:
                    if not install_npm_package(config["requires_npm_global"]):
                        print(f"  Skipping {mcp_id} due to npm install failure")
                        continue

        # Install MCPs
        success_count = 0
        for mcp_id in selected_mcps:
            mcp_name = MCP_CONFIGS.get(mcp_id, {}).get("name", mcp_id)
            print(f"  Adding {mcp_name}...")
            if install_mcp(mcp_id, base_dir):
                success_count += 1
                print(f"   {mcp_name} installed")
            else:
                print(f"   {mcp_name} failed")

        print()
        print(f" Installed {success_count}/{len(selected_mcps)} MCP servers")
        print()

    # Summary
    print("Installation complete!")
    print()
    print("Next steps:")
    print("  1. Restart Claude Code to load new configurations")
    print("  2. Check MCP status with: claude mcp list")
    print("  3. Check workflows with: /workflow")
    print()

    return 0

if __name__ == "__main__":
    sys.exit(main())
