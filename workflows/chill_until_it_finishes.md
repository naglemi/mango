---
allowed-tools: Bash(*), Read(*), Write(*), mcp__pushover__send, mcp__report__send_report, monitor_process, check_process, find_recent_processes
description: Monitor a background process until completion with smart timeout handling and comprehensive reporting
argument-hint: [--pid=12345] or [--last] or [process-pattern]
---

# /chill_until_it_finishes - Process Monitoring with Intelligent Timeout Handling

**PURPOSE**: Monitor a background process until completion, handling Claude Code's 2-hour timeout gracefully, and provide comprehensive analysis when done.

## CRITICAL AGENT DOCUMENTATION

### System Constraints You MUST Understand
- **Claude Code enforces a 2-hour timeout** for ALL foreground processes
- **The monitor will timeout after 1hr 55min** to avoid system termination
- **IMPORTANT**: Monitor timeout ≠ Process completion
- **Your background process continues running** even if monitor restarts
- **You must restart monitoring** if timeout occurs while process still runs

### What Monitor Timeout Means
- **NOT** that your background process has finished
- **Only** that the monitoring tool needs to restart to avoid system limits
- **The process being monitored continues running independently**

## Usage Examples

```bash
# Monitor specific PID
/chill_until_it_finishes --pid=12345

# Monitor most recent background job  
/chill_until_it_finishes --last

# Find and monitor process by pattern
/chill_until_it_finishes python train
```

## Implementation Protocol

### Step 1: Process Discovery

If `--pid=XXXX` provided:
- Use that specific PID
- Validate it exists with `check_process`

If `--last` provided:
- Check `$!` for last background job PID
- Validate it's still running

If pattern provided (e.g., "python train"):
- Use `find_recent_processes` with pattern
- If multiple matches, pick most recent or prompt user

### Step 2: Start Monitoring Workflow

```bash
# Send initial notification
await mcp__pushover__send({
  message: "Starting to monitor process {pid}. I'll chill quietly and notify you when it's done. ",
  title: "Process Monitor Started"
})
```

### Step 3: Monitoring Loop with Timeout Handling

```javascript
let processComplete = false;
let monitorRounds = 0;

while (!processComplete) {
  monitorRounds++;
  
  // Monitor for up to 1hr 55min (6900 seconds)
  const result = await monitor_process({
    pid: pid,
    timeout: 6900,        // 1hr 55min to avoid 2hr system limit
    poll_interval: 5      // Check every 5 seconds
  });
  
  if (result.status === 'completed') {
    // Process actually finished!
    processComplete = true;
    
    await mcp__pushover__send({
      message: `Process ${pid} has completed! Preparing summary report... `,
      title: "Process Completed",
      priority: 1
    });
    
    // Proceed to Step 4: Analysis
    
  } else if (result.status === 'monitor_timeout' && result.process_still_running) {
    // Monitor timed out but process still running - restart monitoring
    await mcp__pushover__send({
      message: `Monitor timeout after round ${monitorRounds} (1hr 55min). Process ${pid} still running. Restarting monitor... ⏰`,
      title: "Monitor Cycling",
      priority: 0
    });
    
    // Loop continues - restart monitoring
    
  } else {
    // Unexpected condition
    processComplete = true;
    await mcp__pushover__send({
      message: `Monitor ended unexpectedly: ${result.status}. Check process manually.`,
      title: "Monitor Error",
      priority: 2
    });
  }
}
```

### Step 4: Context-Aware Process Analysis

**This is where Claude's intelligence is critical** - the inspection cannot be programmatic since every process type requires different analysis.

#### For Python/ML Training Processes:
```bash
# Check for common ML output files
ls -la *.log *.csv *.json *.pkl model* checkpoint* wandb-local/
# Look for error patterns in logs
tail -100 training.log | grep -i error
tail -100 training.log | grep -i exception
# Check for metrics/progress files
cat metrics.csv | tail -10
```

#### For Build/Compilation Processes:
```bash
# Check build outputs
ls -la build/ dist/ target/ out/
# Look for error logs
find . -name "*.log" -newer $(date -d '2 hours ago' +%s) -exec tail -50 {} \;
# Check compilation artifacts
ls -la *.so *.dll *.exe *.jar
```

#### For Node.js/Web Processes:
```bash
# Check for logs and outputs
ls -la logs/ .next/ dist/ build/
# Look for package outputs
npm list --depth=0
# Check for error logs
tail -100 npm-debug.log 2>/dev/null || echo "No npm-debug.log"
```

#### For General Process Analysis:
```bash
# Get process info from when it was running
ps aux | grep ${pid} || echo "Process ${pid} no longer running"
# Check working directory for recent files
find . -newer $(date -d '2 hours ago' +%s) -type f | head -20
# Look for any error/output files
find . -name "*error*" -o -name "*output*" -o -name "*.out" -o -name "*.err" | head -10
```

### Step 5: Generate Comprehensive Report

Based on the process analysis, create a detailed summary:

```markdown
# Process ${pid} Completion Report

**Process Information:**
- PID: ${pid}
- Command: ${process_command}
- Working Directory: ${working_dir}
- Total Monitoring Time: ${total_time}
- Monitor Cycles: ${monitor_rounds}

## Process Analysis

### Exit Status
${process_exit_analysis}

### Output Analysis
${output_file_analysis}

### Error Analysis  
${error_log_analysis}

### Performance Metrics
${any_performance_data}

### Key Artifacts Created
${list_of_output_files}

## Summary
${intelligent_summary_of_results}

## Recommendations
${any_followup_actions_needed}
```

### Step 6: Send Final Report

```bash
await mcp__report__send_report({
  agent_name: "Claude Code Process Monitor",
  title: `Process ${pid} Completion Report`,
  text_content: comprehensive_report_markdown
})
```

## Error Handling

### Invalid PID
```bash
if ! check_process ${pid}; then
  echo "Process ${pid} not found or already exited"
  exit 1
fi
```

### No Recent Processes Found
```bash
if [ "$recent_processes" = "[]" ]; then
  echo "No recent processes found. Use --pid=XXXX to specify exact PID"
  exit 1
fi
```

### Monitor Tool Failure
```bash
if monitor_result contains error; then
  await mcp__pushover__send({
    message: "Process monitor failed. Check manually: ps aux | grep ${pid}",
    title: "Monitor Error",
    priority: 2
  })
fi
```

## Quality Assurance Checklist

Before completing the workflow:
- [ ] Process actually completed (not just monitor timeout)
- [ ] Comprehensive analysis performed based on process type
- [ ] All relevant output files identified and analyzed
- [ ] Error logs checked and summarized
- [ ] Performance data captured if available
- [ ] Final report sent via email
- [ ] User notified via Pushover of completion

## Success Criteria

1. **Silent Operation**: No token flooding during monitoring
2. **Robust Timeout Handling**: Automatic restart on monitor timeout
3. **Intelligent Analysis**: Context-aware inspection of results
4. **Comprehensive Reporting**: Detailed summary with actionable insights
5. **Dual Notification**: Quick Pushover alerts + detailed email report

## Implementation Notes

- **Silent Monitoring**: Use `monitor_process` which blocks without output
- **Process Types**: Recognize different process patterns for appropriate analysis
- **File Timestamps**: Use timestamps to identify files created during process run
- **Resource Cleanup**: Don't leave temporary monitoring files
- **Error Recovery**: Handle edge cases like process permissions, system limits