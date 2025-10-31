#!/usr/bin/env python3
"""
Time Estimator MCP Server for Claude Code

Provides fact-based time estimation using actual filesystem timestamps.
NO GUESSING - only measured rates from real data.

Tools:
- estimate_completion: Analyze file timestamps and calculate ETA
- quick_estimate: Get cached estimate if available
- track_rate: Track completion rate over time
"""

import json
import sys
import os
import glob
from pathlib import Path
from datetime import datetime, timedelta


def send_message(message):
    """Send a JSON-RPC message to stdout"""
    print(json.dumps(message))
    sys.stdout.flush()


def receive_message():
    """Receive a JSON-RPC message from stdin"""
    try:
        line = sys.stdin.readline()
        if not line:
            return None
        return json.loads(line.strip())
    except json.JSONDecodeError:
        return None


def analyze_completion_rate(pattern, total_expected, base_dir=None):
    """
    Analyze actual file timestamps to calculate completion rate and ETA.

    Returns dict with measured statistics (NO GUESSES).
    """
    if base_dir:
        pattern = str(Path(base_dir) / pattern)

    files = glob.glob(pattern, recursive=True)

    if not files:
        return {
            'error': f'No files found matching pattern: {pattern}',
            'completed': 0,
            'total': total_expected,
            'pattern': pattern
        }

    # Get timestamps
    timestamps = []
    for f in files:
        try:
            stat = os.stat(f)
            timestamps.append({
                'file': f,
                'timestamp': stat.st_mtime
            })
        except OSError:
            continue

    if not timestamps:
        return {
            'error': 'Could not read timestamps',
            'completed': 0,
            'total': total_expected
        }

    # Sort chronologically
    timestamps.sort(key=lambda x: x['timestamp'])

    completed = len(timestamps)
    remaining = total_expected - completed

    # Measured time span
    first_ts = timestamps[0]['timestamp']
    last_ts = timestamps[-1]['timestamp']

    elapsed_seconds = last_ts - first_ts
    elapsed_hours = elapsed_seconds / 3600

    # Measured rate (actual, not guessed)
    if elapsed_seconds > 0 and completed > 1:
        files_per_hour = (completed - 1) / elapsed_hours
        avg_seconds_per_file = elapsed_seconds / (completed - 1)
        avg_minutes_per_file = avg_seconds_per_file / 60
    else:
        files_per_hour = None
        avg_seconds_per_file = None
        avg_minutes_per_file = None

    # ETA based on measured rate
    if files_per_hour and files_per_hour > 0:
        hours_remaining = remaining / files_per_hour
        days_remaining = hours_remaining / 24
        eta_datetime = datetime.fromtimestamp(last_ts) + timedelta(hours=hours_remaining)
    else:
        hours_remaining = None
        days_remaining = None
        eta_datetime = None

    # Recent rate (last 10 files)
    if len(timestamps) >= 10:
        recent_first = timestamps[-10]['timestamp']
        recent_last = timestamps[-1]['timestamp']
        recent_elapsed = recent_last - recent_first
        recent_rate = 9 / (recent_elapsed / 3600) if recent_elapsed > 0 else None
    else:
        recent_rate = None

    return {
        'pattern': pattern,
        'completed': completed,
        'total': total_expected,
        'remaining': remaining,
        'percent_complete': (completed / total_expected) * 100,

        'first_file': timestamps[0]['file'],
        'last_file': timestamps[-1]['file'],
        'first_timestamp': datetime.fromtimestamp(first_ts).isoformat(),
        'last_timestamp': datetime.fromtimestamp(last_ts).isoformat(),

        'elapsed_seconds': round(elapsed_seconds, 2),
        'elapsed_hours': round(elapsed_hours, 2),
        'elapsed_days': round(elapsed_hours / 24, 2),

        'avg_seconds_per_file': round(avg_seconds_per_file, 2) if avg_seconds_per_file else None,
        'avg_minutes_per_file': round(avg_minutes_per_file, 2) if avg_minutes_per_file else None,
        'files_per_hour': round(files_per_hour, 2) if files_per_hour else None,

        'recent_files_per_hour': round(recent_rate, 2) if recent_rate else None,

        'hours_remaining': round(hours_remaining, 2) if hours_remaining else None,
        'days_remaining': round(days_remaining, 2) if days_remaining else None,
        'eta_timestamp': eta_datetime.isoformat() if eta_datetime else None,
        'eta_human': eta_datetime.strftime('%Y-%m-%d %H:%M') if eta_datetime else None
    }


def format_estimate_output(stats):
    """Format estimate statistics as human-readable text"""
    if 'error' in stats:
        return f"ERROR: {stats['error']}\nPattern: {stats.get('pattern', 'unknown')}"

    lines = []
    lines.append("=" * 80)
    lines.append("FACT-BASED COMPLETION ESTIMATE")
    lines.append("Source: Actual filesystem timestamps (NO GUESSING)")
    lines.append("=" * 80)
    lines.append("")

    lines.append(f"Pattern:         {stats['pattern']}")
    lines.append(f"Progress:        {stats['completed']}/{stats['total']} ({stats['percent_complete']:.1f}%)")
    lines.append(f"Remaining:       {stats['remaining']}")
    lines.append("")

    lines.append(f"First completed: {stats['first_timestamp']}")
    lines.append(f"Last completed:  {stats['last_timestamp']}")
    lines.append(f"Elapsed:         {stats['elapsed_hours']:.2f} hours ({stats['elapsed_days']:.2f} days)")
    lines.append("")

    lines.append("MEASURED RATES (from actual timestamps):")
    if stats['avg_minutes_per_file']:
        lines.append(f"  {stats['avg_minutes_per_file']:.2f} minutes per file (average)")
        lines.append(f"  {stats['files_per_hour']:.2f} files per hour (average)")
    if stats['recent_files_per_hour']:
        lines.append(f"  {stats['recent_files_per_hour']:.2f} files per hour (recent 10 files)")
    lines.append("")

    if stats['eta_human']:
        lines.append("ESTIMATED COMPLETION (based on measured rate):")
        lines.append(f"  {stats['hours_remaining']:.2f} hours remaining ({stats['days_remaining']:.2f} days)")
        lines.append(f"  ETA: {stats['eta_human']}")
        lines.append("")

    return "\n".join(lines)


def handle_initialize(params):
    """Handle initialize request"""
    return {
        "protocolVersion": "2024-11-05",
        "capabilities": {
            "tools": {}
        },
        "serverInfo": {
            "name": "time-estimator",
            "version": "1.0.0"
        }
    }


def handle_tools_list():
    """Handle tools/list request"""
    return {
        "tools": [
            {
                "name": "estimate_completion",
                "description": "Analyze file timestamps to calculate MEASURED completion rate and ETA. NO GUESSING - only fact-based estimates from actual filesystem data.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "pattern": {
                            "type": "string",
                            "description": "Glob pattern for completed files (e.g., 'data/*/DONE', 'results/**/*.complete')"
                        },
                        "total": {
                            "type": "integer",
                            "description": "Total expected number of completions"
                        },
                        "base_dir": {
                            "type": "string",
                            "description": "Base directory to search from (default: current directory)"
                        },
                        "save_json": {
                            "type": "string",
                            "description": "Optional path to save JSON output"
                        }
                    },
                    "required": ["pattern", "total"]
                }
            },
            {
                "name": "quick_estimate",
                "description": "Get cached estimate from JSON file if available. Fast lookup without re-analyzing filesystem.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "json_path": {
                            "type": "string",
                            "description": "Path to cached JSON estimate file"
                        }
                    },
                    "required": ["json_path"]
                }
            },
            {
                "name": "compare_estimates",
                "description": "Compare multiple estimates over time to track rate changes and prediction accuracy.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "json_files": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of JSON estimate files to compare (chronological order)"
                        }
                    },
                    "required": ["json_files"]
                }
            }
        ]
    }


def handle_tools_call(name, arguments):
    """Handle tools/call request"""
    if name == "estimate_completion":
        return estimate_completion(arguments)
    elif name == "quick_estimate":
        return quick_estimate(arguments)
    elif name == "compare_estimates":
        return compare_estimates(arguments)
    else:
        raise ValueError(f"Unknown tool: {name}")


def estimate_completion(arguments):
    """Analyze file timestamps and calculate ETA"""
    pattern = arguments.get("pattern")
    total = arguments.get("total")
    base_dir = arguments.get("base_dir")
    save_json = arguments.get("save_json")

    if not pattern or not total:
        raise ValueError("Both 'pattern' and 'total' are required")

    # Analyze completion rate
    stats = analyze_completion_rate(pattern, total, base_dir)

    # Save JSON if requested
    if save_json and 'error' not in stats:
        try:
            os.makedirs(os.path.dirname(os.path.abspath(save_json)), exist_ok=True)
            with open(save_json, 'w') as f:
                json.dump(stats, f, indent=2)
            stats['json_saved'] = save_json
        except Exception as e:
            stats['json_save_error'] = str(e)

    # Format output
    output_text = format_estimate_output(stats)

    return {
        "content": [
            {
                "type": "text",
                "text": output_text
            }
        ]
    }


def quick_estimate(arguments):
    """Get cached estimate from JSON file"""
    json_path = arguments.get("json_path")

    if not json_path:
        raise ValueError("'json_path' is required")

    try:
        with open(json_path, 'r') as f:
            stats = json.load(f)

        output_text = format_estimate_output(stats)

        return {
            "content": [
                {
                    "type": "text",
                    "text": output_text
                }
            ]
        }
    except FileNotFoundError:
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"ERROR: Cached estimate file not found: {json_path}"
                }
            ]
        }
    except json.JSONDecodeError:
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"ERROR: Invalid JSON in estimate file: {json_path}"
                }
            ]
        }


def compare_estimates(arguments):
    """Compare multiple estimates to track rate changes"""
    json_files = arguments.get("json_files", [])

    if not json_files:
        raise ValueError("'json_files' list is required")

    estimates = []
    for json_file in json_files:
        try:
            with open(json_file, 'r') as f:
                stats = json.load(f)
                estimates.append(stats)
        except Exception as e:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"ERROR loading {json_file}: {str(e)}"
                    }
                ]
            }

    # Build comparison output
    lines = []
    lines.append("=" * 80)
    lines.append("ESTIMATE COMPARISON - TRACKING PREDICTION ACCURACY")
    lines.append("=" * 80)
    lines.append("")

    for i, est in enumerate(estimates, 1):
        lines.append(f"Estimate {i}: {est.get('last_timestamp', 'unknown')}")
        lines.append(f"  Progress: {est['completed']}/{est['total']} ({est['percent_complete']:.1f}%)")
        lines.append(f"  Rate: {est.get('files_per_hour', 'N/A')} files/hour")
        lines.append(f"  ETA: {est.get('eta_human', 'N/A')}")
        lines.append("")

    # Calculate rate trend
    if len(estimates) >= 2:
        first_rate = estimates[0].get('files_per_hour')
        last_rate = estimates[-1].get('files_per_hour')

        if first_rate and last_rate:
            rate_change = ((last_rate - first_rate) / first_rate) * 100
            lines.append("RATE TREND:")
            if rate_change > 5:
                lines.append(f"  ACCELERATING: +{rate_change:.1f}% faster")
            elif rate_change < -5:
                lines.append(f"  DECELERATING: {rate_change:.1f}% slower")
            else:
                lines.append(f"  STABLE: {rate_change:.1f}% change")
            lines.append("")

    return {
        "content": [
            {
                "type": "text",
                "text": "\n".join(lines)
            }
        ]
    }


def main():
    """Main server loop"""
    while True:
        try:
            request = receive_message()
            if request is None:
                break

            method = request.get("method")
            params = request.get("params", {})
            request_id = request.get("id")

            try:
                if method == "initialize":
                    result = handle_initialize(params)
                elif method == "tools/list":
                    result = handle_tools_list()
                elif method == "tools/call":
                    tool_name = params.get("name")
                    arguments = params.get("arguments", {})
                    result = handle_tools_call(tool_name, arguments)
                else:
                    raise ValueError(f"Unknown method: {method}")

                # Send success response
                response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": result
                }
                send_message(response)

            except Exception as e:
                # Send error response
                error_response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32603,
                        "message": str(e)
                    }
                }
                send_message(error_response)

        except KeyboardInterrupt:
            break
        except Exception:
            break


if __name__ == "__main__":
    main()
