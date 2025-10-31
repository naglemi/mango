#!/usr/bin/env python3
"""
Claude Code Hook Installer
Install hooks from registry to global or project settings
"""

import json
import os
import sys
import argparse
from pathlib import Path
from typing import Dict, List, Optional
import subprocess


class HookInstaller:
    """Installs and manages Claude Code hooks from registry."""
    
    def __init__(self, registry_path: str = None):
        self.script_dir = Path(__file__).parent
        self.registry_path = Path(registry_path) if registry_path else self.script_dir / "hook_registry.json"
        self.registry = self._load_registry()
        
        # Define settings paths
        self.global_settings = Path.home() / ".claude" / "settings.json"
        self.project_settings = Path.cwd() / ".claude" / "settings.json"
        self.local_settings = Path.cwd() / ".claude" / "settings.local.json"
        
    def _load_registry(self) -> Dict:
        """Load the hook registry."""
        if not self.registry_path.exists():
            print(f"Error: Registry not found at {self.registry_path}")
            return {"hooks": {}}
        
        try:
            with open(self.registry_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading registry: {e}")
            return {"hooks": {}}
    
    def _get_hook_script_path(self, hook_id: str, scope: str) -> str:
        """Get the appropriate script path based on installation scope."""
        hook = self.registry["hooks"].get(hook_id, {})
        script_name = hook.get("script", "")
        
        if scope == "global":
            # For global hooks, use absolute path
            return str(self.script_dir / script_name)
        else:
            # For project hooks, use $CLAUDE_PROJECT_DIR variable
            return f"$CLAUDE_PROJECT_DIR/hooks/{script_name}"
    
    def _check_dependencies(self, hook_id: str) -> bool:
        """Check if hook dependencies are satisfied."""
        hook = self.registry["hooks"].get(hook_id, {})
        deps = hook.get("dependencies", [])
        
        if not deps:
            return True
        
        print(f"Checking dependencies for {hook_id}...")
        missing = []
        
        for dep in deps:
            # Check if command exists
            result = subprocess.run(
                f"which {dep}",
                shell=True,
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                missing.append(dep)
        
        if missing:
            print(f"Missing dependencies: {', '.join(missing)}")
            print(f"Please install them before using this hook.")
            return False
        
        print(f"All dependencies satisfied")
        return True
    
    def list_available(self, category: Optional[str] = None) -> None:
        """List available hooks from registry."""
        print("\n=== Available Hooks ===\n")
        
        if category:
            # List by category
            cat_info = self.registry.get("categories", {}).get(category)
            if not cat_info:
                print(f"Category not found: {category}")
                return
            
            print(f"Category: {cat_info['name']}")
            print(f"Description: {cat_info['description']}\n")
            
            for hook_id in cat_info.get("hooks", []):
                self._print_hook_info(hook_id)
        else:
            # List all hooks
            for hook_id in self.registry["hooks"]:
                self._print_hook_info(hook_id)
    
    def _print_hook_info(self, hook_id: str) -> None:
        """Print information about a specific hook."""
        hook = self.registry["hooks"].get(hook_id, {})
        if not hook:
            return
        
        print(f"ID: {hook_id}")
        print(f"  Name: {hook['name']}")
        print(f"  Description: {hook['description']}")
        print(f"  Event: {hook['event']}")
        print(f"  Tags: {', '.join(hook.get('tags', []))}")
        print(f"  Compatible: {', '.join(hook.get('compatible_with', []))}")
        if hook.get('dependencies'):
            print(f"  Dependencies: {', '.join(hook['dependencies'])}")
        print()
    
    def install_hook(self, hook_id: str, scope: str = "project", 
                     settings_path: Optional[str] = None) -> bool:
        """Install a hook from the registry."""
        
        # Validate hook exists
        if hook_id not in self.registry["hooks"]:
            print(f"Error: Hook '{hook_id}' not found in registry")
            self._suggest_similar(hook_id)
            return False
        
        hook = self.registry["hooks"][hook_id]
        
        # Check compatibility
        if scope not in hook.get("compatible_with", []):
            print(f"Error: Hook '{hook_id}' is not compatible with {scope} installation")
            print(f"Compatible scopes: {', '.join(hook['compatible_with'])}")
            return False
        
        # Check dependencies
        if not self._check_dependencies(hook_id):
            response = input("Install anyway? (y/N): ")
            if response.lower() != 'y':
                return False
        
        # Determine settings file
        if settings_path:
            settings_file = Path(settings_path)
        elif scope == "global":
            settings_file = self.global_settings
        elif scope == "local":
            settings_file = self.local_settings
        else:
            settings_file = self.project_settings
        
        # Ensure parent directory exists
        settings_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Get script path
        script_path = self._get_hook_script_path(hook_id, scope)
        
        # Install using hook_manager
        from hook_manager import HookManager
        manager = HookManager(str(settings_file))
        
        success = manager.add_hook(
            event=hook["event"],
            matcher=hook.get("matcher", ""),
            command=script_path,
            timeout=hook.get("timeout"),
            description=hook["description"]
        )
        
        if success:
            print(f"Installed '{hook['name']}' to {settings_file}")
            
            # Copy script to project if needed
            if scope == "project" and not (Path.cwd() / "hooks").exists():
                self._copy_hook_to_project(hook_id)
            
            return True
        else:
            print(f"Failed to install hook")
            return False
    
    def _copy_hook_to_project(self, hook_id: str) -> None:
        """Copy hook script to project hooks directory."""
        hook = self.registry["hooks"][hook_id]
        script_name = hook.get("script", "")
        
        src = self.script_dir / script_name
        if not src.exists():
            print(f"Warning: Script {script_name} not found")
            return
        
        dst_dir = Path.cwd() / "hooks"
        dst_dir.mkdir(exist_ok=True)
        
        dst = dst_dir / script_name
        
        try:
            import shutil
            shutil.copy2(src, dst)
            # Make executable
            dst.chmod(dst.stat().st_mode | 0o111)
            print(f"Copied script to {dst}")
        except Exception as e:
            print(f"Warning: Could not copy script: {e}")
    
    def _suggest_similar(self, hook_id: str) -> None:
        """Suggest similar hook IDs."""
        suggestions = []
        for existing_id in self.registry["hooks"]:
            if hook_id.lower() in existing_id.lower() or existing_id.lower() in hook_id.lower():
                suggestions.append(existing_id)
        
        if suggestions:
            print(f"Did you mean: {', '.join(suggestions)}?")
    
    def install_category(self, category: str, scope: str = "project") -> bool:
        """Install all hooks from a category."""
        cat_info = self.registry.get("categories", {}).get(category)
        if not cat_info:
            print(f"Error: Category '{category}' not found")
            print(f"Available categories: {', '.join(self.registry.get('categories', {}).keys())}")
            return False
        
        print(f"\nInstalling category: {cat_info['name']}")
        print(f"Description: {cat_info['description']}\n")
        
        installed = 0
        failed = 0
        
        for hook_id in cat_info.get("hooks", []):
            print(f"Installing {hook_id}...")
            if self.install_hook(hook_id, scope):
                installed += 1
            else:
                failed += 1
        
        print(f"\nInstalled {installed} hooks")
        if failed:
            print(f"Failed to install {failed} hooks")
        
        return failed == 0
    
    def create_hook_script(self, hook_id: str, template: str = "basic") -> bool:
        """Create a new hook script from template."""
        templates = {
            "basic": '''#!/usr/bin/env python3
import json
import sys

try:
    input_data = json.load(sys.stdin)
except json.JSONDecodeError as e:
    print(f"Error: Invalid JSON input: {e}", file=sys.stderr)
    sys.exit(1)

# Extract relevant data
tool_name = input_data.get("tool_name", "")
tool_input = input_data.get("tool_input", {})

# Your validation logic here
# ...

# Exit codes:
# 0 - Allow operation
# 2 - Block operation (stderr shown to Claude)
# Other - Non-blocking error (stderr shown to user)

sys.exit(0)
''',
            "validator": '''#!/usr/bin/env python3
import json
import sys
import re

VALIDATION_RULES = [
    # (pattern, error_message)
]

def validate(data):
    """Validate the input data."""
    issues = []
    # Add validation logic
    return issues

try:
    input_data = json.load(sys.stdin)
    
    issues = validate(input_data)
    
    if issues:
        for issue in issues:
            print(f"• {issue}", file=sys.stderr)
        sys.exit(2)  # Block with feedback
    
    sys.exit(0)  # Allow
    
except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
    sys.exit(1)
''',
            "notifier": '''#!/usr/bin/env python3
import json
import sys

try:
    input_data = json.load(sys.stdin)
    
    # Send notification
    # Your notification logic here
    
    sys.exit(0)
    
except Exception as e:
    print(f"Error: {e}", file=sys.stderr)
    sys.exit(1)
'''
        }
        
        if template not in templates:
            print(f"Error: Unknown template '{template}'")
            print(f"Available templates: {', '.join(templates.keys())}")
            return False
        
        script_path = self.script_dir / f"{hook_id}.py"
        
        if script_path.exists():
            response = input(f"Script {script_path} already exists. Overwrite? (y/N): ")
            if response.lower() != 'y':
                return False
        
        try:
            with open(script_path, 'w') as f:
                f.write(templates[template])
            
            # Make executable
            script_path.chmod(script_path.stat().st_mode | 0o111)
            
            print(f"Created hook script: {script_path}")
            print(f"Edit the script to add your logic, then register it in hook_registry.json")
            return True
            
        except Exception as e:
            print(f"Error creating script: {e}")
            return False


def main():
    parser = argparse.ArgumentParser(description="Claude Code Hook Installer")
    parser.add_argument("--registry", help="Path to hook registry JSON")
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List available hooks")
    list_parser.add_argument("--category", help="Filter by category")
    
    # Install command
    install_parser = subparsers.add_parser("install", help="Install a hook")
    install_parser.add_argument("hook_id", help="Hook ID from registry")
    install_parser.add_argument("--scope", choices=["global", "project", "local"],
                               default="project", help="Installation scope")
    install_parser.add_argument("--settings", help="Custom settings file path")
    
    # Install category
    cat_parser = subparsers.add_parser("install-category", help="Install all hooks from a category")
    cat_parser.add_argument("category", help="Category name")
    cat_parser.add_argument("--scope", choices=["global", "project", "local"],
                           default="project", help="Installation scope")
    
    # Create command
    create_parser = subparsers.add_parser("create", help="Create new hook script")
    create_parser.add_argument("hook_id", help="New hook ID")
    create_parser.add_argument("--template", choices=["basic", "validator", "notifier"],
                              default="basic", help="Template type")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    installer = HookInstaller(args.registry if hasattr(args, 'registry') else None)
    
    if args.command == "list":
        installer.list_available(args.category)
        return 0
    
    elif args.command == "install":
        success = installer.install_hook(args.hook_id, args.scope, args.settings)
        return 0 if success else 1
    
    elif args.command == "install-category":
        success = installer.install_category(args.category, args.scope)
        return 0 if success else 1
    
    elif args.command == "create":
        success = installer.create_hook_script(args.hook_id, args.template)
        return 0 if success else 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())