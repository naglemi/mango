# Estimate MCP Server

Fact-based time estimation MCP server using filesystem timestamps.

## What It Does

Analyzes actual file creation timestamps to provide evidence-based completion estimates.

**NO GUESSING. ONLY MEASURED RATES FROM ACTUAL FILESYSTEM TIMESTAMPS.**

## Installation

```bash
cd estimate_mcp
pip install -e .
```

## Running the Server

### Stdio mode (for Claude Desktop integration)
```bash
estimate-mcp
```

### SSE mode (for testing)
```bash
estimate-mcp --serve --port 8001
```

## Claude Desktop Integration

Add to your Claude Desktop config (`~/.config/claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "estimate": {
      "command": "estimate-mcp"
    }
  }
}
```

Or with full path:
```json
{
  "mcpServers": {
    "estimate": {
      "command": "/home/ubuntu/.local/bin/estimate-mcp"
    }
  }
}
```

## Usage in Claude

Once integrated, Claude will have access to:

```python
mcp__estimate__analyze_completion(
    pattern="data/md_runs/production/complexes/*/PARAMETERIZED",
    total=474
)
```

### Parameters

- **pattern** (required): Glob pattern for completed files
  - Example: `"data/*/DONE"`
  - Example: `"results/**/*.complete"`
  - Supports recursive globs with `**`

- **total** (required): Total expected number of completions
  - Must be an integer

- **base_dir** (optional): Base directory to search from
  - Defaults to current working directory

### Output

Returns structured data with:

- **Progress**: completed/total, percent complete
- **Timestamps**: first and last completion times
- **Measured rates**:
  - Files per hour
  - Minutes per file
  - Recent rate (last 10 files)
- **Estimates**:
  - Hours/days remaining
  - ETA timestamp and human-readable format

## Example Output

```json
{
  "pattern": "data/md_runs/production/complexes/*/PARAMETERIZED",
  "completed": 83,
  "total": 474,
  "remaining": 391,
  "percent_complete": 17.51,
  "first_timestamp": "2025-10-29T15:33:42",
  "last_timestamp": "2025-10-29T19:01:28",
  "elapsed_hours": 3.46,
  "avg_minutes_per_file": 2.53,
  "files_per_hour": 23.68,
  "recent_files_per_hour": 35.38,
  "hours_remaining": 16.51,
  "eta_human": "2025-10-30 11:32"
}
```

## Features

✅ **Evidence-based**: Every number backed by filesystem timestamps
✅ **Verifiable**: Anyone can run same tool to check
✅ **Trend detection**: Shows acceleration/deceleration
✅ **General-purpose**: Works with any file-based workflow
✅ **Structured output**: Clean JSON for programmatic use
✅ **Zero guessing**: All estimates based on measured data

## Use Cases

### MD Parameterization
```python
mcp__estimate__analyze_completion(
    pattern="data/md_runs/production/complexes/*/PARAMETERIZED",
    total=474
)
```

### MD Simulations
```python
mcp__estimate__analyze_completion(
    pattern="data/md_runs/production/complexes/*/trajectory.dcd",
    total=474
)
```

### Batch Analysis
```python
mcp__estimate__analyze_completion(
    pattern="results/*/analysis_complete.txt",
    total=1000
)
```

### Any Workflow
```python
mcp__estimate__analyze_completion(
    pattern="path/to/*/DONE_MARKER",
    total=<expected_count>
)
```

## Why This Exists

### The Problem
Agents making wild guesses about completion times:
- "This will take 2-4 days" ← No basis
- "Approximately 50 hours" ← Pulled from thin air
- "Should be done tomorrow" ← Hope is not a plan

### The Solution
Measure actual completion rates from filesystem timestamps:
- "At measured rate of 23.68 files/hour..." ← Verifiable
- "Based on 83 completions over 3.46 hours..." ← Evidence
- "Recent acceleration to 35.38 files/hour..." ← Shows trends

### Real Example
- **Agent guess**: 50-70 hours remaining
- **Measured reality**: 16.51 hours remaining
- **Error**: 3-4x overestimate

This tool catches such errors immediately by using actual data.

## Development

### Project Structure
```
estimate_mcp/
├── estimate_mcp/
│   ├── __init__.py
│   ├── server.py          # FastMCP server
│   └── tools/
│       ├── base_tool.py   # Base tool class
│       └── estimate_tool.py  # Estimation implementation
├── pyproject.toml
└── README.md
```

### Testing Locally
```bash
# Install in development mode
pip install -e .

# Run server
estimate-mcp

# Or with SSE for testing
estimate-mcp --serve --port 8001
```

## License

MIT
