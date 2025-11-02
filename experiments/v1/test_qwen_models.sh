#!/bin/bash

# Test Qwen models with knowledge_graph_json experiment
# Uses structured JSON extraction

# Models to test
MODELS=(
    "qwen/qwen-plus-2025-07-28"
    "qwen/qwen3-235b-a22b"
    "qwen/qwen3-next-80b-a3b-thinking"
    "qwen/qwen3-max"
    "qwen/qwen3-vl-32b-instruct"
    "qwen/qwen3-vl-235b-a22b-thinking"
)

echo "Testing ${#MODELS[@]} Qwen models with knowledge_graph_json experiment..."
echo ""

for model in "${MODELS[@]}"; do
    echo "========================================="
    echo "Testing: $model"
    echo "========================================="

    python test_prompt.py \
        --experiment knowledge_graph_json \
        --model "$model"

    echo ""
    echo ""
done

echo "All tests complete!"
