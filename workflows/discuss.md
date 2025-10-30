# discuss

Enable two or more agents to communicate with each other via GitHub issue threads, facilitating collaborative problem-solving and consensus building.

This command accepts an optional GitHub issue number. If no issue exists for the current problem, it creates one. If an issue exists, it reads the thread and posts to it. After posting, it monitors for new messages and responds when other agents contribute.

** CRITICAL REQUIREMENT: READ ENTIRE ISSUE FROM START TO FINISH**
- The agent MUST read the ENTIRE issue thread from the very first post to the latest post
- EVERY SINGLE COMMENT must be read completely - no skipping, no sampling, no shortcuts
- DO NOT use grep or search to find specific content - read the full thread sequentially
- This ensures complete context understanding before posting responses
- Missing any post can lead to redundant questions, misaligned responses, or incorrect assumptions

---
**Purpose**

1. Allow multiple agents to collaborate on complex problems through structured GitHub issue discussions
2. Enable consensus-building between agents working on the same codebase
3. Provide a persistent communication channel that survives across agent sessions
4. Generate individual reports from each agent about their interpretation of the consensus

---
## Steps

1. **Parse arguments**  
   - Extract optional issue number from command arguments
   - If no issue number provided, prepare to search for or create a new issue

2. **Determine current context**  
   - Get current hostname using `hostname` command
   - Get current git branch using `git branch --show-current`
   - Identify the current GitHub repository using `gh repo view --json name,owner`

3. **Handle GitHub issue**  
   - **If issue number provided**: Read the existing issue thread using `gh issue view <number> --comments`
   - **If no issue number**: Search for existing issues related to current problem using `gh issue list --search "<problem keywords>"`
   - **If no relevant issue found**: Create a new issue using `gh issue create --title "<problem summary>" --body "<initial problem description>"`

4. **Post initial message**  
   - Craft a message introducing this agent's perspective on the problem
   - Include relevant context, current understanding, and proposed approaches
   - Sign the message with: `---\n**Agent**: \`{hostname}\` | **Branch**: \`{current_branch}\``
   - Post using `gh issue comment <issue_number> --body "<message>"`

5. **Enter monitoring loop**  
   - Sleep for 60 seconds between checks
   - Query issue comments with retry logic for GitHub API timeouts
   - Use exponential backoff on 504/502/503 errors (start with 30s, max 300s)
   - Parse JSON to find comments newer than this agent's last comment timestamp
   - When new messages from other agents are detected:
     - Read and analyze the new messages
     - **Context-Aware Code Analysis**: Automatically check code modules mentioned in comments
       - Extract file paths, function names, class names from comment text
       - Use Read tool to examine mentioned files
       - Use Grep tool to find relevant code sections
       - Consider broader context when modules are discussed
     - Formulate a thoughtful response addressing points raised
     - Post response with agent signature
     - Continue monitoring

6. **Detect consensus or conclusion**  
   - Monitor for consensus indicators in messages:
     - Explicit agreement statements
     - Summary of agreed-upon next steps
     - Assignment of responsibilities
     - Timeline agreements
   - When consensus appears to be reached, or after extended discussion without progress:
     - Prepare to generate final report

7. **Generate individual report**  
   - Create a comprehensive report including:
     - Summary of the problem discussed
     - Key points from each participating agent
     - Personal interpretation of any consensus reached
     - Understanding of next steps and agent responsibilities
     - Areas of disagreement or uncertainty (if any)
     - Recommended actions for this specific agent
   - Send report to user via available reporting mechanism

8. **Exit monitoring**  
   - Stop the monitoring loop after generating the report
   - Provide the issue URL for reference

---
## Implementation Details

### Comment Parsing Best Practices

**EFFICIENT PARSING**: Use single API call with comprehensive jq processing instead of multiple separate calls.

**Bad Example** (multiple inefficient calls):
```bash
# DON'T DO THIS - Too many API calls
gh issue view 33 --comments --json comments | jq '.comments | length'
gh issue view 33 --comments --json comments | jq '.comments[-1].author.login'  
gh issue view 33 --comments --json comments | jq '.comments[-1].createdAt'
gh issue view 33 --comments --json comments | jq -r '.comments[-1].body'
```

**Good Example** (single efficient call handling multiple new comments):
```bash
# DO THIS - Single call with comprehensive parsing of ALL new comments
gh issue view 33 --comments --json comments,createdAt,updatedAt,author | jq --arg since "$LAST_TIMESTAMP" '{
  total_comments: (.comments | length),
  new_comments: [
    .comments[] | select(.createdAt > $since) | {
      author: .author.login,
      created: .createdAt,
      body_preview: (.body | split("\n")[0:3] | join(" | ")),
      full_body: .body,
      mentioned_files: [.body | scan("`[^`]*\\.(py|js|yaml|md|sh)`"; "g")],
      mentioned_functions: [.body | scan("`[a-zA-Z_][a-zA-Z0-9_]*\\(`"; "g")],
      is_from_other_agent: (.author.login != "current_user" and (.body | test("Agent.*:")))
    }
  ],
  latest_timestamp: (.comments | max_by(.createdAt) | .createdAt)
}'
```

### Multi-Participant Discussion Handling

**CRITICAL**: In active discussions, multiple participants may comment simultaneously:
- **Human user** providing clarifications or new requirements
- **Other agents** posting analysis or responses  
- **Issue owner** adding context or decisions

**Always process ALL new comments since last check**, not just the latest one.

**Example Scenario**:
```
T+0: Agent A posts implementation plan
T+1: Human responds with corrections  
T+2: Agent B posts alternative approach
T+3: Agent A checks (should see BOTH human + Agent B comments)
```

### Context-Aware Response Triggers

When processing new comments, automatically extract and investigate:

1. **File Mentions**: `*.py`, `*.js`, `*.yaml`, etc.
2. **Function/Method Calls**: `function_name()`, `Class.method()`
3. **Configuration References**: Config files, YAML sections
4. **Code Blocks**: Anything in triple backticks
5. **Error Messages**: Stack traces, error descriptions
6. **Agent Signatures**: Detect other agents by `**Agent**: hostname` patterns

**Implementation Pattern** (handling multiple new comments):
```bash
# Process ALL new comments since last check
NEW_COMMENTS_JSON=$(gh issue view $ISSUE_NUM --comments --json comments | \
    jq --arg since "$LAST_TIMESTAMP" '[.comments[] | select(.createdAt > $since)]')

# Process each new comment individually
echo "$NEW_COMMENTS_JSON" | jq -c '.[]' | while read -r comment; do
    AUTHOR=$(echo "$comment" | jq -r '.author.login')
    BODY=$(echo "$comment" | jq -r '.body')
    TIMESTAMP=$(echo "$comment" | jq -r '.createdAt')
    
    echo "Processing comment from $AUTHOR at $TIMESTAMP"
    
    # Extract mentioned files from THIS comment
    MENTIONED_FILES=$(echo "$BODY" | grep -oE '`[^`]*\.(py|js|yaml|md|sh)`' | tr -d '`')
    
    # Check each mentioned file
    for file in $MENTIONED_FILES; do
        if [[ -f "$file" ]]; then
            echo "Reading mentioned file: $file"
            # Use Read tool to examine the file
            # Consider the context for your response
        fi
    done
    
    # Update latest timestamp for this comment
    LATEST_TIMESTAMP="$TIMESTAMP"
done

# Update the stored timestamp with the most recent
LAST_TIMESTAMP="$LATEST_TIMESTAMP"
```

---

### GitHub CLI Commands Used
```bash
# Get repository info (with retry on timeout)
gh repo view --json name,owner

# Create new issue
gh issue create --title "Agent Discussion: <topic>" --body "<description>"

# List existing issues
gh issue list --state open --limit 30

# EFFICIENT COMMENT PARSING - Single call gets everything needed
gh issue view <number> --comments --json comments,createdAt,updatedAt,author | jq '{
  total_comments: (.comments | length),
  latest_comment: {
    author: .comments[-1].author.login,
    created: .comments[-1].createdAt,
    body_preview: (.comments[-1].body | split("\n")[0:3] | join(" | ")),
    full_body: .comments[-1].body
  },
  previous_comment: {
    author: .comments[-2].author.login,
    created: .comments[-2].createdAt,
    body_preview: (.comments[-2].body | split("\n")[0:3] | join(" | "))
  }
}'

# Extract just new comments since last check
gh issue view <number> --comments --json comments | jq --arg since "$LAST_TIMESTAMP" '
  .comments[] | select(.createdAt > $since) | {
    author: .author.login,
    created: .createdAt,
    body: .body
  }'

# Fallback: simple text view when JSON fails
gh issue view <number> --comments

# Add comment to issue
gh issue comment <number> --body "<message>"

# Get current branch
git branch --show-current

# Get hostname
hostname

# Retry logic example for monitoring
for i in {1..3}; do
  if gh issue view <number> --comments --json comments 2>/dev/null; then
    break
  else
    echo "GitHub API timeout, retrying in $((30 * i)) seconds..."
    sleep $((30 * i))
  fi
done
```

### Message Format
Each agent message should follow this structure:
```markdown
## Agent Perspective: <hostname>

<agent's contribution to the discussion>

### Current Understanding
- <bullet points of current understanding>

### Proposed Actions
- <bullet points of proposed next steps>

### Questions/Concerns
- <any questions or concerns>

---
**Agent**: `<hostname>` | **Branch**: `<current_branch>` | **Timestamp**: `<ISO timestamp>`
```

### Consensus Detection
Monitor for these phrases indicating consensus:
- "I agree with"
- "We've reached agreement"
- "The plan is"
- "Next steps are"
- "I'll take responsibility for"
- "Timeline agreed"

### Efficient Monitoring Loop

**Store last seen timestamp** to avoid re-processing old comments:
```bash
LAST_TIMESTAMP=$(date -Iseconds)

while true; do
    sleep 60
    
    # Get ALL new comments since last check (could be multiple from human + agents)
    NEW_COMMENTS_JSON=$(gh issue view $ISSUE_NUM --comments --json comments | \
        jq --arg since "$LAST_TIMESTAMP" '[.comments[] | select(.createdAt > $since)]')
    
    COMMENT_COUNT=$(echo "$NEW_COMMENTS_JSON" | jq 'length')
    
    if [[ "$COMMENT_COUNT" -gt 0 ]]; then
        echo "Found $COMMENT_COUNT new comment(s) to process"
        
        # Process each new comment individually with full context awareness
        echo "$NEW_COMMENTS_JSON" | jq -c '.[]' | while read -r comment; do
            AUTHOR=$(echo "$comment" | jq -r '.author.login')
            BODY=$(echo "$comment" | jq -r '.body')
            TIMESTAMP=$(echo "$comment" | jq -r '.createdAt')
            
            echo "Processing comment from $AUTHOR at $TIMESTAMP"
            
            # Context-aware analysis of THIS specific comment
            MENTIONED_FILES=$(echo "$BODY" | grep -oE '`[^`]*\.(py|js|yaml|md|sh)`' | tr -d '`')
            MENTIONED_FUNCTIONS=$(echo "$BODY" | grep -oE '`[a-zA-Z_][a-zA-Z0-9_]*\(`' | tr -d '`(')
            
            # Read mentioned files if they exist
            for file in $MENTIONED_FILES; do
                [[ -f "$file" ]] && echo "Reading: $file" # Use Read tool here
            done
            
            # Search for mentioned functions if needed  
            for func in $MENTIONED_FUNCTIONS; do
                echo "Searching for function: $func" # Use Grep tool here
            done
        done
        
        # Update timestamp to most recent comment
        LAST_TIMESTAMP=$(echo "$NEW_COMMENTS_JSON" | jq -r 'max_by(.createdAt) | .createdAt')
        echo "Updated timestamp to: $LAST_TIMESTAMP"
    fi
done
```

### Error Handling
- If GitHub CLI is not authenticated, prompt user to run `gh auth login`
- If repository is not a GitHub repo, exit with error message  
- If issue creation fails, retry once before failing
- If comment posting fails, retry with exponential backoff
- **GitHub API timeouts (504/502/503)**: Implement retry with exponential backoff
  - First retry: wait 30 seconds
  - Second retry: wait 60 seconds  
  - Third retry: wait 120 seconds
  - Max retry: wait 300 seconds
  - After 5 failures, inform user of GitHub API issues and suggest manual check
- **Parse failures**: Always have fallback to simple text parsing when JSON fails

---
## Usage

```bash
# Start discussion on new topic
/discuss

# Join existing discussion
/discuss 123

# The command will:
# 1. Either create issue or join issue #123
# 2. Post initial perspective
# 3. Monitor for responses
# 4. Engage in discussion
# 5. Generate final report when consensus reached
```

---
## Example Flow

1. **Agent A** runs `/discuss` → Creates issue #456 about "Database migration strategy"
2. **Agent B** runs `/discuss 456` → Joins the discussion
3. **Agent C** runs `/discuss 456` → Also joins the discussion
4. Agents discuss back and forth through GitHub issue comments
5. Eventually reach consensus on migration approach and timeline
6. Each agent generates their own report with their understanding
7. User receives three reports with each agent's interpretation

---
### Notes
- The monitoring loop runs indefinitely until consensus is detected or manually interrupted
- Avoid creating new issue unless you are SURE comment is not appropriate for an existing issue. Avoid duplicate issues!
- Agent signatures help track who said what in multi-agent discussions
- Each agent maintains its own understanding and generates independent reports
- GitHub issues provide persistent, searchable discussion history
- Use `Ctrl+C` to manually exit the monitoring loop if needed(base) ubuntu@ip-172
