#!/bin/bash
# Test script for block-python-c-inline.py hook

echo "Testing block-python-c-inline.py hook..."
echo ""

# Test 1: Simple one-liner (should pass)
echo "Test 1: Simple one-liner"
echo 'python -c "print(2+2)"' | python3 /home/ubuntu/usability/hooks/block-python-c-inline.py
if [ $? -eq 0 ]; then
    echo " PASS: Simple one-liner allowed"
else
    echo " FAIL: Simple one-liner was blocked"
fi
echo ""

# Test 2: Multi-line script (should be blocked)
echo "Test 2: Multi-line script"
echo 'python -c "
import os
print(os.getcwd())
"' | python3 /home/ubuntu/usability/hooks/block-python-c-inline.py 2>&1
if [ $? -ne 0 ]; then
    echo " PASS: Multi-line script blocked"
else
    echo " FAIL: Multi-line script was not blocked"
fi
echo ""

# Test 3: Script with semicolons (should be blocked)
echo "Test 3: Script with semicolons"
echo 'python -c "import os; print(os.getcwd())"' | python3 /home/ubuntu/usability/hooks/block-python-c-inline.py 2>&1
if [ $? -ne 0 ]; then
    echo " PASS: Script with semicolons blocked"
else
    echo " FAIL: Script with semicolons was not blocked"
fi
echo ""

# Test 4: Script with import (should be blocked)
echo "Test 4: Script with import statement"
echo 'python -c "import json; print(json.dumps({'"'"'test'"'"': 1}))"' | python3 /home/ubuntu/usability/hooks/block-python-c-inline.py 2>&1
if [ $? -ne 0 ]; then
    echo " PASS: Import script blocked"
else
    echo " FAIL: Import script was not blocked"
fi
echo ""

# Test 5: Normal bash command (should pass)
echo "Test 5: Normal bash command"
echo 'ls -la' | python3 /home/ubuntu/usability/hooks/block-python-c-inline.py
if [ $? -eq 0 ]; then
    echo " PASS: Normal bash command allowed"
else
    echo " FAIL: Normal bash command was blocked"
fi

echo ""
echo "Testing complete!"