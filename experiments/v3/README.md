# Summary Evaluation System

LLM-as-judge evaluation framework for testing and improving summary quality.

## Quick Start

1. **Create your evaluation set** with URLs and expectations:

```bash
# Edit eval_sets/bad_links.json or good_links.json
# Add your URLs with verbal descriptions of what makes a good summary
```

Example eval set format:
```json
[
  {
    "url": "https://example.com/article",
    "expectations": "Should explain the core algorithm with specific examples. Must include time complexity and real-world applications.",
    "anti_patterns": "Don't just list features without explaining why they matter."
  }
]
```

2. **Run evaluation**:

```bash
# Evaluate with baseline prompts
uv run python experiments/v3/evaluate.py --eval-set eval_sets/bad_links.json

# Use different prompts
uv run python experiments/v3/evaluate.py \
  --eval-set eval_sets/good_links.json \
  --prompts v2

# Use different model
uv run python experiments/v3/evaluate.py \
  --eval-set eval_sets/bad_links.json \
  --model deepseek/deepseek-chat-v3

# Force regenerate summaries (ignore cache)
uv run python experiments/v3/evaluate.py \
  --eval-set eval_sets/bad_links.json \
  --force
```

## How It Works

1. **Load eval set** - URLs with expectations
2. **Generate summaries** - Uses your actual pipeline code (`SummaryGenerator`)
3. **Judge quality** - LLM evaluates summary against expectations
4. **Output reports** - Both JSON (for analysis) and Markdown (for reading)

### What Gets Cached

- **Bronze layer** (artifacts/bronze/): Downloaded HTML (never re-downloaded)
- **Silver extracted content** (artifacts/silver/extracted_content/): Parsed text
- **Silver summaries** (artifacts/silver/summaries/): Generated summaries

Use `--force` to regenerate summaries even if cached (useful when testing prompt changes).

### Judge Model

Default: `google/gemini-2.0-flash-exp:free` (cheap, fast, good quality)

Override with:
```bash
uv run python experiments/v3/evaluate.py \
  --eval-set eval_sets/bad_links.json \
  --judge-model anthropic/claude-3.5-sonnet
```

## Directory Structure

```
experiments/v3/
├── evaluate.py              # Main evaluation script
├── eval_sets/               # Your evaluation datasets
│   ├── bad_links.json       # URLs with poor summaries
│   └── good_links.json      # URLs with great summaries
├── prompts/                 # Prompt variants
│   ├── baseline/
│   │   ├── system.txt       # System prompt
│   │   └── user.txt         # User prompt template
│   └── v2/                  # (create for experimentation)
└── results/                 # Evaluation outputs
    ├── TIMESTAMP_baseline.json  # Full results (machine-readable)
    └── TIMESTAMP_baseline.md    # Human-readable report
```

## Creating New Prompt Variants

```bash
# Copy baseline prompts
cp -r prompts/baseline prompts/v2

# Edit prompts/v2/system.txt and prompts/v2/user.txt
# Make your changes...

# Test new prompts
uv run python experiments/v3/evaluate.py \
  --eval-set eval_sets/bad_links.json \
  --prompts v2 \
  --force
```

## Output Format

### JSON Results
```json
[
  {
    "url": "...",
    "title": "...",
    "expectations": "...",
    "judgement": {
      "score": 7,
      "reasoning": "...",
      "strengths": ["...", "..."],
      "weaknesses": ["...", "..."],
      "meets_expectations": true,
      "violates_anti_patterns": false
    },
    "model": "mistralai/mistral-medium-3.1",
    "tokens_used": 5234,
    "latency_ms": 1234
  }
]
```

### Markdown Report
Human-readable report with:
- Summary statistics (avg score, pass rate)
- Individual results with scores and feedback
- Strengths and weaknesses for each URL

## Workflow: Improving Prompts

1. **Gather bad examples** - Add URLs where summaries fail to `eval_sets/bad_links.json`
2. **Run baseline** - See current performance
3. **Analyze failures** - Read markdown report, identify patterns
4. **Iterate on prompts** - Create new prompt variant, test with `--prompts v2 --force`
5. **Compare results** - Check if scores improved
6. **Repeat** - Keep iterating until satisfied

## Tips

- **Start small** - 3-5 URLs per eval set is enough to spot patterns
- **Be specific** - Good expectations are concrete, not vague
- **Mix types** - Include different content types (tutorials, research, opinions)
- **Version prompts** - Use v2, v3, etc. so you can compare
- **Check JSON** - Use `jq` to analyze results: `cat results/*.json | jq '.[] | {url, score: .judgement.score}'`

## Advanced Usage

### Custom judge prompt
Edit `evaluate.py` line ~165 to customize judge evaluation criteria.

### Different judge per eval
Run multiple evaluations with different judge models to get consensus.

### Batch comparison
```bash
# Evaluate same set with multiple prompt versions
for prompts in baseline v2 v3; do
  uv run python experiments/v3/evaluate.py \
    --eval-set eval_sets/bad_links.json \
    --prompts $prompts \
    --force
done

# Compare results
ls -t results/*.md | head -n 3  # View latest 3 reports
```
