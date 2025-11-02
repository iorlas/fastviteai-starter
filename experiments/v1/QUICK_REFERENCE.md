# Prompt Testing Quick Reference

## 🚀 Common Commands

```bash
# Run experiment
python test_prompt.py --experiment knowledge_graph_json

# Run with different model
python test_prompt.py --experiment knowledge_graph_json --model qwen/qwen3-max

# View leaderboard
python test_prompt.py --leaderboard

# Track to MLflow
python test_prompt.py --experiment knowledge_graph_json --mlflow
```

## 📋 Workflow Cheat Sheet

### Optimization Loop

1. **Run** → `python test_prompt.py --experiment X`
2. **Analyze** → Check coverage %, read missing insights
3. **Edit** → Modify `prompts.yaml`
4. **Repeat** → Run again (auto v2)
5. **Compare** → `python test_prompt.py --leaderboard`

### Quick Analysis

```bash
# View all runs for an experiment
grep "knowledge_graph_json" experiment_history.csv

# Best coverage overall
sort -t',' -k5 -rn experiment_history.csv | head -5

# Compare two versions
grep "knowledge_graph_json,v1" experiment_history.csv
grep "knowledge_graph_json,v2" experiment_history.csv
```

## 📊 Output Files

```
reports/{experiment}/
├── {model}_{version}_{timestamp}.json   # Structured data
└── {model}_{version}_{timestamp}.txt    # Human-readable

experiment_history.csv                    # All runs tracked
```

## 🎯 Coverage Status

- ✅ **yes** - Insight fully captured
- ⚠️ **partial** - Mentioned but incomplete
- ❌ **no** - Missing from summary

## 🏆 Leaderboard Symbols

- 🏆 100% coverage
- 🥇 90-99% coverage
- 🥈 75-89% coverage
- 🥉 <75% coverage

## 💡 Tips

**Auto-Versioning:**
- Edit `prompts.yaml` → next run auto-creates v2
- Same prompt = same version number
- Track changes via `prompt_hash` column

**Best Practices:**
- Make incremental changes
- Check leaderboard after each iteration
- Document what changed in YAML comments

**Model Selection:**
| Priority | Metric | Best Choice |
|----------|--------|-------------|
| Coverage | 100% | qwen/qwen3-235b-a22b |
| Speed | <10s | gemini-2.5-flash |
| Cost | <$1/1K | qwen/qwen3-235b-a22b |

## 🔧 Troubleshooting

| Problem | Solution |
|---------|----------|
| Empty summary | Try different model or simplify prompt |
| Version not incrementing | Edit actual prompt content, not comments |
| Coverage decreased | Revert and try different approach |
| MLflow error | Run `uv add mlflow && mlflow ui` |

## 📖 Full Docs

See [PROMPT_TESTING_WORKFLOW.md](./PROMPT_TESTING_WORKFLOW.md) for complete guide.
