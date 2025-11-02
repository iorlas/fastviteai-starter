# Migration from V1 to V2

This document explains the transition from v1 to v2 experiments.

## 📅 Timeline

- **V1 Development**: Started ~2025-11-01
- **V1 Archive**: 2025-11-02
- **V2 Design**: 2025-11-02 (current)

## 🎯 Why V2?

V1 successfully demonstrated structured JSON extraction with 100% coverage across multiple models. However, several limitations emerged:

1. **OpenAI-only** - Beta API restricted to OpenAI models
2. **Single test file** - Not statistically significant
3. **Manual insights** - Brittle ground truth
4. **Tight coupling** - Hard to extend or modify
5. **No iteration** - Manual failure analysis

V2 addresses these issues with a redesigned architecture.

## 📂 Directory Structure

```
experiments/
├── README.md           # Overview of versions
├── MIGRATION.md        # This file
├── v1/                 # Archived working implementation
│   ├── ARCHIVE.md      # V1 lessons learned
│   ├── README.md       # V1 documentation
│   ├── test_prompt.py  # Main runner (working)
│   ├── evaluator.py    # LLM-as-judge (working)
│   ├── schema.py       # Pydantic models (working)
│   ├── prompts.yaml    # Experiments config (working)
│   ├── eval_dataset/   # Test content + insights
│   ├── reports/        # Generated reports
│   └── experiment_history.csv  # Run history
└── v2/                 # Next generation (in design)
    ├── README.md       # V2 design document
    └── (TBD)
```

## 🔄 Using V1 (Still Works!)

V1 is fully functional and archived for reference:

```bash
cd experiments/v1

# Run an experiment
python test_prompt.py --experiment knowledge_graph_json

# View leaderboard
python test_prompt.py --leaderboard

# Run with different model
python test_prompt.py --experiment knowledge_graph_json --model mistralai/mistral-medium-3.1
```

## 🚀 Starting V2 Development

V2 is a clean slate based on v1 learnings:

```bash
cd experiments/v2

# Follow v2/README.md for design and implementation plan
```

## 📊 V1 Final Stats

Last successful runs:

| Model | Coverage | Latency | Tokens |
|-------|----------|---------|--------|
| openai/gpt-4o | 100.0% | 16.73s | 3449 |
| mistralai/mistral-medium-3.1 | 100.0% | 21.83s | 3395 |
| qwen/qwen3-235b-a22b | 100.0% | 26.24s | 3645 |

All experiments used structured JSON extraction with the `knowledge_graph_json` experiment.

## 🎓 Key Learnings from V1

### What to Keep
1. ✅ Pydantic schema validation
2. ✅ Auto-versioning based on prompt hash
3. ✅ Simple CSV history tracking
4. ✅ Leaderboard visualization
5. ✅ Structured JSON output

### What to Change
1. ❌ OpenAI-only → Multi-provider support
2. ❌ Single test file → Batch evaluation
3. ❌ Manual insights → Auto ground truth
4. ❌ Monolithic code → Modular architecture
5. ❌ No iteration → Automatic failure analysis

## 🔗 Compatibility

V2 should maintain compatibility with v1 data:

```python
# V2 will support importing v1 history
from v2.importers import import_v1_history

v1_data = import_v1_history("../v1/experiment_history.csv")
# Use v1 baseline for comparison
```

## 📚 Documentation

- **V1 Archive**: `v1/ARCHIVE.md` - Complete v1 documentation and lessons
- **V2 Design**: `v2/README.md` - V2 architecture and roadmap
- **Overview**: `README.md` - High-level version comparison

## 🤔 Which Version to Use?

### Use V1 if:
- You need working code right now
- You're using OpenAI models only
- You're testing prompts on a single content piece
- You need a simple, proven solution

### Use V2 when:
- It's implemented (currently in design)
- You need multi-provider support
- You want batch evaluation
- You need advanced features (cost tracking, iteration, etc.)

## 🛠️ Contributing to V2

V2 is in the design phase. See `v2/README.md` for:
- Architecture design
- Development roadmap
- Technical decisions
- Getting started guide

---

**Migration Date**: 2025-11-02
**V1 Status**: Archived (still functional)
**V2 Status**: Design phase
