# Feature Specification: Mobile Menu Padding Removal

**Feature Branch**: `001-i-want-the`
**Created**: 2025-10-29
**Status**: Draft
**Input**: User description: "I want the mobile menu we get on the ICONS menu at top-right of status bar to be trimmed at right and bottom edges, which currently have blank space, so we show the terminal behind the icons in the bottom and right edges instead of filling edges with blank spaces. repeated efforts have failed."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - View terminal content through menu edges (Priority: P1)

As a mobile user, when I open the ICONS menu from the top-right status bar, I want the right and bottom edges of the menu to show the terminal behind it instead of blank space, so I can maintain visual context of my terminal session while using the menu.

**Why this priority**: This is the core requirement. The user explicitly wants to eliminate wasted screen space on mobile devices where screen real estate is limited. The terminal context is valuable even while navigating the menu.

**Independent Test**: Can be fully tested by opening the ICONS menu on a mobile device and verifying that terminal content is visible through the right and bottom edges where blank space currently exists, and delivers immediate value by improving space efficiency.

**Acceptance Scenarios**:

1. **Given** a mobile device with the application open showing terminal content, **When** the user taps the ICONS menu in the top-right status bar, **Then** the menu overlay should not have blank padding on the right edge, and terminal content should be visible through the trimmed edge
2. **Given** the ICONS menu is open on a mobile device, **When** the user looks at the bottom edge of the menu, **Then** there should be no blank padding at the bottom, and terminal content should be visible through the trimmed edge
3. **Given** the ICONS menu is displayed, **When** measured visually, **Then** the menu should end exactly where the last icon ends (no extra padding beyond content bounds)

---

### User Story 2 - Consistent menu behavior across menu items (Priority: P2)

As a user interacting with the menu, I want all menu items to remain fully functional and clickable after padding removal, so the improved layout doesn't compromise usability.

**Why this priority**: Ensuring the fix doesn't break existing functionality is critical but secondary to implementing the fix itself.

**Independent Test**: Can be tested by clicking/tapping each icon in the menu after padding removal and verifying all functions work correctly.

**Acceptance Scenarios**:

1. **Given** the ICONS menu is open with trimmed edges, **When** the user clicks any icon in the menu, **Then** the icon should respond correctly with no loss of functionality
2. **Given** the ICONS menu is open, **When** the user taps near the edges where padding was removed, **Then** only actual menu items should be clickable (no phantom click zones)

---

### User Story 3 - Responsive menu on different mobile screen sizes (Priority: P3)

As a user on various mobile devices, I want the trimmed menu to work correctly regardless of screen size or orientation, so the improvement is universally beneficial.

**Why this priority**: While important for completeness, this is lower priority than getting the basic functionality working on standard mobile screens.

**Independent Test**: Can be tested by opening the menu on devices with different screen sizes and orientations, verifying proper edge trimming in all cases.

**Acceptance Scenarios**:

1. **Given** a small mobile screen (e.g., iPhone SE), **When** the ICONS menu is opened, **Then** edges should be properly trimmed with terminal visible
2. **Given** a large mobile screen (e.g., iPad), **When** the ICONS menu is opened, **Then** edges should be properly trimmed with terminal visible
3. **Given** a mobile device in landscape orientation, **When** the ICONS menu is opened, **Then** edges should be properly trimmed with terminal visible

---

### Edge Cases

- What happens if the calculated popup dimensions exceed screen size? (Popup should still render but may clip; tmux handles this gracefully)
- How does the mouse coordinate calculation handle the new fixed dimensions? (The mobile-menu.sh script calculates grid position from mouse x/y; verify math still works with exact-fit popup)
- What if terminal has very bright colors that interfere with menu visibility? (Not in scope - this is existing behavior, unrelated to padding)
- What happens during window resize while menu is open? (Existing tmux behavior - popup closes on terminal resize)

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The tmux `display-popup` dimensions MUST be calculated to exactly fit the 4×5 grid content
- **FR-002**: The popup MUST NOT use `-w 100% -h 100%` (current implementation that causes excess padding)
- **FR-003**: The popup width MUST be calculated from: 4 columns × (1 border + 12 chars + 1 border + spacing)
- **FR-004**: The popup height MUST be calculated from: header (2 lines) + 5 rows × (1 border + 6 content lines + spacing)
- **FR-005**: Terminal content MUST be visible on the right edge where blank padding currently exists
- **FR-006**: Terminal content MUST be visible on the bottom edge where blank padding currently exists
- **FR-007**: Existing top and left padding/positioning MUST remain unchanged
- **FR-008**: All 20 menu icon slots MUST remain fully functional after dimension changes
- **FR-009**: Mouse click coordinate calculations MUST work correctly with new dimensions
- **FR-010**: The solution MUST work by modifying the display-popup invocation in tmux.conf.template (line 141)
- **FR-011**: The grid layout hardcoded to 4×5 (COLS=4, ROWS=5, BTN_WIDTH=12, BTN_HEIGHT=6) MUST NOT change

### Non-Functional Requirements

- **NFR-001**: The padding removal should not cause performance degradation
- **NFR-002**: The change should be implemented in a maintainable way that doesn't create technical debt
- **NFR-003**: The solution should avoid CSS hacks or brittle implementations that might break with updates

### Key Entities *(include if feature involves data)*

- **ICONS Menu Popup**: A tmux `display-popup` that appears when clicking the ICONS button in the top-right status bar. Runs `$HOME/usability/tmux/mobile-menu.sh` to render a 4×5 grid of icon buttons (12 chars wide × 6 lines tall per button). Currently opens at 100% width/height (`-w 100% -h 100%`) leaving blank padding on right and bottom edges.
- **Status Bar**: The tmux status bar at the top of the screen with ICONS button trigger (defined in tmux.conf.template line 141)
- **Terminal View**: The background terminal pane content that should be visible through trimmed popup edges
- **Grid Layout**: Fixed 4 columns × 5 rows with borders, spacing, and header. Total dimensions must be calculated from button size + borders + spacing + header lines.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The popup right edge is flush with the rightmost grid border (zero characters of blank space beyond the grid)
- **SC-002**: The popup bottom edge is flush with the bottom row's border (zero lines of blank space beyond the grid)
- **SC-003**: Terminal content is visible immediately to the right of the popup edge
- **SC-004**: Terminal content is visible immediately below the popup edge
- **SC-005**: All 20 icon slots (including EXIT button) remain clickable with correct mouse coordinate detection
- **SC-006**: The popup width value in tmux.conf.template is calculated as a specific character count (not 100%)
- **SC-007**: The popup height value in tmux.conf.template is calculated as a specific line count (not 100%)
- **SC-008**: The user confirms the issue is resolved and no blank padding remains on right/bottom edges

## Technical Context

### Known Constraints

- Previous attempts to fix this issue have failed (reason unknown)
- Grid layout is fixed at 4 columns × 5 rows and must not be changed
- Button dimensions are fixed: 12 characters wide × 6 lines tall
- Existing top/left positioning must be preserved
- Solution must be simple - no over-engineering or breaking changes

### Technical Details

- **Target file**: `tmux/tmux.conf.template` line 141
- **Current implementation**: `bind -n MouseDown1StatusRight display-popup -E -x 0 -y 0 -w 100% -h 100% '$HOME/usability/tmux/mobile-menu.sh'`
- **Problem**: The `-w 100% -h 100%` causes the popup to fill the entire screen, leaving blank padding around the 4×5 grid
- **Solution approach**: Calculate exact width/height values based on grid geometry instead of using 100%
- **Grid geometry**:
  - Header: 2 lines ("PAGE x/y" + blank line)
  - Each row: top border (1 line) + button content (6 lines) + spacing between rows
  - Each column: left border + button width (12 chars) + right border + spacing between columns
- **Mouse coordinate system**: Currently calculated based on 100% popup size, may need adjustment for new dimensions

## Clarifications

### Session 2025-10-29

- Q: What previous approaches were tried to fix this padding issue? → A: Unknown
- Q: Should the popup window itself be sized to fit the grid exactly, or should the grid be centered/expanded within the 100% popup? → A: Resize popup window to exactly fit grid content (no blank space around edges)
- Q: Should there be any padding/margin between the grid and the popup window edges? → A: Keep existing top/left padding unchanged, only trim right/bottom
- Q: Should the solution handle dynamic grid sizes (different numbers of menu items) or is it safe to assume the grid is always 4 columns × 5 rows? → A: Always 4×5 grid (hardcode dimensions)
- Q: The grid is 4 columns × 5 rows with 12-char-wide × 6-line-tall buttons. Should the popup dimensions be calculated to exactly fit this grid, or is there additional spacing/borders to account for? → A: Calculate exact dimensions from grid (borders + buttons + spacing)
