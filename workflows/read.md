---
allowed-tools: Read(*), Bash(*), Glob(*), Grep(*)
description: Read entire files into context before proceeding with tasks - no searching, grepping, or head/tail operations
argument-hint: [file1] [file2] [...] or [directory] or leave empty to read context-relevant files
---

# Read Entire Files Into Context

**Purpose**: Load complete file contents into context before proceeding with existing todo/instructions. This workflow emphasizes READING ENTIRE FILES rather than searching, grepping, or using head/tail operations.

## EXECUTION STRATEGY

**Core Principle**: Read files completely to understand the full context rather than searching for specific snippets. Follow imports, dependencies, and related files to build comprehensive understanding.

## ARGUMENT PARSING

Parse arguments to determine what to read:
```bash
if [[ -z "$ARGUMENTS" ]]; then
    # No arguments - read context-relevant files based on current working directory and existing todos
    MODE="context"
elif [[ -f "$ARGUMENTS" ]]; then
    # Single file provided
    MODE="file"
    TARGET="$ARGUMENTS"
elif [[ -d "$ARGUMENTS" ]]; then
    # Directory provided
    MODE="directory"
    TARGET="$ARGUMENTS"
else
    # Multiple files or pattern
    MODE="files"
    FILES="$ARGUMENTS"
fi
```

## READING STRATEGY BY MODE

### MODE: "context" (No arguments provided)
1. **Analyze current working directory**
   - Read main entry points (main.py, index.js, README.md, etc.)
   - Read configuration files (package.json, requirements.txt, Cargo.toml, etc.)
   - Read project documentation files

2. **Follow the dependency chain**
   - After reading main files, identify imports/dependencies
   - Read imported modules and dependencies
   - Continue following the chain until comprehensive understanding is achieved

3. **Check for existing todos/instructions**
   - Read any SCIENTIST.md, ADVISOR.md, or other project-specific instruction files
   - Read CLAUDE.md files for project-specific context

### MODE: "file" (Single file provided)
1. **Read the target file completely**
2. **Follow imports and dependencies**
   - Identify all imports, includes, or dependencies in the file
   - Read each imported file completely
   - Continue following the dependency chain recursively

### MODE: "directory" (Directory provided)
1. **Survey directory structure**
   - List all files in the directory and subdirectories
   - Identify key files (entry points, configs, docs)

2. **Read systematically**
   - Start with main/entry files
   - Read configuration and documentation
   - Read source files in logical order
   - Follow import chains

### MODE: "files" (Multiple files provided)
1. **Read each file completely**
2. **For each file, follow its imports**
3. **Build comprehensive understanding of the entire system**

## READING METHODOLOGY

### File Reading Approach
- **ALWAYS use Read tool** - never head, tail, cat, or other partial reading methods
- **Read files completely** - avoid skipping sections or limiting line counts
- **Follow imports systematically** - when you see an import/include, read that file too
- **Understand relationships** - how files connect and depend on each other

### Import/Dependency Following
For different languages, follow these patterns:

**Python**:
```python
import module_name          # → Read module_name.py
from package import func    # → Read package/__init__.py and related files
```

**JavaScript/TypeScript**:
```javascript
import { func } from './file'    # → Read ./file.js/.ts
const module = require('path')   # → Read path/index.js
```

**Other Languages**:
- Follow #include statements in C/C++
- Follow import/use statements in Rust, Go, etc.
- Follow require statements in Ruby
- Follow package declarations and dependencies

### Context Building Strategy
1. **Start broad** - Read main files to understand overall purpose
2. **Go deep** - Follow specific functionality into implementation details
3. **Connect dots** - Understand how different components interact
4. **Build mental model** - Form comprehensive understanding before taking action

## EXECUTION PROTOCOL

1. **DETERMINE MODE** from arguments
2. **READ SYSTEMATICALLY** following the mode-specific strategy
3. **FOLLOW IMPORTS** recursively to build complete context
4. **AVOID SEARCHING** - never use grep, find, head, tail for understanding
5. **BUILD COMPREHENSIVE MODEL** of the codebase/system
6. **PROCEED WITH EXISTING TODOS** once context is fully loaded

## IMPORTANT PRINCIPLES

### DO:
- Read entire files using the Read tool
- Follow import chains completely
- Understand file relationships and dependencies
- Build comprehensive mental models
- Read configuration files, documentation, and related files

### DON'T:
- Use head, tail, cat, or other partial reading methods
- Use grep or search tools to find specific lines
- Skip files or sections
- Make assumptions without reading the full context
- Stop at the first file - follow the entire dependency chain

## COMPLETION CRITERIA

This workflow is complete when:
- All relevant files have been read completely
- Import/dependency chains have been followed
- A comprehensive understanding of the system has been built
- You can proceed with existing todos/instructions with full context

The goal is to have COMPLETE understanding of the relevant codebase/system before taking any action, ensuring decisions are made with full knowledge rather than partial context from searching or grepping.