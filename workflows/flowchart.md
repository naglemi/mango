---
description: Generate workflow flowcharts using pygraphviz
tags: [visualization, workflow, documentation]
---

# Flowchart Generation Workflow

## WHEN THIS COMMAND IS INVOKED

**EXECUTE THE FLOWCHART GENERATION IMMEDIATELY** - Do not just read the documentation and ask what to do next.

### DEFAULT BEHAVIOR - `/flowchart` (NO ARGUMENTS)

**CREATE ENTIRELY NEW FLOWCHART FROM SCRATCH - OVERWRITE EVERYTHING**

1. **DELETE/IGNORE any existing `*_edges.csv` files** - Start fresh
2. **Examine the codebase** to identify all scripts and data flows
3. **Read each script** to understand inputs/outputs
4. **Create NEW edges CSV file** with complete workflow mapping
   - **CRITICAL**: Every input file must have a row with empty `from` field
   - Pre-existing data files that scripts read MUST be shown as incoming arrows
   - Example: If script reads `/path/to/config.yaml`, add row: `,script.R,/path/to/config.yaml`
5. **Generate the flowchart** using `generate_flowchart.py`
6. **Send result via Pushover** automatically
7. **Report completion** with file path and stats

**CRITICAL RULES**:
- When invoked without arguments, ALWAYS build the flowchart from scratch by analyzing the code
- Do NOT reuse old CSV files
- **EVERY INPUT FILE MUST HAVE AN INCOMING ARROW** - even if it existed before the workflow
- If a script reads a file that no other script creates, use empty `from` field

---

### ALTERNATIVE - `/flowchart revise` (WITH "revise" ARGUMENT)

**Use existing CSV, just regenerate the PNG**

1. Look for existing `*_edges.csv` or `*workflow*.csv` in current directory
2. Regenerate the flowchart PNG using existing CSV (no code analysis)
3. Send result via Pushover automatically
4. Report completion

---

**DO NOT** just display the documentation and wait for further instructions.

## Purpose

Create publication-quality flowcharts that visualize analysis pipelines where:
- **Nodes = Code files ONLY** (scripts: .R, .pl, .py, .sh)
- **Edges = Data files** (arrows represent data flowing between scripts)
- **CRITICAL RULE**: EVERY SINGLE OUTPUT must have its own separate arrow
- Arrows can point to another script OR to empty space (terminal outputs)
- Arrow labels show the data filename

## Standard Approach

### 1. Define Pipeline Structure

Create a 3-column CSV defining edges (data files):

```csv
from,to,label
script_A.R,script_B.R,intermediate_data.rda
script_A.R,script_C.pl,processed.txt
script_B.R,script_D.R,results.csv
script_C.pl,script_D.R,metadata.txt
script_D.R,,final_output.pdf
script_D.R,,summary_stats.csv
script_D.R,,diagnostic_plot.png
```

**CRITICAL RULES**:
1. **Nodes are code files ONLY** - only .R, .pl, .py, .sh files are nodes
2. **Edges are data files** - arrows represent data flowing
3. **EVERY output needs a row** - if script produces 3 outputs, needs 3 rows
4. **EVERY input needs a row** - if script reads 2 pre-existing files, needs 2 rows
5. `from` = Script that produces the data file (code file) OR empty if pre-existing input
6. `to` = Script that consumes the data file (code file) OR empty if terminal output
7. `label` = The data filename (shown on arrow)
8. Empty `from` = arrow comes from nowhere (pre-existing input file)
9. Empty `to` = arrow points to nowhere (terminal output with no downstream use)
10. Each row = exactly ONE data file

### 2. Standard Python Script

Save this as `generate_flowchart.py` (requires NO modification):

```python
#!/usr/bin/env python3

import sys
import csv
import pygraphviz as pgv

if len(sys.argv) < 3:
    print("Usage: python generate_flowchart.py <edges.csv> <output.png> [title]")
    sys.exit(1)

edges_file = sys.argv[1]
output_file = sys.argv[2]
plot_title = sys.argv[3] if len(sys.argv) >= 4 else "Workflow Pipeline"

# Read edges
edges_connected = []
edges_terminal = []
edges_input = []

with open(edges_file, 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if not row['from'] or not row['from'].strip():
            # Pre-existing input file (empty from)
            edges_input.append(row)
        elif row['to'] and row['to'].strip():
            # Connected edge (script to script)
            edges_connected.append(row)
        else:
            # Terminal output (empty to)
            edges_terminal.append(row)

# Create directed graph
G = pgv.AGraph(directed=True, strict=False, rankdir='TB')

# Set graph attributes
G.graph_attr['label'] = plot_title
G.graph_attr['labelloc'] = 't'
G.graph_attr['fontsize'] = '20'
G.graph_attr['fontname'] = 'Arial'

# Set default node attributes (for code files)
G.node_attr['shape'] = 'box'
G.node_attr['style'] = 'filled,rounded'
G.node_attr['fillcolor'] = 'lightblue'
G.node_attr['color'] = 'darkblue'
G.node_attr['fontname'] = 'Arial'
G.node_attr['fontsize'] = '11'
G.node_attr['width'] = '2.5'
G.node_attr['height'] = '0.6'

# Set default edge attributes
G.edge_attr['fontname'] = 'Arial'
G.edge_attr['fontsize'] = '9'

# Add all nodes first (scripts)
all_scripts = set()
for edge in edges_connected + edges_terminal:
    if edge['from']:
        all_scripts.add(edge['from'])
for edge in edges_connected + edges_input:
    if edge['to']:
        all_scripts.add(edge['to'])

for script in all_scripts:
    G.add_node(script)

# Add input edges with labels (pre-existing files)
for edge in edges_input:
    # Create invisible input node
    input_node = f"input_{edge['to']}_{edge['label']}"
    G.add_node(input_node, shape='point', width='0.1', style='invis')
    G.add_edge(input_node, edge['to'], label=edge['label'])

# Add connected edges with labels
for edge in edges_connected:
    G.add_edge(edge['from'], edge['to'], label=edge['label'])

# Add terminal edges with labels
for edge in edges_terminal:
    # Create invisible terminal node
    terminal_node = f"terminal_{edge['from']}_{edge['label']}"
    G.add_node(terminal_node, shape='point', width='0.1', style='invis')
    G.add_edge(edge['from'], terminal_node, label=edge['label'])

# Layout and render
G.layout(prog='dot')
G.draw(output_file, format='png')

total_edges = len(edges_input) + len(edges_connected) + len(edges_terminal)
print(f"Flowchart saved to: {output_file}")
print(f"Nodes: {len(all_scripts)} scripts")
print(f"Edges: {total_edges} data files ({len(edges_input)} inputs, {len(edges_connected)} connected, {len(edges_terminal)} terminal)")
```

**Requirements**: `pygraphviz` (Python package wrapping graphviz)

```bash
conda install -y pygraphviz
```

### 3. Usage

```bash
python generate_flowchart.py <edges.csv> <output.png> [title]
```

**Example**:
```bash
python generate_flowchart.py mwas_workflow_edges.csv mwas_workflow.png "MWAS Region-Level Workflow"
```

### OLD R Script Template (DEPRECATED - use Python version above)

The R version had layout issues. Save this as `generate_flowchart.R` only for legacy purposes:

```r
#!/usr/bin/env Rscript

# Standard workflow flowchart generator
# Usage: Rscript generate_flowchart.R <edges.csv> <output.png> [title]

library(tidyverse)
library(igraph)

# Parse arguments
args <- commandArgs(trailingOnly = TRUE)
if (length(args) < 2) {
  stop("Usage: Rscript generate_flowchart.R <edges.csv> <output.png> [title]")
}

edges_file <- args[1]
output_file <- args[2]
plot_title <- if (length(args) >= 3) args[3] else "Workflow Pipeline"

# Read edge list
edges_raw <- read_csv(edges_file, col_types = cols(
  from = col_character(),
  to = col_character(),
  label = col_character()
), show_col_types = FALSE)

# Separate edges into: script->script and script->terminal
edges_connected <- edges_raw %>% filter(!is.na(to) & to != "")
edges_terminal <- edges_raw %>% filter(is.na(to) | to == "")

# Create graph from connected edges only
if (nrow(edges_connected) > 0) {
  g <- graph_from_data_frame(edges_connected[, c("from", "to")], directed = TRUE)
} else {
  # Handle case where ALL outputs are terminal
  g <- graph_from_data_frame(data.frame(from = character(0), to = character(0)),
                              directed = TRUE)
  g <- add_vertices(g, length(unique(edges_terminal$from)),
                    name = unique(edges_terminal$from))
}

# Add any isolated nodes (scripts with only terminal outputs)
all_scripts <- unique(c(edges_raw$from, edges_connected$to))
missing_scripts <- setdiff(all_scripts, V(g)$name)
if (length(missing_scripts) > 0) {
  g <- add_vertices(g, length(missing_scripts), name = missing_scripts)
}

# Layout
coords <- layout_as_tree(g)
colnames(coords) <- c("x", "y")

# Prepare node data (code files only)
plot_nodes <- as_tibble(coords) %>%
  mutate(
    script = vertex_attr(g, "name"),
    label = script,
    x = x * -1,
    xmin = x - 0.45,
    xmax = x + 0.45,
    ymin = y - 0.3,
    ymax = y + 0.3
  )

# Prepare edge data for connected edges (script->script)
if (nrow(edges_connected) > 0) {
  plot_edges_connected <- edges_connected %>%
    mutate(id = row_number(), type = "connected") %>%
    pivot_longer(cols = c("from", "to"), names_to = "s_e", values_to = "script") %>%
    left_join(plot_nodes %>% select(script, x, ymin, ymax), by = "script") %>%
    mutate(y = ifelse(s_e == "from", ymin, ymax)) %>%
    select(id, type, x, y, label)

  # Edge label positions (midpoints)
  edge_labels_connected <- plot_edges_connected %>%
    group_by(id) %>%
    summarise(
      x = mean(x),
      y = mean(y),
      label = first(label),
      .groups = "drop"
    ) %>%
    filter(!is.na(label) & label != "")
} else {
  plot_edges_connected <- tibble()
  edge_labels_connected <- tibble()
}

# Prepare terminal edges (script->nowhere)
if (nrow(edges_terminal) > 0) {
  plot_edges_terminal <- edges_terminal %>%
    left_join(plot_nodes %>% select(script, x, ymin), by = c("from" = "script")) %>%
    mutate(
      id = row_number() + nrow(edges_connected),
      type = "terminal",
      x_end = x,  # Arrow points straight down
      y_end = ymin - 0.5  # Extends below the box
    )

  # Create arrow segments
  plot_edges_terminal_segments <- plot_edges_terminal %>%
    select(id, label) %>%
    crossing(s_e = c("from", "to")) %>%
    left_join(plot_edges_terminal, by = c("id", "label")) %>%
    mutate(
      x = ifelse(s_e == "from", x, x_end),
      y = ifelse(s_e == "from", ymin, y_end)
    ) %>%
    select(id, type, x, y, label)

  # Terminal edge labels
  edge_labels_terminal <- plot_edges_terminal %>%
    mutate(
      x = x_end,
      y = (ymin + y_end) / 2
    ) %>%
    select(x, y, label) %>%
    filter(!is.na(label) & label != "")
} else {
  plot_edges_terminal_segments <- tibble()
  edge_labels_terminal <- tibble()
}

# Combine all edges
plot_edges <- bind_rows(plot_edges_connected, plot_edges_terminal_segments)
edge_labels <- bind_rows(edge_labels_connected, edge_labels_terminal)

# Create plot
p <- ggplot() +
  # Draw node rectangles (code files only)
  geom_rect(
    data = plot_nodes,
    mapping = aes(xmin = xmin, ymin = ymin, xmax = xmax, ymax = ymax),
    fill = "lightblue", colour = "darkblue", alpha = 0.7, linewidth = 1
  ) +
  # Add node labels (script names)
  geom_text(
    data = plot_nodes,
    mapping = aes(x = x, y = y, label = label),
    size = 3, fontface = "bold"
  ) +
  # Draw arrows (data files)
  geom_path(
    data = plot_edges,
    mapping = aes(x = x, y = y, group = id),
    arrow = arrow(length = unit(0.3, "cm"), type = "closed"),
    linewidth = 0.8
  ) +
  # Add edge labels (data filenames)
  geom_label(
    data = edge_labels,
    mapping = aes(x = x, y = y, label = label),
    size = 2.5, fill = "white", alpha = 0.85,
    label.padding = unit(0.15, "lines")
  ) +
  labs(
    title = plot_title,
    subtitle = "Boxes = Scripts | Arrows = Data files"
  ) +
  theme_void() +
  theme(
    plot.margin = unit(c(1, 1, 1, 1), "cm"),
    plot.title = element_text(hjust = 0.5, face = "bold", size = 18, margin = margin(b = 5)),
    plot.subtitle = element_text(hjust = 0.5, size = 12, margin = margin(b = 10))
  )

# Save
ggsave(output_file, p, width = 12, height = 14, dpi = 300)
cat("Flowchart saved to:", output_file, "\n")
cat("Nodes:", nrow(plot_nodes), "scripts\n")
cat("Edges:", nrow(edges_raw), "data files (",
    nrow(edges_connected), "connected,",
    nrow(edges_terminal), "terminal)\n")
```

### 3. Usage Examples

**Basic MWAS workflow**:
```bash
cat > mwas_edges.csv << 'EOF'
from,to,label
00_brain_regulatory_regions.pl,01_bed_split.R,brain_hg38.bed
01_bed_split.R,BSobj_subset.R,brain_chr*_*.bed (208 files)
BSobj_subset.R,region_level.R,BS_chr*_*.rda (208 files)
region_level.R,04_pca.R,methyl_chr*_*.rda (208 files)
region_level.R,mwas.R,methyl_chr*_*.rda (208 files)
04_pca.R,mwas.R,pc.csv
04_pca.R,,pca.pdf
mwas.R,06_mwas_collect.R,res_chr*_*_res.txt (208 files)
06_mwas_collect.R,07_overlap_gwas_loci.pl,mwas_100k.txt
06_mwas_collect.R,,mwas_100k.bed
07_overlap_gwas_loci.pl,08_plot_mwas_gwas.R,mwas_100k_dist2gwas.bed
07_overlap_gwas_loci.pl,,risk_loci_hg19.bed
07_overlap_gwas_loci.pl,,risk_loci_hg38.bed
08_plot_mwas_gwas.R,,gwas_mwas.pdf
EOF

Rscript generate_flowchart.R mwas_edges.csv mwas_workflow.png "MWAS Region-Level Workflow"
```

**Script with multiple terminal outputs**:
```bash
cat > example.csv << 'EOF'
from,to,label
analysis.R,visualize.R,results.csv
analysis.R,,diagnostic_plot.pdf
analysis.R,,summary_stats.txt
analysis.R,,supplementary.xlsx
visualize.R,,final_figure.png
visualize.R,,interactive_plot.html
EOF
```

## Validation Rules

1. **Count script outputs**: Look at each script's code, count how many files it writes
2. **Count CSV rows**: Count rows where that script is in `from` column
3. **Must match exactly**: outputs = CSV rows for that script
4. **Terminal outputs**: Use empty `to` field for outputs with no downstream use
5. **All code files are nodes**: Every .R/.pl/.py/.sh file is a node
6. **All data files are edges**: Every data file is an arrow (row in CSV)

### Validation Checklist

For each script:
```
Script: 04_pca.R
Outputs: pc.csv, pca.pdf (2 files)
CSV rows where from=04_pca.R: 2 rows ✓
  - pc.csv → mwas.R (connected)
  - pca.pdf → (empty) (terminal)
```

## Common Patterns

### Linear pipeline with terminal output
```csv
from,to,label
step1.R,step2.R,data.csv
step2.R,step3.R,processed.rda
step3.R,,final_results.pdf
```

### Script with multiple outputs (some connected, some terminal)
```csv
from,to,label
analysis.R,plot.R,results_for_viz.csv
analysis.R,,diagnostic.pdf
analysis.R,,full_results.txt
plot.R,,figure.png
```

### Parallel processing
```csv
from,to,label
prepare.R,process1.R,data_part1.rda
prepare.R,process2.R,data_part2.rda
prepare.R,process3.R,data_part3.rda
process1.R,collect.R,result1.txt
process2.R,collect.R,result2.txt
process3.R,collect.R,result3.txt
collect.R,,combined.csv
```

### Workflow with pre-existing input files
```csv
from,to,label
,prepare.R,config.yaml
,prepare.R,reference_genome.fa
prepare.R,analyze.R,processed_data.rda
analyze.R,plot.R,results.csv
analyze.R,,summary_stats.txt
plot.R,,figure.pdf
```

In this example, `config.yaml` and `reference_genome.fa` are pre-existing input files (empty `from`), so arrows come from nowhere pointing to `prepare.R`.

## Key Points

- **Nodes** = Blue boxes = Code files (.R, .pl, .py)
- **Edges** = Arrows = Data files (.csv, .rda, .pdf, .txt)
- **Terminal outputs** = Arrows pointing to empty space (nowhere)
- **Every output = one arrow** = If script writes 5 files, it needs 5 rows in CSV

## Pushover Integration

The flowchart generation scripts now automatically send the generated PNG via Pushover if credentials are available. This feature:

- **Wrapped in try-catch**: Will not fail the script if Pushover is unavailable
- **Optional**: Skips notification if credentials not found
- **Binary attachment**: Sends the PNG file directly as an image attachment (not a link)
- **Works across all versions**: R (tidyverse + httr), R (simple igraph), and Python versions

**Setup**:
```bash
export PUSHOVER_TOKEN="your_app_token_here"
export PUSHOVER_USER="your_user_key_here"
```

**Requirements**:
- R scripts: `httr` package for HTTP requests
- Python script: `requests` package for HTTP requests

If packages are not available, the script will skip Pushover notification and continue normally.

**Pushover Message Format**:
- **Title**: Plot title (e.g., "MWAS Region-Level Workflow")
- **Message**: Summary stats (e.g., "Flowchart generated: 9 scripts, 14 data files (9 connected, 5 terminal)")
- **Attachment**: The generated PNG file (up to 5 MB)

## References

- Tutorial: https://nrennie.rbind.io/blog/creating-flowcharts-with-ggplot2/
- {igraph}: https://igraph.org/r/
- {ggplot2}: https://ggplot2.tidyverse.org/
- Pushover API: https://pushover.net/api
