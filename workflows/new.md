

# new

Create or rotate the primary scientific notebook (`SCIENTIST.md`) following the scientific method.

---
**Purpose**

Automate the maintenance of a single **living research log** (`SCIENTIST.md`).  When the log grows large or a new research effort begins, rotate the old log into `.LABNOTEBOOKS/` with a timestamp so history is preserved while keeping the primary log concise.

---
## Steps

1. **Check for an existing notebook**  
   - If `SCIENTIST.md` **does not exist**, jump to **Step&nbsp;4**.
   - If it **does exist**, continue to **Step&nbsp;2**.

2. **Archive the current notebook**  
   1. Capture the current UTC time as `YYYY-MM-DD_HH-MM`.  
   2. Ensure a directory named `.LABNOTEBOOKS/` exists at the repository root (create it if needed).  
   3. Move the existing `SCIENTIST.md` to `.LABNOTEBOOKS/SCIENTIST_${TIMESTAMP}.md`.
   4. If an `ADVISOR.md` is present, move it to `.LABNOTEBOOKS/ADVISOR_${TIMESTAMP}.md` so the scientist’s guidance remains in sync.

3. **Reference previous notebooks**  
   - Scan `.LABNOTEBOOKS/` and gather every notebook filename.  
   - For each file, extract the first heading (line beginning with `#`) if available; fall back to the filename.  
   - Build a brief bullet-list summary that links to each archived notebook.  

4. **Create a fresh `SCIENTIST.md`**  
   Paste the following template.  If **Step&nbsp;3** produced a list of previous notebooks, insert that list under *Historical Notebooks*.

   ```markdown
   # SCIENTIST Notebook

   *Last updated: <!-- Cascade will insert timestamp here -->*

   ## Historical Notebooks
   <!-- Cascade inserts bullet list here (if any) -->

   ## 1. Objective / Hypothesis
   Describe what you are trying to discover or accomplish.

   ## 2. Background / Prior Work
   Summarize relevant context, literature, or previous experiments.

   ## 3. Experimental Design
   - Variables (independent, dependent, controlled)
   - Materials / Data
   - Methods / Procedures (step-by-step and reproducible)

   ## 4. Execution Log
   <!-- Add dated entries as work progresses -->
   ### YYYY-MM-DD
   - *Step* – Observation / result
   - ...

   ## 5. Results
   Present findings, tables, plots, metrics.

   ## 6. Analysis & Interpretation
   Discuss what the results mean relative to the hypothesis.
   - State observations objectively
   - Avoid overstating findings or claiming impact/significance
   - No superlatives or hype
   - Let data speak for itself

   ## 7. Conclusions & Next Steps
   Summarize takeaways and outline future work.
   - Focus on what was learned, not how important it is
   - Avoid editorial commentary on significance
   - State limitations clearly
   ```

5. **Confirm completion**  
   Print a short confirmation indicating where the old notebook was archived and that a new `SCIENTIST.md` has been created.

---
### Notes
- Follow a strict *scientific method* structure so every project remains reproducible.
- Keep each log concise; rotate often to avoid bloat.
- This Workflow can be invoked any time via `/new`.
