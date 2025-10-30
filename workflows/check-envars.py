#!/usr/bin/env python3
"""
Check and configure required environment variables for MCPs
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple

# MCP environment variable requirements
MCP_ENV_REQUIREMENTS = {
    "pushover": {
        "name": "Pushover Notifications",
        "required_vars": {
            "PUSHOVER_APP_TOKEN": "Pushover application token",
            "PUSHOVER_USER_KEY": "Pushover user key"
        },
        "instructions": "Get your keys from https://pushover.net/"
    },
    "report": {
        "name": "Report System",
        "required_vars": {
            "REPORT_EMAIL_FROM": "Email address to send reports from",
            "REPORT_EMAIL_TO": "Email address to send reports to",
            "REPORT_AWS_ACCESS_KEY_ID": "AWS access key for Report MCP S3/SES (EMAIL mode only)",
            "REPORT_AWS_SECRET_ACCESS_KEY": "AWS secret key for Report MCP S3/SES (EMAIL mode only)"
        },
        "optional_vars": ["REPORT_AWS_ACCESS_KEY_ID", "REPORT_AWS_SECRET_ACCESS_KEY"],
        "mode_check": "USABILIDE_REPORT_FOLDER",
        "instructions": "For EMAIL mode (cloud reports via S3/SES):\n  - Enter AWS credentials for the usability-reports S3 bucket\n  - These are DIFFERENT from CLAUDE.md credentials\n  - Report MCP needs its own dedicated AWS account credentials\n\nFor LOCAL mode (filesystem reports):\n  - Set USABILIDE_REPORT_FOLDER to a directory path\n  - AWS credentials are NOT needed in LOCAL mode"
    },
    "gpt5-proxy": {
        "name": "GPT-5 Proxy",
        "required_vars": {
            "OPENAI_API_KEY": "OpenAI API key for GPT-5 access"
        },
        "instructions": "Get your API key from https://platform.openai.com/api-keys"
    },
    "grok-proxy": {
        "name": "Grok Proxy",
        "required_vars": {
            "XAI_API_KEY": "xAI API key for Grok model access"
        },
        "instructions": "Get your API key from https://x.ai/api"
    }
}

# Workflow environment variable requirements
WORKFLOW_ENV_REQUIREMENTS = {
    "deepseek-plea": {
        "name": "DeepSeek Plea (AWS Bedrock)",
        "required_vars": {
            "AWS_ACCESS_KEY_ID": "AWS access key ID for Bedrock API",
            "AWS_SECRET_ACCESS_KEY": "AWS secret access key for Bedrock API"
        },
        "instructions": "Get AWS credentials from https://console.aws.amazon.com/iam/\nEnsure your IAM user has bedrock:InvokeModel permissions"
    },
    "gpt5plea": {
        "name": "GPT-5 Plea (OpenAI)",
        "required_vars": {
            "OPENAI_API_KEY": "OpenAI API key for GPT-5 access"
        },
        "instructions": "Get your API key from https://platform.openai.com/api-keys"
    },
    "grokplea": {
        "name": "Grok Plea (xAI)",
        "required_vars": {
            "XAI_API_KEY": "xAI API key for Grok model access"
        },
        "instructions": "Get your API key from https://x.ai/api"
    }
}

def check_var_exists(var_name: str) -> bool:
    """Check if environment variable exists"""
    return var_name in os.environ and os.environ[var_name].strip() != ""

def check_var_in_bashrc(var_name: str) -> bool:
    """Check if variable is defined in ~/.bashrc"""
    bashrc = Path.home() / ".bashrc"
    if not bashrc.exists():
        return False

    with open(bashrc, 'r') as f:
        content = f.read()
        return f'export {var_name}=' in content or f'{var_name}=' in content

def add_to_bashrc(var_name: str, var_value: str):
    """Add environment variable to ~/.bashrc"""
    bashrc = Path.home() / ".bashrc"

    # Escape double quotes in value
    var_value_escaped = var_value.replace('"', '\\"')

    with open(bashrc, 'a') as f:
        f.write(f'\n# Added by mango workflows setup\n')
        f.write(f'export {var_name}="{var_value_escaped}"\n')

    print(f" Added {var_name} to ~/.bashrc")

def configure_envars(item_id: str, item_type: str = "mcp") -> bool:
    """
    Configure environment variables for an MCP or workflow
    Returns True if vars configured/not needed, False if user wants to skip this item
    """
    requirements = MCP_ENV_REQUIREMENTS if item_type == "mcp" else WORKFLOW_ENV_REQUIREMENTS

    if item_id not in requirements:
        # No env vars required for this item - always include it
        return True

    item_config = requirements[item_id]

    # Check if this item has mode-based optional vars (like report MCP)
    mode_check_var = item_config.get("mode_check")
    optional_vars = item_config.get("optional_vars", [])

    # If mode check variable is set (LOCAL mode), skip AWS credential requirements
    if mode_check_var and check_var_exists(mode_check_var):
        mode_value = os.environ.get(mode_check_var, "").strip()
        if mode_value and mode_value != "EMAIL":
            print(f"\n{'='*60}")
            print(f"{item_config['name']}: LOCAL MODE DETECTED")
            print(f"{'='*60}")
            print(f"  {mode_check_var}={mode_value}")
            print(f"  AWS credentials not required in LOCAL mode")
            print(f"  Configuration complete")
            return True

    print(f"\n{'='*60}")
    print(f"Configuring: {item_config['name']}")
    print(f"{'='*60}")

    if "instructions" in item_config:
        print(f"\n{item_config['instructions']}\n")

    missing_vars = []
    for var_name, var_desc in item_config["required_vars"].items():
        # Skip optional vars if they're truly optional (not required for current mode)
        if var_name in optional_vars:
            # These are conditional - only required in EMAIL mode
            continue
        if not check_var_exists(var_name) and not check_var_in_bashrc(var_name):
            missing_vars.append((var_name, var_desc))

    if not missing_vars:
        print(f" All required environment variables already configured")
        return True

    print(f"Missing environment variables:")
    for var_name, var_desc in missing_vars:
        print(f"  • {var_name}: {var_desc}")

    print(f"\nOptions:")
    print(f"  1. Enter keys now (will be added to ~/.bashrc)")
    print(f"  2. Skip - disable {item_config['name']} (can configure later)")
    print(f"  3. Abort setup")

    while True:
        choice = input("\nChoice [1/2/3]: ").strip()

        if choice == "1":
            # Prompt for each missing variable
            for var_name, var_desc in missing_vars:
                print(f"\nEnter {var_name}")
                print(f"  ({var_desc})")
                value = input(f"  Value: ").strip()

                if value:
                    add_to_bashrc(var_name, value)
                    os.environ[var_name] = value  # Set in current environment too
                else:
                    print(f"  Skipped {var_name} (left empty)")

            print(f"\n Configuration complete for {item_config['name']}")
            return True

        elif choice == "2":
            print(f"\n⊘ Skipping {item_config['name']} - will be disabled")
            return False  # Signal that this item should be skipped

        elif choice == "3":
            print("\nAborting setup...")
            sys.exit(0)

        else:
            print("Invalid choice. Please enter 1, 2, or 3.")

def check_selected_items(selected_items: List[str], item_type: str = "mcp") -> Tuple[List[str], List[str]]:
    """
    Check environment variables for selected MCPs or workflows
    Returns (valid_items, skipped_items)
    """
    valid_items = []
    skipped_items = []
    requirements = MCP_ENV_REQUIREMENTS if item_type == "mcp" else WORKFLOW_ENV_REQUIREMENTS
    item_type_name = "MCP" if item_type == "mcp" else "workflow"

    for item_id in selected_items:
        # Check if env vars needed
        if item_id not in requirements:
            print(f" {item_id}: No environment variables required")
            valid_items.append(item_id)
        elif configure_envars(item_id, item_type):
            valid_items.append(item_id)
        else:
            skipped_items.append(item_id)

    return valid_items, skipped_items

def main():
    """Check environment variables for MCPs and workflows"""
    if len(sys.argv) < 3:
        print("Usage: check-envars.py --mcps mcp1 mcp2 ... [--workflows wf1 wf2 ...]")
        print("   or: check-envars.py --workflows wf1 wf2 ...")
        sys.exit(1)

    import json

    # Parse arguments
    mcps = []
    workflows = []
    current_list = None

    for arg in sys.argv[1:]:
        if arg == "--mcps":
            current_list = mcps
        elif arg == "--workflows":
            current_list = workflows
        elif current_list is not None:
            current_list.append(arg)

    valid_mcps = []
    skipped_mcps = []
    valid_workflows = []
    skipped_workflows = []

    # Check MCPs
    if mcps:
        print("\n" + "="*60)
        print("CHECKING MCP ENVIRONMENT VARIABLES")
        print("="*60)
        valid_mcps, skipped_mcps = check_selected_items(mcps, "mcp")

    # Check workflows
    if workflows:
        print("\n" + "="*60)
        print("CHECKING WORKFLOW ENVIRONMENT VARIABLES")
        print("="*60)
        valid_workflows, skipped_workflows = check_selected_items(workflows, "workflow")

    # Print summary
    print("\n" + "="*60)
    print("CONFIGURATION SUMMARY")
    print("="*60)
    if mcps:
        print(f"MCPs to install: {len(valid_mcps)}")
        if skipped_mcps:
            print(f"MCPs skipped: {len(skipped_mcps)} ({', '.join(skipped_mcps)})")
    if workflows:
        print(f"Workflows to install: {len(valid_workflows)}")
        if skipped_workflows:
            print(f"Workflows skipped: {len(skipped_workflows)} ({', '.join(skipped_workflows)})")
    print("="*60)

    # Output as JSON for easy parsing by shell script
    print("VALID_MCPS=" + json.dumps(valid_mcps))
    print("VALID_WORKFLOWS=" + json.dumps(valid_workflows))

    return 0

if __name__ == "__main__":
    sys.exit(main())
