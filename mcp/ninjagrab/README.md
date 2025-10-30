# ninjagrab MCP

A file collection MCP server that replaces CLI calls to `ninjagrab.sh` in plea workflows.

## What It Does

- Concatenates multiple files with clear delimiters
- Outputs content to stdout AND saves to `ninjagrab-out.txt`
- Provides MCP interface for file collection in plea workflows
- Handles file errors gracefully like the original `ninjagrab.sh`
- **Only processes code and config files**: `.json`, `.yaml`, `.yml`, `.py`, `.R`, `.sh`
- **Filters out logs and large data files** - other file types are automatically excluded

## Allowed File Types

**IMPORTANT**: Ninjagrab is designed for code and configuration files only. It will **automatically filter out** any files that don't match these extensions:

- `.json` - JSON configuration and data files
- `.yaml` / `.yml` - YAML configuration files
- `.py` - Python scripts
- `.R` - R scripts
- `.sh` - Shell scripts

**Filtered file types** (automatically excluded):
- Log files (`.log`, `.txt`)
- Data files (`.csv`, `.parquet`, `.pkl`)
- Binary files
- Any other extensions

When a file is filtered, you'll see: `[FILTERED] Skipping filename.ext (extension .ext not allowed - only json, yaml, yml, py, R, sh allowed)`

## How It Works

The MCP server replicates the exact functionality of `ninjagrab.sh`:

1. **Takes file paths as input** - List of files to collect
2. **Filters by extension** - Only processes allowed file types (json, yaml, yml, py, R, sh)
3. **Creates delimiters** - `===== filename =====` for each file
4. **Concatenates content** - Reads and combines all file contents
5. **Dual output** - Returns content AND saves to `ninjagrab-out.txt`
6. **Error handling** - Reports missing files and filtered files, continues processing others

## Setup

1. **Run Setup Script**
```bash
cd mcp/ninjagrab
./setup-ninjagrab-mcp.sh
```

2. **Restart Claude Code**
The MCP will only be available after restarting Claude Code.

## Usage

### From Plea Workflows
The MCP is designed to be used in `/plea` and `/o3plea` workflows:

```
Instead of CLI:
~/usability/ninjagrab.sh train.py utils.py config.yaml

Use MCP:
"Use the ninjagrab MCP to collect these files: train.py utils.py config.yaml"
```

**Example with filtering**:
```
Input files: train.py, config.yaml, output.log, data.csv
Processed: train.py, config.yaml (only allowed extensions)
Filtered: output.log, data.csv (automatically excluded)
```

### Tool Details
- **Tool name**: `mcp__ninjagrab__ninjagrab_collect`
- **Input**: Array of file paths, optional working directory
- **Output**: Concatenated content, output file path, files processed count, errors
- **Files created**: `ninjagrab-out.txt` in working directory

## Backup Fallback

If the MCP fails for any reason, workflows can fall back to manual collection:

```bash
# For each required file, use this format:
echo "===== FILENAME ====="
cat FILENAME
echo ""
```

This produces identical output to both `ninjagrab.sh` and the MCP server.

## Integration with Plea Workflows

The ninjagrab MCP is specifically designed for use in:
- `/plea` - Technical pleas to human architects  
- `/o3plea` - Direct consultation with o3 model

Both workflows use file collection to provide complete code context for analysis.

## Error Handling

Like the original `ninjagrab.sh`, the MCP:
- Reports missing files but continues processing others
- Writes errors to both response AND `ninjagrab-out.txt`
- Returns error details for workflow decision making
- Maintains exact compatibility with existing plea workflow expectations

## Files

```
mcp/ninjagrab/
├── README.md                   # This file
├── ninjagrab_mcp.py           # FastMCP server implementation
└── setup-ninjagrab-mcp.sh     # Automated setup script
```

## Comparison with Original

| Feature | ninjagrab.sh | ninjagrab MCP |
|---------|--------------|---------------|
| File concatenation |  |  |
| Delimiter format |  |  |
| Save to ninjagrab-out.txt |  |  |
| Extension filtering (json, yaml, yml, py, R, sh only) |  |  |
| Error handling |  |  |
| Exit on missing files |  |  |
| Working directory support |  |  |
| MCP integration |  |  |
| Structured output |  |  |

The MCP version provides the same core functionality with additional structured output for better integration with AI workflows. Both versions now enforce file type restrictions to prevent accidental inclusion of logs or large data files.