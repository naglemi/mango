# Time Estimator MCP Server

Fact-based time estimation using actual filesystem timestamps.
NO GUESSING - only measured rates from real data.

## Purpose

Eliminates guesswork in time estimates by analyzing actual file creation timestamps to measure real completion rates and project accurate ETAs.

## Tools

### 1. estimate_completion
Analyze file timestamps to calculate measured completion rate and ETA.

**Parameters:**
- `pattern` (required): Glob pattern for completed files (e.g., `"data/*/DONE"`, `"results/**/*.complete"`)
- `total` (required): Total expected number of completions
- `base_dir` (optional): Base directory to search from (default: current directory)
- `save_json` (optional): Path to save JSON output for later reference

**Example:**
```python
# Via MCP tool call
{
  "pattern": "data/md_runs/production/complexes/*/PARAMETERIZED",
  "total": 474,
  "save_json": "data/md_runs/production/estimate.json"
}
```

**Output:**
```
================================================================================
FACT-BASED COMPLETION ESTIMATE
Source: Actual filesystem timestamps (NO GUESSING)
================================================================================

Pattern:         data/md_runs/production/complexes/*/PARAMETERIZED
Progress:        83/474 (17.5%)
Remaining:       391

First completed: 2025-10-29T15:33:42
Last completed:  2025-10-29T19:01:28
Elapsed:         3.46 hours (0.14 days)

MEASURED RATES (from actual timestamps):
  2.53 minutes per file (average)
  23.68 files per hour (average)
  35.38 files per hour (recent 10 files)

ESTIMATED COMPLETION (based on measured rate):
  16.51 hours remaining (0.69 days)
  ETA: 2025-10-30 11:32
```

### 2. quick_estimate
Get cached estimate from JSON file if available. Fast lookup without re-analyzing filesystem.

**Parameters:**
- `json_path` (required): Path to cached JSON estimate file

**Example:**
```python
{
  "json_path": "data/md_runs/production/estimate.json"
}
```

### 3. compare_estimates
Compare multiple estimates over time to track rate changes and prediction accuracy.

**Parameters:**
- `json_files` (required): List of JSON estimate files to compare (in chronological order)

**Example:**
```python
{
  "json_files": [
    "estimate_1hour.json",
    "estimate_2hour.json",
    "estimate_3hour.json"
  ]
}
```

**Output:**
```
================================================================================
ESTIMATE COMPARISON - TRACKING PREDICTION ACCURACY
================================================================================

Estimate 1: 2025-10-29T16:00:00
  Progress: 25/474 (5.3%)
  Rate: 20.5 files/hour
  ETA: 2025-10-30 14:30

Estimate 2: 2025-10-29T17:00:00
  Progress: 50/474 (10.5%)
  Rate: 25.0 files/hour
  ETA: 2025-10-30 10:00

RATE TREND:
  ACCELERATING: +22.0% faster
```

## Use Cases

1. **MD Parameterization**
   ```python
   estimate_completion({
     "pattern": "data/md_runs/*/complexes/*/PARAMETERIZED",
     "total": 474
   })
   ```

2. **MD Simulations**
   ```python
   estimate_completion({
     "pattern": "data/md_runs/*/complexes/*/trajectory.dcd",
     "total": 474
   })
   ```

3. **Analysis Outputs**
   ```python
   estimate_completion({
     "pattern": "results/*/analysis_complete.txt",
     "total": 1000
   })
   ```

4. **Any Batch Process**
   ```python
   estimate_completion({
     "pattern": "output/**/DONE",
     "total": 500
   })
   ```

## Workflow

1. **Start long-running process**
2. **Wait for 5-10 completions** (need real data to measure)
3. **Run estimate_completion** to measure actual rate
4. **Report ETA** with evidence from measured data
5. **Re-run hourly** to update with fresh measurements
6. **Track accuracy** using compare_estimates

## Why This Matters

### Old Approach (Guessing)
❌ "This will take 2-4 days" ← No basis
❌ "Approximately 50 hours" ← Pulled from thin air
❌ "Should be done tomorrow" ← Hope, not data

### New Approach (Measuring)
✅ "At measured rate of 23.68 files/hour..." ← Verifiable
✅ "Based on 83 completions over 3.46 hours..." ← Evidence
✅ "Recent acceleration to 35.38 files/hour..." ← Shows trends

## Real-World Results

**QSAR Project Example:**
- **Initial guess:** 50-70 hours
- **Measured reality:** 16.51 hours
- **Error:** 3-4x overestimate

Tool caught this immediately by using actual data instead of guesses.

## Configuration

Added to `~/.claude.json` by `configure-mcp-servers.sh`:

```json
{
  "mcpServers": {
    "time-estimator": {
      "command": "python3",
      "args": ["/home/ubuntu/mango/mcp/time-estimator/time_estimator_mcp_server.py"],
      "env": {}
    }
  }
}
```

## Dependencies

- Python 3.6+
- Standard library only (no external packages)

## Testing

```bash
# Test estimate_completion
python3 time_estimator_mcp_server.py << 'EOF'
{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
{"jsonrpc": "2.0", "id": 2, "method": "tools/list"}
{"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "estimate_completion", "arguments": {"pattern": "test/*/*.done", "total": 100}}}
EOF
```

## See Also

- `tools/estimate_from_timestamps.py` - Standalone CLI version
- `tools/ESTIMATION_WORKFLOW.md` - Complete workflow documentation
- `tools/QUICK_REFERENCE.md` - Command reference
