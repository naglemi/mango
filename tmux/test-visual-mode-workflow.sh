#!/usr/bin/env bash
# Demo of Visual Mode workflow

echo "========================================"
echo "Visual Mode - Workflow Demonstration"
echo "========================================"
echo ""
echo "This is the NEW recommended way to move panes around."
echo "It works exactly like you'd expect - you SEE the layouts,"
echo "you PICK what you see, you MOVE it where you want."
echo ""
echo "──────────────────────────────────────────"
echo "STEP 1: Choose Source Window"
echo "──────────────────────────────────────────"
echo ""
cat << 'EOF'
Available Windows:
  [0] vim (3 panes)
  [1] monitoring (2 panes)
  [2] logs (1 pane)

Which window contains the pane you want to move? 0
EOF

echo ""
echo "──────────────────────────────────────────"
echo "STEP 2: Visual Pane Selection"
echo "──────────────────────────────────────────"
echo ""
echo "Script switches to window 0 and runs 'display-panes'"
echo "You see your ACTUAL tmux window with numbers on each pane:"
echo ""
cat << 'EOF'
┌─────────────────────┬──────────────┐
│                     │      1       │
│                     │              │
│         0           │    (bash)    │
│                     ├──────────────┤
│       (vim)         │      2       │
│                     │              │
│                     │    (htop)    │
└─────────────────────┴──────────────┘
EOF

echo ""
echo "Which pane number do you want to move? 1"
echo ""

echo "──────────────────────────────────────────"
echo "STEP 3: Choose Destination"
echo "──────────────────────────────────────────"
echo ""
cat << 'EOF'
Where do you want to move pane 0.1?

  [n] New window (create a new window for this pane)
  [e] Existing window (join to an existing window)

Destination [n/e]: e
EOF

echo ""
echo "──────────────────────────────────────────"
echo "STEP 4: Pick Destination Window"
echo "──────────────────────────────────────────"
echo ""
cat << 'EOF'
Available Windows:
  [0] vim (2 panes now - we just removed pane 1)
  [1] monitoring (2 panes)
  [2] logs (1 pane)

Which window to join to? 2
EOF

echo ""
echo "Script switches to window 2 so you can see its layout:"
echo ""
cat << 'EOF'
┌────────────────────────────────────┐
│                                    │
│               0                    │
│                                    │
│           (tail -f)                │
│                                    │
└────────────────────────────────────┘
EOF

echo ""
echo "──────────────────────────────────────────"
echo "STEP 5: Execute Move"
echo "──────────────────────────────────────────"
echo ""
echo " Moved pane successfully"
echo "Moved: bash (pane 0.1) → window 2"
echo ""

echo "Result - Window 2 now looks like:"
echo ""
cat << 'EOF'
┌───────────────┬────────────────────┐
│               │                    │
│       0       │         1          │
│               │                    │
│   (tail -f)   │      (bash)        │
│               │                    │
└───────────────┴────────────────────┘
EOF

echo ""
echo "──────────────────────────────────────────"
echo "Move another pane? [y/n]: n"
echo ""
echo "══════════════════════════════════════════"
echo "Done!"
echo "══════════════════════════════════════════"
echo ""
echo "──────────────────────────────────────────"
echo "Why This Works Better:"
echo "──────────────────────────────────────────"
echo ""
echo " You SEE the actual layouts (not lists)"
echo " You PICK by pane number (what's on screen)"
echo " You NAVIGATE windows to see them"
echo " You MOVE one pane at a time (clear & simple)"
echo " No confusion about hierarchy or structure"
echo " Works exactly like manual tmux operations"
echo ""
echo "This is how you naturally think about panes:"
echo "\"I want to move THAT pane (points at screen) to THAT window\""
echo ""
