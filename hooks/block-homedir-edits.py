#!/usr/bin/env python3
"""
Block edits to files in home directory

Prevents agents from modifying configuration files, settings, or any files
outside of project directories.

Allowed edit locations:
- /home/ubuntu/finetune_safe/
- /home/ubuntu/blog-with-comments-a2/
- /home/ubuntu/trl-fork/
- /home/ubuntu/mango/ (for hook development only)

All other locations in /home/ubuntu are FORBIDDEN.
"""
import sys
import json
import os


def main():
    # Read the tool input from stdin
    input_data = json.load(sys.stdin)

    # Get the file path being edited
    file_path = input_data.get("file_path", "")

    # Normalize to absolute path
    if not file_path.startswith("/"):
        file_path = os.path.abspath(file_path)

    # Define allowed directories (must be project directories)
    allowed_dirs = [
        "/home/ubuntu/finetune_safe/",
        "/home/ubuntu/blog-with-comments-a2/",
        "/home/ubuntu/trl-fork/",
        "/home/ubuntu/mango/hooks/",  # Only for hook development
    ]

    # Check if file is in an allowed directory
    allowed = any(file_path.startswith(allowed_dir) for allowed_dir in allowed_dirs)

    if not allowed:
        # Block the edit
        result = {
            "allow": False,
            "message": f"""
================================================================================
CRITICAL ERROR: HOME DIRECTORY EDIT BLOCKED
================================================================================

You attempted to edit a file outside of project directories:
  {file_path}

This is STRICTLY FORBIDDEN. Agents must NOT edit files in the home directory.

Allowed edit locations:
  - /home/ubuntu/finetune_safe/
  - /home/ubuntu/blog-with-comments-a2/
  - /home/ubuntu/trl-fork/
  - /home/ubuntu/mango/hooks/ (hook development only)

DO NOT attempt to edit:
  - ~/.claude/settings.json
  - ~/.config/
  - ~/.ssh/
  - Any other home directory files

If you need to configure something, do it in the PROJECT directory,
not in the home directory.

================================================================================
"""
        }
    else:
        # Allow the edit
        result = {"allow": True}

    # Write result to stdout
    json.dump(result, sys.stdout)


if __name__ == "__main__":
    main()
