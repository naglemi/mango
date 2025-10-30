# Implementation Plan: Mobile Menu Padding Removal

**Branch**: `001-i-want-the` | **Date**: 2025-10-29 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/home/ubuntu/usability/specs/001-i-want-the/spec.md`

## Summary

Remove blank padding from right and bottom edges of the tmux mobile menu popup by replacing the current `-w 100% -h 100%` dimensions with calculated exact dimensions that fit the 4×5 icon grid. The popup is triggered by clicking the ICONS button in the status bar and runs `mobile-menu.sh` which renders a fixed grid layout. Terminal content will be visible through the trimmed edges.

## Technical Context

**Language/Version**: Bash (tmux configuration)
**Primary Dependencies**: tmux display-popup, mobile-menu.sh script
**Storage**: N/A (configuration file change only)
**Testing**: Manual visual testing on mobile device
**Target Platform**: tmux on Linux/Unix with mobile/iOS client
**Project Type**: Configuration change (tmux.conf.template)
**Performance Goals**: Instant popup rendering (no performance impact)
**Constraints**: Must not break existing mouse coordinate calculations, must preserve top/left positioning
**Scale/Scope**: Single configuration file edit (1 line change in tmux.conf.template)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

✅ **Principle VIII: No Pointless Overcomplication** - This is a simple configuration change. Calculate exact dimensions, replace one line in tmux.conf.template. No frameworks, no abstractions, no new dependencies.

✅ **Principle V: Simplicity Over Cleverness** - Linear solution: measure grid, calculate dimensions, update config. No complex logic required.

✅ **Development Philosophy: Start Simple** - Hardcode the calculated dimensions for the fixed 4×5 grid. No dynamic calculation, no configuration system, no overengineering.

**Status**: PASS - This solution embodies simplicity. Single file edit, hardcoded dimensions, done.

## Project Structure

### Documentation (this feature)

```
specs/001-i-want-the/
├── spec.md              # Feature specification
├── plan.md              # This file
└── research.md          # Dimension calculation research
```

Note: No data-model.md, contracts/, quickstart.md, or tasks.md needed for this simple configuration change.

### Target Files

```
tmux/
├── tmux.conf.template   # Line 141: Update display-popup dimensions
└── mobile-menu.sh       # Reference only - contains grid layout constants
```

**Structure Decision**: This is a single-line configuration change in an existing file. No new files needed, no source code structure changes. The `mobile-menu.sh` script remains unchanged - we only modify how tmux sizes the popup window that runs it.

## Complexity Tracking

N/A - No complexity violations. This is as simple as it gets: calculate two numbers, update one line.

## Implementation Design

### Phase 0: Research ✅

See [research.md](./research.md) for detailed dimension calculations.

**Grid dimensions calculated**:
- Width: 59 characters (4 columns × borders + button widths + spacing)
- Height: 46 lines (2-line header + 5 rows × borders + button heights + spacing)

### Phase 1: Implementation

**Single file change**: `tmux/tmux.conf.template` line 141

**Current**:
```bash
bind -n MouseDown1StatusRight display-popup -E -x 0 -y 0 -w 100% -h 100% '$HOME/usability/tmux/mobile-menu.sh'
```

**New**:
```bash
bind -n MouseDown1StatusRight display-popup -E -x 0 -y 0 -w 59 -h 46 '$HOME/usability/tmux/mobile-menu.sh'
```

**Changes**:
- Replace `-w 100%` with `-w 59`
- Replace `-h 100%` with `-h 46`
- Keep all other parameters unchanged (`-E -x 0 -y 0` for positioning)

### Phase 2: Testing

**Manual verification steps**:
1. Reload tmux configuration: `tmux source-file ~/.tmux.conf`
2. Click ICONS button in status bar on mobile device
3. Verify popup appears with exact grid fit
4. Verify no blank space on right edge (terminal visible immediately after grid border)
5. Verify no blank space on bottom edge (terminal visible immediately after grid border)
6. Click each of the 20 icon buttons to verify mouse coordinates still work
7. Test on different screen sizes (small phone, large tablet)
8. Confirm top/left positioning unchanged

**Success criteria**:
- All 20 buttons remain clickable
- Terminal content visible through right and bottom edges
- No regression in existing functionality

### No Additional Phases Needed

This implementation requires:
- ✅ No data model
- ✅ No API contracts
- ✅ No quickstart guide (testing is manual visual inspection)
- ✅ No complex task breakdown (single line change)

## Implementation Notes

### Why These Dimensions

From the grid rendering code in `mobile-menu.sh`:

**Width calculation** (59 chars):
- 4 columns, each column renders: `+` + 12 chars + `+` or `+ ` (space between)
- Columns 0-2: 15 chars each (14 for borders/content + 1 space)
- Column 3: 14 chars (no trailing space)
- Total: 15 + 15 + 15 + 14 = 59

**Height calculation** (46 lines):
- Header: 2 lines ("PAGE x/y" + blank line)
- Each row: 1 top border + 6 content lines + 1 bottom border + 1 spacing = 9 lines
- Last row: 1 top border + 6 content lines + 1 bottom border + 0 spacing = 8 lines
- Total: 2 + (4 × 9) + 8 = 2 + 36 + 8 = 46

### Risk Analysis

**Low risk change**:
- Single hardcoded value substitution
- No logic changes
- No script modifications
- Easily reversible (revert to `-w 100% -h 100%`)

**Potential issue**: Mouse coordinate calculations in `mobile-menu.sh` (lines 275-306)
- Current code calculates grid position from mouse x/y coordinates
- With exact-fit popup, the coordinate math should still work
- The script doesn't assume 100% dimensions - it calculates from actual mouse position
- **Mitigation**: Test all 20 buttons after change

### Rollback Plan

If mouse coordinates break or other issues arise:
```bash
# Revert line 141 in tmux.conf.template back to:
bind -n MouseDown1StatusRight display-popup -E -x 0 -y 0 -w 100% -h 100% '$HOME/usability/tmux/mobile-menu.sh'
```

Then reload: `tmux source-file ~/.tmux.conf`

## Progress Tracking

- [x] Phase 0: Research (dimension calculations complete)
- [x] Phase 1: Implementation (edit tmux.conf.template line 141) ✅ COMPLETED
- [ ] Phase 2: Testing (manual verification on mobile device)

## Next Steps

Ready for implementation. The plan is complete and simple:
1. Edit one line in tmux.conf.template
2. Test on mobile device
3. Done

No additional artifacts needed. Proceed to `/implement` or directly edit the file.
