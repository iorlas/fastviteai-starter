# V2 Experiments - Minimal Prompt Engineering Workshop

**Status:** ✅ Ready to use

Minimal system for iterative prompt and model optimization through Claude-assisted evaluation.

## Design Philosophy

- **Goal:** Find best model + prompt combo for structured extraction (10-20 iterations)
- **Evaluation:** Manual by Claude (qualitative feedback + scores)
- **Workflow:** Run → Show Claude → Get evaluation → Iterate
- **Code:** ~100 lines total, no over-engineering

## Structure

```
v2/
├── experiments.yaml      # Experiment definitions (prompts)
├── schemas.py           # Pydantic V2 models
├── run.py              # Run experiment (~80 lines)
├── eval.py             # Append evaluation (~15 lines)
├── test_data/          # Content + expected insights
│   └── microservices.json
└── runs/               # Timestamped results
```

## Workflow

### 1. Run Experiment

```bash
cd experiments/v2
python run.py knowledge_graph openai/gpt-4o test_data/microservices.json
```

Output:
```
✓ Saved to runs/20251102_143052_knowledge_graph_openai-gpt-4o.json
```

### 2. Show Claude the Result

```bash
cat runs/20251102_143052_knowledge_graph_openai-gpt-4o.json
```

Claude will analyze:
- Which vital insights were found/missing
- Which nice-to-have insights were found/missing
- Coverage percentages
- Quality scores (completeness, accuracy, structure, usefulness)
- Specific prompt improvement suggestions

### 3. Append Evaluation

Claude provides JSON in this format:

```json
{
  "insights_analysis": {
    "found_vital": ["insight 1", "insight 2"],
    "missing_vital": ["insight 3"],
    "found_nice_to_have": ["insight 4"],
    "missing_nice_to_have": [],
    "coverage_vital": 0.67,
    "coverage_total": 0.75
  },
  "quality_scores": {
    "completeness": {"score": 7, "reasoning": "..."},
    "accuracy": {"score": 10, "reasoning": "..."},
    "structure": {"score": 10, "reasoning": "..."},
    "usefulness": {"score": 8, "reasoning": "..."}
  },
  "overall_score": 8.75,
  "prompt_suggestions": [
    "Add 'include specific numbers' to prompt",
    "Emphasize quantitative details"
  ],
  "notes": "Strong extraction but needs emphasis on numbers"
}
```

Append to file:

```bash
python eval.py runs/20251102_143052_knowledge_graph_openai-gpt-4o.json
# Paste JSON, then Ctrl+D
```

### 4. Iterate

Based on Claude's suggestions, modify the prompt:

```bash
vim experiments.yaml
# Add suggested improvements to prompt
```

Then repeat: run → evaluate → improve.

## Test Data Format

Files in `test_data/` contain:

```json
{
  "title": "Article Title",
  "content": "Full article text...",
  "metadata": {
    "type": "article",
    "source": "https://..."
  },
  "expected_insights": {
    "vital": ["Must-have insight 1", "Must-have insight 2"],
    "nice_to_have": ["Optional insight 1"]
  }
}
```

## Adding Experiments

Edit `experiments.yaml`:

```yaml
experiments:
  my_new_experiment:
    system_prompt: |
      Your system instructions...
    user_template: |
      Extract from: {content}
    default_model: openai/gpt-4o
    temperature: 0
    max_tokens: 3000
```

## Supported Models

Currently:
- `openai/gpt-4o`
- `openai/gpt-4o-mini`
- Any OpenAI model

Other providers: Not yet implemented (add to `run.py` if needed)

## File Structure

### Run Files

Each run creates a timestamped JSON:

```json
{
  "timestamp": "20251102_143052",
  "experiment": "knowledge_graph",
  "model": "openai/gpt-4o",
  "test_file": "test_data/microservices.json",
  "content": {"title": "...", "type": "article"},
  "expected_insights": {"vital": [...], "nice_to_have": [...]},
  "output": {...},
  "metadata": {"latency": 16.73, "tokens": 3449},
  "evaluation": null  // ← Filled by eval.py
}
```

After evaluation:

```json
{
  ...
  "evaluation": {
    "insights_analysis": {...},
    "quality_scores": {...},
    "overall_score": 8.75,
    "prompt_suggestions": [...],
    "notes": "..."
  }
}
```

## Why This Design?

✅ **10-20 iterations total** - Manual eval is fine
✅ **Qualitative feedback** - Claude gives actionable suggestions
✅ **Expected insights tracked** - Compare against ground truth
✅ **Iterative debugging** - Each run informs next
✅ **Minimal code** - ~100 lines, no databases, no complexity
✅ **Human-guided** - Best for prompt engineering workshops

## Next Steps

1. Run first experiment
2. Get Claude evaluation
3. Iterate based on feedback
4. After 10-20 runs, you'll have your winner
5. Deploy the winning combo

---

**Created:** 2025-11-02
**Status:** Production ready
