# EC2 & CloudWatch MCP Server

Unified MCP server for EC2 instance management and CloudWatch log access.

## Purpose

Consolidates all EC2/CloudWatch operations into MCP tools, eliminating the need for bash AWS CLI commands in workflows.

**Replaces:**
- Inline `aws ec2 describe-instances` bash commands
- Inline `aws logs get-log-events` bash commands
- Python scripts: `stream_ec2_logs.py`, `diagnose_ec2_crash.py`, `monitor_ec2_30min.py`
- Bash scripts: `get_cloudwatch_logs.sh`, `monitor_ec2.sh`, `check_ec2_training.sh`

## Tools

### `list_instances(state=None)`
List all EC2 instances with details.

**Parameters:**
- `state` (optional): Filter by "running", "stopped", or "terminated"

**Returns:**
- Instance ID, state, type, IP, launch time, name tag

**Example:**
```python
mcp__ec2__list_instances()
mcp__ec2__list_instances(state="running")
```

---

### `get_instance_logs(instance_id, stream_type='training', tail=100, hours_back=24)`
Fetch CloudWatch logs for EC2 instance.

**Parameters:**
- `instance_id` (required): EC2 instance ID (e.g., "i-0abc123")
- `stream_type` (optional): "training", "errors", "boot", or "crashes" (default: "training")
- `tail` (optional): Number of lines from end (default: 100, use 0 for all)
- `hours_back` (optional): Hours of history to fetch (default: 24)

**Auto-discovers log groups from instance Name tag.**

**Returns:**
- Formatted log events with timestamps

**Example:**
```python
mcp__ec2__get_instance_logs(instance_id="i-0abc123")
mcp__ec2__get_instance_logs(instance_id="i-0abc123", stream_type="errors", tail=200)
```

---

### `monitor_instance(instance_id)`
Health check for EC2 instance.

**Parameters:**
- `instance_id` (required): Instance to monitor

**Returns:**
- State, type, IP, launch time, runtime (if running)

**Example:**
```python
mcp__ec2__monitor_instance(instance_id="i-0abc123")
```

---

### `diagnose_crash(instance_id)`
Analyze crashed instance.

**Parameters:**
- `instance_id` (required): Crashed instance ID

**Returns:**
- State, state reason, error analysis guidance

**Example:**
```python
mcp__ec2__diagnose_crash(instance_id="i-0abc123")
```

## Installation

```bash
cd ~/mango/mcp/ec2
./setup-ec2-mcp.sh
```

Restart Claude Code to load the server.

## Credentials

Hardcoded AWS credentials (per CLAUDE.md policy):
- Account: 746491138304
- Region: us-east-2
- Access: Full EC2 and CloudWatch read access

## Architecture

**CloudWatch Log Streams:**
- `i-xxxxx` - training.log (main output)
- `i-xxxxx_errors` - error_log_*.txt files
- `i-xxxxx_crashes` - crash_report_*.txt files
- `i-xxxxx_boot` - boot/startup logs

**Log Group Format:**
- `/aws/ec2/training/{config_path}`
- Example: `/aws/ec2/training/configs/05_benchmarks/fexofenadine_mpo.yaml`

## Workflow Integration

**Before (WRONG - inline bash):**
```markdown
```bash
export AWS_ACCESS_KEY_ID="..."
aws ec2 describe-instances --filters ...
aws logs get-log-events --log-group-name ... | jq ...
```
```

**After (CORRECT - MCP):**
```markdown
Use MCP tool: `mcp__ec2__list_instances(state="running")`
Use MCP tool: `mcp__ec2__get_instance_logs(instance_id="i-xxx", stream_type="errors")`
```

## Related MCPs

- `mcp__wandb_runs__*` - W&B run tracking
- `mcp__process-monitor__*` - Local process monitoring
- `mcp__report__*` - Report generation

## Maintenance

All EC2/CloudWatch functionality should go through this MCP. Do NOT:
- Add new bash scripts for AWS operations
- Use inline AWS CLI commands in workflows
- Create duplicate Python scripts for EC2/CloudWatch

Instead:
- Add new tools to this MCP server
- Update workflows to use MCP tools
- Keep all AWS logic centralized here
