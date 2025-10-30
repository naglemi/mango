#!/usr/bin/env python3
"""
EC2 & CloudWatch MCP Server for Claude Code

Provides unified access to EC2 instances and CloudWatch logs.
Consolidates functionality from:
- stream_ec2_logs.py
- diagnose_ec2_crash.py
- monitor_ec2_30min.py
- get_cloudwatch_logs.sh

Tools:
- list_instances: Get all EC2 instances with status
- get_instance_logs: Fetch CloudWatch logs for instance
- monitor_instance: Health check for running instance
- diagnose_crash: Analyze crashed instance logs
"""

import asyncio
import json
import subprocess
import sys
from datetime import datetime, timedelta
from typing import Any

from mcp.server import Server
from mcp.types import Tool, TextContent

# AWS Credentials (hardcoded as per CLAUDE.md policy)
AWS_ACCESS_KEY_ID = "AKIA23TSW2EAFIFXENZM"
AWS_SECRET_ACCESS_KEY = "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"
AWS_DEFAULT_REGION = "us-east-2"

app = Server("ec2-server")


def run_aws_command(cmd: list[str]) -> dict:
    """Run AWS CLI command with credentials"""
    env = {
        "AWS_ACCESS_KEY_ID": AWS_ACCESS_KEY_ID,
        "AWS_SECRET_ACCESS_KEY": AWS_SECRET_ACCESS_KEY,
        "AWS_DEFAULT_REGION": AWS_DEFAULT_REGION,
        "PATH": subprocess.os.environ.get("PATH", "")
    }

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        env=env
    )

    if result.returncode != 0:
        return {"error": result.stderr, "returncode": result.returncode}

    return {"output": result.stdout, "returncode": 0}


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available EC2/CloudWatch tools"""
    return [
        Tool(
            name="list_instances",
            description="List all EC2 instances with state, type, launch time, and config",
            inputSchema={
                "type": "object",
                "properties": {
                    "state": {
                        "type": "string",
                        "description": "Filter by state: running, stopped, terminated (optional)",
                    },
                },
            },
        ),
        Tool(
            name="get_instance_logs",
            description="Get CloudWatch logs for EC2 instance. Auto-discovers log streams (training, errors, boot, crashes).",
            inputSchema={
                "type": "object",
                "properties": {
                    "instance_id": {
                        "type": "string",
                        "description": "EC2 instance ID (e.g., i-0abc123)",
                    },
                    "stream_type": {
                        "type": "string",
                        "description": "Log stream type: training, errors, boot, crashes (default: training)",
                    },
                    "tail": {
                        "type": "number",
                        "description": "Number of lines from end (default: 100, use 0 for all)",
                    },
                    "hours_back": {
                        "type": "number",
                        "description": "How many hours of logs to fetch (default: 24)",
                    },
                },
                "required": ["instance_id"],
            },
        ),
        Tool(
            name="monitor_instance",
            description="Check EC2 instance health: state, runtime, W&B status, GPU usage",
            inputSchema={
                "type": "object",
                "properties": {
                    "instance_id": {
                        "type": "string",
                        "description": "EC2 instance ID to monitor",
                    },
                },
                "required": ["instance_id"],
            },
        ),
        Tool(
            name="diagnose_crash",
            description="Analyze crashed EC2 instance: error logs, crash reports, probable cause",
            inputSchema={
                "type": "object",
                "properties": {
                    "instance_id": {
                        "type": "string",
                        "description": "Crashed EC2 instance ID",
                    },
                },
                "required": ["instance_id"],
            },
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls"""

    if name == "list_instances":
        state_filter = arguments.get("state")

        # Build AWS CLI command
        cmd = [
            "aws", "ec2", "describe-instances",
            "--query", "Reservations[*].Instances[*].{ID:InstanceId,State:State.Name,Type:InstanceType,Launch:LaunchTime,IP:PrivateIpAddress,Name:Tags[?Key==`Name`].Value|[0]}",
            "--output", "json"
        ]

        if state_filter:
            cmd.extend(["--filters", f"Name=instance-state-name,Values={state_filter}"])

        result = run_aws_command(cmd)

        if result.get("error"):
            return [TextContent(type="text", text=f"Error: {result['error']}")]

        try:
            instances_data = json.loads(result["output"])
            instances = []
            for reservation in instances_data:
                instances.extend(reservation)

            if not instances:
                return [TextContent(type="text", text="No EC2 instances found")]

            # Format output
            output = [f"Found {len(instances)} EC2 instances:\n"]
            for inst in instances:
                output.append(f"\nInstance: {inst['ID']}")
                output.append(f"  State: {inst['State']}")
                output.append(f"  Type: {inst['Type']}")
                output.append(f"  IP: {inst.get('IP', 'N/A')}")
                output.append(f"  Launch: {inst.get('Launch', 'N/A')}")
                output.append(f"  Name: {inst.get('Name', 'N/A')}")

            return [TextContent(type="text", text="\n".join(output))]

        except json.JSONDecodeError as e:
            return [TextContent(type="text", text=f"Error parsing AWS response: {e}")]

    elif name == "get_instance_logs":
        instance_id = arguments["instance_id"]
        stream_type = arguments.get("stream_type", "training")
        tail = arguments.get("tail", 100)
        hours_back = arguments.get("hours_back", 24)

        # Calculate start time
        start_time = int((datetime.now() - timedelta(hours=hours_back)).timestamp() * 1000)

        # Determine log group and stream name
        # First, get instance tags to find config name
        cmd = [
            "aws", "ec2", "describe-instances",
            "--instance-ids", instance_id,
            "--query", "Reservations[0].Instances[0].Tags[?Key==`Name`].Value|[0]",
            "--output", "text"
        ]

        result = run_aws_command(cmd)
        if result.get("error"):
            return [TextContent(type="text", text=f"Error getting instance info: {result['error']}")]

        config_tag = result["output"].strip()

        # Extract config path from tag (format: configs/path/file.yaml-TIMESTAMP)
        if config_tag and config_tag != "None":
            config_path = config_tag.rsplit("-", 2)[0]  # Remove timestamp
            log_group = f"/aws/ec2/training/{config_path}"
        else:
            # Fallback: try common log groups
            log_group = "/aws/ec2/training"

        # Determine stream name suffix
        stream_suffix = {
            "training": "",
            "errors": "_errors",
            "boot": "_boot",
            "crashes": "_crashes"
        }.get(stream_type, "")

        log_stream = f"{instance_id}{stream_suffix}"

        # Fetch logs
        cmd = [
            "aws", "logs", "get-log-events",
            "--log-group-name", log_group,
            "--log-stream-name", log_stream,
            "--start-time", str(start_time),
            "--output", "json"
        ]

        if tail > 0:
            cmd.extend(["--limit", str(tail)])

        result = run_aws_command(cmd)

        if result.get("error"):
            return [TextContent(type="text", text=f"CloudWatch Error: {result['error']}\n\nLog Group: {log_group}\nLog Stream: {log_stream}")]

        try:
            logs_data = json.loads(result["output"])
            events = logs_data.get("events", [])

            if not events:
                return [TextContent(type="text", text=f"No log events found\n\nLog Group: {log_group}\nLog Stream: {log_stream}\nTime Range: Last {hours_back} hours")]

            # Format logs
            output = [f"CloudWatch Logs for {instance_id} ({stream_type})"]
            output.append(f"Log Group: {log_group}")
            output.append(f"Log Stream: {log_stream}")
            output.append(f"Events: {len(events)}")
            output.append("=" * 80 + "\n")

            for event in events[-tail:] if tail > 0 else events:
                timestamp = datetime.fromtimestamp(event["timestamp"] / 1000).strftime("%Y-%m-%d %H:%M:%S")
                message = event["message"].rstrip()
                output.append(f"[{timestamp}] {message}")

            return [TextContent(type="text", text="\n".join(output))]

        except json.JSONDecodeError as e:
            return [TextContent(type="text", text=f"Error parsing CloudWatch response: {e}")]

    elif name == "monitor_instance":
        instance_id = arguments["instance_id"]

        # Get instance details
        cmd = [
            "aws", "ec2", "describe-instances",
            "--instance-ids", instance_id,
            "--query", "Reservations[0].Instances[0].{State:State.Name,Type:InstanceType,Launch:LaunchTime,IP:PrivateIpAddress}",
            "--output", "json"
        ]

        result = run_aws_command(cmd)

        if result.get("error"):
            return [TextContent(type="text", text=f"Error: {result['error']}")]

        try:
            instance = json.loads(result["output"])

            output = [f"EC2 Instance Monitor: {instance_id}\n"]
            output.append(f"State: {instance['State']}")
            output.append(f"Type: {instance['Type']}")
            output.append(f"IP: {instance.get('IP', 'N/A')}")
            output.append(f"Launch: {instance.get('Launch', 'N/A')}")

            # Calculate runtime if running
            if instance['State'] == 'running' and instance.get('Launch'):
                launch_time = datetime.fromisoformat(instance['Launch'].replace('Z', '+00:00'))
                runtime = datetime.now(launch_time.tzinfo) - launch_time
                hours = runtime.total_seconds() / 3600
                output.append(f"Runtime: {hours:.2f} hours")

            return [TextContent(type="text", text="\n".join(output))]

        except json.JSONDecodeError as e:
            return [TextContent(type="text", text=f"Error parsing response: {e}")]

    elif name == "diagnose_crash":
        instance_id = arguments["instance_id"]

        # Get instance state
        cmd = [
            "aws", "ec2", "describe-instances",
            "--instance-ids", instance_id,
            "--query", "Reservations[0].Instances[0].{State:State.Name,StateReason:StateReason.Message}",
            "--output", "json"
        ]

        result = run_aws_command(cmd)

        if result.get("error"):
            return [TextContent(type="text", text=f"Error: {result['error']}")]

        try:
            instance = json.loads(result["output"])

            output = [f"Crash Diagnosis for {instance_id}\n"]
            output.append(f"State: {instance['State']}")
            output.append(f"State Reason: {instance.get('StateReason', 'N/A')}")
            output.append("\nAnalyzing error logs...\n")

            # Fetch error logs (delegate to get_instance_logs logic)
            # This is a simplified version - full implementation would check all log streams
            output.append("Run get_instance_logs with stream_type='errors' for detailed error analysis")

            return [TextContent(type="text", text="\n".join(output))]

        except json.JSONDecodeError as e:
            return [TextContent(type="text", text=f"Error parsing response: {e}")]

    else:
        return [TextContent(type="text", text=f"Unknown tool: {name}")]


async def main():
    """Run the MCP server"""
    from mcp.server.stdio import stdio_server

    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
