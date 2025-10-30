#!/bin/bash
# Simple test hook that just logs
echo "$(date): Stop hook fired!" >> /tmp/stop-hook-test.log
echo '{"suppressOutput": true}'