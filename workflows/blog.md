
How to Create Blog Posts: Experiments vs Methods/Theory

This guide provides instructions for creating two distinct types of blog posts using the Jupyter notebook-based blog system in your blog repository.

## Two Types of Blog Posts

### Type 1: Experimental Results Posts
- **Purpose**: Document experimental runs, show metrics, analyze outcomes
- **Style**: Exploratory, data-driven, objective description
- **Content**: W&B metrics, plots, tables, performance comparisons
- **Example**: "KISS Learning Rate Experiments", "MGDA vs PCGrad Performance"

### Type 2: Methods & Theory Posts
- **Purpose**: Explain algorithms, mathematical concepts, implementation details
- **Style**: Educational, progressive understanding, intuitive + rigorous
- **Content**: Mathematical derivations, algorithmic walkthroughs, code implementations
- **Example Style**: https://andrewkchan.dev/posts/diffusion.html

##  CRITICAL: NO MOCK/SIMULATED DATA POLICY

**STRICTLY PROHIBITED: Mock, simulated, or synthetic data of any kind**

All blog posts MUST use REAL experimental data from W&B. Creating fake data for "demonstration" or "testing" is absolutely forbidden. This includes:
-  Random number generation to simulate metrics
-  Made-up performance numbers
-  Synthetic gradients or loss curves
-  Placeholder visualizations
-  Any form of np.random data presented as real results
-  **HARDCODED STATISTICS OR NUMBERS** (e.g., `results = [0.734, 0.689, 0.712]`)
-  **MANUALLY TYPED NUMERICAL VALUES** in DataFrames or arrays

**ONLY ALLOWED:**
-  Real W&B metrics from actual training runs
-  Actual experimental results
-  True performance measurements
-  Genuine data from executed experiments
-  **NUMBERS COMPUTED FROM LOADED DATA FILES**

**HARDCODED NUMBERS ARE FABRICATED DATA:**
- ALL numbers must be computed from data loaded directly from SOURCE
- NEVER type numerical values directly in code (except for plotting parameters, axis limits, etc.)
- Creating a DataFrame with hardcoded values like `pd.DataFrame({'metric': [0.5, 0.6, 0.7]})` is FABRICATED DATA
- This is the #1 risk for hallucinated/fabricated statistics

**CHAIN OF CUSTODY - NO INTERMEDIATE STAGING:**
- NEVER copy data into the blog repo (blog_data/, cached_data/, etc.)
- Load ONLY from:
  - Main codebase raw data (e.g., `/home/ubuntu/qsar/data/raw/`)
  - W&B API directly (wandb.Api())
  - W&B MCP tools directly (mcp__wandb__)
- Perform ALL analysis in the notebook where you plot
- End-to-end replicability is the ENTIRE POINT
- Any intermediate data directory in blog repo = CHAIN OF CUSTODY VIOLATION

**STATISTICS IN PLAINTEXT MARKDOWN ARE ALSO FABRICATED DATA:**
- NEVER write statistics in markdown cells like "Mean score: -6.55 kcal/mol"
- NEVER write summaries like "Total molecules: 500, Successful: 474 (94.8%)"
- NEVER write markdown tables with hardcoded numbers like "| Method | R² | p-value |"
- NEVER write results sections with numbers like "We tested 500 molecules..."
- ALL statistics must be OUTPUT BY CODE CELLS, not typed in markdown
- Correct approach: Use `print(f"Mean score: {df['score'].mean():.2f} kcal/mol")`
- Or better: Display as formatted table or plot
- If a number appears in your blog post, it MUST be in the output of a code cell, never in markdown text
- Markdown cells should ONLY contain: section headers, QUESTIONS, NOT NUMBERS

**HARDCODED CONCLUSIONS/INTERPRETATIONS ARE FABRICATED:**
- Print statements with conclusions are fabricated interpretations
- ❌ WRONG: `print("The models have no predictive power")`
- ❌ WRONG: `print("R² values are not significantly different from zero")`
- ❌ WRONG: `print("Method A significantly outperforms Method B")`
- ✓ CORRECT: Show quantitative data, let humans interpret:
  ```python
  print(f"R² = {r2:.3f}, p = {p_value:.4f}, N = {n}")
  print(f"Method A: {score_a:.3f}, Method B: {score_b:.3f}")
  ```
- Markdown cells: ask questions
- Code cells: compute answers
- Output cells: show quantitative answers
- Human readers: interpret the data themselves

**EXAMPLE OF COMPLETELY UNACCEPTABLE BLOG POST:**
```markdown
## Results

Total molecules: 500
Successful: 474 (94.8%)
Mean docking score: -6.55 kcal/mol

| Stage | R² | p-value |
|-------|-----|---------|
| Stage 0 | 0.061 | 0.220 |
| Stage 1 | 0.078 | 0.157 |

We found that R²=0.078 for Stage 1...
```
**Every single number in the above is FABRICATED - there is no code showing these came from real data!**

**WORKFLOW MUST FAIL LOUDLY IF:**
- **CHAIN OF CUSTODY VIOLATIONS:**
  - blog_data/, cached_data/, staged_data/, or any data directory exists in blog repo
  - Notebooks load from anywhere within blog repo (relative paths like ../../data/)
  - Notebooks don't load from legitimate sources (main codebase, W&B)
  - Data is "copied in" from analysis performed elsewhere
- **HARDCODED DATA:**
  - Any notebook cell contains hardcoded statistics in lists/arrays/DataFrames
  - Any numbers appear without being derived from loaded files
- **HARDCODED CONCLUSIONS/INTERPRETATIONS:**
  - Print statements assert conclusions not computed from data
  - Keywords: "no predictive power", "significantly better/worse", "proves that", "demonstrates that", "shows that", "outperforms"
  - ANY interpretation that isn't a direct quantitative output
- **STATISTICS IN MARKDOWN:**
  - Any markdown cell contains statistical summaries with numbers (e.g., "Mean: 5.4", "N=100", "p<0.05")
  - Any markdown cell contains inline numbers like "500 molecules" or "R²=0.078"
  - Any markdown table cells contain numerical values
  - Results sections describe numbers without showing the code that computed them
- **PRINCIPLE**: Load raw data → Compute → Show quantitative results → Let humans interpret

**AUTOMATED ENFORCEMENT:**

The `validate_notebook_integrity.py` script provides **multiple rigorous, loud, explained, unbeatable, idiotproof protections** against fabricated data:

```bash
# Location: blog-with-comments-a2/validate_notebook_integrity.py
# Run BEFORE converting notebook to markdown:
python validate_notebook_integrity.py _notebooks/your-notebook.ipynb
```

**What the validator detects:**
1. **Chain of custody violations:**
   - Forbidden directories exist (blog_data/, cached_data/, staged_data/)
   - Loading from paths containing "blog" (loading from blog repo)
   - Loading from relative paths (../../data/)
   - No legitimate data sources (main codebase, W&B)
2. **Numbers > 3 digits in markdown cells** (e.g., "500 molecules", "R²=0.078")
3. **Statistical patterns in markdown** (R²=, p<, N=, Mean:, Total:, percentages)
4. **Hardcoded DataFrames** (e.g., `pd.DataFrame({'col': [0.5, 0.6, 0.7]})`)
5. **Hardcoded lists with 3+ numbers** (e.g., `results = [0.734, 0.689, 0.712]`)
6. **Hardcoded conclusions in print statements** (e.g., `print("models have no predictive power")`)

**The validator FAILS LOUDLY:**
- Exit code 1 if violations found
- Prints detailed error message showing exact cell index, violation type, and context
- Blocks workflow from proceeding
- Makes it **IMPOSSIBLE** to accidentally publish fabricated statistics

**ACCEPTABLE USES OF NUMBERS IN MARKDOWN:**
- Section numbering: "## 1. Introduction" ✓
- References: "see Figure 3" ✓
- Dates: "Published 2025-10-29" ✓
- Everything else: ❌ PUT IT IN CODE OUTPUT

Violating this policy undermines scientific integrity and is considered research misconduct.

## CRITICAL: ALWAYS SHOW ACTUAL P-VALUES, NOT SYMBOLIC CODES

**ANTIPATTERN: Using *, **, *** symbols instead of actual p-values**

```python
# ❌ WRONG - Hiding p-values behind symbols
print(f'R² = 0.078**')  # What is the actual p-value?
print(f'Significance: *')  # Completely useless

# ❌ WRONG - Table with symbols
print('| Method | R² | Sig |')
print('| A | 0.078 | ** |')  # Reader cannot see actual p-value
```

**CORRECT: Always show the actual numerical p-value**

```python
# ✓ CORRECT - Show actual p-values
pval = calculate_pvalue(r2_mean, r2_std)
print(f'R² = {r2_mean:.3f}, p = {pval:.4f}')

# ✓ CORRECT - Table with actual p-values
print('| Method | R² | p-value | Significant? |')
print(f'| A | {r2:.3f} | {pval:.4f} | {"Yes" if pval < 0.05 else "NO"} |')

# ✓ CORRECT - Show both in DataFrame
df = pd.DataFrame({
    'Stage': ['Stage 0', 'Stage 1'],
    'R²': [0.061, 0.078],
    'p-value': [0.2198, 0.1570],
    'Significant (p<0.05)': ['NO', 'NO']
})
print(df.to_string(index=False))
```

### Why Symbolic Codes Are Unacceptable

- **Reader cannot make their own judgment** about significance threshold
- **Cannot compare magnitudes** (p=0.051 vs p=0.90 both marked "ns")
- **Patronizing** - treats reader like they can't interpret numbers
- **Standard in publications** is to report actual p-values, not symbols
- **Scientific rigor** requires showing the actual statistical test results

### Rules for P-Values

1. **ALWAYS show the actual numerical p-value** (e.g., p=0.0234, not p<0.05)
2. **Show at least 3-4 decimal places** for p-values (e.g., 0.0234, not 0.02)
3. **Never use only symbols** (*, **, ***) without showing actual values
4. **If table has limited space**, create separate detailed table with p-values
5. **DO NOT hardcode interpretations** in print statements (NO "p=0.0234 (significant)")

**CRITICAL**: If you report statistical significance, you MUST show the actual p-values. Symbols alone are unacceptable.

## Overview

The blog system uses a **Jupyter notebook-first approach** where all content is executable and reproducible. Blog posts are generated from executed notebooks, ensuring every claim is backed by runnable code using REAL DATA.

### Quick Start (TL;DR)

```bash
# 1. Create notebook in _notebooks/
cd $BLOG_PATH/$BLOG_NOTEBOOKS_DIR/

# 2. Write notebook with real data from W&B or main codebase
# ... (use Write tool to create .ipynb file)

# 3. Submit the blog post (automated)
cd $BLOG_PATH
python submit_blog_post.py $BLOG_NOTEBOOKS_DIR/your-notebook.ipynb
```

The `submit_blog_post.py` script automates validation, execution, conversion, image fixing, git commit/push, and Vercel deployment verification.

## Step 0: Get W&B Data Using MCP (REQUIRED!)

**CRITICAL: NEVER USE INLINE PYTHON SCRIPTS FOR W&B**

All W&B data fetching MUST use the `mcp__wandb__*` MCP tools OR load directly from W&B API. These tools:
- Have hardcoded credentials (no configuration needed)
- Return data structures you use DIRECTLY in notebooks
- Enforce runtime filtering to exclude crashes
- Prevent entity/project discovery errors

**CRITICAL**: Do NOT save W&B data to intermediate files. Use the returned data structures directly.

**CRITICAL: Only analyze runs with runtime >= 3 hours**
- Runs shorter than 3 hours are crashes/failures with no useful data
- W&B MCP automatically filters by runtime
- This prevents wasting time analyzing garbage runs

### Two Workflows: By Run ID vs By Name Prefix

#### Workflow A: User Provides Run IDs

When the user gives you specific run IDs (e.g., "pfg80fwf", "mznpm90g"):

**IN YOUR NOTEBOOK (direct W&B API):**
```python
import wandb
import pandas as pd

# Connect directly to W&B - NO intermediate files
api = wandb.Api()
entity = "your-entity"
project = "your-project"

# Get runs by ID
run_ids = ["pfg80fwf", "mznpm90g", "jlrcc7wq", "c48rc8f9"]
runs = [api.run(f"{entity}/{project}/{rid}") for rid in run_ids]

# Extract history DIRECTLY into DataFrame
history_data = []
for run in runs:
    hist = run.history(pandas=True)
    hist['run_id'] = run.id
    hist['run_name'] = run.name
    history_data.append(hist)

df = pd.concat(history_data, ignore_index=True)
print(f"Loaded {len(df)} history rows from {len(runs)} runs")

# Analyze and plot directly - end-to-end in this notebook
```

**Chain of custody**: W&B API → DataFrame → Analysis → Plot (all in one place)

#### Workflow B: User Provides Experiment Names

When the user mentions experiment groups (e.g., "KISS", "LOUD", "compare MGDA and PCGrad"):

**IN YOUR NOTEBOOK (direct W&B API with filtering):**
```python
import wandb
import pandas as pd
from datetime import datetime, timedelta

# Connect directly to W&B
api = wandb.Api()

# Filter runs by name prefix and runtime
filters = {
    "display_name": {"$regex": "^(kiss|rekiss)"},
    "created_at": {"$gte": (datetime.now() - timedelta(hours=96)).isoformat()}
}

runs = api.runs(f"{entity}/{project}", filters=filters)

# Filter by runtime >= 3 hours
valid_runs = []
for run in runs:
    runtime_seconds = (run.summary.get('_runtime', 0))
    if runtime_seconds >= 10800:  # 3 hours
        valid_runs.append(run)

print(f"Found {len(valid_runs)} valid runs (runtime >= 3h)")

# Extract metrics DIRECTLY into DataFrame
metrics = []
for run in valid_runs:
    metrics.append({
        'run_id': run.id,
        'name': run.name,
        'runtime_hours': run.summary.get('_runtime', 0) / 3600,
        'final_reward': run.summary.get('train/reward', None),
        # ... extract whatever metrics you need
    })

df = pd.DataFrame(metrics)

# Analyze and plot directly - end-to-end in this notebook
```

**Chain of custody**: W&B API (filtered) → DataFrame → Analysis → Plot

### Examples

**Example 1: User says "create a blog post comparing these 4 runs" and gives run IDs**
```
mcp__wandb__fetch_runs_by_id(
  run_ids=["run1_id", "run2_id", "run3_id", "run4_id"],
  output_prefix="comparison"
)
```

**Example 2: User says "analyze the KISS learning rate experiments from this week"**
```
mcp__wandb__fetch_runs_by_prefix(
  prefixes=["kiss", "rekiss"],
  hours_ago=168,
  min_runtime_hours=3.0
)
```

**Example 3: User says "compare MGDA vs PCGrad"**
```
mcp__wandb__fetch_runs_by_prefix(
  prefixes=["mgda", "pcgrad"],
  hours_ago=720,
  min_runtime_hours=3.0
)
```

### FORBIDDEN: Inline Python for W&B

**NEVER DO THIS:**
```python
# FORBIDDEN - inline script
python -c "import wandb; api = wandb.Api(); ..."

# FORBIDDEN - writing temporary scripts
cat > /tmp/fetch_wandb.py << 'EOF'
import wandb
...
EOF
python /tmp/fetch_wandb.py

# FORBIDDEN - any form of inline W&B API calls
```

**ALWAYS USE MCP TOOLS INSTEAD**

### Example: Analysis from Main Codebase

For QSAR/docking analysis, load raw data directly from source:
```python
import pandas as pd
import json
from pathlib import Path

# Load from MAIN CODEBASE - NOT from blog repo
qsar_dir = Path('/home/ubuntu/qsar')

# Load raw experimental data
raw_data = pd.read_csv(qsar_dir / 'data' / 'raw' / 'experimental_measurements.csv')

# Load model results computed by main codebase
with open(qsar_dir / 'results' / 'stage0_metrics.json') as f:
    stage0 = json.load(f)

# Perform analysis IN THIS NOTEBOOK
mean_r2 = stage0['regression']['pam_efficacy']['r2_mean']
n_folds = 10  # From cross-validation setup

print(f"Mean R² = {mean_r2:.3f} (N folds = {n_folds})")

# ✓ CORRECT: Load from source, analyze here, plot here
# ✓ End-to-end replicability

# ❌ NEVER DO THIS - HARDCODED NUMBERS (FABRICATED DATA):
# fake_data = np.random.randn(100, 10)  # FORBIDDEN
# mock_metrics = {"comt": 0.5, "loss": 0.2}  # FORBIDDEN
# results = pd.DataFrame({'method': ['A', 'B'], 'comt': [0.5, 0.6]})  # FORBIDDEN
# performance = [0.734, 0.689, 0.712]  # FORBIDDEN - WHERE DID THESE NUMBERS COME FROM?
```

**CRITICAL: NEVER put statistics in markdown cells:**

```markdown
# ❌ WRONG - Statistics in markdown cell (FABRICATED DATA):
## Docking Statistics

Total molecules: 500
Successful: 474 (94.8%)
Failed: 26 (salts/multi-fragment SMILES)
Mean docking score: -6.55 kcal/mol (range: -8.5 to -4.2 kcal/mol)
```

```python
# ✓ CORRECT - Load from main codebase, compute statistics, display:
df = pd.read_csv('/home/ubuntu/qsar/data/processed/docking_results.csv')

print(f"Total molecules: {len(df)}")
print(f"Successful: {df['success'].sum()} ({df['success'].mean()*100:.1f}%)")
print(f"Failed: {(~df['success']).sum()}")
print(f"Mean docking score: {df['score'].mean():.2f} kcal/mol "
      f"(range: {df['score'].min():.1f} to {df['score'].max():.1f} kcal/mol)")

# Even better: Show as table
summary = pd.DataFrame({
    'Metric': ['Total molecules', 'Successful', 'Failed', 'Success rate'],
    'Value': [len(df), df['success'].sum(), (~df['success']).sum(),
              f"{df['success'].mean()*100:.1f}%"]
})
display(summary)

# Best: Show distribution with plot
plt.hist(df['score'], bins=30)
plt.xlabel('Docking Score (kcal/mol)')
plt.ylabel('Count')
plt.title(f'Docking Score Distribution (N={len(df)})')
plt.show()
```

**KEY PRINCIPLE:** If a number appears in the notebook, it must be in CODE OUTPUT, not markdown text

## Directory Structure

```
$BLOG_PATH/
 $BLOG_NOTEBOOKS_DIR/  # SOURCE: Write Jupyter notebooks here (default: _notebooks)
 _posts/                # OUTPUT: Generated markdown (never edit directly)
 public/assets/blog/    # Generated images from notebooks
 conversion scripts:
     convert_notebook.py           # Main converter
     execute_and_convert_notebooks.py  # Execute + convert
     convert_notebooks_simple.py   # Simple conversion
```

Environment variables are configured during setup:
- `$BLOG_PATH` - Path to your blog repository
- `$BLOG_NOTEBOOKS_DIR` - Notebooks directory (default: _notebooks)
- `$BLOG_REPORTS_DIR` - Reports directory (default: _reports)
- `$ENSURE_BLOGPOST` - Wait for Vercel deployment to complete (default: "true" for REPO mode, "false" for FOLDER mode)

## Step-by-Step Blog Creation Process

###  CRITICAL: JUPYTER NOTEBOOK CREATION

**CORRECT APPROACH: Write complete notebook in ONE STEP**

**Use the Write tool to create the complete .ipynb file with all content in a single operation.**

Do NOT use NotebookEdit for creating new notebooks. NotebookEdit is ONLY for editing notebooks that already exist.

**Example: Creating a new notebook**
```python
# Build complete notebook structure with all cells populated
notebook = {
    "cells": [
        {
            "cell_type": "markdown",
            "id": "frontmatter",
            "metadata": {},
            "source": [
                "---\n",
                "title: 'Your Post Title'\n",
                "excerpt: 'Brief description'\n",
                "date: 'AUTO'\n",
                "author:\n",
                "  name: Michael Nagle\n",
                "  picture: '/assets/blog/authors/jupyter.png'\n",
                "---"
            ]
        },
        {
            "cell_type": "markdown",
            "id": "intro",
            "metadata": {},
            "source": ["## Introduction\n\nThis post analyzes..."]
        },
        {
            "cell_type": "code",
            "id": "setup",
            "metadata": {},
            "source": [
                "import wandb\n",
                "import pandas as pd\n",
                "import matplotlib.pyplot as plt\n",
                "# ... rest of imports"
            ],
            "outputs": [],
            "execution_count": None
        },
        # ... all other cells with complete content
    ],
    "metadata": {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3.10.0"}
    },
    "nbformat": 4,
    "nbformat_minor": 4
}

# Use Write tool once with complete notebook structure
Write(file_path="/path/to/notebook.ipynb", content=json.dumps(notebook, indent=2))
```

**When to use NotebookEdit:**
- ONLY for editing cells in notebooks that already exist
- Use edit_mode="replace" with cell_id to modify existing cells
- NEVER use edit_mode="insert" (has known bugs)

**NEVER:**
- Use NotebookEdit to create new notebooks
- Use NotebookEdit insert mode (it reverses cell order)
- Create notebooks through multiple incremental operations

**ALWAYS:**
- Write complete notebook in one step using Write tool
- Build the full JSON structure with all cells populated
- Only use NotebookEdit for editing existing notebooks

### Step 1: Create a Jupyter Notebook in $BLOG_NOTEBOOKS_DIR/

Create a new notebook with a descriptive name using Write tool (see example above):
```bash
cd $BLOG_PATH/$BLOG_NOTEBOOKS_DIR/
# Name format: experiment-name-analysis.ipynb
# Use Write tool to create complete .ipynb file in one step
```

**Notebook Structure:**

```python
# Cell 1: Frontmatter (MUST be first cell, raw or markdown type)
---
title: 'Your Experiment Title'  # Use proper title with spaces, not underscores
excerpt: 'Brief description of the analysis'
date: 'AUTO'  #  CRITICAL: Use 'AUTO' to automatically insert git commit timestamp in ISO 8601 format!
author:
  name: Your Name
  picture: '/assets/blog/authors/jupyter.png'
coverImage: '/assets/blog/your-experiment/cover.jpg'
ogImage:
  url: '/assets/blog/your-experiment/cover.jpg'
---

# Cell 2: Setup and Imports
import wandb
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

# Set up plotting style
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

# Cell 3: Fetch REAL Data from W&B (NO MOCK DATA!)
api = wandb.Api()
entity = "your-entity"
project = "cluster-pareto-grpo-safe"

# Get ACTUAL runs - never simulate!
runs = api.runs(f"{entity}/{project}")
print(f"Found {len(runs)} REAL runs in project")

#  FORBIDDEN: Creating fake runs or mock data
#  NEVER: mock_run = {"metrics": {"loss": np.random.rand()}}

# Cell 4: Analysis Narrative (Markdown)
## Experiment Overview

Let's explore what happened in these experiments...

# Cell 5: Data Processing
# Extract metrics
data = []
for run in runs[:10]:  # Limit for example
    data.append({
        'name': run.name,
        'comt_mean': run.summary.get('objectives/COMT_activity_maximize/raw_mean', 0),
        'kcnh2_mean': run.summary.get('objectives/KCNH2_activity_minimize/inverted_mean', 0),
        'steps': run.summary.get('_step', 0)
    })
df = pd.DataFrame(data)
df.head()

# Cell 6: Visualizations
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# Plot 1: COMT Performance
axes[0].bar(df['name'][:5], df['comt_mean'][:5])
axes[0].set_xlabel('Experiment')
axes[0].set_ylabel('COMT Activity')
axes[0].set_title('COMT Performance Across Experiments')
axes[0].tick_params(axis='x', rotation=45)

# Plot 2: COMT vs KCNH2 Tradeoff
axes[1].scatter(df['comt_mean'], df['kcnh2_mean'], alpha=0.6)
axes[1].set_xlabel('COMT Activity (Higher Better)')
axes[1].set_ylabel('KCNH2 Activity (Lower Better)')
axes[1].set_title('Objective Tradeoff Analysis')

plt.tight_layout()
plt.show()

# Cell 7: Observations (Markdown)
## What the Data Shows

The plot above reveals... [describe visible patterns]
The table demonstrates... [describe metrics]

# Cell 8: Detailed Metrics
# Show specific run details
best_run = df.loc[df['comt_mean'].idxmax()]
print(f"Best COMT performance: {best_run['name']}")
print(f"  COMT: {best_run['comt_mean']:.4f}")
print(f"  KCNH2: {best_run['kcnh2_mean']:.4f}")
print(f"  Steps: {best_run['steps']}")
```

### Step 2: Execute the Notebook

**Option 1: Run in Jupyter (Recommended)**
```bash
jupyter notebook $BLOG_PATH/$BLOG_NOTEBOOKS_DIR/your-analysis.ipynb
# Execute all cells and save with outputs
```

**Option 2: Execute via Command Line**
```bash
cd $BLOG_PATH/
jupyter nbconvert --execute --inplace $BLOG_NOTEBOOKS_DIR/your-analysis.ipynb
```

**Option 3: Use Execution Scripts**
```bash
cd $BLOG_PATH/
python execute_notebooks.py  # Executes all notebooks
```

###  CRITICAL: Frontmatter Format Requirements

**The blog build will FAIL if frontmatter is incorrect!** Common errors that break Vercel deployment:

1. **Date should use 'AUTO' for programmatic timestamps**:
   -  CORRECT: `date: 'AUTO'` (automatically replaced with actual git commit timestamp)
   -  WRONG: `'1759023326.3970373'` (Unix timestamp - causes "Invalid time value" error)
   -  WRONG: `'September 27, 2025'` (text date)
   -  ACCEPTABLE: `'2025-09-27T12:00:00.000Z'` (ISO 8601 format, but hardcoded - not recommended)

2. **Title must be readable**: Use spaces, not underscores
   -  WRONG: `'2025_09_27_Frank_Wolfe_Vs_Gradient_Descent'`
   -  CORRECT: `'Frank-Wolfe vs Gradient Descent for MGDA'`

3. **All string values must be quoted** in YAML frontmatter

**If Vercel build fails with "RangeError: Invalid time value", the date format is wrong!**

### Step 3: Convert to Blog Post

** CRITICAL: WITHOUT PROPER EXECUTION, YOUR BLOG POST WILL BE BROKEN!**

**Common Failures:**
1. **No visualizations showing** → Notebook wasn't executed
2. **Mangled/duplicate content** → Notebook has malformed cells
3. **Build fails with "Invalid time value"** → Bad date format in frontmatter
4. **Title has underscores** → convert_notebook.py generates bad titles
5. **CELLS IN REVERSE ORDER** → Used NotebookEdit insert mode incorrectly!

**BEFORE CONVERTING, CHECK:**
- First cell of notebook has proper frontmatter with ISO date
- All visualization code cells are complete and runnable
- No duplicate or incomplete cells at the end
- **CELLS ARE IN CORRECT ORDER** (intro → body → conclusion, not backwards!)

```bash
cd $BLOG_PATH/

# Note: convert_notebook.py does NOT handle --execute flag!
# It only converts existing notebook content to markdown
python convert_notebook.py $BLOG_NOTEBOOKS_DIR/your-analysis.ipynb

# If you need to execute first, use jupyter:
jupyter nbconvert --execute --inplace $BLOG_NOTEBOOKS_DIR/your-analysis.ipynb
python convert_notebook.py $BLOG_NOTEBOOKS_DIR/your-analysis.ipynb
```

**What convert_notebook.py does:**
- Reads notebook cells in order
- Extracts frontmatter from first cell
- Converts markdown and code cells
- Saves embedded images from outputs
- Creates markdown file in _posts/

** WARNING:** The script does NOT execute notebooks despite what --execute might suggest!

**Why this is reliable:**
- Jupyter's nbconvert creates images and markdown together atomically
- Image references are automatically generated with relative paths
- The `_files/` directory naming is standard Jupyter behavior
- Git tracks both the .md and _files/ directory together

**DO NOT** use `--inplace` or convert to notebook format!
**DO NOT** use convert_notebook.py without execution - plots won't appear!

### Step 3.5: FIX IMAGE PATHS (CRITICAL!)

** IMAGES WON'T DISPLAY WITHOUT THIS STEP! **

`jupyter nbconvert` creates images in `_posts/your-post_files/` with relative paths, but the Next.js blog needs them in `public/assets/blog/` with absolute paths.

**REQUIRED STEPS AFTER CONVERSION:**

```bash
cd $BLOG_PATH

# 1. Create directory in public/assets/blog/
mkdir -p public/assets/blog/YYYY-MM-DD-your-post-name/

# 2. Copy images from _posts/*_files/ to public/assets/blog/
cp _posts/YYYY-MM-DD-your-post-name_files/*.png public/assets/blog/YYYY-MM-DD-your-post-name/

# 3. Fix image paths in markdown (change relative to absolute)
# BEFORE: ![png](YYYY-MM-DD-your-post-name_files/figure_1.png)
# AFTER:  ![Description](/assets/blog/YYYY-MM-DD-your-post-name/figure_1.png)
```

**Example of fixing image paths:**

```python
# Use Edit tool to update each image reference:
# From: ![png](2025-10-09-batch-size-comparison_files/2025-10-09-batch-size-comparison_5_0.png)
# To:   ![COMT Trajectories](/assets/blog/2025-10-09-batch-size-comparison/2025-10-09-batch-size-comparison_5_0.png)
```

**Why this is necessary:**
- Next.js serves static assets from `public/` directory
- The blog frontend expects images at `/assets/blog/POST_NAME/` paths
- Relative paths `![png](post_files/...)` don't resolve correctly
- All working blog posts use absolute `/assets/blog/` paths

**Verify images will work:**
```bash
# Check images are in public/assets/blog/
ls public/assets/blog/YYYY-MM-DD-your-post-name/

# Check markdown uses absolute paths
grep "assets/blog" _posts/YYYY-MM-DD-your-post-name.md
```

### Step 4: Verify Generated Files

Check that the conversion worked:
```bash
# Check the generated markdown
cat $BLOG_PATH/_posts/your-analysis.md | head -50

# Check images were created
ls -la $BLOG_PATH/public/assets/blog/your-analysis/
```

### Step 5: CRITICAL - Commit and Push (MANDATORY!)

** IMPORTANT: Blog posts will NOT appear online unless committed and pushed!**

```bash
cd $BLOG_PATH

# Check git status
git status

# Add the new post files (markdown, notebook, AND images in public/)
git add _posts/YYYY-MM-DD-your-post-title.md
git add $BLOG_NOTEBOOKS_DIR/YYYY-MM-DD-your-post-title.ipynb
git add public/assets/blog/YYYY-MM-DD-your-post-title/

# Commit with descriptive message
git commit -m "Add blog post: Your Post Title

Brief description of the post content

Co-Authored-By: Claude <noreply@anthropic.com>"

# Push to GitHub (this makes it go live!)
git push origin main

echo " Blog post pushed and will appear online shortly!"
```

**Without this step, your post exists only locally and will NOT be visible on the website!**

### ENSURE_BLOGPOST Setting

When `$ENSURE_BLOGPOST` is set to `"true"` (default for REPO mode):
- Blog submission scripts will wait for Vercel deployment to complete
- Script will not finish until deployment succeeds without errors
- Provides immediate feedback if deployment fails
- Prevents assuming success when deployment actually failed

When set to `"false"` (default for FOLDER mode):
- Scripts complete immediately after git push
- No deployment verification
- Useful for local/folder-only workflows

Configure this setting in the tmux settings menu (`~/mango/tmux/settings-menu.py`) or by editing `~/.claude/settings.json` directly.

## Section A: Creating Experimental Results Posts

The following rules apply to experimental results posts:

### 1. NEVER Edit _posts/*.md Directly
These files are generated from notebooks. Any manual edits will be overwritten.

### 2. Exploratory Writing Style (NOT Prescriptive!)
- NEVER write conclusions before the code that discovers them
- Write as if you don't know what the results will be
- Let the code and plots reveal the truth
- NO "Key Findings" or "Conclusions" sections - humans draw conclusions from data

**OBJECTIVE DESCRIPTION ONLY**
- Describe the experiments, methods, variables in detail
- Explain what was tested and how
- Present data through plots and tables
- DO NOT interpret or conclude - that's for humans

**Examples:**
-  "We tested X configurations..."
-  "The experiments varied parameter Y from..."
-  "Let's examine the data..."
-  "The table above shows..."
-  "All experiments failed..."
-  "The best strategy was..."
-  "This proves that..."

### 3. Data Presentation Requirements

**Statistical Rigor (IF reporting statistics):**
- IF you report an R² value → MUST also include p-value and N
  - Example: "R² = 0.73, p < 0.001, N = 245"
  - Do NOT create regression analyses just to have an R² value
- IF reporting correlation/regression → MUST include complete statistical context
- Don't add statistical tests that aren't relevant to the analysis

**Table Formatting (IF using tables):**
- IF displaying tabular data → MUST use actual formatted tables (pandas DataFrames, markdown tables, HTML)
- NEVER use plaintext representations of tables
- NEVER use print() to display tabular data - use df.head(), df.to_markdown(), or proper table rendering
- Don't create tables just to have tables - only use when tabular format is natural for the data

**Comprehensive Visualization:**
- Plot ALL available information, not just selected highlights
- Show full distributions, not just summary statistics
- Include error bars, confidence intervals when applicable
- Don't cherry-pick "interesting" subsets - show complete data
- This applies to ALL blog posts with data visualizations

**Minimal Interpretation Philosophy:**
- Be LIGHT on interpretation and conclusions
- Be ULTRA-HEAVY on showing all data
- Let humans draw their own conclusions from complete information
- Present data objectively without prescriptive narrative
- Example of good practice: "The plot shows all 150 experiments across 5 methods"
- Example of bad practice: "This proves method X is superior because..."

### 4. Every Claim Must Have Code Using REAL Data
Support assertions with executed code using REAL metrics:
```python
# Show the source of your claim from REAL W&B data
print(f"COMT improved by {improvement:.2%} over baseline")
df[['experiment', 'comt_mean']].sort_values('comt_mean', ascending=False)

#  NEVER create fake improvements:
# fake_improvement = 0.25  # FORBIDDEN - use real data only!
```

### 4. Include W&B Links
Reference specific runs:
```python
run_url = f"https://wandb.ai/{entity}/{project}/runs/{run.id}"
print(f"Full metrics available at: {run_url}")
```

## Common Patterns

### Pattern 0: Proper Statistical Reporting and Table Formatting (IF APPLICABLE)
```python
# These examples show HOW to handle R² values, tables, and data when they
# naturally exist in your analysis. Don't create these just to have them.

# ═══════════════════════════════════════════════════════════════════════
# CRITICAL: ALL NUMBERS MUST COME FROM SOURCE DATA
# ═══════════════════════════════════════════════════════════════════════
# NEVER hardcode statistics - this leads to fabricated/hallucinated data
# Load data DIRECTLY from main codebase or W&B API - NO intermediate staging

# CORRECT: Load from W&B API directly
import pandas as pd
from scipy import stats
import wandb

# Load REAL data from W&B directly
api = wandb.Api()
runs = api.runs("entity/project", filters={"display_name": {"$regex": "^mgda"}})

# Extract data directly
data = []
for run in runs:
    hist = run.history(pandas=True)
    hist['run_id'] = run.id
    data.append(hist)

df = pd.concat(data, ignore_index=True)

# IF you have a regression analysis → Include complete statistical context
# CORRECT: Compute statistics FROM loaded data
x = df['learning_rate']  # From loaded data
y = df['final_performance']  # From loaded data
slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)

# Report R², p-value, and N (all computed from actual data)
print(f"R² = {r_value**2:.3f}, p = {p_value:.4f}, N = {len(x)}")

# CORRECT: Create table by aggregating REAL loaded data
results_df = df.groupby('method').agg({
    'comt_mean': ['mean', 'std'],
    'kcnh2_mean': ['mean', 'std'],
    'run_id': 'count'
}).reset_index()
results_df.columns = ['Method', 'COMT Mean', 'COMT Std', 'KCNH2 Mean', 'KCNH2 Std', 'N Runs']
display(results_df)  # In Jupyter
# Or for markdown:
print(results_df.to_markdown(index=False))

# ❌ WRONG: Hardcoded statistics (FABRICATED DATA - NEVER DO THIS!)
# results_df = pd.DataFrame({
#     'Method': ['MGDA', 'PCGrad', 'Aligned MTL', 'ImTLG'],
#     'COMT Mean': [0.734, 0.689, 0.712, 0.701],  # ❌ HARDCODED = FABRICATED
#     'KCNH2 Mean': [0.412, 0.438, 0.425, 0.431],  # ❌ HARDCODED = FABRICATED
# })
# THIS IS RESEARCH MISCONDUCT - ALL NUMBERS MUST BE COMPUTED FROM LOADED DATA

# ❌ WRONG: Plaintext table representation
# print("Method          COMT    KCNH2")
# print("MGDA            0.734   0.412")  # ❌ NEVER DO THIS

# IF you're creating visualizations (which you should for experimental posts)
# → Plot ALL available data, not cherry-picked subsets
# CORRECT: Plot ALL available data
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# Plot full distributions, not just means
for method in methods:
    method_data = df[df['method'] == method]
    axes[0,0].hist(method_data['comt'], alpha=0.5, label=method, bins=20)

axes[0,0].set_title(f'COMT Distribution Across All Runs (N={len(df)})')
axes[0,0].legend()

# Include error bars on summary plots
summary = df.groupby('method').agg({
    'comt': ['mean', 'std', 'count']
}).reset_index()
axes[0,1].bar(summary['method'], summary['comt']['mean'],
              yerr=summary['comt']['std'], capsize=5)
axes[0,1].set_title('COMT Performance with Standard Deviation')

plt.tight_layout()
plt.show()
```

### Pattern 1: Comparing Experiment Series
```python
# Compare different gradient methods
methods = ['pcgrad', 'mgda', 'imtlg', 'aligned_mtl']
for method in methods:
    method_runs = [r for r in runs if method in r.name]
    avg_comt = np.mean([r.summary.get('comt_mean', 0) for r in method_runs])
    print(f"{method}: {avg_comt:.4f}")
```

### Pattern 2: Training Curves
```python
# Get history for a specific run
run = api.run(f"{entity}/{project}/{run_id}")
history = run.history()

plt.figure(figsize=(12, 6))
plt.plot(history['_step'], history['objectives/COMT_activity_maximize/raw_mean'])
plt.xlabel('Steps')
plt.ylabel('COMT Activity')
plt.title(f'Training Progress: {run.name}')
plt.show()
```

### Pattern 3: Gradient Alignment Analysis
```python
# Analyze gradient conflicts
alignment_data = history['gradients/alignment/COMT_activity_vs_KCNH2_activity'].dropna()
improvement_point = alignment_data[alignment_data > -0.1].index[0] if any(alignment_data > -0.1) else None

if improvement_point:
    print(f"Gradient conflict resolved at step {improvement_point}")
```

## Section B: Creating Methods & Theory Posts

Methods and theory posts explain algorithms, concepts, and implementations in an educational style inspired by posts like https://andrewkchan.dev/posts/diffusion.html.

### Core Philosophy: Human-Friendly Learning

**Most Important**: We write for humans learning complex concepts. Every post should provide:
- **Intuitive explanations** that build understanding step-by-step
- **Detailed walkthroughs** that don't skip steps or assume knowledge
- **Mathematical formulas** in LaTeX with every symbol explained
- **Python implementations** that translate math directly into code
- **Citations** to original papers and implementations

### The Golden Rule: Math + Code Together

For every mathematical concept, provide BOTH:

```python
## Example: Understanding Gradient Projection

# The Math (LaTeX)
"""
When gradients conflict (negative dot product), PCGrad projects gradient g₁
to remove its component along g₂:

$$g_1^{\perp} = g_1 - \frac{\langle g_1, g_2 \rangle}{\|g_2\|^2} g_2$$

Where:
- $\langle g_1, g_2 \rangle$ is the dot product (measures alignment)
- $\|g_2\|^2$ is the squared L2 norm of g₂
- The fraction gives us the scalar projection
- Multiplying by g₂ gives the vector component to remove
"""

# The Code (Python/PyTorch)
def project_gradient(g1, g2):
    """
    Project g1 to remove its component along g2.

    This implements the formula above directly:
    g1_perp = g1 - (g1·g2 / ||g2||²) * g2
    """
    # Step 1: Compute dot product (how aligned are the gradients?)
    dot_product = torch.dot(g1.flatten(), g2.flatten())

    # Step 2: Compute squared norm of g2
    g2_norm_sq = torch.dot(g2.flatten(), g2.flatten())

    # Step 3: Compute the projection coefficient
    projection_coeff = dot_product / (g2_norm_sq + 1e-8)  # Add epsilon for stability

    # Step 4: Remove the g2 component from g1
    g1_projected = g1 - projection_coeff * g2

    # Let's verify our understanding:
    print(f"Original alignment: {dot_product:.4f}")
    print(f"After projection: {torch.dot(g1_projected.flatten(), g2.flatten()):.4f}")
    # Should be ~0 after projection!

    return g1_projected
```

### Key Principles for Methods & Theory Posts

#### 1. Progressive Understanding with Human Touch
Build concepts from simple to complex:
```python
# Cell 1: Start with intuition
## What is MGDA?

Imagine you're trying to optimize multiple objectives simultaneously...
[Simple analogy or visual example]

# Cell 2: Mathematical foundation
## The Mathematics Behind MGDA

Let's formalize this intuition. Given $n$ objective functions $f_1, ..., f_n$:

$$\min_{\alpha \in \Delta^n} \left\| \sum_{i=1}^n \alpha_i \nabla f_i \right\|^2$$

where $\Delta^n$ is the probability simplex...

# Cell 3: Implementation
## Implementing MGDA in PyTorch

Now let's translate the math into code:
```

#### 2. Balance Intuition with Rigor
```python
# Intuitive explanation first
## Understanding Gradient Surgery

Think of gradients as forces pulling your model in different directions...
[Visual diagram or animation]

# Then mathematical precision
## Formal Definition

PCGrad modifies conflicting gradients through projection:
If $\langle g_i, g_j \rangle < 0$, then:
$$g_i' = g_i - \frac{\langle g_i, g_j \rangle}{\|g_j\|^2} g_j$$
```

#### 3. Interactive Visualizations
```python
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import numpy as np

# Create interactive visualizations
def visualize_gradient_conflict(grad1, grad2):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    # Before projection
    ax1.quiver(0, 0, grad1[0], grad1[1], angles='xy', scale_units='xy', scale=1, color='blue', label='Task 1')
    ax1.quiver(0, 0, grad2[0], grad2[1], angles='xy', scale_units='xy', scale=1, color='red', label='Task 2')
    ax1.set_title('Conflicting Gradients')

    # After PCGrad
    grad1_proj = project_gradient(grad1, grad2)
    ax2.quiver(0, 0, grad1_proj[0], grad1_proj[1], angles='xy', scale_units='xy', scale=1, color='blue', alpha=0.7)
    ax2.quiver(0, 0, grad2[0], grad2[1], angles='xy', scale_units='xy', scale=1, color='red', alpha=0.7)
    ax2.set_title('After Gradient Surgery')

    return fig
```

#### 4. Working Implementations
```python
# Complete, runnable implementation
class MGDA:
    """Multiple Gradient Descent Algorithm implementation."""

    def __init__(self, solver='frank_wolfe'):
        self.solver = solver

    def find_min_norm_element(self, grads):
        """
        Find the minimum norm element in the convex hull of gradients.

        Args:
            grads: List of gradient tensors

        Returns:
            weights: Optimal convex combination weights
        """
        # Full implementation with comments
        ...

# Test the implementation
mgda = MGDA()
test_grads = [torch.randn(10), torch.randn(10), torch.randn(10)]
weights = mgda.find_min_norm_element(test_grads)
print(f"Optimal weights: {weights}")
```

#### 5. Connect Theory to Practice
```python
# Show real-world impact
## How MGDA Improves Multi-Objective Optimization

Let's see how MGDA performs on a real problem:

# Load from W&B directly - NO intermediate files
import wandb
api = wandb.Api()
runs = api.runs("entity/project", filters={"display_name": {"$regex": "^mgda"}})

df = pd.DataFrame([{
    'name': r.name,
    'comt': r.summary.get('property/comt_mean', None),
    'kcnh2': r.summary.get('property/kcnh2_mean', None)
} for r in runs])

# Compare methods
fig, ax = plt.subplots(figsize=(10, 6))
ax.plot(df['steps'], df['mgda_loss'], label='MGDA')
ax.plot(df['steps'], df['baseline_loss'], label='Weighted Sum')
ax.set_xlabel('Training Steps')
ax.set_ylabel('Multi-Objective Loss')
ax.legend()
plt.show()

# Explain what we observe
print(f"MGDA converges {faster_by:.1f}x faster than weighted sum")
```

### Template for Methods & Theory Posts

```python
# Cell 1: Frontmatter
---
title: 'Understanding [Algorithm/Concept Name]: A Step-by-Step Journey'
excerpt: 'An intuitive yet rigorous exploration of [topic] with complete math and code'
date: 'AUTO'
author:
  name: Your Name
  picture: '/assets/blog/authors/jupyter.png'
coverImage: '/assets/blog/[topic]/cover.jpg'
ogImage:
  url: '/assets/blog/[topic]/cover.jpg'
---

# Cell 2: Hook & Human Context
## Why [Topic] Matters to Us

# Start with a human story or relatable problem
"""
When I first encountered [topic], I was confused by...
The breakthrough came when I realized it's actually like...
"""

# Cell 3: Prerequisites & Citations
## What You'll Need to Know

"""
This post builds on concepts from:
1. Linear Algebra: vectors, dot products, projections
2. Calculus: gradients, derivatives
3. PyTorch basics: tensors, autograd

Key Papers:
- Original [Algorithm] paper: [Author et al., Year] (https://arxiv.org/...)
- Implementation reference: [GitHub repo]
- Related work: [Other paper]
"""

# Cell 3: Intuitive Introduction
## Understanding [Topic] Intuitively

[Start with analogies, simple examples, visual explanations]

# Cell 4: Building Blocks
## Core Concepts

[Introduce necessary background, prerequisites]

# Cell 5: Mathematical Framework
## The Mathematics of [Topic]

[Formal definitions, theorems, proofs if needed]
[Use LaTeX liberally but explain each symbol]

# Cell 6: Step-by-Step Derivation
## Deriving [Key Result]

[Walk through important derivations]
[Explain each step's intuition]

# Cell 7: Implementation
## From Math to Code

[Translate mathematics into clean, commented code]
[Show multiple implementation approaches if relevant]

# Cell 8: Visualizations
## Visualizing [Concept]

[Interactive plots, animations, diagrams]
[Help reader build visual intuition]

# Cell 9: Experiments
## Testing Our Implementation

[Run small experiments to verify understanding]
[Compare with existing libraries if applicable]

# Cell 10: Applications
## Real-World Applications

[Connect to actual research/production use cases]
[Show performance on real problems]

# Cell 11: Extensions & Variations
## Beyond Basic [Topic]

[Discuss variants, improvements, open problems]
[Point to further reading]
```

### Style Guidelines for Methods & Theory

1. **Human-First Writing**: Write as if explaining to a smart friend who's new to the topic
2. **Step-by-Step Details**: Never skip steps in derivations or implementations
3. **Math + Code Unity**: Every equation gets a code implementation, every algorithm gets mathematical justification
4. **Comprehensive Citations**: Link to papers, codebases, blog posts that helped you understand
5. **Progressive Disclosure**: Start simple, add complexity gradually
6. **Visual Understanding**: Use plots to verify mathematical intuitions
7. **Personal Journey**: Share confusions, breakthroughs, "aha" moments
8. **Test Everything**: Verify claims with runnable experiments

### Example: The Perfect Math + Code Explanation

```python
## Understanding the Frank-Wolfe Algorithm for MGDA

# First, let's understand what we're solving (Sener & Koltun, 2018)
"""
MGDA solves this optimization problem:

$$\min_{\alpha \in \Delta^n} \left\| \sum_{i=1}^n \alpha_i g_i \right\|^2$$

In human terms:
- We have n gradients (g₁, g₂, ..., gₙ) from different objectives
- We want to find weights α that minimize the norm of their weighted sum
- The weights must be on the probability simplex (sum to 1, all non-negative)

This finds the "best compromise" direction that helps all objectives.
"""

# Now let's implement it step-by-step
import torch
import numpy as np

def frank_wolfe_mgda(gradients, max_iters=50, epsilon=1e-3):
    """
    Frank-Wolfe algorithm for finding minimum-norm element in convex hull.

    Based on Algorithm 1 from Sener & Koltun (NeurIPS 2018):
    "Multi-Task Learning as Multi-Objective Optimization"
    https://arxiv.org/abs/1810.04650

    Args:
        gradients: List of gradient tensors [g₁, g₂, ..., gₙ]
        max_iters: Maximum iterations (paper suggests 50 is enough)
        epsilon: Convergence threshold

    Returns:
        weights: Optimal convex combination weights α
    """
    n_tasks = len(gradients)

    # Stack gradients into matrix G where each row is a gradient
    # Shape: (n_tasks, gradient_dimension)
    G = torch.stack([g.flatten() for g in gradients])

    # Step 1: Initialize weights uniformly on the simplex
    # α⁽⁰⁾ = [1/n, 1/n, ..., 1/n]
    alpha = torch.ones(n_tasks) / n_tasks

    print(f"Initial weights: {alpha.numpy()}")

    for t in range(max_iters):
        # Step 2: Compute current weighted gradient
        # d = Σᵢ αᵢ gᵢ = αᵀG
        d = alpha @ G  # Shape: (gradient_dimension,)

        # Step 3: Compute gradient of ||d||² with respect to α
        # ∇_α ||d||² = 2Gd = 2G(Gᵀα)
        grad_alpha = 2 * G @ d  # Shape: (n_tasks,)

        # Step 4: Find the vertex of simplex with minimum gradient
        # This is the Frank-Wolfe direction
        # s = argmin_{s ∈ vertices(Δⁿ)} <grad_alpha, s>
        idx_min = torch.argmin(grad_alpha)
        s = torch.zeros_like(alpha)
        s[idx_min] = 1.0  # Pure vertex (all weight on one task)

        # Step 5: Compute step size (can use line search or fixed)
        # Classic Frank-Wolfe uses γ = 2/(t+2)
        gamma = 2.0 / (t + 2.0)

        # Step 6: Update weights as convex combination
        # α⁽ᵗ⁺¹⁾ = (1-γ)α⁽ᵗ⁾ + γs
        alpha_new = (1 - gamma) * alpha + gamma * s

        # Check convergence
        weight_change = torch.norm(alpha_new - alpha)
        if weight_change < epsilon:
            print(f"Converged at iteration {t}")
            break

        alpha = alpha_new

        # Log progress every 10 iterations
        if t % 10 == 0:
            current_norm = torch.norm(alpha @ G)
            print(f"Iter {t}: norm = {current_norm:.4f}, "
                  f"weights = {alpha.numpy()}")

    return alpha

# Let's test with a simple example
if __name__ == "__main__":
    # Create conflicting gradients
    g1 = torch.tensor([1.0, 0.0])  # Wants to go right
    g2 = torch.tensor([0.0, 1.0])  # Wants to go up
    g3 = torch.tensor([-0.5, -0.5])  # Wants to go down-left

    weights = frank_wolfe_mgda([g1, g2, g3])

    print(f"\nFinal weights: {weights.numpy()}")
    print(f"Sum of weights: {weights.sum():.6f}")  # Should be 1.0

    # Verify this is indeed the minimum norm solution
    combined = weights[0] * g1 + weights[1] * g2 + weights[2] * g3
    print(f"Combined gradient: {combined.numpy()}")
    print(f"Norm of combined: {torch.norm(combined):.4f}")

    # Visualize the result
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(8, 8))

    # Plot original gradients
    ax.quiver(0, 0, g1[0], g1[1], angles='xy', scale_units='xy',
              scale=1, color='red', width=0.01, label='g₁')
    ax.quiver(0, 0, g2[0], g2[1], angles='xy', scale_units='xy',
              scale=1, color='blue', width=0.01, label='g₂')
    ax.quiver(0, 0, g3[0], g3[1], angles='xy', scale_units='xy',
              scale=1, color='green', width=0.01, label='g₃')

    # Plot the MGDA solution
    ax.quiver(0, 0, combined[0], combined[1], angles='xy', scale_units='xy',
              scale=1, color='purple', width=0.02, label='MGDA solution')

    ax.set_xlim(-1, 1.5)
    ax.set_ylim(-1, 1.5)
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.3)
    ax.legend()
    ax.set_title('MGDA finds minimum-norm point in convex hull')

    plt.show()
```

### Common Patterns for Theory Posts

#### Pattern 1: Algorithm Comparison
```python
# Compare multiple algorithms side-by-side
algorithms = {
    'MGDA': MGDA(),
    'PCGrad': PCGrad(),
    'GradNorm': GradNorm()
}

results = {}
for name, algo in algorithms.items():
    results[name] = algo.optimize(test_problem)

# Visualize differences
plot_algorithm_trajectories(results)
```

#### Pattern 2: Ablation Studies
```python
# Show impact of each component
configurations = {
    'baseline': {'use_projection': False, 'normalize': False},
    '+projection': {'use_projection': True, 'normalize': False},
    '+normalization': {'use_projection': True, 'normalize': True}
}

for config_name, settings in configurations.items():
    performance = run_experiment(**settings)
    print(f"{config_name}: {performance:.4f}")
```

#### Pattern 3: Proof by Implementation
```python
# Verify theoretical properties through code
def verify_pareto_optimality(weights, gradients):
    """Verify that MGDA solution is Pareto optimal."""
    combined = sum(w * g for w, g in zip(weights, gradients))

    # Check if any single objective has better direction
    for g in gradients:
        if torch.dot(combined, g) < -1e-6:  # Significantly better
            return False
    return True

# Test the property
assert verify_pareto_optimality(mgda_weights, gradients)
print(" MGDA solution is Pareto optimal")
```

## Troubleshooting

### Issue: Notebook won't execute
- Check W&B API credentials are set
- Verify imports are available
- Run cells sequentially first time

### Issue: Plots not showing in markdown
- Ensure notebook was saved WITH outputs
- Check matplotlib backend is correct
- Verify convert_notebook.py ran without errors

### Issue: Frontmatter not recognized
- Must be in first cell
- Use raw cell type or markdown with --- delimiters
- Check YAML syntax is valid

## Examples of Existing Posts

Check these notebooks for reference (in your blog's `$BLOG_NOTEBOOKS_DIR/`):
- `kiss-final.ipynb` - Learning rate experiments
- `loud-final.ipynb` - Reward transformation analysis
- `comt-final.ipynb` - Single vs multi-objective comparison
- `eureka-bug-fix.ipynb` - Debugging documentation

## Quick Checklist

### For Experimental Results Posts:

#### Data Integrity (enforced by validate_notebook_integrity.py)
- [ ] Using only real data, no mock/simulated data
- [ ] No hardcoded numbers - all statistics computed from loaded data
- [ ] No statistics in markdown cells - all numbers output by code cells
- [ ] Chain of custody verified: load from source (main codebase OR W&B API directly)
- [ ] NO data directories in blog repo (blog_data/, cached_data/, etc.)
- [ ] No loading from paths containing "blog" substring
- [ ] No hardcoded DataFrames like `pd.DataFrame({'col': [0.5, 0.6, 0.7]})`
- [ ] Markdown cells contain no numbers like "Mean: 5.4" or "N=100" or "p<0.05"

#### Content Requirements
- [ ] Load data DIRECTLY from main codebase (e.g., /home/ubuntu/qsar/) OR W&B API
- [ ] Created notebook in `$BLOG_PATH/$BLOG_NOTEBOOKS_DIR/` with descriptive name
- [ ] Added frontmatter in first cell
- [ ] Perform ALL analysis in the notebook (load raw → analyze → plot)
- [ ] Created visualizations from actual data
- [ ] If using R² values: also included p-value and N
- [ ] If using tables: proper formatting (DataFrame/markdown), no plaintext
- [ ] Plotted all available data, not cherry-picked subsets
- [ ] Light on interpretation, heavy on data presentation
- [ ] Added exploratory narrative (not prescriptive)

#### Execution and Validation
- [ ] Executed all cells
- [ ] Saved notebook with outputs
- [ ] Ran validation: `python validate_notebook_integrity.py _notebooks/your-notebook.ipynb`
- [ ] Validation passed - no fabricated data detected

#### Publishing
- [ ] Ran `jupyter nbconvert --execute --to markdown` to generate markdown
- [ ] Copied images from `_posts/*_files/` to `public/assets/blog/POST_NAME/`
- [ ] Fixed all image paths in markdown to use `/assets/blog/` absolute paths
- [ ] Verified markdown in `_posts/`
- [ ] Verified images exist in `public/assets/blog/POST_NAME/`
- [ ] Verified markdown contains `/assets/blog/` paths (not relative paths)
- [ ] Committed and pushed all files (notebook, markdown, and public/assets/blog/ images)

### For Methods & Theory Posts:
- [ ] Created notebook in `$BLOG_PATH/$BLOG_NOTEBOOKS_DIR/` with descriptive name
- [ ] Added frontmatter with clear educational focus
- [ ] Included citations to original papers and implementations
- [ ] Provided intuitive explanation before mathematical formulation
- [ ] Included complete LaTeX equations with symbol explanations
- [ ] Implemented every equation in Python/PyTorch code
- [ ] Added step-by-step comments in implementations
- [ ] Created visualizations to verify understanding
- [ ] Tested all code with concrete examples
- [ ] Shared personal learning journey and insights
- [ ] Executed all cells to ensure reproducibility
- [ ] Ran conversion command to generate markdown
- [ ] Verified mathematical rendering in output
- [ ] Committed and pushed changes

## Complete Workflow Summary

### Automated Pipeline (RECOMMENDED)

**Use the automated submission script for error-free blog generation:**

```bash
cd $BLOG_PATH

# Submit a blog post (full automation)
python submit_blog_post.py $BLOG_NOTEBOOKS_DIR/your-notebook.ipynb
```

The `submit_blog_post.py` script handles:
1. ✓ Validates notebook integrity (detects fabricated data)
2. ✓ Executes notebook (generates plots with real data)
3. ✓ Converts to markdown
4. ✓ Fixes image paths (relative → absolute)
5. ✓ Commits and pushes to GitHub
6. ✓ Waits for Vercel deployment (if ENSURE_BLOGPOST=true)
7. ✓ Fails loudly if any step fails

**Environment variables used:**
- `$BLOG_PATH` - Blog repository path
- `$BLOG_NOTEBOOKS_DIR` - Notebooks subdirectory
- `$ENSURE_BLOGPOST` - "true" to wait for deployment, "false" to skip

### Manual Pipeline (if needed)

```bash
# 1. ALWAYS extract metrics from W&B using MCP tools
# See Step 0 above for MCP tool usage

# For run IDs:
# Use: mcp__wandb__fetch_runs_by_id(run_ids=[...], output_prefix="...")

# For name prefixes:
# Use: mcp__wandb__fetch_runs_by_prefix(prefixes=[...], hours_ago=96)

# 2. Create notebook in $BLOG_PATH/$BLOG_NOTEBOOKS_DIR/
cd $BLOG_PATH/$BLOG_NOTEBOOKS_DIR/
# Create: YYYY-MM-DD-your-post-name.ipynb using Write tool (one step)

# 3. Execute and convert notebook to markdown WITH plots
cd $BLOG_PATH/
jupyter nbconvert --execute --to markdown \
    --output-dir=_posts \
    --output=YYYY-MM-DD-your-post.md \
    $BLOG_NOTEBOOKS_DIR/YYYY-MM-DD-your-post.ipynb

# 4. FIX IMAGE PATHS (CRITICAL - images won't display without this!)
# Copy images to public/assets/blog/
mkdir -p public/assets/blog/YYYY-MM-DD-your-post/
cp _posts/YYYY-MM-DD-your-post_files/*.png public/assets/blog/YYYY-MM-DD-your-post/

# Fix all image paths in markdown using Edit tool:
# Change: ![png](YYYY-MM-DD-your-post_files/image.png)
# To:     ![Description](/assets/blog/YYYY-MM-DD-your-post/image.png)

# 5. Verify outputs exist
ls _posts/YYYY-MM-DD-your-post.md
ls public/assets/blog/YYYY-MM-DD-your-post/*.png
grep "assets/blog" _posts/YYYY-MM-DD-your-post.md  # Verify absolute paths

# 6. MANDATORY: Commit and push (no git add -A!)
git add $BLOG_NOTEBOOKS_DIR/YYYY-MM-DD-your-post.ipynb
git add _posts/YYYY-MM-DD-your-post.md
git add public/assets/blog/YYYY-MM-DD-your-post/
git commit -m "Add blog post: Your Title"
git push origin main
```

**Without step 6, your blog post will NOT appear online!**

### Common Failure Modes

1. **No visualizations** → Forgot to execute notebook
2. **Build error "Invalid time value"** → Wrong date format (use ISO 8601)
3. **Blog doesn't update** → Forgot to push to GitHub
4. **Duplicate/mangled content** → Notebook cells out of order

The automated script prevents all these issues!

## Final Notes

Remember: The goal is **executable documentation** where every insight comes from code that others can run and verify using **REAL DATA**. This creates a permanent, searchable record of our experiments that tells the story of our research progress.

**REMINDER: Mock/simulated data is STRICTLY PROHIBITED. Only use real experimental results from W&B.**
