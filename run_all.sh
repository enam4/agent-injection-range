#!/usr/bin/env bash
# run every model through all four arms, then score and render
cd "$(dirname "$0")"; [ -f .venv/bin/activate ] && source .venv/bin/activate
export THREADS=${THREADS:-4}
for m in qwen2.5-0.5b llama3.2-1b qwen2.5-1.5b; do python agent.py $m none,spotlight,hierarchy,both > runs/log-$m.txt 2>&1; done
python score.py && python render.py && python show.py
