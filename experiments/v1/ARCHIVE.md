# V1 Experiments - Archive

**Status:** Archived on 2025-11-02

This is the original experiments pipeline that successfully demonstrated structured JSON extraction from content using OpenAI's beta API.

## 🎯 What Was Achieved

### Core Functionality
- ✅ Structured JSON extraction using OpenAI beta API (`beta.chat.completions.parse`)
- ✅ Pydantic schema validation (`KnowledgeGraphSummary`)
- ✅ Hand-crafted insights evaluation (LLM-as-judge)
- ✅ Auto-versioning based on prompt hash (MD5)
- ✅ CSV-based experiment tracking
- ✅ Multiple model support (GPT-4o, Mistral Medium 3.1, Qwen)

### Results Achieved
- **100% coverage** on microservices article with multiple models
- **GPT-4o**: 100% coverage, 16.73s, 3449 tokens
- **Mistral Medium 3.1**: 100% coverage, 21.83s, 3395 tokens
- Validated programmatic JSON processing with Pydantic

## 📊 Final Experiment Configuration

### Single Experiment: `knowledge_graph_json`
```yaml
system_message: Extract information into structured JSON
model: openai/gpt-4o
temperature: 0
max_tokens: 3000
```

### Pydantic Schema
```python
class KnowledgeGraphSummary(BaseModel):
    core_answer: str
    unique_insights: list[str]
    classification: Classification
    core_insights: list[CoreInsight]
    knowledge_graph_ascii: str
    people: list[Entity]
    organizations: list[Entity]
    concepts: list[Entity]
    formulas_data: list[Entity]
    examples_analogies: list[Entity]
    forward_looking: list[str]
    memory_aids: MemoryAids
```

## 🔧 Technical Stack

- **OpenAI Python SDK**: `beta.chat.completions.parse`
- **Pydantic V2**: Schema definition and validation
- **structlog**: Structured logging
- **MLflow**: Optional experiment tracking
- **CSV**: Simple experiment history

## 🎓 Lessons Learned

### What Worked Well

1. **OpenAI Beta API Integration**
   - Direct Pydantic schema validation was clean
   - Type-safe responses with `.parsed` attribute
   - No manual JSON parsing needed

2. **Auto-Versioning**
   - MD5 hash of prompts for version detection
   - Automatic version increment on prompt changes
   - Clean experiment tracking

3. **Simple CSV History**
   - Easy to analyze with command-line tools
   - No database overhead
   - Human-readable format

4. **Leaderboard View**
   - Quick comparison of experiments
   - Visual emoji indicators for performance

### Problems & Pain Points

1. **OpenRouter Compatibility Issues**
   - Started with OpenRouter, had to switch to OpenAI
   - Beta API only works with OpenAI
   - Not portable across providers

2. **Limited Model Support**
   - Beta API restricted to OpenAI models
   - Could only test Mistral through OpenAI
   - Qwen models inaccessible via beta API

3. **Manual Schema Maintenance**
   - Pydantic schema had to be manually defined
   - Changes required code updates
   - Schema evolution was difficult

4. **Single Test File**
   - `eval_dataset/example_002.json` only
   - Not testing across diverse content
   - No batch evaluation

5. **Insights as Ground Truth**
   - Hand-crafted insights were brittle
   - Required manual creation for each test file
   - Subjective "vital" vs "nice-to-have" classification

6. **Tight Coupling**
   - `test_prompt.py` mixed concerns (run, eval, report)
   - `evaluator.py` embedded prompt strings
   - Hard to modify or extend

7. **Report Fragmentation**
   - JSON reports
   - Text reports
   - CSV history
   - MLflow (optional)
   - No single source of truth

8. **No Iteration Support**
   - Each run was independent
   - No ability to refine prompts based on failures
   - Manual inspection of missing insights

## 🚀 Recommendations for V2

### Must Have

1. **Provider Agnostic**
   - Support OpenAI, OpenRouter, Anthropic, etc.
   - Fallback to JSON mode + manual parsing for non-OpenAI
   - Unified interface across providers

2. **Multiple Test Files**
   - Batch evaluation across diverse content
   - Different content types (articles, videos, technical docs)
   - Statistical significance

3. **Better Ground Truth**
   - LLM-generated reference summaries
   - Multiple quality dimensions
   - Automatic ground truth generation

4. **Cleaner Architecture**
   - Separate concerns (runner, evaluator, reporter)
   - Plugin architecture for evaluators
   - Composable components

5. **Iteration Support**
   - Identify failure modes automatically
   - Suggest prompt improvements
   - A/B testing framework

### Nice to Have

1. **Schema Evolution**
   - Dynamic schema generation
   - Schema versioning
   - Migration tools

2. **Cost Tracking**
   - Per-run cost calculation
   - Budget alerts
   - Cost optimization suggestions

3. **Richer Visualization**
   - Web dashboard
   - Comparison views
   - Trend analysis

4. **Collaborative Features**
   - Share experiments
   - Comment on runs
   - Voting on best prompts

## 📁 File Reference

### Core Files
- `test_prompt.py` - Main test runner (20K lines)
- `evaluator.py` - LLM-as-judge insights evaluation
- `schema.py` - Pydantic models for JSON schema
- `prompts.yaml` - Experiment configurations
- `experiment_history.csv` - Run history

### Documentation
- `README.md` - Main documentation
- `QUICK_REFERENCE.md` - Command cheatsheet
- `PROMPT_TESTING_WORKFLOW.md` - Detailed workflow guide

### Data
- `eval_dataset/` - Test content + insights
- `reports/` - Experiment outputs
- `mlruns/` - MLflow artifacts (optional)

## 🔗 Migration to V2

V2 should be able to import v1 experiment history for comparison:

```python
# V2 code should support:
from v1.experiment_history import load_v1_history

v1_runs = load_v1_history()
# Compare v2 results against v1 baseline
```

---

**Archive Date:** 2025-11-02
**Last Run:** knowledge_graph_json v2 with mistralai/mistral-medium-3.1
**Final Coverage:** 100.0%
