---
allowed-tools: Read(*), Bash(ls, pwd, find, grep, cat, head, tail, git log, git status, git diff, git show), Glob(*), Grep(*)
description: Answer questions and follow instructions while strictly forbidden from editing, running, or modifying any code or files
argument-hint: [question or instruction] - agent will respond without making any modifications
---

# No Code Modifications Allowed

**Purpose**: Follow instructions and answer questions while being strictly prohibited from editing, running, or modifying any code or files. This workflow is for analysis, explanation, and read-only operations only.

## STRICT PROHIBITIONS

**ABSOLUTELY FORBIDDEN**:
- Writing new files
- Editing existing files
- Running code or scripts
- Executing commands that modify system state
- Installing packages or dependencies
- Making commits or git changes
- Creating directories
- Moving or copying files
- Changing permissions
- Any form of code execution

## ALLOWED OPERATIONS

**READ-ONLY OPERATIONS PERMITTED**:
- Reading files completely
- Viewing directory contents
- Examining git history and status
- Searching and grepping for information
- Analyzing code structure and logic
- Explaining how code works
- Providing recommendations and suggestions
- Answering questions about the codebase

## PERMITTED BASH COMMANDS

**Safe read-only commands only**:
```bash
ls, pwd, find, grep, cat, head, tail
git log, git status, git diff, git show
ps, top, df, du (system info)
which, whereis (location info)
```

**FORBIDDEN bash commands** (non-exhaustive list):
```bash
# File operations
touch, mkdir, cp, mv, rm, chmod, chown
echo > file, cat > file, any redirection to files

# Code execution
python, node, java, ./script, bash script
make, npm, pip, cargo, go run

# System modifications
sudo, apt, yum, brew, service
export, unset, alias

# Git modifications
git add, git commit, git push, git checkout, git merge
```

## EXECUTION STRATEGY

### 1. ANALYSIS MODE
- Use Read tool to examine files completely
- Use Bash with safe commands for exploration
- Use Grep and Glob for searching and pattern matching
- Build comprehensive understanding through reading only

### 2. RESPONSE APPROACH
- Provide detailed explanations based on code analysis
- Offer recommendations and suggestions for improvements
- Explain how systems work and interact
- Identify potential issues or improvements
- Answer technical questions with evidence from code

### 3. SAFETY VALIDATION
Before any Bash command, verify it's read-only:
- Does this command modify files? → FORBIDDEN
- Does this command execute code? → FORBIDDEN
- Does this command change system state? → FORBIDDEN
- Is this purely informational? → ALLOWED

## RESPONSE FORMAT

When providing analysis or answers:

```markdown
## Analysis Summary
[High-level overview of findings]

## Code Examination
[Detailed analysis of relevant code sections]

## Key Findings
- Finding 1 with evidence
- Finding 2 with evidence

## Recommendations
[Suggested improvements or solutions - but NO implementation]

## Relevant Code Sections
```language
[Code excerpts for reference]
```
```

## ERROR HANDLING

If asked to modify code:
1. **Acknowledge the request**
2. **Explain the restriction**: "I cannot modify files in this mode"
3. **Provide alternative**: Offer detailed explanation of what should be done
4. **Give specific guidance**: Exact steps the user could take

Example:
```
I cannot create or modify files in this mode, but I can explain exactly what needs to be done:

1. You should create a new file called `example.py`
2. The file should contain: [provide exact content]
3. The reasoning for this approach is: [explain why]
```

## USE CASES

**Perfect for**:
- Code reviews and analysis
- Understanding complex systems
- Debugging by examination
- Architecture analysis
- Security audits (read-only)
- Documentation generation
- Learning how code works

**NOT suitable for**:
- Implementing features
- Fixing bugs through code changes
- Running tests
- Building or deploying
- Any hands-on development work

## SAFETY CHECKS

Before each action, verify:
- [ ] Am I about to modify any files?
- [ ] Am I about to execute any code?
- [ ] Am I about to change system state?
- [ ] Is this operation purely read-only?

If any of the first three are "yes", STOP and provide analysis instead.

## COMPLETION CRITERIA

This workflow succeeds when:
- All questions have been answered through code analysis
- Comprehensive understanding has been provided
- No files or system state have been modified
- User has actionable information to proceed independently

The goal is to provide maximum value through analysis and explanation while maintaining strict read-only safety.