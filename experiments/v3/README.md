# V3 Experimentation Framework

CLI-based experimentation for iterative improvement of summarization with full traceability.

## Setup

### 1. Extract Test Cases (one-time)

```bash
cd /Users/iorlas/Projects/my/ailabbrains
python experiments/v3/extract_test_cases.py
```

This will:
- Show all extracted content from silver layer
- Let you select test cases by number
- Create `test_cases/case_NNN.json` files

### 2. Create Insights Files (manual)

For each test case, create a corresponding `.insights.json` file:

```bash
# Format: test_cases/case_001.insights.json
[
  {"insight": "...", "vitality": "vital"},
  {"insight": "...", "vitality": "vital"},
  {"insight": "...", "vitality": "okay"}
]
```

See `experiments/v1/eval_dataset/example_002.insights.json` for reference.

## Running Experiments

### Basic Run

```bash
python experiments/v3/run.py \
  --test-case test_cases/case_001.json \
  --model "mistralai/mistral-medium-3.1" \
  --system-prompt prompts/system_baseline.txt \
  --user-prompt prompts/user_baseline.txt
```

### With Custom Parameters

```bash
python experiments/v3/run.py \
  --test-case test_cases/case_001.json \
  --model "openai/gpt-4o" \
  --system-prompt prompts/system_baseline.txt \
  --user-prompt prompts/user_baseline.txt \
  --temperature 0.3 \
  --max-tokens 4000 \
  --notes "Testing higher temperature"
```

### Trying Prompt Variations

```bash
# Create new prompt file
cp prompts/system_baseline.txt prompts/variations/system_condensed.txt
# Edit the condensed version...

# Run with new prompt
python experiments/v3/run.py \
  --test-case test_cases/case_001.json \
  --model "mistralai/mistral-medium-3.1" \
  --system-prompt prompts/variations/system_condensed.txt \
  --user-prompt prompts/user_baseline.txt
```

## Evaluating Results

### 1. Review Output

```bash
# Run saves to: runs/YYYYMMDD_HHMMSS_model-slug.json
cat runs/20250311_143052_mistral-medium.json | jq .output.structured_summary
```

### 2. Calculate Completeness

```bash
python experiments/v3/calculate_completeness.py runs/20250311_143052_mistral-medium.json
```

This compares the output with ground truth insights and updates the run file with:
- Which insights were found/missing
- Vital coverage percentage

### 3. Add Manual Judgement

Edit the run file and add your evaluation:

```json
{
  ...
  "evaluation": {
    "judgement": {
      "quality_notes": "Good coverage but missed key formula",
      "strengths": ["Clear core answer", "Good entity extraction"],
      "weaknesses": ["Missing team size formula"],
      "suggestions": ["Emphasize formulas in prompt"]
    },
    "completeness": { ... }
  }
}
```

## Iteration Workflow

1. **Run experiment** → creates `runs/{timestamp}_{model}.json`
2. **Review output** → examine structured_summary
3. **Calculate completeness** → compare vs insights file
4. **Add judgement** → manual evaluation notes
5. **Adjust** → modify prompts/model/params based on findings
6. **Repeat** → run new experiment with changes

## Directory Structure

```
experiments/v3/
├── run.py                   # Main runner
├── extract_test_cases.py    # Setup helper
├── calculate_completeness.py # Evaluation helper
├── test_cases/              # Test data + insights
│   ├── case_001.json
│   ├── case_001.insights.json
│   ├── case_002.json
│   └── case_002.insights.json
├── runs/                    # All experiment results
│   ├── 20250311_143052_mistral-medium-3.1.json
│   └── 20250311_145230_openai_gpt-4o.json
└── prompts/                 # Prompt templates
    ├── system_baseline.txt
    ├── user_baseline.txt
    └── variations/
        ├── system_condensed.txt
        └── user_condensed.txt
```

## Run File Format

Each run file contains complete traceability:

```json
{
  "timestamp": "2025-03-11T14:30:52Z",
  "model": "mistralai/mistral-medium-3.1",
  "config": {
    "temperature": 0,
    "max_tokens": 3000,
    "system_prompt": "...",
    "user_prompt_template": "...",
    "notes": ""
  },
  "input": {
    "test_case": "case_001",
    "url": "...",
    "title": "...",
    "content": "...",
    "content_type": "html",
    "content_length": 7373
  },
  "output": {
    "structured_summary": { /* full KnowledgeGraphSummary */ },
    "tokens_used": 2847,
    "latency_ms": 3421
  },
  "evaluation": {
    "judgement": { /* manual evaluation */ },
    "completeness": {
      "insights_found": [...],
      "insights_missing": [...],
      "vital_coverage_percent": 83.3
    }
  },
  "insights_file": "test_cases/case_001.insights.json"
}
```

## Experimentation Dimensions

### 1. Models

Change `--model` parameter:
- `mistralai/mistral-medium-3.1` (baseline)
- `openai/gpt-4o`
- `anthropic/claude-sonnet-4.5`
- `deepseek/deepseek-r1-0528`
- `google/gemini-2.5-flash`

### 2. Prompts

Edit files in `prompts/` or create variations:
- System prompt: Overall instructions
- User prompt: Input formatting and specific requests

### 3. Schema

To test schema variations, modify the schema in `dagster_project/core/summary_schema.py` or create alternative schemas in `experiments/v3/schemas/`.

### 4. Parameters

- `--temperature`: 0 (deterministic) to 1 (creative)
- `--max-tokens`: Output length limit

## Tips

- Start with baseline to establish performance floor
- Change ONE dimension at a time for clear attribution
- Use `--notes` to document hypotheses
- Compare runs side-by-side using jq or Python scripts
- Track what works in evaluation.judgement.suggestions
