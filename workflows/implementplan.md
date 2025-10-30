# implementplan

Execute approved implementation plans with rigorous diff application, partial approval handling, and complete verification tracking.

---
**Purpose**

Systematically implement approved diffs from planreport with bulletproof application logic, handling full approval, partial approval, and modified diffs. Ensures zero corruption, complete traceability, and safe rollback capability.

---
## Critical Requirements

1. **Approval Processing**
   - Parse human feedback for approved diff numbers
   - Handle "approve all", "approve 1,3,5", "modify 2", "reject 4"
   - Track approval status for each diff
   - Validate no conflicting approvals

2. **Diff Application Rules**
   - Apply diffs in numerical order
   - Verify each application succeeds before proceeding
   - Maintain backup at each step
   - Rollback on any failure

3. **File Management**
   ```
   Full Approval Path:
   ./temp/scripts_with_diffs_applied/[file] → cp → [original_location]
   
   Partial Approval Path:
   ./temp/original_files/[file] → apply approved diffs → [original_location]
   
   Modified Diff Path:
   Generate new diff → apply → verify → [original_location]
   ```

---
## Steps

### 1. **Initialization & State Recovery**
   - Load previous planreport artifacts
   - Verify temp directories intact
   - Check all diff files present
   - Validate original backups exist
   - Document current git status

### 2. **Approval Parsing & Validation**
   ```python
   # Parse approval format examples:
   "approve all" → apply all diffs
   "approve 1,3,5-7" → apply diffs 1,3,5,6,7
   "reject 2,4" → skip diffs 2,4
   "modify 2: [new instructions]" → regenerate diff 2
   ```
   
   **Validation checks:**
   - All referenced diff numbers exist
   - No diff both approved and rejected
   - Modified diffs have clear instructions
   - Dependencies respected (if diff 3 needs 2, both must be approved)

### 3. **Implementation Execution**

   **Case 1: Full Approval**
   ```bash
   # Simple copy from pre-generated complete version
   cp ./temp/scripts_with_diffs_applied/[file] [target]
   # Verify checksum matches
   sha256sum [target] == stored_hash
   ```

   **Case 2: Partial Approval**
   ```bash
   # Start from original
   cp ./temp/original_files/[file] ./temp/working/[file]
   
   # Apply each approved diff in order
   for diff in approved_diffs:
       patch ./temp/working/[file] < ./temp/proposed_diffs/[diff]
       # Verify success
       if error: rollback and report
   
   # Move to target
   mv ./temp/working/[file] [target]
   ```

   **Case 3: Modified Diffs**
   ```bash
   # Generate new diff based on instructions
   # Apply to test file first
   # Verify no conflicts with other approved diffs
   # Apply in correct sequence position
   ```

### 4. **Verification Protocol**

   **Per-Diff Verification:**
   - Diff applies without conflicts
   - No unexpected line changes
   - Indentation preserved
   - Syntax valid (language-specific check)

   **Cumulative Verification:**
   - All approved diffs applied
   - File compiles/parses correctly
   - Functionality tests pass
   - No unintended side effects

### 5. **Implementation Report Structure**
   ```markdown
   # Implementation Report: [Topic]
   Generated: [Timestamp]
   
   ## Approval Summary
   - Total diffs: [N]
   - Approved: [List]
   - Rejected: [List]
   - Modified: [List]
   
   ## Implementation Log
   
   ### Diff 1: [Description]
   **Status**: [Approved/Rejected/Modified]
   **Human Feedback**: "[exact quote]"
   
   #### Original Proposal
   ```diff
   [original diff content]
   ```
   
   #### What Was Implemented
   - Applied: [Yes/No/Modified]
   - Verification: [Pass/Fail]
   - Checksum after: [hash]
   
   #### Deviations
   [Any differences from plan]
   
   [Repeat for each diff...]
   
   ## Final State
   - Files modified: [List with checksums]
   - Syntax check: [Results]
   - Test results: [If applicable]
   
   ## Rollback Instructions
   ```bash
   # To rollback all changes:
   cp ./temp/original_files/* [targets]
   
   # To rollback specific file:
   cp ./temp/original_files/[file] [target]
   ```
   ```

### 6. **Commit Process (if requested)**
   ```bash
   # Only if explicitly approved
   git add [modified files]
   git commit -m "Apply approved diffs from planreport [timestamp]
   
   Approved diffs: [list]
   Rejected diffs: [list]
   
   Implementation verified with:
   - Syntax checking: [tool]
   - Test results: [summary]"
   
   # Push only if explicitly requested
   git push origin [branch]
   ```

### 7. **Cleanup & Archival**
   - Move temp/proposed_diffs/ → temp/old_proposed_diffs/[timestamp]/
   - Archive implementation report
   - Keep originals for 3 iterations
   - Document final state in manifest

---
### Error Handling

1. **Diff Application Failure**
   ```bash
   # Immediate rollback
   cp ./temp/original_files/[file] [target]
   # Report exact error
   # Suggest resolution
   # Await human intervention
   ```

2. **Partial Application Failure**
   ```bash
   # Rollback to last known good state
   # Report which diffs succeeded
   # Identify conflict point
   # Propose resolution options
   ```

3. **Verification Failure**
   ```bash
   # Do not proceed with commit
   # Generate detailed error report
   # Provide debug information
   # Suggest fixes
   ```

---
### Invocation
Run with `/implementplan` after plan approval to begin bulletproof implementation.

---
### Critical Safety Features

1. **Never Destructive**
   - Always preserve originals
   - Incremental backups at each step
   - Rollback capability maintained
   - No force operations

2. **Verification Gates**
   - Pre-application: File exists and readable
   - During: Each diff applies cleanly
   - Post: Syntax and functionality preserved
   - Final: All assertions pass

3. **Audit Trail**
   - Every action logged with timestamp
   - Human approvals quoted verbatim
   - Deviations documented with rationale
   - Complete reproducibility

4. **Failure Recovery**
   - Graceful degradation
   - Clear error messages
   - Rollback instructions
   - State preservation for debugging

---
### Notes
- NEVER apply diffs without explicit approval
- ALWAYS verify each step programmatically
- MUST maintain ability to rollback at any point
- Test partial approval scenarios thoroughly
- Document every decision and deviation
- Preserve human feedback verbatim
- No assumptions about approval intent