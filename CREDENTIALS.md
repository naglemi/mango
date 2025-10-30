# AWS Credentials Management

This project uses **multiple AWS credential sets** for different purposes. It's critical to never mix them up.

## Credential Sets

### 1. General AWS Operations (CLAUDE.md credentials)
**Location**: `~/CLAUDE.md`
**Environment Variables**:
- `AWS_ACCESS_KEY_ID="<your-general-aws-key>"`
- `AWS_SECRET_ACCESS_KEY="<your-general-aws-secret>"`
- `AWS_DEFAULT_REGION="us-east-2"`

**Account**: Your primary AWS account
**IAM Role**: EC2-Full-Power-User or equivalent
**Purpose**: General EC2 operations, AWS Bedrock API access, EC2 instance management
**Used By**: DeepSeek workflows, general AWS CLI operations, agent instructions

**IMPORTANT**: These credentials are for DEVELOPMENT/INTERNAL use only. They are stored in CLAUDE.md for agent reference and should NEVER be committed to the public repository.

### 2. Report MCP S3/SES Credentials
**Location**: `~/.bashrc` (set during setup)
**Environment Variables**:
- `REPORT_AWS_ACCESS_KEY_ID` (user-provided during setup)
- `REPORT_AWS_SECRET_ACCESS_KEY` (user-provided during setup)

**Purpose**: S3 uploads to `mango-reports` bucket and SES email delivery
**Used By**: Report MCP (EMAIL mode only)
**Account**: Different from CLAUDE.md credentials

**IMPORTANT**:
- These credentials are ONLY needed for EMAIL mode (cloud reports)
- LOCAL mode (filesystem reports) does NOT require AWS credentials
- Users provide these credentials during `setup-workflows.sh` if they choose EMAIL mode
- Never hardcode these in the repository

## Mode-Based Credential Requirements

### Report MCP - EMAIL Mode
- **Requires**: `REPORT_AWS_ACCESS_KEY_ID` and `REPORT_AWS_SECRET_ACCESS_KEY`
- **Purpose**: Upload reports to S3, send emails via SES
- **Setup**: User provides during `setup-workflows.sh --developer` or normal setup

### Report MCP - LOCAL Mode
- **Requires**: `USABILIDE_REPORT_FOLDER` set to a directory path
- **No AWS credentials needed**
- **Purpose**: Save reports to local filesystem only

## Repository Safety

### Files That Should NEVER Be Committed
1. `~/CLAUDE.md` - Contains development credentials
2. `~/.bashrc` - May contain user-specific credentials
3. `.env` files - May contain secrets
4. `credentials.json` - AWS/GCP/Azure credential files

### Files Safe to Commit
1. `CREDENTIALS.md` (this file) - Documentation only, no actual secrets
2. `mcp/report/index.js` - Now uses environment variables, no hardcoded credentials
3. `workflows/check-envars.py` - Prompts for credentials, doesn't contain them

## Setup Process

### For Developers (--developer mode)
The developer setup automatically uses the CLAUDE.md credentials for general AWS operations and provides the Report MCP credentials from your ~/.bashrc configuration.

**Developer ~/.bashrc should contain**:
```bash
# General AWS (CLAUDE.md)
export AWS_ACCESS_KEY_ID="<your-general-aws-key>"
export AWS_SECRET_ACCESS_KEY="<your-general-aws-secret>"
export AWS_DEFAULT_REGION="us-east-2"

# Report MCP (EMAIL mode)
export REPORT_AWS_ACCESS_KEY_ID="<your-report-mcp-key>"
export REPORT_AWS_SECRET_ACCESS_KEY="<your-report-mcp-secret>"
export REPORT_EMAIL_FROM="<your-email>"
export REPORT_EMAIL_TO="<your-email>"
```

### For Public Users
Public users will be prompted during setup:
1. **Report MCP Mode Selection**:
   - LOCAL mode: No AWS credentials needed
   - EMAIL mode: User provides their own AWS credentials for S3/SES

2. **Credential Prompts** (EMAIL mode only):
   - `REPORT_AWS_ACCESS_KEY_ID`
   - `REPORT_AWS_SECRET_ACCESS_KEY`
   - `REPORT_EMAIL_FROM`
   - `REPORT_EMAIL_TO`

These are added to their ~/.bashrc during setup.

## Never Mix Credentials

**WRONG**:
```bash
# DON'T DO THIS - using general AWS creds for Report MCP
export REPORT_AWS_ACCESS_KEY_ID="<same-as-AWS_ACCESS_KEY_ID>"  # ❌ WRONG - must be different
```

**CORRECT**:
```bash
# General AWS operations use CLAUDE.md credentials
export AWS_ACCESS_KEY_ID="<your-general-aws-key>"
export AWS_SECRET_ACCESS_KEY="<your-general-aws-secret>"

# Report MCP uses separate dedicated credentials
export REPORT_AWS_ACCESS_KEY_ID="<different-key-for-reports>"
export REPORT_AWS_SECRET_ACCESS_KEY="<different-secret-for-reports>"
```

## Troubleshooting

### "Report MCP S3 bucket endpoint error"
**Cause**: Wrong AWS credentials being used (likely CLAUDE.md credentials instead of Report MCP credentials)

**Fix**:
1. Check `~/.bashrc` for `REPORT_AWS_ACCESS_KEY_ID` and `REPORT_AWS_SECRET_ACCESS_KEY`
2. Ensure they are NOT the same as `AWS_ACCESS_KEY_ID` from CLAUDE.md
3. Remove any exports of general AWS credentials that might override Report MCP credentials
4. Restart Claude sessions to pick up correct environment variables

### "Missing Report MCP credentials"
**Cause**: Report MCP is in EMAIL mode but credentials not set

**Fix**:
1. Either set `USABILIDE_REPORT_FOLDER=/path/to/reports` for LOCAL mode (no AWS needed)
2. Or add Report MCP credentials to ~/.bashrc for EMAIL mode

## Security Best Practices

1. **Never commit credentials to git**
2. **Use environment variables, not hardcoded values**
3. **Keep different credential sets separated**
4. **Document which credentials are for what purpose**
5. **Rotate credentials regularly**
6. **Use least-privilege IAM policies**
7. **For public repositories, prompt users to provide their own credentials**
