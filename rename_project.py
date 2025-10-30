#!/usr/bin/env python3
"""
Rename project from 'usability' to 'mango' throughout codebase.
This script performs the renaming and outputs the changes for review.
"""

import os
import re
from pathlib import Path

def should_skip(path):
    """Check if path should be skipped"""
    skip_patterns = ['.git', 'node_modules', '__pycache__', '.pyc']
    return any(pattern in str(path) for pattern in skip_patterns)

def process_file(filepath):
    """Process a single file and return replacements made"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content
        changes = []

        # Replace /home/ubuntu/mango with /home/ubuntu/mango
        if '/home/ubuntu/mango' in content:
            content = content.replace('/home/ubuntu/mango', '/home/ubuntu/mango')
            changes.append('path: /home/ubuntu/mango -> /home/ubuntu/mango')

        # Replace ~/mango with ~/mango
        if '~/mango' in content:
            content = content.replace('~/mango', '~/mango')
            changes.append('path: ~/mango -> ~/mango')

        # Replace $HOME/mango with $HOME/mango
        if '$HOME/mango' in content:
            content = content.replace('$HOME/mango', '$HOME/mango')
            changes.append('path: $HOME/mango -> $HOME/mango')

        # Replace mango-reports bucket with mango-reports
        if 'mango-reports' in content:
            content = content.replace('mango-reports', 'mango-reports')
            changes.append('bucket: mango-reports -> mango-reports')

        # Replace .mango_ prefixes with .mango_
        if '.mango_' in content:
            content = content.replace('.mango_', '.mango_')
            changes.append('prefix: .mango_ -> .mango_')

        # Replace "Mango Toolkit" with "Mango Toolkit"
        if 'Mango Toolkit' in content:
            content = content.replace('Mango Toolkit', 'Mango Toolkit')
            changes.append('name: Mango Toolkit -> Mango Toolkit')

        # Replace usability/workflows with mango/workflows (case where not full path)
        if 'usability/workflows' in content and '/home/ubuntu/mango/workflows' not in content:
            content = content.replace('usability/workflows', 'mango/workflows')
            changes.append('path: usability/workflows -> mango/workflows')

        # Write back if changes were made
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True, changes

        return False, []
    except Exception as e:
        return False, [f'ERROR: {e}']

def main():
    base_dir = Path('/home/ubuntu/mango')
    extensions = {'.sh', '.py', '.js', '.mjs', '.json', '.md', '.conf'}

    print("🥭 Renaming project from 'usability' to 'mango'\n")

    total_files = 0
    modified_files = 0

    for root, dirs, files in os.walk(base_dir):
        # Skip unwanted directories
        dirs[:] = [d for d in dirs if not should_skip(Path(root) / d)]

        for file in files:
            filepath = Path(root) / file

            if filepath.suffix in extensions and not should_skip(filepath):
                total_files += 1
                modified, changes = process_file(filepath)

                if modified:
                    modified_files += 1
                    print(f"✓ {filepath.relative_to(base_dir)}")
                    for change in changes:
                        print(f"  - {change}")

    print(f"\n📊 Summary:")
    print(f"  Total files scanned: {total_files}")
    print(f"  Files modified: {modified_files}")
    print(f"\n✅ Renaming complete!")

if __name__ == '__main__':
    main()
