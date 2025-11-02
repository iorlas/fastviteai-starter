# Prompt Testing & Optimization Workflow

A streamlined system for iterative prompt engineering with automatic versioning, performance tracking, and quality evaluation.

## Overview

This workflow enables rapid experimentation with LLM prompts for content summarization. The system:
- Loads prompts from `prompts.yaml` (no manual copying)
- Auto-detects changes and versions prompts (v1, v2, v3...)
- Evaluates coverage against ground truth insights
- Tracks all experiments in CSV history
- Organizes reports by experiment name
- Optionally integrates with MLflow for detailed tracking

## Quick Start

### 1. Run an Experiment

```bash
python test_prompt.py --experiment knowledge_graph_json
```

This will:
1. Load the experiment from `prompts.yaml`
2. Run it on the test content (`eval_dataset/example_002.json`)
3. Evaluate insights coverage
4. Save reports to `reports/knowledge_graph_json/`
5. Append to `experiment_history.csv`

### 2. View Performance

```bash
python test_prompt.py --leaderboard
```

Shows all experiments ranked by coverage:
```
🏆 #1   knowledge_graph_json (v2)        openai/gpt-4o           100.0%    16.73s    3449
```

### 3. Iterate on Prompts

```bash
# 1. Edit prompts.yaml (modify the experiment)
vim prompts.yaml

# 2. Run again - system auto-creates v2
python test_prompt.py --experiment knowledge_graph_json

# 3. Compare versions in leaderboard
python test_prompt.py --leaderboard
```

## Prompt Optimization Workflow

### Conversational Iteration Process

This workflow is designed for **human-AI collaboration** where you (the user) and Claude Code work together to optimize prompts:

```
1. You: "Run the knowledge_graph_json experiment"
2. Claude: *runs test_prompt.py*
   Result: 91.7% coverage
   Missing: SOA/WS-* specs comparison

3. Claude: *analyzes gaps*
   "The model is missing historical comparisons.
    I'll add explicit instruction to capture 'how SOA failed'"
   *edits prompts.yaml*

4. You: "Run it again"
5. Claude: *runs test_prompt.py*
   Result: 100% coverage!
   System auto-detected prompt change → v2

6. You: "Show leaderboard"
7. Claude: *shows comparison*
   v1: 91.7% vs v2: 100.0% ✅
```

### Step-by-Step Example

**Initial Run (v1):**
```bash
$ python test_prompt.py --experiment knowledge_graph_json
🟢 Insights Coverage: 91.7% (Excellent)

📋 Coverage Details:
   ✅ [yes    ] Microservices success is fundamentally about organizational structure
   ✅ [yes    ] Amazon's two-pizza rule limits teams to 6-8 members
   ...
   ❌ [no     ] SOA had similar principles but lost focus by getting caught up in WS-* specs
```

**Claude Analyzes:**
- Missing: Historical comparison insight
- Root cause: No explicit instruction to capture "how previous approaches failed"
- Solution: Add to system_message

**Claude Edits prompts.yaml:**
```yaml
system_message: |
  ...
  CRITICAL: Capture ALL details, including:
  - Historical comparisons and lessons learned (e.g., how SOA failed, what went wrong with predecessors)
  - Cautionary tales and warnings about pitfalls
  ...
```

**Re-run (automatic v2):**
```bash
$ python test_prompt.py --experiment knowledge_graph_json
✅ Insights Coverage: 100.0% (PERFECT!)

ℹ️  Prompt hash changed - automatically created v2

📋 Coverage Details:
   ✅ [yes    ] SOA had similar principles but lost focus by getting caught up in WS-* specs ← NOW CAPTURED!
```

## File Structure

```
experiments/
├── prompts.yaml                 # Experiment definitions (edit here!)
├── test_prompt.py               # Main test script
├── experiment_history.csv       # Complete run history
├── eval_dataset/               # Test content + ground truth
│   ├── example_001.json
│   ├── example_001.insights.json
│   ├── example_002.json
│   └── example_002.insights.json
└── reports/                    # Organized by experiment
    └── knowledge_graph_json/
        ├── openai-gpt-4o_v1_20251102_200353.json
        ├── openai-gpt-4o_v1_20251102_200353.txt
        ├── openai-gpt-4o_v2_20251102_205807.json
        └── openai-gpt-4o_v2_20251102_205807.txt
```

## Understanding Outputs

### Console Output

```
================================================================================
🔬 Running: knowledge_graph_json (v2)
================================================================================
Model: qwen/qwen3-235b-a22b
Content: The Real Success Story of Microservices Architectures
================================================================================

✅ Summary generated

================================================================================
📊 RESULTS
================================================================================

✅ Insights Coverage: 100.0% (PERFECT!)

📈 Stats:
   Vital insights found: 12/12
   All insights found: 12/12

⚡ Performance:
   Latency: 26.24s
   Tokens: 3645 (prompt: 2340, completion: 1305)

📋 Coverage Details:
   ✅ [yes    ] Microservices success is fundamentally about organizational...
   ✅ [yes    ] Amazon's two-pizza rule limits teams to 6-8 members...
   ⚠️ [partial] Prematurely breaking apps into microservices...
   ❌ [no     ] Author plans to discuss OpenShift and fabric8io...
```

### Coverage Status Indicators

- ✅ **yes** - Insight fully captured with all details
- ⚠️ **partial** - Insight mentioned but missing context or specifics
- ❌ **no** - Insight completely missing from summary

### JSON Report

Full structured output at `reports/{experiment}/{model}_{version}_{timestamp}.json`:

```json
{
  "timestamp": "20251102_185138",
  "experiment": "knowledge_graph_json",
  "version": "v1",
  "model": "qwen/qwen3-235b-a22b",
  "coverage_pct": 100.0,
  "latency_sec": 26.24,
  "tokens_total": 3645,
  "missing_insights": [],
  "partial_insights": ["Prematurely breaking apps..."],
  "coverage_details": [...]
}
```

### Text Report

Human-readable report at `reports/{experiment}/{model}_{version}_{timestamp}.txt` with:
- Full generated summary
- Coverage breakdown
- Missing/partial insights
- Complete prompt configuration

### History CSV

`experiment_history.csv` tracks every run:

```csv
timestamp,experiment,version,model,coverage_pct,latency_sec,tokens_total,prompt_hash
2025-11-02T20:58:07,knowledge_graph_json,v2,openai/gpt-4o,100.0,16.73,3449,a8c4d1f2
```

Easy to analyze with command line tools:

```bash
# Best coverage per experiment
sort -t',' -k5 -rn experiment_history.csv | head

# Show all versions of an experiment
grep "knowledge_graph_complete" experiment_history.csv

# Average latency by model
awk -F',' '{sum[$4]+=$6; count[$4]++} END {for (m in sum) print m, sum[m]/count[m]}' experiment_history.csv
```

## Commands Reference

### Basic Usage

```bash
# Run experiment
python test_prompt.py --experiment <name>

# Run with different model
python test_prompt.py --experiment <name> --model qwen/qwen3-235b-a22b

# View leaderboard
python test_prompt.py --leaderboard

# Track to MLflow
python test_prompt.py --experiment <name> --mlflow
```

### Examples

```bash
# Test knowledge_graph_complete with Qwen
python test_prompt.py --experiment knowledge_graph_json --model qwen/qwen3-235b-a22b

# Test with GPT-4o and track to MLflow
python test_prompt.py --experiment knowledge_graph_ready --model openai/gpt-4o --mlflow

# Compare all experiments
python test_prompt.py --leaderboard
```

## Auto-Versioning Details

### How It Works

1. **Prompt Hash**: System generates MD5 hash of `system_message + user_template`
2. **Version Lookup**: Checks `experiment_history.csv` for this hash
3. **Same hash** → Use existing version number
4. **New hash** → Increment to next version (v2, v3, etc.)

### Example: Version Detection

```yaml
# prompts.yaml - v1 (hash: 6c2b94cd)
- name: "knowledge_graph_complete"
  system_message: |
    Extract information for rapid scanning...

# Edit the prompt
- name: "knowledge_graph_complete"
  system_message: |
    Extract information for rapid scanning...
    CRITICAL: Capture historical comparisons...  # ← CHANGED

# Next run detects new hash (a7f3e2bd) → auto-creates v2
```

### Viewing Version History

```bash
# Show all versions of an experiment
grep "knowledge_graph_complete" experiment_history.csv

# Output:
# 2025-11-02T18:52:14,knowledge_graph_complete,v1,qwen/qwen3-235b-a22b,91.7,...,6c2b94cd
# 2025-11-02T19:15:22,knowledge_graph_complete,v2,qwen/qwen3-235b-a22b,100.0,...,a7f3e2bd

# Compare v1 vs v2 coverage
grep "knowledge_graph_complete" experiment_history.csv | awk -F',' '{print $3, $5}'
# Output:
# v1 91.7
# v2 100.0
```

## MLflow Integration

### Enabling MLflow

```bash
# Run with MLflow tracking
python test_prompt.py --experiment knowledge_graph_json --mlflow
```

### What Gets Tracked

**Parameters:**
- `experiment`: Experiment name
- `version`: Auto-detected version
- `model`: Model identifier
- `temperature`: Generation temperature
- `max_tokens`: Max token limit
- `prompt_hash`: For version tracking

**Metrics:**
- `coverage_pct`: Vital insights coverage %
- `latency_sec`: Generation time
- `tokens_total`: Total tokens used
- `tokens_prompt`: Prompt tokens
- `tokens_completion`: Completion tokens
- `compression_ratio`: Input/output ratio

**Artifacts:**
- `system_prompt.txt`: Full system message
- `user_template.txt`: User template
- `summary.txt`: Generated summary
- JSON report
- Text report

### Viewing in MLflow UI

```bash
# Start MLflow UI
mlflow ui

# Open http://localhost:5000
# Navigate to experiment: prompt_testing_knowledge_graph_complete
# Compare runs, view artifacts, analyze metrics
```

## Creating New Experiments

### 1. Add to prompts.yaml

```yaml
experiments:
  - name: "my_new_experiment"
    system_message: |
      Your system prompt here...

      Guidelines:
      - What to focus on
      - How to structure output

    user_template: |
      Process this {content_type}:

      Title: {title}

      Content:
      {content}

      [Your format instructions]

    model: "qwen/qwen3-235b-a22b"
    temperature: 0
    max_tokens: 2000
```

### 2. Run It

```bash
python test_prompt.py --experiment my_new_experiment
```

### 3. Iterate

Edit `prompts.yaml` → run again → system auto-versions!

## Best Practices

### 1. Meaningful Experiment Names

```yaml
# Good - describes what's being optimized
- name: "knowledge_graph_complete"
- name: "concise_bullets"
- name: "action_oriented"

# Bad - no information about intent
- name: "test1"
- name: "new_prompt"
- name: "v2"
```

### 2. Incremental Changes

Make small, focused changes between versions so you can identify what improved coverage.

**Good iteration:**
```
v1: Baseline
v2: + "historical comparisons" instruction
v3: + "forward-looking statements" instruction
```

**Bad iteration:**
```
v1: Baseline
v2: Changed everything (can't tell what helped!)
```

### 3. Document Intent with Comments

```yaml
# Knowledge graph complete - Optimized for 100% coverage
# Focus: Historical comparisons, exact numbers, forward-looking statements
# Performance: 100% coverage @ 26s with qwen/qwen3-235b-a22b
- name: "knowledge_graph_complete"
  system_message: |
    ...
```

### 4. Track Learnings

Keep notes on what worked:

```bash
# In your notes or comments
v1 → v2: Added "historical comparisons" instruction → +8.3% coverage
v2 → v3: Increased max_tokens 2000→2500 → no improvement, reverted
v3 → v4: Added "Forward-Looking" section → captured missing insight
v4 → v5: Emphasized "exact numbers" → partial→yes on Navy SEALs insight
```

### 5. Use Leaderboard Regularly

```bash
# Check after each iteration
python test_prompt.py --leaderboard

# Helps you see if changes are actually improving
```

## Common Workflows

### Workflow 1: Optimize for 100% Coverage

**Goal**: Achieve perfect insight capture

```bash
# 1. Baseline
python test_prompt.py --experiment knowledge_graph_ready
# Result: 91.7% coverage

# 2. Analyze gaps
cat reports/knowledge_graph_ready/qwen-*.txt | grep "MISSING INSIGHTS" -A 10

# Output:
# - SOA had similar principles but lost focus by getting caught up in WS-* specs

# 3. Claude analyzes and edits prompts.yaml
# Adds: "Historical comparisons and lessons learned (e.g., how SOA failed)"

# 4. Re-run (auto v2)
python test_prompt.py --experiment knowledge_graph_ready
# Result: 95% coverage (better!)

# 5. Repeat until 100%
```

### Workflow 2: Optimize for Speed

**Goal**: Reduce latency while maintaining coverage

```bash
# 1. Baseline
python test_prompt.py --experiment knowledge_graph_json
# Result: 100% coverage, 26.24s

# 2. Try reducing max_tokens
# Edit prompts.yaml: max_tokens: 2500 → 2000

# 3. Re-run (auto v2)
python test_prompt.py --experiment knowledge_graph_json
# Result: 100% coverage, 21.5s ✅ FASTER!

# 4. Check leaderboard
python test_prompt.py --leaderboard
# Compare v1 vs v2 side-by-side
```

### Workflow 3: Find Best Model

**Goal**: Test multiple models, find optimal cost/quality

```bash
# Test with different models (same prompt)
python test_prompt.py --experiment knowledge_graph_json --model qwen/qwen3-235b-a22b
python test_prompt.py --experiment knowledge_graph_json --model qwen/qwen3-max
python test_prompt.py --experiment knowledge_graph_json --model openai/gpt-4o
python test_prompt.py --experiment knowledge_graph_json --model deepseek/deepseek-r1-0528

# View results
python test_prompt.py --leaderboard

# Output:
# 🏆 #1  knowledge_graph_complete (v1)  qwen/qwen3-235b-a22b  100.0%  26s  3645  ← WINNER!
# 🥇 #2  knowledge_graph_complete (v1)  qwen/qwen3-max        100.0%  38s  2993
# 🥈 #3  knowledge_graph_complete (v1)  openai/gpt-4o          91.7%  15s  3262
```

## Performance Benchmarks

Based on `knowledge_graph_complete` experiment (100% coverage target):

| Model | Coverage | Latency | Tokens | Cost/1K | Value Score |
|-------|----------|---------|--------|---------|-------------|
| **qwen/qwen3-235b-a22b** | **100%** | 26s | 3,645 | **$0.99** | ⭐⭐⭐⭐⭐ Best |
| qwen/qwen3-max | 100% | 38s | 2,993 | $7.71 | ⭐⭐ Expensive |
| mistral-medium-3.1 | 91.7% | 42s | 3,504 | $3.50 | ⭐⭐⭐ OK |
| openai/gpt-4o | 91.7% | 15s | 3,262 | $2.93 | ⭐⭐⭐⭐ Fast |
| gemini-2.5-flash | 83.3% | 6s | 3,056 | $2.93 | ⭐⭐⭐ Speed |

**Recommendation**: `qwen/qwen3-235b-a22b` offers the best balance of perfect coverage, reasonable speed, and lowest cost.

## Troubleshooting

### Empty Summary Generated

**Symptom**: 0 completion tokens, empty summary

**Cause**: Model incompatibility with prompt format (often emoji-heavy prompts with some models)

**Solution**:
1. Simplify prompt (remove emojis)
2. Try different model
3. Check model supports your prompt length

### Version Not Incrementing

**Symptom**: Still showing v1 after editing prompt

**Cause**: Edit didn't actually change the hash (e.g., only YAML comments changed)

**Solution**: Make substantive change to `system_message` or `user_template` content

### Coverage Decreases After Edit

**Symptom**: v2 has lower coverage than v1

**Cause**: Your change removed important instruction or added conflicting guidance

**Solution**: Revert to v1 and try different approach

### MLflow Tracking Fails

**Symptom**: "MLflow not installed" or connection error

**Solution**:
```bash
# Install if missing
uv add mlflow

# Start MLflow server
mlflow ui
```

## Advanced Topics

### Batch Testing Multiple Models

```bash
#!/bin/bash
# test_models.sh

MODELS=(
  "qwen/qwen3-235b-a22b"
  "qwen/qwen3-max"
  "openai/gpt-4o"
  "openai/gpt-4o-mini"
  "deepseek/deepseek-r1-0528"
)

for model in "${MODELS[@]}"; do
  echo "Testing $model..."
  python test_prompt.py --experiment knowledge_graph_json --model "$model"
done

python test_prompt.py --leaderboard
```

### Export History for Analysis

```python
# analyze_history.py
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv('experiment_history.csv')
df['timestamp'] = pd.to_datetime(df['timestamp'])

# Coverage by experiment
print(df.groupby('experiment')['coverage_pct'].mean())

# Latency trend over time
for exp in df['experiment'].unique():
    exp_df = df[df['experiment'] == exp]
    plt.plot(exp_df['timestamp'], exp_df['latency_sec'], label=exp)

plt.legend()
plt.ylabel('Latency (seconds)')
plt.savefig('latency_trends.png')
```

### Compare Two Specific Versions

```bash
# Find report paths for v1 and v2
v1_report=$(grep "knowledge_graph_complete,v1" experiment_history.csv | head -1 | cut -d',' -f11)
v2_report=$(grep "knowledge_graph_complete,v2" experiment_history.csv | head -1 | cut -d',' -f11)

# Compare coverage details
diff <(jq '.coverage_details' "$v1_report") <(jq '.coverage_details' "$v2_report")
```

## FAQ

**Q: How do I reset versioning?**

A: Delete rows from `experiment_history.csv` for that experiment, or delete entire file to start fresh.

**Q: Can I manually set version numbers?**

A: No, versions are auto-detected by hash. To force new versions, rename the experiment (e.g., `my_exp_v2`).

**Q: How do I test on different content?**

A: Modify `test_prompt.py` line 418 to point to a different example file in `eval_dataset/`.

**Q: Can I run experiments in parallel?**

A: Yes, but use different experiment names to avoid CSV write conflicts.

**Q: What if two people edit the same experiment?**

A: System will create separate versions. Use `prompt_hash` column to identify unique prompt versions.

## Integration with Production

### From Testing to Production

1. **Identify Winner**: Use leaderboard to find best performer
2. **Validate**: Review text reports to confirm quality
3. **Extract Prompt**: Get from latest report or `prompts.yaml`
4. **Deploy**: Update production code with winning prompt
5. **Monitor**: Track production metrics, iterate if needed

### Continuous Improvement Loop

```
Production → Collect edge cases → Add to eval_dataset → Test new prompts → Deploy winner → Repeat
```

## Next Steps

1. **Run baseline**: Test all experiments in `prompts.yaml`
2. **Analyze leaders**: Check leaderboard for top performers
3. **Optimize**: Iterate on best candidates to reach 100%
4. **Deploy**: Use winning configuration in production
5. **Monitor**: Track real-world performance, add edge cases to eval dataset

---

**Happy Prompt Engineering! 🚀**

For MLflow-based batch experiments, see [README.md](./README.md)
