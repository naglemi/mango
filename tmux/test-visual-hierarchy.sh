#!/usr/bin/env bash
# Demo of the new visual hierarchy display

echo "========================================"
echo "Visual Hierarchy Example Output"
echo "========================================"
echo ""
echo "Imagine you have:"
echo "  - Window 0: vim (3 panes)"
echo "  - Window 1: monitoring (2 panes)"
echo "  - Window 2: logs (1 pane)"
echo ""
echo "The new interface shows:"
echo ""

cat << 'EOF'
Current window structure:

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Window 0 : vim                          (3 pane(s)) ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
  ├─ 0.0    vim          | main.py         | 80x24
  ├─ 0.1    bash         | shell           | 80x12
  └─ 0.2    htop         | monitoring      | 80x12

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Window 1 : monitoring                   (2 pane(s)) ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
  ├─ 1.0    watch        | GPU usage       | 120x30
  └─ 1.1    nvidia-smi   | GPU stats       | 120x30

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Window 2 : logs                         (1 pane(s)) ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
  └─ 2.0    tail         | train.log       | 160x60

Press ENTER to continue to pane selection...

EOF

echo ""
echo "After pressing ENTER, you see the fzf selector where:"
echo "  - Each line shows: pane_id [Window: name] command | title"
echo "  - You can see which window each pane belongs to"
echo "  - TAB to multi-select panes across any windows"
echo "  - Live preview shows pane content on the right"
echo ""

cat << 'EOF'
Example fzf list:
  0.0    [Win: vim          ] vim          | main.py
  0.1    [Win: vim          ] bash         | shell
  0.2    [Win: vim          ] htop         | monitoring
  1.0    [Win: monitoring   ] watch        | GPU usage
  1.1    [Win: monitoring   ] nvidia-smi   | GPU stats
  2.0    [Win: logs         ] tail         | train.log

You could select (example):
  - 0.0, 1.0, 1.1 → Create 1 window: [vim, watch, nvidia-smi]
  - 0.1, 2.0      → Create 1 window: [bash, tail]
  - Leave 0.2 alone (stays in Window 0)
EOF

echo ""
echo "========================================"
echo "Benefits:"
echo "   Clear visual structure before selection"
echo "   See window groupings and pane counts"
echo "   See pane sizes (helps identify layouts)"
echo "   Tree structure shows hierarchy"
echo "   Window context preserved in selection list"
echo "========================================"
