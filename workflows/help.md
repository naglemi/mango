# help

Provide strategic guidance (via `ADVISOR.md`) and then update the active research log (`SCIENTIST.md`) accordingly.

---
**Purpose**

Keep projects on track by injecting periodic "big-picture" reflection without blocking the scientist's autonomy.

---
## Steps

1. **Ensure an Advisor notebook exists**  
   - If `ADVISOR.md` **does not exist**, create it from the *Advisor Template* in **Step&nbsp;4**.  
   - If it **does exist**, open it for update.

2. **Update `ADVISOR.md`**
   - Append a new dated entry under *Advisor Log* suggesting strategic guidance, time-management tips, or reminders of overarching objectives.
   - Keep tone: concise, laissez-faire, non-dictatorial.
   - **Content requirements**:
     * Avoid claiming findings are "critical" or "significant"
     * No superlatives or hype about importance
     * State suggestions objectively without editorial emphasis
     * Let scientist decide actual importance

3. **Reflect in `SCIENTIST.md`**  
   - Open current `SCIENTIST.md`.  
   - After reading latest advisor entry, add a short response noting whether the scientist will adopt, modify, or decline each suggestion (and brief rationale).  
   - If declining, state why; if accepting, outline concrete next actions.

4. **Advisor Template**  
   Paste if creating a new file:

   ```markdown
   # ADVISOR Notebook

   *Last updated: <!-- Cascade inserts timestamp -->*

   ## Purpose
   Offer high-level guidance to keep the research efficient and goal-oriented.

   ## Advisor Log
   <!-- Add entries such as:
   ### 2025-07-07
   - Encourage scientist to define clear success metrics before running more experiments.
   -->
   ```

5. **Archive on rotation**  
   If this Workflow is invoked immediately after `/new` rotated notebooks, `ADVISOR.md` will already have been archived alongside the old scientist notebook.  No extra action needed.

---
### Notes
- Advisor guidance should be *suggestive*, not prescriptive.  The scientist can disagree.
- Keep both notebooks lightweight: the advisor focuses on strategy, the scientist on execution.
- Consider suggesting a revert to earlier git commit when fixes create cascading new problems.
- Invoke anytime with `/help`.