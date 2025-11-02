# Experiments Directory

This directory contains different iterations of the experiments pipeline.

## 📁 Structure

### v1/ - Original Experiments (Archived)
The initial implementation of the summarization experiments pipeline.

**Key Features:**
- OpenAI beta API structured outputs
- JSON schema extraction with Pydantic
- Hand-crafted insights evaluation
- CSV-based experiment tracking
- Single experiment: `knowledge_graph_json`

**Location:** `v1/README.md` for detailed documentation

**Status:** ✅ Archived - Working, but lessons learned led to v2

---

### v2/ - Next Generation (Current)
Improved experiments pipeline based on v1 learnings.

**Location:** `v2/README.md` for detailed documentation

**Status:** 🚧 In Development

---

## 🔄 Migration Guide

If you need to reference v1 experiments:
```bash
cd v1
python test_prompt.py --leaderboard
```

For new experiments, work in v2:
```bash
cd v2
# Follow v2/README.md for setup
```

---

## 📚 Version History

| Version | Status | Focus |
|---------|--------|-------|
| v1 | Archived | Structured JSON extraction with OpenAI beta API |
| v2 | Current | TBD - Design based on v1 learnings |
