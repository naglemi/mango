---
allowed-tools: Bash(*), Read(*), Write(*), mcp__gpt5_proxy__gpt5_chat, mcp__ninjagrab__ninjagrab_collect, mcp__architect_report__send_report
description: Generate comprehensive technical request, send to GPT-5 for consultation, and implement recommendations
argument-hint: [implement|fix|wait] [issue description - will be expanded with massive detail and sent to GPT-5]
---

# Generate Comprehensive Technical Request for GPT-5 Consultation

**Note: Please provide thorough technical details for effective analysis.**

You are creating a technical document that will be sent directly to OpenAI's GPT-5 reasoning model for analysis and solution.

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
2. Send plea directly to GPT-5 via mcp__gpt5_proxy__gpt5_chat
3. Receive GPT-5's detailed response and implementation guidance  
4. Immediately implement GPT-5's recommended solution autonomously

**If EXECUTION_MODE = "wait":**
1. Generate comprehensive technical plea with complete context
2. Send plea directly to GPT-5 via mcp__gpt5_proxy__gpt5_chat
3. Receive GPT-5's detailed response and implementation guidance
4. Send BOTH the plea AND GPT-5's response to human via mcp__architect_report__send_report for review
5. STOP and wait for human approval/disapproval/comments before proceeding
6. Do NOT implement anything until human explicitly approves

## RECOMMENDED CONTENT FOR TECHNICAL REQUEST

### 1. PROBLEM CONTEXT
- **Root cause analysis** of the issue
- **Error documentation** with relevant stack traces and logs
- **Timeline** of attempted solutions and outcomes
- **System state** including relevant resource information

### 2. TECHNICAL ARCHAEOLOGY  
- **Every solution attempted** with exact commands, code changes, configuration modifications
- **Why each attempt failed** with specific error messages, performance metrics, behavioral observations
- **Code evolution** showing how the problem has been approached over time
- **Configuration drift** documenting all environment/container/system changes

### 3. SPECIFIC TECHNICAL QUESTIONS
Request specific technical guidance:
- **Root cause identification** with supporting evidence
- **Technical solution** with implementation steps
- **Alternative approaches** if applicable
- **Performance considerations** for the solution
- **Best practices** to prevent similar issues

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

GPT-5 needs to see EVERY piece of our code that's involved in the issue.

**CRITICAL: You MUST identify and collect ALL relevant code files for the specific issue.**

Use ninjagrab.sh to collect files. For example:
```bash
~/mango/workflows/ninjagrab.sh \
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

## SUGGESTED REQUEST STRUCTURE

### EXECUTIVE SUMMARY
- **Technical Issue**: Description of the problem
- **Impact**: Consequences for the project
- **Priority**: Relative importance of resolution
- **Scope**: Affected functionality

### TECHNICAL ANALYSIS

#### A. Problem Investigation
- **Primary issue** with error messages and relevant logs
- **Contributing factors** (configuration, environment, dependencies)
- **Reproducibility** (consistent/intermittent)
- **System state** when issue occurs

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

### SPECIFIC TECHNICAL GUIDANCE NEEDED

**Be specific about what you need from GPT-5:**
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

### FOCUSED QUESTIONS FOR GPT-5 (1-2 MAXIMUM)

**Ask specific, actionable questions:**
- "What exact line should I modify and what value should I set?"
- "What exact commands should I add to the container build?"
- "Should I change X to Y in file Z at line N?"

**TEMPLATE FOR QUESTIONS**:
```
**QUESTION 1**: [Specific technical question with file paths, line numbers, exact values needed]

**QUESTION 2**: [Alternative approach question with specific implementation steps required]
```

### QUALITY CHECKLIST

Before sending, verify the request includes:
- [ ] **Error messages** with relevant logs
- [ ] **Solution history** documenting attempts
- [ ] **System context** (environment, configuration)
- [ ] **Specific questions** for GPT-5
- [ ] **Required code files** included with @ syntax
- [ ] **Complete file contents** for referenced files
- [ ] **Container details** (if applicable)
- [ ] **File collection** via ninjagrab.sh completed
- [ ] **Collected files** appended to PLEA.md
- [ ] **PLEA.md prepared** as file attachment

## EXECUTION PROTOCOL

1. **PARSE EXECUTION MODE** - Determine if mode is "implement", "fix", or "wait" from arguments
2. **Gather comprehensive system state** using all bash commands above
3. **EXECUTE NINJAGRAB.SH** - Must run the exact command specified above (creates ninjagrab-out.txt)
4. **IF NINJAGRAB FAILS** - Use manual fallback: `echo "===== filename ====="` then `cat filename` for each file
5. **VERIFY ALL FILES COLLECTED** - Check that every required file was successfully read
6. **Write exhaustive PLEA.md** following mandatory structure above
7. **APPEND NINJAGRAB OUTPUT** - Add complete ninjagrab-out.txt contents to end of PLEA.md
8. **Quality check** against checklist - REJECT if insufficient detail or missing any files
9. **SEND PLEA DIRECTLY TO GPT-5** - Use mcp__gpt5_proxy__gpt5_chat to send complete plea to GPT-5
10. **HANDLE GPT-5 RESPONSE OR FAILURE**:
    - **If GPT-5 succeeds**: Get detailed analysis and implementation guidance from GPT-5
    - **If GPT-5 fails (model unavailable)**: Automatically send plea to human via mcp__architect_report__send_report
11. **PROCESS BASED ON MODE AND RESULT**:
    - **If GPT-5 succeeded and "implement"/"fix" mode**: Immediately execute GPT-5's recommended solution autonomously
    - **If GPT-5 succeeded and "wait" mode**: Send plea + GPT-5 response to human via mcp__architect_report__send_report and STOP
    - **If GPT-5 failed**: Plea already sent to human, STOP and wait for human response

## FINAL PLEA.md STRUCTURE

The final PLEA.md should follow this structure:

```markdown
# Technical Architecture Request - [ISSUE DESCRIPTION]

[... your analysis and findings ...]

---

# COMPLETE CODE REPOSITORY

The following section contains ALL relevant source code files collected via ninjagrab.sh:

[PASTE COMPLETE ninjagrab-out.txt CONTENTS HERE]
```

**CRITICAL**: You must `cat ninjagrab-out.txt >> PLEA.md` to append the complete file collection to your analysis. This ensures GPT-5 receives a single markdown file with everything needed.

## IMPORTANT GUIDELINES

**GUIDELINE 1**: If file collection fails, troubleshoot and retry to collect all necessary files
**GUIDELINE 2**: Include complete file contents when referenced with @ syntax
**GUIDELINE 3**: Provide full source code, not summaries or excerpts
**GUIDELINE 4**: Include all relevant code for proper analysis
**GUIDELINE 5**: Use mcp__gpt5_proxy__gpt5_chat to send the request to GPT-5
**GUIDELINE 6**: **GPT-5 AVAILABILITY**:
  - **Do not use alternative models as fallback**
  - **If GPT-5 is unavailable**: Send request to human via mcp__architect_report__send_report
  - **Avoid simulated or placeholder responses**
**GUIDELINE 7**: Response handling based on execution mode:
  - **"implement"/"fix" mode**: Implement GPT-5's solution
  - **"wait" mode**: Send request + response to human for approval
  - **GPT-5 unavailable**: Send request to human and await guidance

GPT-5 must have COMPLETE code visibility to provide precise, actionable solutions that you will implement.