#!/usr/bin/env python3

"""
Process Monitor MCP server for Claude Code
Monitors a process until completion with smart timeout handling to avoid 2hr system limit
Enhanced with Pushover notifications and W&B metrics reporting
"""

import json
import sys
import os
import time
import signal
import subprocess
import base64
import socket
import requests
from datetime import datetime
from collections import deque

SYSTEM_TIMEOUT_WARNING = """
IMPORTANT: This monitor will timeout after 1hr 55min due to Claude Code's 2-hour 
foreground process limit. This timeout does NOT mean your background process has 
finished - it only means the monitor needs to restart to avoid system termination.
"""

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

def process_exists(pid):
    """Check if process exists without killing it"""
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True  # Process exists but we can't access it
    except ValueError:
        return False  # Invalid PID

def get_process_info(pid):
    """Get basic process information"""
    try:
        # Try to read from /proc if available (Linux)
        proc_path = f"/proc/{pid}"
        if os.path.exists(proc_path):
            # Read command line
            try:
                with open(f"{proc_path}/cmdline", 'r') as f:
                    cmdline = f.read().replace('\x00', ' ').strip()
            except:
                cmdline = "unknown"
            
            # Read working directory
            try:
                cwd = os.readlink(f"{proc_path}/cwd")
            except:
                cwd = "unknown"
            
            return {
                "command": cmdline,
                "cwd": cwd
            }
    except:
        pass
    
    return {
        "command": "unknown",
        "cwd": "unknown"
    }

def handle_initialize(params):
    """Handle initialize request"""
    return {
        "protocolVersion": "2024-11-05",
        "capabilities": {
            "tools": {}
        },
        "serverInfo": {
            "name": "process-monitor",
            "version": "1.0.0"
        }
    }

def handle_tools_list():
    """Handle tools/list request"""
    return {
        "tools": [
            {
                "name": "monitor_process",
                "description": "Monitor a process until completion or timeout. Returns when process exits or monitor times out (1hr 55min). Can send email crash reports.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "pid": {
                            "type": "integer",
                            "description": "Process ID to monitor"
                        },
                        "log_path": {
                            "type": "string",
                            "description": "Path to the log file for this process (for crash reporting)"
                        },
                        "timeout": {
                            "type": "integer",
                            "description": "Maximum monitoring time in seconds (default: 6900 = 1hr 55min)",
                            "default": 6900
                        },
                        "poll_interval": {
                            "type": "number",
                            "description": "How often to check process status in seconds (default: 5)",
                            "default": 5.0
                        }
                    },
                    "required": ["pid"]
                }
            },
            {
                "name": "check_process",
                "description": "Check if a process is currently running (non-blocking)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "pid": {
                            "type": "integer",
                            "description": "Process ID to check"
                        }
                    },
                    "required": ["pid"]
                }
            },
            {
                "name": "find_recent_processes",
                "description": "Find recent processes that might be candidates for monitoring",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "pattern": {
                            "type": "string",
                            "description": "Optional pattern to filter process names",
                            "default": ""
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of processes to return",
                            "default": 10
                        }
                    }
                }
            }
        ]
    }

def handle_tools_call(name, arguments):
    """Handle tools/call request"""
    if name == "monitor_process":
        return monitor_process(arguments)
    elif name == "check_process":
        return check_process(arguments)
    elif name == "find_recent_processes":
        return find_recent_processes(arguments)
    else:
        raise ValueError(f"Unknown tool: {name}")

def send_crash_email(pid, log_path, log_content):
    """Send crash report email directly"""
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        import socket
        
        # Email configuration (from environment)
        smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        sender_email = os.getenv("SMTP_EMAIL")
        sender_password = os.getenv("SMTP_PASSWORD")
        recipient_email = os.getenv("CRASH_REPORT_EMAIL", sender_email)

        if not sender_email or not sender_password:
            logging.error("SMTP credentials not configured (SMTP_EMAIL, SMTP_PASSWORD)")
            return
        
        # Create email
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        msg['Subject'] = f"Training Process Crashed - PID {pid}"
        msg['X-Priority'] = '1'
        msg['Priority'] = 'urgent'
        msg['Importance'] = 'high'
        
        # Email body
        body = f"""## Training Process Termination Report

**Process ID:** {pid}
**Log File:** {log_path}
**Hostname:** {socket.gethostname()}
**Detected:** {datetime.now().isoformat()}

## Last 2000 Lines of Training Log

```
{log_content}
```

## Summary
The training process has terminated unexpectedly. Please review the log above for error details.

---
*This is an automated crash report from the process monitor.*"""
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Send email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
        
        # Silent - email sent
        return True
    except Exception as e:
        # Silent - failed but don't flood output
        return False

def get_log_tail(log_path, lines=500):
    """Get the last N lines from a log file"""
    try:
        if not os.path.exists(log_path):
            return f"Log file not found: {log_path}"
        
        with open(log_path, 'r') as f:
            # Read all lines for small files, or use deque for large files
            return ''.join(deque(f, maxlen=lines))
    except Exception as e:
        return f"Error reading log file: {e}"

def get_wandb_metrics_and_url(pid):
    """Get current W&B metrics and run URL for the training process"""
    try:
        # Try to get the W&B run ID from the latest run tracking
        cmd = ["python3", "/home/ubuntu/finetune_safe/wandb_tools/get_latest_run.py", "--info-only"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            output = result.stdout
            # Parse the run URL from output
            for line in output.split('\n'):
                if "Run URL:" in line:
                    run_url = line.split("Run URL:")[-1].strip()
                    return run_url, output
        
        return None, None
    except Exception as e:
        # Silent - error but don't flood output
        return None, None

def generate_training_plots(output_dir="/tmp"):
    """Generate training plots using plot_panels.R"""
    try:
        # First download the W&B bundle for current run
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        bundle_dir = f"{output_dir}/wandb_bundle_{timestamp}"
        
        # Download bundle using wandb_tools
        cmd = [
            "python3", "/home/ubuntu/finetune_safe/wandb_tools/download_run_bundle.py",
            "--output", bundle_dir
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0:
            # Silent - failed but don't flood output
            return []
        
        # Generate plots with R script
        plot_base = f"{output_dir}/training_plots_{timestamp}"
        cmd = [
            "Rscript", "/home/ubuntu/finetune_safe/wandb_tools/plot_panels.R",
            "--bundle", bundle_dir,
            "--out", f"{plot_base}.png"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0:
            # Silent - failed but don't flood output
            return []
        
        # Find generated plot files
        plot_files = []
        for i in range(1, 6):
            plot_file = f"{plot_base}_{i}.png"
            if os.path.exists(plot_file):
                plot_files.append(plot_file)
        
        return plot_files
    except Exception as e:
        # Silent - error but don't flood output
        return []

def send_pushover_with_attachment(title, message, attachment_path=None, priority=0):
    """Send Pushover notification with optional image attachment"""
    try:
        # Pushover credentials (from environment)
        app_token = os.getenv("PUSHOVER_APP_TOKEN")
        user_key = os.getenv("PUSHOVER_USER_KEY")

        if not app_token or not user_key:
            logging.error("Pushover credentials not configured")
            return
        
        # Prepare the request
        url = "https://api.pushover.net/1/messages.json"
        data = {
            "token": app_token,
            "user": user_key,
            "title": title,
            "message": message,
            "priority": priority,
            "html": "1"
        }
        
        # Add attachment if provided and exists
        files = None
        if attachment_path and os.path.exists(attachment_path):
            # Check file size (5MB limit)
            file_size = os.path.getsize(attachment_path)
            if file_size < 5242880:  # 5MB in bytes
                files = {
                    "attachment": (
                        os.path.basename(attachment_path),
                        open(attachment_path, 'rb'),
                        'image/png'
                    )
                }
            else:
                print(f"Attachment too large ({file_size/1048576:.1f}MB), skipping", file=sys.stderr)
        
        # Send request
        if files:
            response = requests.post(url, data=data, files=files, timeout=30)
            files['attachment'][1].close()  # Close the file handle
        else:
            response = requests.post(url, data=data, timeout=30)
        
        if response.status_code == 200 and response.json().get('status') == 1:
            # Silent - notification sent successfully
            return True
        else:
            # Silent - failed but don't flood output
            return False
            
    except Exception as e:
        # Silent - error but don't flood output
        return False

def format_metrics_for_pushover(metrics_output):
    """Format W&B metrics output for Pushover HTML"""
    if not metrics_output:
        return "No metrics available"
    
    # Convert plain text metrics to HTML with basic formatting
    html_lines = []
    for line in metrics_output.split('\n'):
        if line.strip():
            # Bold headers
            if any(x in line for x in ['Run:', 'Status:', 'Duration:', 'Step:']):
                line = f"<b>{line}</b>"
            # Format URLs as links
            elif 'http' in line:
                parts = line.split('http')
                if len(parts) > 1:
                    url = 'http' + parts[1].split()[0]
                    line = parts[0] + f'<a href="{url}">View in W&B</a>'
            html_lines.append(line + "<br>")
    
    return ''.join(html_lines)

def monitor_process(arguments):
    """Monitor a process until completion or timeout"""
    pid = arguments.get("pid")
    if not isinstance(pid, int) or pid <= 0:
        raise ValueError("Invalid PID")
    
    log_path = arguments.get("log_path", None)
    timeout = arguments.get("timeout", 6900)  # 1hr 55min default
    poll_interval = arguments.get("poll_interval", 5.0)
    
    start_time = time.time()
    process_info = get_process_info(pid)
    
    # Check if process exists at start
    if not process_exists(pid):
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Process {pid} not found or already exited"
                }
            ]
        }
    
    # SILENT - DO NOT output anything during monitoring to avoid flooding context
    
    # Send initial Pushover notification with W&B URL
    wandb_url, metrics_output = get_wandb_metrics_and_url(pid)
    initial_msg = f"<b>Training Started</b><br><br>"
    initial_msg += f"<b>PID:</b> {pid}<br>"
    initial_msg += f"<b>Hostname:</b> {socket.gethostname()}<br>"
    if log_path:
        initial_msg += f"<b>Log:</b> {log_path}<br>"
    if wandb_url:
        initial_msg += f'<br><b>W&B:</b> <a href="{wandb_url}">View Run</a><br>'
    
    send_pushover_with_attachment(
        title=f"Training Started - PID {pid}",
        message=initial_msg,
        priority=0
    )
    
    # Track when to send next notification (1 hour intervals)
    next_notification_time = start_time + 3600  # 1 hour
    notification_count = 0
    
    # Silent monitoring loop
    while True:
        elapsed_time = time.time() - start_time
        
        # Check if it's time for periodic notification (every hour)
        if elapsed_time >= next_notification_time - start_time:
            notification_count += 1
            hours_elapsed = int(elapsed_time / 3600)
            
            # Get W&B metrics
            wandb_url, metrics_output = get_wandb_metrics_and_url(pid)
            
            # Generate plots (only after 1hr when there's data)
            plot_files = []
            if notification_count > 0:
                plot_files = generate_training_plots()
            
            # Format message
            msg = f"<b>Training Progress Update</b><br><br>"
            msg += f"<b>Duration:</b> {hours_elapsed} hour{'s' if hours_elapsed != 1 else ''}<br>"
            msg += f"<b>PID:</b> {pid}<br>"
            msg += f"<b>Status:</b> Running <br>"
            if wandb_url:
                msg += f'<br><b>W&B:</b> <a href="{wandb_url}">View Metrics</a><br>'
            
            # Add metrics summary if available
            if metrics_output:
                # Extract key metrics from output
                for line in metrics_output.split('\n'):
                    if 'Step:' in line or 'Loss:' in line or 'Reward:' in line:
                        msg += f"<b>{line.strip()}</b><br>"
            
            # Send with first plot as attachment if available
            attachment = plot_files[0] if plot_files else None
            send_pushover_with_attachment(
                title=f"Training Update - {hours_elapsed}hr",
                message=msg,
                attachment_path=attachment,
                priority=0
            )
            
            # Update next notification time
            next_notification_time += 3600  # Next hour
        
        # Check if process is still running
        if not process_exists(pid):
            # Process finished/crashed!
            duration = int(time.time() - start_time)
            
            # Get log tail and send crash report if log path provided
            log_tail_500 = ""
            log_tail_2000 = ""
            if log_path:
                log_tail_500 = get_log_tail(log_path, 500)
                log_tail_2000 = get_log_tail(log_path, 2000)
                
                # Send email with 2000 lines
                send_crash_email(pid, log_path, log_tail_2000)
            
            # Return with clear agent instructions
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"""
{'='*80}
TRAINING PROCESS NO LONGER RUNNING
{'='*80}
PID: {pid}
LOG FILE: {log_path if log_path else 'Not specified'}
STATUS: CRASHED/TERMINATED
DURATION: {duration} seconds
EXIT TIME: {datetime.now().isoformat()}
{'='*80}

AGENT INSTRUCTIONS:
1. Training has CRASHED - this is NOT normal completion
2. Email with last 2000 log lines has been sent to human
3. You MUST now use report MCP to explain the crash
4. Analyze the log below to determine the cause
5. After reporting, fix the issue and restart with /train

{'='*80}
LAST 500 LINES OF LOG:
{'='*80}

{log_tail_500 if log_tail_500 else 'No log available'}

{'='*80}
REQUIRED ACTIONS:
1. Send report via mcp__report__send_report explaining the crash
2. Analyze error and implement fix
3. Restart training with /train command
{'='*80}
"""
                    }
                ]
            }
        
        if time.time() - start_time >= timeout:
            # Monitor timeout (NOT process timeout)
            hours_elapsed = int(timeout / 3600)
            
            # Send final notification before monitor restart
            wandb_url, metrics_output = get_wandb_metrics_and_url(pid)
            
            # Generate final plots
            plot_files = generate_training_plots()
            
            msg = f"<b>Monitor Restarting (2hr limit)</b><br><br>"
            msg += f"<b>Duration:</b> {hours_elapsed} hour{'s' if hours_elapsed != 1 else ''}<br>"
            msg += f"<b>PID:</b> {pid}<br>"
            msg += f"<b>Status:</b> Still Running <br>"
            msg += f"<b>Note:</b> Monitor will restart to avoid system timeout<br>"
            if wandb_url:
                msg += f'<br><b>W&B:</b> <a href="{wandb_url}">View Metrics</a><br>'
            
            attachment = plot_files[0] if plot_files else None
            send_pushover_with_attachment(
                title=f"Monitor Restarting - {hours_elapsed}hr",
                message=msg,
                attachment_path=attachment,
                priority=0
            )
            
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps({
                            "pid": pid,
                            "log_path": log_path,
                            "status": "monitor_timeout",
                            "duration_seconds": int(timeout),
                            "process_still_running": process_exists(pid),
                            "reason": "monitor_reached_time_limit",
                            "message": SYSTEM_TIMEOUT_WARNING.strip(),
                            "process_info": process_info
                        }, indent=2)
                    }
                ]
            }
        
        # Continuous monitoring with minimal sleep (0.5 sec default for responsiveness)
        # Use smaller interval for faster detection
        actual_interval = min(poll_interval, 0.5)
        time.sleep(actual_interval)

def check_process(arguments):
    """Check if a process is running"""
    pid = arguments.get("pid")
    if not isinstance(pid, int) or pid <= 0:
        raise ValueError("Invalid PID")
    
    exists = process_exists(pid)
    process_info = get_process_info(pid) if exists else None
    
    return {
        "content": [
            {
                "type": "text",
                "text": json.dumps({
                    "pid": pid,
                    "running": exists,
                    "checked_at": datetime.now().isoformat(),
                    "process_info": process_info
                }, indent=2)
            }
        ]
    }

def find_recent_processes(arguments):
    """Find recent processes that might be candidates for monitoring"""
    pattern = arguments.get("pattern", "")
    limit = arguments.get("limit", 10)
    
    processes = []
    
    try:
        # Try to find processes using ps command
        import subprocess
        result = subprocess.run(['ps', 'ax', '-o', 'pid,etime,comm,args'], 
                              capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')[1:]  # Skip header
            for line in lines[:limit * 2]:  # Get more than needed to filter
                parts = line.strip().split(None, 3)
                if len(parts) >= 4:
                    try:
                        pid = int(parts[0])
                        etime = parts[1]
                        comm = parts[2]
                        args = parts[3] if len(parts) > 3 else comm
                        
                        # Filter by pattern if provided
                        if not pattern or pattern.lower() in args.lower() or pattern.lower() in comm.lower():
                            processes.append({
                                "pid": pid,
                                "elapsed_time": etime,
                                "command": comm,
                                "full_command": args
                            })
                            
                            if len(processes) >= limit:
                                break
                    except ValueError:
                        continue
                        
    except Exception as e:
        # Fallback: try to read /proc directly
        try:
            for pid_dir in sorted(os.listdir("/proc"), key=lambda x: x if x.isdigit() else "0")[:limit]:
                if pid_dir.isdigit():
                    try:
                        pid = int(pid_dir)
                        proc_path = f"/proc/{pid}"
                        
                        with open(f"{proc_path}/cmdline", 'r') as f:
                            cmdline = f.read().replace('\x00', ' ').strip()
                        
                        if not pattern or pattern.lower() in cmdline.lower():
                            processes.append({
                                "pid": pid,
                                "command": cmdline[:50] + "..." if len(cmdline) > 50 else cmdline,
                                "full_command": cmdline
                            })
                            
                    except:
                        continue
        except:
            pass
    
    return {
        "content": [
            {
                "type": "text",
                "text": json.dumps({
                    "found_processes": processes,
                    "pattern_used": pattern,
                    "timestamp": datetime.now().isoformat()
                }, indent=2)
            }
        ]
    }

def main():
    """Main MCP server loop"""
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