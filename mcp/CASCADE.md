# MCP Integration Guide for Windsurf Cascade

> **Status:** Working  (tested 2025-07-07)
> 
> This document explains **how to enable the existing Pushover and Report Model Context Protocol (MCP) servers inside the Windsurf Cascade IDE/agent runtime**. The same servers already run under Claude Code; only the registration method is different.

---

## 1. Prerequisites

1. **Node ≥ 18** (needed by both MCP servers).  Install via `nvm` or your package-manager.
2. **AWS CLI + credentials** – required only for the Report MCP (S3 + SES).
3. **Pushover account & app** (one-time $5) for push notifications.
4. **`npm` global packages**
   ```bash
   # One-time installs
   npm install -g pushover-mcp           # Pushover server wrapper
   npm install -g @modelcontextprotocol/cli  # Provides the `cascade mcp` command
   ```
5. Environment variables (add to `~/.bashrc` or `~/.zshrc`):
   ```bash
   # Pushover (get tokens from https://pushover.net/)
   export PUSHOVER_APP_TOKEN="your-app-token-here"
   export PUSHOVER_USER_KEY="your-user-key-here"

   # AWS (Report MCP - use your IAM credentials)
   export AWS_ACCESS_KEY_ID="your-access-key-id"
   export AWS_SECRET_ACCESS_KEY="your-secret-access-key"
   export AWS_DEFAULT_REGION="us-east-1"   # or your region of choice
   ```
   *Reload your shell afterwards:* `source ~/.bashrc`

---

## 2. Install Local Dependencies

```bash
# Inside the project root
cd mcp/report
npm ci --silent      # installs server deps defined in package.json
```

Pushover has no local deps – the global `pushover-mcp` package you installed earlier is enough.

---

## 3. Register the MCP servers with Cascade

Cascade reads a single JSON file: `~/.codeium/windsurf/mcp_config.json`.  Add your servers there (user-scope).  The helper script we provide writes this file for you.

Cascade uses the **same MCP JSON schema** as Claude but exposes it through the `cascade mcp` CLI instead of `claude mcp`.  The commands below create two servers named `pushover-notify` and `report-s3` in the **user scope** so they are available to every project launched by Cascade.

Create (or update) `~/.codeium/windsurf/mcp_config.json` with:
```json
{
  "mcpServers": {
    "pushover-notify": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "pushover-mcp", "start", "--token", "$PUSHOVER_APP_TOKEN", "--user", "$PUSHOVER_USER_KEY"]
    },
    "report-s3": {
      "type": "stdio",
      "command": "node",
      "args": ["/absolute/path/to/your/project/mcp/report/index.js"],
      "env": {
        "REPORT_BUCKET": "usability-reports",
        "AWS_REGION": "us-east-1",
        "REPORT_EMAIL_FROM": "slurmalerts1017@gmail.com",
        "REPORT_EMAIL_TO": "slurmalerts1017@gmail.com",
        "REPORT_URL_EXPIRATION": "604800"
      }
    }
  }
}
```
After saving, restart Cascade and press the **Refresh** button in the Plugins pane.

> **Why the `-s user` scope?**  Cascade runs each workspace in a sandbox.  The *user* scope ensures the server is started **once per developer login**, not once per project, conserving memory and ports.

---

## 4. Verify & Activate

1. Restart Windsurf Cascade completely (⌘ Q → relaunch, or exit/re-open the `cascade` CLI).
2. Run `cascade mcp list`.  You should see lines similar to:
   ```
    pushover-notify   stdio  running   mcp2_pushover-notify__send_notification
    report-s3         stdio  running   mcp3_report-s3__send_report  mcp3_report-s3__list_reports
   ```
3. Inside any Cascade chat, type `/mcp` and confirm that the new tool functions (e.g. `send_notification`, `send_report`) appear.

---

## 5. Quick Usage Examples

### Notification at the end of a long task
```text
AI: "Notify me with sound *success* that the 12-hour training just finished."
```

### Send a report with plots & logs
```text
AI: "Send a report called *Model Performance* with `loss.png`, `accuracy.png`, and `training.log`"
```

Cascade will transparently call the appropriate MCP tools.

---

## 6. Troubleshooting

| Symptom | Fix |
|---------|------|
| `send_notification` / `send_report` tool not listed | Run the registration commands again and **restart Cascade**. |
| Notification not delivered | Check `PUSHOVER_*` env vars, ensure your device is online. |
| `AccessDenied` when uploading to S3 | Verify bucket policy or use an IAM user with `s3:PutObject` & `s3:GetObject` permissions. |
| SES email not sent | The `REPORT_EMAIL_FROM` address must be *verified* in the same AWS region. |

---

## 7. Automating Everything

Run `mcp/setup-cascade-mcp.sh` to install dependencies **and** write the `mcp_config.json` for you.  Then restart Cascade and click Refresh.

For convenience you can create a single-click script similar to `setup-claude-mcp.sh`:

```bash
# mcp/setup-cascade-mcp.sh (make executable with chmod +x)
#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# install deps
cd "$SCRIPT_DIR/report" && npm ci --silent && cd "$SCRIPT_DIR/.."
command -v pushover-mcp >/dev/null || npm install -g pushover-mcp

# register servers (uses the same JSON as above)
$(dirname "$0")/../mcp/CASCADE-register.sh   # or inline the add-json commands
```

Run it once and then restart Cascade.

---

## 8. Security Notes

* Keep Pushover tokens **private** – they allow anyone to send you unlimited push messages.
* Limit the IAM user used by the Report MCP to **only** the S3 bucket & SES actions it needs.
* Pre-signed report URLs expire after 7 days by default (configurable via `REPORT_URL_EXPIRATION`).

---

## 9. References

* Model Context Protocol spec — <https://modelcontextprotocol.org>
* Pushover API — <https://pushover.net/api>
* AWS SDK for JavaScript v3 — <https://docs.aws.amazon.com/sdk-for-javascript>
* Windsurf Cascade docs (internal) — *See Notion → Engineering → Cascade → MCP Integration*

---

### Enjoy using MCPs natively in Windsurf Cascade! 
