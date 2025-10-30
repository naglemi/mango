# report

Produce and deliver a **comprehensive progress report** to the project stakeholders using the S3 Report MCP.

This workflow compiles the latest scientific progress – notebook entries, insights, figures, and next-steps – and emails / uploads it through the `report-s3` MCP server.

---
**Purpose**

1. Capture the current state of research without manual formatting.
2. Persist reports in S3 (via MCP) and automatically link them back into the living notebook (`SCIENTIST.md`).
3. Provide rich emails (Markdown + LaTeX) with embedded images and attachments for easy review.

---
## Steps

1. **Collect notebook content**  
   Read the entire `SCIENTIST.md` (and `ADVISOR.md` if present). This becomes the core `text_content` of the report.

2. **Gather figures & supplementary files**  
   Recursively search common output directories (e.g. `figures/`, `plots/`, `results/`) for up-to-date image or data files created within the last 24 h.  
   • Supported image extensions: `.png`, `.jpg`, `.jpeg`, `.gif`, `.webp`  
   • Include small CSV / TSV result tables if they exist.

3. **Prepare metadata**  
   - `agent_name`: your Cascade agent or lab identifier (e.g. `scientist`)  
   - `title`: a concise human-readable title for the report (e.g. *“Week-27 Results & Analysis”*).

4. **Send the report via MCP**  
   Use the `report-s3` MCP tool `send_report` with:
   ```json
   {
     "agent_name": "scientist",
     "title": "<YOUR TITLE>",
     "text_content": "<CONCATENATED NOTEBOOK MARKDOWN>",
     "files": [
       "figures/*.png",
       "results/latest_metrics.csv"
     ]
   }
   ```
   Notes:
   - Provide **either** `text_content` **or** `report_file`, not both. We use `text_content` here.  
   - All `files` are uploaded to S3; up to five smallest images (≤ 8 MB total) are also attached to the email automatically.

5. **Confirmation & notebook update**  
   Upon success the MCP replies with the 4-character **report tag** and signed URL. Thanks to previous server enhancement, the tag & title are appended to `SCIENTIST.md` automatically.

6. **Usage**  
   Invoke this workflow at any time with the slash command `/report`.

---
### Example quick-run snippet
```cascade
/workflows report.send_report {
  "agent_name": "scientist",
  "title": "Sprint-12 Progress Report",
  "text_content": read_file("SCIENTIST.md") + "\n\n---\n\n" + (file_exists("ADVISOR.md") ? read_file("ADVISOR.md") : ""),
  "files": glob_last24h(["figures/**/*.{png,jpg,jpeg,gif,webp}", "results/**/*.csv"])
}
```

> The helper functions `read_file`, `file_exists`, and `glob_last24h` are pseudo-functions understood by Cascade workflows.

---
### Notes
- Reports are stored under `s3://<REPORT_BUCKET>/<agent>/<date_time>/` with an HTML index and metadata.
- The report email contains a rich HTML body, embedded MathJax, all images via pre-signed URLs, and small attachments for convenience.
- Stakeholders can reply directly to the email; responses remain outside the workflow.
