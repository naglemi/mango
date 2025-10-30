# Report MCP Server

A lightweight MCP server for managing frequent text and image reports through S3 and email notifications.

##  For Michael Nagle / Primary User

**You already have S3 and SES configured!** When setting up on a new machine:

1. **Use existing S3 bucket**: `mango-reports`
2. **Use verified email**: `slurmalerts1017@gmail.com` (already verified in SES)
3. **AWS credentials**: Already in your `~/.bashrc` or `~/.zshrc`

Just run:
```bash
./setup-report-mcp.sh
# When prompted:
# S3 Bucket: mango-reports
# Region: us-east-1  
# From email: slurmalerts1017@gmail.com
# To email: slurmalerts1017@gmail.com
```

**No need to create new buckets or verify emails - everything is already set up!**

## Overview

This MCP server provides a simple solution for agents to send reports with:
- Text content delivered immediately via email
- **First 5 images embedded directly in email** (up to 10MB total)
- Full report content displayed in email body
- Large files/images uploaded to S3 with pre-signed URLs
- Organized storage for easy retrieval
- No heavy dependencies or complex systems

### Smart Email Embedding
- First 5 images (PNG, JPG, JPEG, GIF, WebP) are embedded inline
- Up to 10MB total embedded size for fast email loading
- Full report content shown directly in email
- Additional files available via S3 links
- No clicking required for most reports!

## Architecture

```
Agent → MCP Server → S3 (files) + SES (email) → User Inbox
```

1. Agent calls `send_report` with text and file paths
2. MCP server uploads files to S3 bucket
3. Generates pre-signed URLs (7-day expiration by default)
4. Sends email with text content and links to files
5. User receives lightweight email with immediate visibility

## Configuration

Environment variables:
- `REPORT_BUCKET` - S3 bucket name
- `AWS_REGION` - AWS region
- `REPORT_EMAIL_FROM` - Sender email (must be verified in SES)
- `REPORT_EMAIL_TO` - Recipient email
- `REPORT_URL_EXPIRATION` - URL expiration in seconds (default: 604800 = 7 days)

## Tools

### send_report
Send a report with text and optional file attachments.

Parameters:
- `agent_name` (required) - Name of the reporting agent
- `title` (required) - Report title
- `text_content` (required) - Main text content
- `files` (optional) - Array of file paths to attach

Example:
```
"Send a report from agent hayato titled 'Training Complete' with content 'Model converged at epoch 50' and attach ./loss_chart.png"
```

### list_reports
List recent reports from S3.

Parameters:
- `agent_name` (optional) - Filter by agent
- `max_results` (optional) - Maximum results (default: 20)

## S3 Organization

Reports are organized as:
```
bucket/
  agent_name/
    YYYY-MM-DD_HH-MM-SS/
      file1.png
      file2.csv
      ...
```

## Email Format

Subject: `[Agent Name] Title - Timestamp`

Body includes:
- Full report text content (no need to click through!)
- First 5 images embedded inline (up to 10MB total)
- Thumbnails with "View full size" links
- List of all attachments with direct S3 links
- "View Full Report in Browser" button for complete experience

### Embedded vs Linked
- **Embedded**: First 5 images under 10MB total - shown directly in email
- **Linked**: Additional images, large files, non-image attachments - via S3 URLs

## Setup Requirements

### For New Users (Not Michael Nagle)

1. **S3 Bucket**: Create bucket with appropriate permissions
2. **AWS SES**: Verify sender email address
3. **AWS Credentials**: Configure via AWS CLI or IAM role
4. **Node.js**: Required to run the MCP server

### For Michael Nagle (Existing Infrastructure)

1. **S3 Bucket**:  Already exists - `mango-reports`
2. **AWS SES**:  Already verified - `slurmalerts1017@gmail.com`
3. **AWS Credentials**:  Already in your shell config
4. **Node.js**: Just need to install if not present

## Security

- Pre-signed URLs expire after configured time
- S3 bucket can be private (URLs provide temporary access)
- Email content is sent via AWS SES (encrypted in transit)

## Usage with AI Assistants

Once configured, AI assistants can send reports naturally:

"Send a report about the test results including the graphs from ./output/"

The AI will use the MCP tools to upload files and send the notification automatically.