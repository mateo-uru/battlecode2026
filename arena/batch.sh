#!/bin/bash
. /workspace/battlecode/.venv/bin/activate
cd /workspace/battlecode/arena
cat ${1:-jobs.txt} | xargs -P 7 -L1 sh -c 'grep -q "team bot" res/$2_$3.log 2>/dev/null || cambc run $0 $1 --map $2 --release -o res/$2_$3 > res/$2_$3.log 2>&1'
echo DONE
