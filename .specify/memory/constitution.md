<!-- Sync Impact Report
Version change: 1.0.0 → 1.1.0 (Added Principle VIII)
Modified principles: None (existing principles unchanged)
Added sections:
  - Principle VIII: No Pointless Overcomplication
  - Updated Simplicity Over Cleverness rationale for consistency
Removed sections: None
Templates requiring updates:
  ✅ plan-template.md - Constitution Check gate already present, will include new principle
  ✅ spec-template.md - Requirements structure compatible
  ✅ tasks-template.md - Phase structure compatible, new principle reinforces simplicity
Follow-up TODOs: None
-->

# Research Blog with Interactive Components Constitution

## Core Principles

### I. Executable Truth
Every claim, number, plot, and finding MUST come from executed code that anyone can verify. Blog posts are Jupyter notebooks first, rendered markdown second. No hallucinated data, no manual plotting, no copy-pasted results. The source notebook is the source of truth.

**Rationale**: Scientific integrity requires reproducibility. If a reader can't execute your code and get the same results, it's not science—it's storytelling.

### II. Exploratory Writing
Notebooks MUST discover results, not prescribe them. Never state conclusions before the code that generates them. Write as if you don't know what the results will be. The code reveals truth; your prose observes and interprets, never predicts.

**Rationale**: Prescriptive writing creates confirmation bias. Exploratory writing maintains intellectual honesty and allows data to surprise you.

### III. Backend Integration Transparency
The blog integrates with powerful backend services (Gradio training UI on :8080, JupyterHub on :8888, terminal on :7681). These integrations MUST be clearly documented, with connection status checks and helpful error messages when services are offline. iframes embed external services; the blog doesn't fake their functionality.

**Rationale**: Users need to understand what's running locally vs remotely, what requires setup, and how to troubleshoot. Transparent integration builds trust and enables reproducibility.

### IV. W&B as Single Source of Truth
All experimental data MUST come from Weights & Biases API calls. Every plot MUST print verification information (run IDs, project names, W&B URLs). No cached data files unless clearly documented. The W&B API is the authoritative data source.

**Rationale**: Data provenance is critical. W&B provides auditable, timestamped, immutable records of experiments. Local files can drift, but W&B URLs never lie.

### V. Simplicity Over Cleverness
Notebooks should be simple, linear, and obvious. Avoid complex abstractions, unnecessary functions, and premature optimization. If a task runs once over one dataset, inline code is better than abstraction. Keep it simple, stupid (KISS).

**Rationale**: Blog notebooks are communication tools first, code artifacts second. Readers need to understand methodology quickly. Complexity hides understanding. Simple solutions are easier to debug, maintain, and explain.

### VI. No Fake Data Ever
Never use simulated, mocked, placeholder, or synthetic data. Not for testing, not for development, not for examples. Real data, real analysis, real results, always. If you can't get real data, stop and ask for help.

**Rationale**: Using fake data creates a slippery slope toward scientific misconduct. One placeholder becomes two, and suddenly you're publishing fiction.

### VII. Vercel Deployment Compatibility
All blog functionality MUST work on Vercel's serverless platform. External backend services (Gradio, Jupyter, terminal) are optional enhancements, not requirements. The core blog (posts, research, comments) MUST be fully functional without backend dependencies.

**Rationale**: Serverless deployment enables global distribution and reliability. Backend services enhance power users but shouldn't break basic functionality for readers.

### VIII. No Pointless Overcomplication
Avoid unnecessary layers of abstraction, excessive planning, and solving problems that don't exist. If a solution can be 50 lines instead of 500, choose 50. If a feature can be implemented with existing tools instead of building new infrastructure, use existing tools. Question every new dependency, framework, and abstraction layer.

**Key Tests**:
- Can this be done with a simple bash script instead of a framework?
- Are we solving an actual problem or a hypothetical one?
- Does this add real value or just architectural beauty?
- Can we ship this in hours instead of days?

**Rationale**: Overengineering wastes time, creates maintenance burden, and obscures the actual problem being solved. The best code is code you don't have to write. Premature abstraction is the root of much wasted effort. Start simple, add complexity only when real requirements demand it.

## Technical Standards

### Notebook Structure
- **Frontmatter First**: YAML frontmatter in first cell (title, excerpt, date, author)
- **Setup Explicit**: Import all dependencies with clear comments
- **Data Fetching Transparent**: Print what you're fetching and from where
- **Analysis Progressive**: Build understanding step by step
- **Visualization Self-Contained**: Each plot cell should be independently executable
- **Verification Mandatory**: Include W&B URLs and run IDs for all data sources

### Conversion Workflow
1. Write notebook in `_notebooks/` directory
2. Execute with `jupyter nbconvert --execute --inplace`
3. Convert with `python convert_notebook.py`
4. Generated markdown in `_posts/`, images in `public/assets/blog/`
5. Commit both notebook and generated artifacts
6. Never edit `_posts/*.md` directly

### Backend Services Integration
- **Training Control**: Gradio UI at :8080 for experiment configuration and EC2 launches
- **Interactive Notebooks**: JupyterHub at :8888 for live editing
- **Terminal Access**: ttyd at :7681 for system access
- **Status Checking**: All integrations MUST check service availability before iframe
- **Graceful Degradation**: Clear instructions when services are offline

### Research Article Generation
- **AI-Powered**: Uses Anthropic Claude for deep research and writing
- **Multi-Stage**: Outline generation → approval → full article → publish
- **Configuration**: Model selection, query depth, guidelines customization
- **Automation**: Scheduled re-runs with feedback integration
- **Quality Control**: Human approval required before publication

## Development Workflow

### Creating Blog Posts
1. Create notebook in `_notebooks/[topic].ipynb`
2. Write exploratory code that discovers results
3. Execute notebook: `jupyter nbconvert --execute --inplace _notebooks/[topic].ipynb`
4. Convert to post: `python convert_notebook.py _notebooks/[topic].ipynb`
5. Verify images saved to `public/assets/blog/[topic]/`
6. Preview locally: `npm run dev`
7. Commit notebook + markdown + images
8. Push to trigger Vercel deployment

### Modifying Notebooks
- **New Notebooks**: Use Write tool to create programmatic structure
- **Existing Notebooks**: Use NotebookEdit tool for cell operations
- **Build in Order**: Construct cell sequence before writing
- **Avoid Reverse Order**: Don't insert cells repeatedly (causes backwards notebooks)

### Backend Service Management
- **Start Services**: Use scripts in `finetune_safe/` (start_web_ui.sh, start_jupyterhub.sh, start_terminal.sh)
- **Run in tmux**: Keep services alive after disconnect
- **Port Management**: Gradio :8080, Jupyter :8888, ttyd :7681
- **AWS Setup**: Load credentials with `source aws_credentials.sh` for EC2 features

### Implementation Philosophy
- **Start Simple**: Build the minimal solution first, add features only when needed
- **Question Complexity**: Every abstraction layer must justify its existence
- **Prefer Boring Technology**: Use well-tested, simple tools over new, complex ones
- **Ship Fast**: A working simple solution today beats a perfect complex solution next week

## Governance

### Amendment Process
- **Major version**: Changing core principles or fundamental approach
- **Minor version**: Adding new principles, integration types, or workflow stages
- **Patch version**: Clarifications and documentation improvements

### Compliance Verification
- All blog posts MUST link to source notebooks
- All data claims MUST reference W&B runs
- Backend integrations MUST check service status
- No manual data entry or fake examples
- Solutions MUST be as simple as possible (but no simpler)

### Review Cadence
- Constitution reviewed when adding major features
- Updated when deployment patterns change
- Versioned to track evolution of blog philosophy
- Complexity questioned in all planning and code review

**Version**: 1.1.0 | **Ratified**: 2025-10-08 | **Last Amended**: 2025-10-09
