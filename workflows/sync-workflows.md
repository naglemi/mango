---
description: Sync workflow files between ~/mango/workflows/ and Claude commands directories with git safety checks
allowed-tools: Bash(git *), Bash(cp *), Bash(ls *), Bash(diff *), Read, Write, mcp__report__send_report
---

# Workflow: Sync Workflows Between Locations

This workflow manages one-way synchronization of workflow markdown files between the central repository and Claude Code command directories, with comprehensive git safety checks.

## Critical Path Distinctions

**IMPORTANT: Do NOT confuse these directories:**
- `~/.claude/commands/` = User-level Claude commands directory (in HOME directory)
- `./.claude/commands/` = Project-level Claude commands directory (in CURRENT project)
- `~/mango/workflows/` = Central workflow repository (source of truth)

## User Intent Recognition

When the user requests workflow sync, determine their intent:

### Option 1: Central Repo → User Commands
**Intent**: "Sync workflows to my user commands" or "Update my Claude commands from the repo"
- **Source**: `~/mango/workflows/`
- **Destination**: `~/.claude/commands/`
- **Direction**: ONE-WAY ONLY (central repo → user commands)

### Option 2: Project Commands → Central Repo
**Intent**: "Sync project workflows back to the repo" or "Update repo from project commands"
- **Source**: `./.claude/commands/` (project-level)
- **Destination**: `~/mango/workflows/`
- **Direction**: ONE-WAY ONLY (project commands → central repo)

**If unclear which direction**, ask the user to clarify before proceeding.

---

## Pre-Sync Git Safety Protocol

**MANDATORY STEPS - Execute these BEFORE any file operations:**

### Step 1: Check Git Status
```bash
cd ~/mango
git status
```

**Required State**: Working tree must be clean
-  Acceptable: "nothing to commit, working tree clean"
-  Acceptable: Only untracked files in specs/ or other non-workflow areas
-  BLOCKER: Modified or staged files in workflows/
-  BLOCKER: Merge conflicts

### Step 2: Sync with Remote
```bash
cd ~/mango
git pull origin main
```

**Required Outcome**: Clean merge or already up-to-date
-  Acceptable: "Already up to date"
-  Acceptable: "Fast-forward" merge
-  BLOCKER: Merge conflicts
-  BLOCKER: Diverged branches requiring manual resolution

### Step 3: Blocker Handling

If ANY blocker is encountered:

1. **STOP immediately** - Do NOT proceed with sync
2. **Send detailed report** using mcp__report__send_report:
   - Title: "Workflow Sync BLOCKED - Manual Intervention Required"
   - Agent name: "workflow-sync-agent"
   - Include:
     - Current git status output
     - Specific blocker encountered
     - Current working directory
     - List of conflicting files if applicable
3. **Output clear message**: " BLOCKER DETECTED - Sent report and waiting for human guidance"
4. **WAIT** - Do not attempt to:
   - Stash changes
   - Reset branches
   - Force push
   - Resolve conflicts automatically
   - Continue with sync operation

---

## Sync Operation (Execute ONLY if Pre-Sync checks passed)

### Option 1: Central Repo → User Commands

**Purpose**: Deploy workflows from central repository to user's Claude Code commands

```bash
# Ensure destination exists
mkdir -p ~/.claude/commands/

# Copy all markdown files from central repo to user commands
cd ~/mango/workflows/
for file in *.md; do
  if [ -f "$file" ]; then
    echo "Syncing: $file → ~/.claude/commands/"
    cp -f "$file" ~/.claude/commands/
  fi
done

# Verify sync
echo " Sync complete: ~/mango/workflows/ → ~/.claude/commands/"
ls -la ~/.claude/commands/*.md
```

**Verification**:
- List all .md files in `~/.claude/commands/`
- Confirm file count matches source
- Spot-check 2-3 files with diff to verify content

### Option 2: Project Commands → Central Repo

**Purpose**: Sync project-specific workflows back to central repository

```bash
# Ensure source exists
if [ ! -d "./.claude/commands" ]; then
  echo " ERROR: ./.claude/commands/ does not exist in current project"
  exit 1
fi

# Copy all markdown files from project commands to central repo
cd ./.claude/commands/
for file in *.md; do
  if [ -f "$file" ]; then
    echo "Syncing: $file → ~/mango/workflows/"
    cp -f "$file" ~/mango/workflows/
  fi
done

# Verify sync
echo " Sync complete: ./.claude/commands/ → ~/mango/workflows/"
ls -la ~/mango/workflows/*.md
```

**Verification**:
- List all .md files in `~/mango/workflows/`
- Confirm new/updated files are present
- Show diff summary if files were modified

---

## Post-Sync Git Commit & Push

**Execute ONLY for Option 2** (Project Commands → Central Repo):

If files were synced TO ~/mango/workflows/, commit and push:

```bash
cd ~/mango
git add workflows/*.md
git status

# Show what will be committed
git diff --staged --stat

# Commit with descriptive message
git commit -m "$(cat <<'EOF'
Sync workflows from project commands to central repository

Updated workflow files from ./.claude/commands/ to ~/mango/workflows/

 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"

# Push to remote
git push origin main
```

**Verification**:
- Confirm commit was created successfully
- Confirm push completed without errors
- Check git status shows clean working tree

---

## Final Status Report

Provide summary to user:

```
 Workflow Sync Complete

Direction: [Source] → [Destination]
Files synced: [count]
Git status: [clean/committed/pushed]

Files updated:
- [list of filenames]

All operations completed successfully.
```

---

## Error Handling

### During Sync Operation
- If `cp` fails: Report specific file and error, ask user to check permissions
- If directory doesn't exist: Create it (mkdir -p) for destination
- If source directory is empty: Report but don't error (nothing to sync)

### During Git Operations
- If git add fails: Report files that couldn't be staged
- If git commit fails: Show error message, check for empty changeset
- If git push fails: Report error (e.g., network issue, remote ahead), ask user for guidance

**NEVER** use:
- `git stash`
- `git reset --hard`
- `git push --force`
- Any destructive git operation

---

## Usage Examples

**Example 1: User wants to update their Claude commands from the repo**
```
User: "Sync workflows to my Claude commands"
Agent: [Runs Pre-Sync checks] → [Executes Option 1] → " Synced 28 workflows to ~/.claude/commands/"
```

**Example 2: User wants to save project workflows back to repo**
```
User: "Update the repo with my project workflows"
Agent: [Runs Pre-Sync checks] → [Executes Option 2] → [Commits & Pushes] → " Synced and pushed 3 new workflows to main"
```

**Example 3: Git blocker encountered**
```
Agent: [Runs Pre-Sync checks] → [Detects uncommitted changes]
Agent: " BLOCKER: workflows/ has uncommitted changes"
Agent: [Sends report] → [Waits for human guidance]
```

---

## Notes

- This workflow is **one-way** only in each direction
- Source files always overwrite destination files (cp -f)
- No automatic conflict resolution - human decides
- Git operations use clean merges only
- All operations are transparent and logged
