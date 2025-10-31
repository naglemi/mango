#!/usr/bin/env python3
import json
import re
import sys

def check_command_for_protected_vars(command):
    """
    Check if a bash command attempts to modify protected environment variables.
    Protected variables are:
    1. Any variable containing "HUMAN" substring
    2. The "timeout" variable
    3. BASH_DEFAULT_TIMEOUT_MS
    4. BASH_MAX_TIMEOUT_MS
    """
    issues = []
    
    # Patterns that indicate variable modification
    modification_patterns = [
        # Direct assignment: VAR=value, export VAR=value
        r'\b(\w*HUMAN\w*|timeout|BASH_DEFAULT_TIMEOUT_MS|BASH_MAX_TIMEOUT_MS)\s*=',
        r'\bexport\s+(\w*HUMAN\w*|timeout|BASH_DEFAULT_TIMEOUT_MS|BASH_MAX_TIMEOUT_MS)\s*=',
        
        # Using set command: set VAR=value
        r'\bset\s+(\w*HUMAN\w*|timeout|BASH_DEFAULT_TIMEOUT_MS|BASH_MAX_TIMEOUT_MS)\s*=',
        
        # Using declare/typeset: declare VAR=value
        r'\b(declare|typeset)\s+.*\b(\w*HUMAN\w*|timeout|BASH_DEFAULT_TIMEOUT_MS|BASH_MAX_TIMEOUT_MS)\s*=',
        
        # Using unset to remove: unset VAR
        r'\bunset\s+(\w*HUMAN\w*|timeout|BASH_DEFAULT_TIMEOUT_MS|BASH_MAX_TIMEOUT_MS)\b',
        
        # Redirection that overwrites: echo "value" > $VAR
        r'>\s*\$(\w*HUMAN\w*|timeout|BASH_DEFAULT_TIMEOUT_MS|BASH_MAX_TIMEOUT_MS)\b',
        
        # Using eval to modify: eval "VAR=value"
        r'\beval\s+["\'].*(\w*HUMAN\w*|timeout|BASH_DEFAULT_TIMEOUT_MS|BASH_MAX_TIMEOUT_MS)\s*=',
        
        # Using source/. with assignment
        r'\b(source|\.)\s+.*(\w*HUMAN\w*|timeout|BASH_DEFAULT_TIMEOUT_MS|BASH_MAX_TIMEOUT_MS)\s*=',
    ]
    
    # Check for any pattern match
    for pattern in modification_patterns:
        match = re.search(pattern, command, re.IGNORECASE)
        if match:
            # Extract the variable name that was attempted to be modified
            var_name = None
            groups = match.groups()
            for group in groups:
                if group and ('HUMAN' in group.upper() or group.lower() == 'timeout' or group in ['BASH_DEFAULT_TIMEOUT_MS', 'BASH_MAX_TIMEOUT_MS']):
                    var_name = group
                    break
            
            if not var_name:
                # If we couldn't extract the exact variable, use a generic message
                var_name = "protected variable"
            
            issues.append(f"Attempting to modify protected variable '{var_name}'")
    
    # Additional check for indirect modifications through files
    indirect_patterns = [
        # Writing to files that might be sourced later
        r'echo\s+["\']?\w*HUMAN\w*\s*=.*["\']?\s*>',
        r'echo\s+["\']?timeout\s*=.*["\']?\s*>',
        r'printf\s+["\']?\w*HUMAN\w*\s*=.*["\']?\s*>',
        r'printf\s+["\']?timeout\s*=.*["\']?\s*>',
    ]
    
    for pattern in indirect_patterns:
        if re.search(pattern, command, re.IGNORECASE):
            issues.append("Attempting indirect modification of protected variables through file operations")
            break
    
    return issues

def main():
    try:
        # Read input from stdin
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON input: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Extract tool information
    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})
    
    # Only check Bash commands
    if tool_name != "Bash":
        sys.exit(0)
    
    command = tool_input.get("command", "")
    
    if not command:
        sys.exit(0)
    
    # Check for protected variable modifications
    issues = check_command_for_protected_vars(command)
    
    if issues:
        # Block the command and provide feedback
        print("SECURITY VIOLATION: Protected environment variables cannot be modified!", file=sys.stderr)
        print("", file=sys.stderr)
        print("The following issues were detected:", file=sys.stderr)
        for issue in issues:
            print(f"  • {issue}", file=sys.stderr)
        print("", file=sys.stderr)
        print("Protected variables include:", file=sys.stderr)
        print("  • Any variable containing 'HUMAN' substring", file=sys.stderr)
        print("  • The 'timeout' variable", file=sys.stderr)
        print("", file=sys.stderr)
        print("These variables are protected and cannot be modified by agents.", file=sys.stderr)
        
        # Exit code 2 blocks the tool call and shows stderr to Claude
        sys.exit(2)
    
    # Command is safe, allow it to proceed
    sys.exit(0)

if __name__ == "__main__":
    main()