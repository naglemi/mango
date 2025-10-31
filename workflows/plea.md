---
allowed-tools: Bash(*), Read(*), Write(*), mcp__report__send_report, mcp__ninjagrab__ninjagrab_collect
description: Generate comprehensive technical analysis request with complete context
argument-hint: [brief issue description - will be expanded with detail]
---

# Generate Comprehensive Technical Analysis Request

You are creating a technical document that provides complete context for getting expert help with a technical issue.

## Requirements for the Analysis

### 1. Problem Description
- **Root cause analysis** of what's failing and why
- **Error documentation** with stack traces, timing data, system calls
- **Timeline** showing attempts made and their outcomes
- **System state** at time of issue including relevant metrics (memory, CPU, etc.)

### 2. Solution History  
- **Solutions attempted** with commands, code changes, configuration modifications
- **Why each attempt didn't work** with error messages and observations
- **Code evolution** showing how the problem has been approached
- **Configuration changes** documenting environment/container/system modifications

### 3. Information Needed
The analysis should request:
- **Root cause identification** with supporting evidence
- **Technical solution** with implementation steps
- **Alternative approaches** if applicable
- **Optimization suggestions** if relevant
- **Prevention measures** to avoid recurrence

### 4. System Context
Include relevant system information:
- **Environment configuration** (relevant env vars, paths, versions)
- **Resource utilization** if relevant to the issue
- **Process information** if applicable
- **Container details** if using containers
- **Dependencies** (packages, versions, any conflicts)

## Current Context Deep-Dive

**Issue**: $ARGUMENTS

**Project State**:
- Directory: (run pwd to get current directory)
- Git status: (run git status --porcelain to get status)
- Branch: (run git branch --show-current to get branch)
- Recent commits: (run git log --oneline -10 to get commits)

### CRITICAL: AI/ML Project Log Collection

**FOR AI/ML PROJECTS WITH WANDB + CONTAINERS**: If this is an AI/ML training project using W&B and Singularity/Docker containers, you MUST get the MOST RECENT logs using these methods:

1. **Primary Method**: Use wandb_tools to get latest logs by hostname:
   ```bash
   python3 wandb_tools/get_logs_by_hostname.py $(hostname | cut -d'.' -f1)
   ```

2. **Fallback for Container Logs**: If wandb_tools fails, check running containers and get logs directly:
   ```bash
   # Check running instances
   singularity instance list
   # OR: docker ps
   
   # Get most recent log from active container
   singularity exec instance://[MOST_RECENT_INSTANCE] tail -100 /tmp/[LOG_FILE]
   # OR: docker logs [MOST_RECENT_CONTAINER_ID]
   ```

3. **CRITICAL**: Always verify you're getting the MOST RECENT run/container for your hostname - not old logs from previous attempts. Look for:
   - Latest timestamp in instance/container names
   - Most recent creation time in `singularity instance list` or `docker ps`
   - Active training processes (check with `ps aux | grep python | grep -v grep`)

**WARNING**: This guidance applies ONLY to AI/ML training projects. For other types of projects (bioinformatics without training, web development, etc.), ignore this section and follow standard log collection procedures.

## File Collection

You should use the ninjagrab MCP to collect relevant code and implementation files.

Identify and collect relevant code files for the specific issue.

Use the ninjagrab MCP to collect files:
"Use the ninjagrab MCP to collect these files: [list relevant source files] [configuration files] [scripts and build files] [any third-party code being modified]"

**Note: Never include CLAUDE.md files in ninjagrab collection**
- CLAUDE.md files contain agent instructions and should not be sent externally
- Only collect relevant source code, configuration, and implementation files

Include collected files in the final analysis document with complete file contents.

### HOW NINJAGRAB MCP WORKS
The ninjagrab MCP concatenates files with delimiters:
- Takes file paths as input array
- For each file: creates `===== filename =====` delimiter, then full file contents
- Returns concatenated content AND saves to `ninjagrab-out.txt`
- Reports errors for missing files but continues processing others

### MANUAL FALLBACK IF NINJAGRAB MCP FAILS
If the ninjagrab MCP fails, collect files manually using this exact pattern:

```bash
# For each required file, use this format:
echo "===== FILENAME ====="
cat FILENAME
echo ""
```

**CRITICAL**: Whether using ninjagrab MCP or manual collection, you MUST include EVERY collected file in PLEA.md using @ syntax with complete contents. No exceptions.

## Analysis Document Structure

### Problem Summary
- **Current Issue**: Technical issue description
- **Impact**: Consequences if relevant (e.g., blocked tasks, resource usage)

### Technical Analysis

#### A. Root Cause Analysis
- **Primary failure point** with exact error messages and stack traces
- **Contributing factors** (performance, configuration, environment, timing)
- **Failure reproducibility** (always/sometimes/intermittent)
- **System state during failure** (memory, CPU, network, processes)

#### B. Complete Solution History
For EVERY solution attempted, include:
- **What was tried** (exact commands, code changes, config modifications)
- **Why we thought it would work** (hypothesis and reasoning)
- **What happened** (exact results, errors, performance changes)
- **Why it failed** (root cause of the failure)
- **Side effects** (what broke, what improved, what changed)

#### C. Current System State
- **Exact environment configuration** (all relevant env vars, paths, versions)
- **Container architecture** (full Dockerfile/Singularity analysis)
- **Network topology** (ports, services, communication patterns)
- **Resource constraints** (memory limits, CPU allocation, GPU usage)
- **Filesystem layout** (critical paths, permissions, mounted volumes)

### Specific Help Needed

Be specific about what technical assistance you need. For example:

1. **Root Cause Identification**:
   - What is causing the specific failure
   - Where the bottleneck or issue is located
   - Technical details about the failure mode

2. **Solution Approach**:
   - Specific code changes or fixes needed
   - Configuration modifications required
   - Implementation steps

3. **Optimization** (if applicable):
   - Performance improvements
   - Resource usage optimization
   - Architectural improvements

4. **Prevention**:
   - How to prevent similar issues
   - Monitoring or diagnostics to add
   - Best practices to follow

### Specific Questions (1-2 Maximum)

Ask 1-2 specific questions if needed. Focus on actionable details rather than general guidance.

Good examples:
- "What should I modify in [specific file] to fix [specific issue]?"
- "Which approach is better: [option A with details] or [option B with details]?"
- "What value should [specific parameter] be set to?"

Avoid vague questions like "What's the best approach?" or "How should we optimize?"

### Quality Check

Before sending, verify the analysis includes:
- [ ] **Error messages** with stack traces and relevant timing data
- [ ] **Solution history** documenting attempts made
- [ ] **System information** relevant to the issue
- [ ] **Specific technical questions** (not vague requests)
- [ ] **Code files** included via ninjagrab where relevant
- [ ] **Container details** if using containers
- [ ] **Complete file contents** in the document

## Execution Steps

1. **Gather system information** using bash commands as needed
2. **Use ninjagrab MCP** to collect relevant files (creates ninjagrab-out.txt)
3. **If ninjagrab fails** - Use manual collection: `echo "===== filename ====="` then `cat filename` for each file
4. **Verify files collected** - Check that required files were successfully read
5. **Write analysis document** following structure above
6. **Append ninjagrab output** - Add ninjagrab-out.txt contents to end of document
7. **Quality check** against checklist
8. **Send document** via report MCP with title: "Technical Analysis Request - [ISSUE DESCRIPTION]"

## Final Document Structure

The final analysis document should follow this structure:

```markdown
# Technical Analysis Request - [ISSUE DESCRIPTION]

[... your analysis and findings ...]

---

# Code and Configuration Files

The following section contains relevant source code files:

[PASTE ninjagrab-out.txt CONTENTS HERE if applicable]
```

Append the ninjagrab output to your analysis using: `cat ninjagrab-out.txt >> PLEA.md`

## Important Notes

- Include complete file contents when relevant to the issue
- Be thorough but focused on the specific problem
- Provide enough context for someone to understand and help solve the issue
- Keep the tone professional and factual