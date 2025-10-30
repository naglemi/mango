# Mango 🥭

**M**anagement of **A**gents with **N**otebooks and **G**it **O**versight

A rigorous system for managing AI agents with git-based workflows and reproducible research. MANGO enforces replicability standards through programmatic hooks that prevent pushing Jupyter notebooks unless they meet quality criteria. Git commits are mandatory before code execution, notebooks must execute cleanly, and all outputs are version-controlled. Programmatic hooks validate notebook reproducibility, ensuring computational work meets publication standards.

## Quick Start

```bash
git clone https://github.com/naglemi/mango.git
cd mango

# Install three key modules one-by-one and select all features you desire:
./setup-hooks.sh
./setup-tmux.sh
./setup-workflows.sh

# Launch the Mango menu anytime:
mango
```

## Key Feature Overview

### Blog Workflow
![Blog from Jupyter Notebooks](assets/feature-blog.png)
Vercel blog posts from Jupyter Notebooks with JupyterHub replication online

### Multi-Agent Discussion
![Discuss Workflow](assets/feature-discuss.png)
Communication across Claude sessions via GitHub Issues - enables persistent multi-agent collaboration

### Desktop IDE Integration
![Desktop Preset](assets/feature-desktop.png)
Desktop preset familiar to users of VS Code, RStudio, and other common IDEs

### Mobile-Optimized Tools
![Mobile Tools](assets/feature-mobile.png)
Thumb-friendly tmux/tool navigator, Email and Pushover notification MCPs, and quick agent rule editing on-the-go

## Core Features

### 1. Multi-Agent Collaboration (`/discuss`)
**The killer feature.** Multiple agents collaborate asynchronously via GitHub issue threads:
- Persistent communication across agent sessions
- Agents discuss, debate, and reach consensus on complex problems
- Full conversation history in GitHub issues
- Each agent can read others' responses and build on them
- Use: `/discuss "How should we architect the caching layer?"`

### 2. Research Blogging (`/blog`)
Jupyter notebook-based research workflow with executable truth:
- Write blog posts as notebooks with live code and data
- All claims backed by executed code (no hallucinated results)
- W&B API integration for experiment data provenance
- Automatic conversion to markdown with images
- Vercel deployment for global distribution

### 3. Agent Communication (`/report` MCP)
Structured reports for agent handoffs, human-in-the-loop, and long-running tasks:
- S3-backed reports with markdown + LaTeX math + images
- Email notifications with report summaries
- Organized archive by agent/date/tag
- Supports large files and datasets

### 4. IDE-Like Environment (Presets)
The `mango` launcher provides preset workspaces for rigorous development:
- **Mobile Preset**: nvim + Claude Code + lazygit (3 windows)
- **Desktop Preset**: nvim + Claude Code (2 windows)
- **Battlestation Preset**: nvim + Claude + lazygit + hooks manager (4 panes)

Each preset gives you an IDE-like environment with:
- **nvim**: Code editing with full vim power
- **Claude Code**: AI agent in dedicated pane
- **lazygit**: Git operations with visual interface (crucial for agent oversight)
- **hooks manager**: Real-time control over agent permissions

### 5. Agent Safety Hooks
Critical hooks for preventing agent mistakes:
- **Block destructive commands**: Prevent `rm -rf`, `sed -i`, `git stash`, environment variable changes
- **Enforce git commits**: Block agents from running code without committing changes first
- **Require human approval**: Block dangerous operations until you review
- **Audit trail**: Every command logged and reviewable

37 hooks total available via `./setup-hooks.sh` - pick what you need.

## How to Use

Detailed instructions and explanations are in the installation scripts. Once installed, Mango workflows are invoked using **slash commands** in Claude Code - special commands that start with `/` to trigger workflows and MCPs.

**Slash commands can be used with or without arguments:**

```bash
# Without argument - uses current context
/blog

# With argument - specifies what to do
/blog "Explain our new caching architecture"
```

**Multi-agent collaboration example (`/discuss`):**

Agent 1 starts a discussion:
```bash
/discuss "How should we optimize the database queries?"
```
This creates a GitHub issue and returns an issue number (e.g., #42).

Agent 2 joins the same discussion:
```bash
/discuss 42
```
Now both agents collaborate in real-time on issue #42, building on each other's responses.

**Research blogging example (`/blog`):**
```bash
# Blog about your current work
/blog

# Blog about a specific topic
/blog "Performance improvements in our ML pipeline"
```

To learn more about available workflows and how they work, read the workflow documents in `workflows/` - they're in markdown format, readable by both humans and LLMs.

##  Acknowledgements

This work used EXPANSE at the San Diego Supercomputer Center at the University of California, San Diego through allocation BIO240034 from the Advanced Cyberinfrastructure Coordination Ecosystem: Services & Support (ACCESS) program, which is supported by National Science Foundation grants #2138259, #2138286, #2138307, #2137603, and #2138296.

This work was supported by an Amazon Web Services Imagine Pathfinder grant.
