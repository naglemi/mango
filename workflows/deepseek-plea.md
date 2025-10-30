---
allowed-tools: Bash(*), Read(*), Write(*), mcp__deepseek_proxy__deepseek_chat, mcp__ninjagrab__ninjagrab_collect, mcp__architect_report__send_report
description: Generate EXHAUSTIVE technical plea, send directly to DeepSeek via AWS Bedrock, get response, and implement DeepSeek's advice
argument-hint: [implement|fix|wait] [issue description - will be expanded with massive detail and sent to DeepSeek]
---

# CRITICAL: Generate Exhaustive Technical Plea for DeepSeek and Process Response

**WARNING: This plea must be EXHAUSTIVELY DETAILED. A superficial plea is UNACCEPTABLE.**

You are creating a technical document that will be sent directly to DeepSeek reasoning model via AWS Bedrock for analysis and solution.

## EXECUTION MODE PARSING

First, determine the execution mode from arguments:
```bash
# Parse first word to determine mode
FIRST_WORD=$(echo "$ARGUMENTS" | awk '{print $1}')
REMAINING=$(echo "$ARGUMENTS" | cut -d' ' -f2-)

# Determine execution mode
if [[ "$FIRST_WORD" == "implement" ]] || [[ "$FIRST_WORD" == "fix" ]]; then
    EXECUTION_MODE="implement"
    ISSUE_DESCRIPTION="$REMAINING"
elif [[ "$FIRST_WORD" == "wait" ]]; then
    EXECUTION_MODE="wait"
    ISSUE_DESCRIPTION="$REMAINING"
else
    # No mode specified - default to implement
    EXECUTION_MODE="implement"
    ISSUE_DESCRIPTION="$ARGUMENTS"
fi
```

## WORKFLOW BASED ON MODE

**If EXECUTION_MODE = "implement" or "fix" (DEFAULT):**
1. Generate comprehensive technical plea with complete context
2. Send plea directly to DeepSeek via mcp__deepseek_proxy__deepseek_chat
3. Receive DeepSeek's detailed response and implementation guidance  
4. Immediately implement DeepSeek's recommended solution autonomously

**If EXECUTION_MODE = "wait":**
1. Generate comprehensive technical plea with complete context
2. Send plea directly to DeepSeek via mcp__deepseek_proxy__deepseek_chat
3. Receive DeepSeek's detailed response and implementation guidance
4. Send BOTH the plea AND DeepSeek's response to human via mcp__architect_report__send_report for review
5. STOP and wait for human approval/disapproval/comments before proceeding
6. Do NOT implement anything until human explicitly approves

## MANDATORY REQUIREMENTS FOR THE PLEA

### 1. COMPLETE PROBLEM LANDSCAPE
- **Root cause analysis** of exactly what's failing and why
- **Exhaustive error documentation** with full stack traces, timing data, system calls
- **Comprehensive failure timeline** showing every attempt and outcome
- **Detailed system state** at time of failure including memory, CPU, network, filesystem

### 2. TECHNICAL ARCHAEOLOGY  
- **Every solution attempted** with exact commands, code changes, configuration modifications
- **Why each attempt failed** with specific error messages, performance metrics, behavioral observations
- **Code evolution** showing how the problem has been approached over time
- **Configuration drift** documenting all environment/container/system changes

### 3. ACTIONABLE INTELLIGENCE REQUIREMENTS
DeepSeek needs these SPECIFIC deliverables in your plea (NOT vague "guidance"):
- **Exact root cause identification** with supporting evidence
- **Precise technical solution** with implementation steps
- **Alternative approaches** ranked by feasibility and risk
- **Performance optimization strategy** for the chosen solution
- **Failure prevention measures** to avoid recurrence

### 4. SYSTEM FORENSICS
Include COMPLETE system context:
- **Full environment state** (all env vars, paths, versions, configurations)
- **Resource utilization** (memory, CPU, GPU, disk, network) during failures
- **Process hierarchy** and inter-process communication details
- **Container internals** (filesystem layout, mounted volumes, network stack)
- **Dependencies graph** (all packages, versions, conflicts, missing components)

## Current Context Deep-Dive

**Issue**: $ISSUE_DESCRIPTION (or $ARGUMENTS if no mode parsing needed)

**Project State**:
- Directory: !`pwd`
- Git status: !`git status --porcelain`
- Branch: !`git branch --show-current`
- Recent commits: !`git log --oneline -10`

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

## EXHAUSTIVE FILE COLLECTION - MANDATORY

**CRITICAL: You MUST use ninjagrab.sh to collect ALL our code and implementation files. NO EXCEPTIONS.**

DeepSeek needs to see EVERY piece of our code that's involved in the issue.

**CRITICAL: You MUST identify and collect ALL relevant code files for the specific issue.**

Use ninjagrab.sh to collect files. For example:
```bash
~/usability/workflows/ninjagrab.sh \
  [list all relevant source files for the issue] \
  [configuration files] \
  [scripts and build files] \
  [any third-party code being modified]
```

**CRITICAL: NEVER include ANY CLAUDE.md file in ninjagrab.sh collection**
- CLAUDE.md files contain agent instructions and should never be sent to architects
- ninjagrab.sh will automatically filter out and exclude all CLAUDE.md files
- This protects sensitive agent configuration from external exposure

**MANDATORY: You MUST include ALL collected files using @ syntax in the final PLEA.md** with complete file contents.

**ENFORCEMENT: If ninjagrab.sh fails or any @ files are missing from PLEA.md, you MUST abort and fix the collection process. The architect requires COMPLETE code visibility.**

### HOW NINJAGRAB.SH WORKS
ninjagrab.sh simply concatenates files with delimiters:
- Takes file paths as arguments
- For each file: prints `===== filename =====`, then full file contents
- Outputs to stdout AND saves to `ninjagrab-out.txt`
- Exits with error if any file not found

### MANUAL FALLBACK IF NINJAGRAB FAILS
If ninjagrab.sh fails, collect files manually using this exact pattern:

```bash
# For each required file, use this format:
echo "===== FILENAME ====="
cat FILENAME
echo ""
```

**CRITICAL**: Whether using ninjagrab.sh or manual collection, you MUST include EVERY collected file in PLEA.md using @ syntax with complete contents. No exceptions.

## MANDATORY PLEA STRUCTURE

### EXECUTIVE CRISIS SUMMARY
- **CRITICAL BLOCKER**: Exact technical issue blocking progress
- **BUSINESS IMPACT**: Specific consequences (wasted GPU hours, blocked research)
- **URGENCY LEVEL**: Why this needs immediate resolution
- **FAILURE SCOPE**: What percentage of functionality is broken

### COMPREHENSIVE TECHNICAL DEEP-DIVE

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

### SPECIFIC ARCHITECT DELIVERABLES REQUIRED

**NOT ACCEPTABLE**: "We need guidance on PIDGIN integration"

**REQUIRED SPECIFICITY**:
1. **Root Cause Identification**:
   - Exact technical reason PIDGIN servers fail to start within 30 seconds
   - Specific bottleneck (CPU, memory, I/O, network, dependency loading)
   - Precise timing breakdown of startup sequence

2. **Technical Solution**:
   - Exact code changes required (file, line number, before/after)
   - Specific configuration modifications (env vars, container settings, timeouts)
   - Precise deployment steps with verification commands

3. **Performance Optimization**:
   - Specific timeout adjustments with rationale
   - Memory allocation recommendations with sizing calculations
   - Resource scheduling optimizations (CPU, GPU, I/O priorities)

4. **Architecture Decision**:
   - Should we fix current Flask-based PIDGIN servers OR migrate to direct model loading?
   - If Flask: exactly how to optimize server startup performance
   - If direct loading: exact implementation approach with memory management

5. **Failure Prevention**:
   - Specific monitoring and diagnostics to implement
   - Exact early warning signals to detect impending failures
   - Precise fallback mechanisms with implementation details

### SPECIFIC QUESTIONS FOR ARCHITECT (MAXIMUM 2 QUESTIONS)

**CRITICAL: Ask only 1-2 highly specific questions that will get direct actionable instructions.**

**DO NOT ask vague questions like:**
- "What's the best approach?"
- "How should we optimize this?"
- "What are best practices?"

**DO ask specific questions like:**
- "What exact line should I modify and what value should I set?"
- "What exact commands should I add to the container build?"
- "Should I change X to Y in file Z at line N?"

**TEMPLATE FOR QUESTIONS**:
```
**QUESTION 1**: [Specific technical question with file paths, line numbers, exact values needed]

**QUESTION 2**: [Alternative approach question with specific implementation steps required]
```

### QUALITY ASSURANCE CHECKLIST

Before sending, verify the plea includes:
- [ ] **Complete error messages** with full stack traces and timing data
- [ ] **Exhaustive solution history** with every attempt documented
- [ ] **Full system forensics** (environment, processes, resources, network)
- [ ] **Specific technical asks** (not vague requests for "guidance")
- [ ] **ALL REQUIRED CODE FILES** included with @ syntax (no exceptions, no summaries)
- [ ] **Complete file contents** for every @ referenced file (not excerpts or descriptions)
- [ ] **Container analysis** (if using containers/Docker/Singularity)
- [ ] **ninjagrab.sh successfully executed** with all files collected in ninjagrab-out.txt
- [ ] **Complete ninjagrab-out.txt contents** appended to end of PLEA.md
- [ ] **PLEA.md sent as file attachment** (not just plaintext email report)

## EXECUTION PROTOCOL

1. **PARSE EXECUTION MODE** - Determine if mode is "implement", "fix", or "wait" from arguments
2. **Gather comprehensive system state** using all bash commands above
3. **EXECUTE NINJAGRAB.SH** - Must run the exact command specified above (creates ninjagrab-out.txt)
4. **IF NINJAGRAB FAILS** - Use manual fallback: `echo "===== filename ====="` then `cat filename` for each file
5. **VERIFY ALL FILES COLLECTED** - Check that every required file was successfully read
6. **Write exhaustive PLEA.md** following mandatory structure above
7. **APPEND NINJAGRAB OUTPUT** - Add complete ninjagrab-out.txt contents to end of PLEA.md
8. **Quality check** against checklist - REJECT if insufficient detail or missing any files
9. **SEND PLEA DIRECTLY TO DeepSeek** - Use mcp__deepseek_proxy__deepseek_chat to send complete plea to DeepSeek
10. **RECEIVE DeepSeek RESPONSE** - Get detailed analysis and implementation guidance from DeepSeek
11. **PROCESS BASED ON MODE**:
    - **If "implement"/"fix" mode**: Immediately execute DeepSeek's recommended solution autonomously
    - **If "wait" mode**: Send plea + DeepSeek response to human via mcp__architect_report__send_report and STOP

## FINAL PLEA.md STRUCTURE

The final PLEA.md must have this exact structure:

```markdown
# URGENT: Technical Architecture Plea - [ISSUE DESCRIPTION]

[... your analysis and findings ...]

---

# COMPLETE CODE REPOSITORY

The following section contains ALL relevant source code files collected via ninjagrab.sh:

[PASTE COMPLETE ninjagrab-out.txt CONTENTS HERE]
```

**CRITICAL**: You must `cat ninjagrab-out.txt >> PLEA.md` to append the complete file collection to your analysis. This ensures DeepSeek receives a single markdown file with everything needed.

## CRITICAL ENFORCEMENT RULES

**RULE 1**: If ninjagrab.sh fails for ANY file, you must troubleshoot and retry until ALL files are collected
**RULE 2**: If ANY @ file is missing from the final PLEA.md, the plea is INVALID and must be rewritten
**RULE 3**: @ files must contain COMPLETE source code, not summaries, excerpts, or descriptions
**RULE 4**: DeepSeek needs to see EVERY line of code in our implementation - no exceptions
**RULE 5**: You MUST use mcp__deepseek_proxy__deepseek_chat to send the complete plea to DeepSeek
**RULE 6**: Action after DeepSeek response depends on execution mode:
  - **"implement"/"fix" mode**: You MUST implement DeepSeek's solution immediately
  - **"wait" mode**: You MUST send plea + response to human and await approval

**FAILURE TO INCLUDE ALL CODE FILES OR SKIP DeepSeek CONSULTATION IS UNACCEPTABLE**

DeepSeek must have COMPLETE code visibility to provide precise, actionable solutions that you will implement.