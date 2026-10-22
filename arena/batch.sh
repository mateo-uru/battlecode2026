#!/bin/bash
# 40 maps x both sides. Usage: ./batch.sh [opponent] [jobs]
cd "$(dirname "$0")"
export PATH="${HOME}/.local/bin:${PATH}"
# 3 workers: 4-wide runs have raced the wasm build and run the box out of memory.
python3 suite.py --opponent "${1:-starter-python}" --jobs "${2:-3}" --timeout 420 --out "${3:-/tmp/bc-suite/${1:-starter-python}}"
