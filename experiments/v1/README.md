# Summarization Experiments

This directory contains two complementary systems for prompt engineering and optimization:

## 🚀 Workflows

### 1. **Rapid Prompt Testing** (Recommended for iteration)
**Script**: `test_prompt.py`
**Docs**: [PROMPT_TESTING_WORKFLOW.md](./PROMPT_TESTING_WORKFLOW.md) | [Quick Reference](./QUICK_REFERENCE.md)

**Features:**
- ⚡ Fast iteration cycle with auto-versioning
- 📊 CSV-based history tracking
- 🎯 Leaderboard comparison view
- 🔄 Conversational optimization with Claude Code
- 💾 Optional MLflow integration

**Best for:**
- Rapid prompt iteration
- Quick model comparisons
- Conversational AI-assisted optimization
- Cost/performance testing

**Quick start:**
```bash
python test_prompt.py --experiment knowledge_graph_json
python test_prompt.py --leaderboard
```

### 2. **Batch Experiments** (Comprehensive evaluation)
**Script**: `summarization_experiments.py`
**Docs**: See sections below

**Features:**
- 📦 Batch processing multiple experiments
- 🔬 Full MLflow tracking and visualization
- 📈 Multiple quality metrics (faithfulness, conciseness, readability)
- 📊 Rich comparative analysis in MLflow UI

**Best for:**
- Comprehensive experiment runs
- Detailed metric tracking
- Production validation
- Team collaboration via MLflow UI

**Quick start:**
```bash
python summarization_experiments.py
mlflow ui
```

## Overview

Both systems allow you to:
- Test different prompts and compare results
- Evaluate multiple models (GPT-4o vs GPT-4o-mini, etc.)
- Track metrics and parameters
- Compare experiments

## Evaluation System

This experiment framework includes an **insights-based evaluation system** that measures how well your summaries preserve key information.

### How It Works

1. **Evaluation Dataset**: Hand-picked content files in `eval_dataset/`
2. **Insights Files**: For each content file, you define key facts that MUST be in the summary
3. **LLM-as-Judge**: GPT-4o evaluates summaries on 4 metrics:
   - **Insights Coverage** (PRIMARY): % of vital insights preserved
   - **Faithfulness**: No hallucinations or fabricated facts
   - **Conciseness**: Efficient language, value per word
   - **Readability**: Clear, professional writing style

### Metrics Priority

**PRIMARY METRIC:**
- `avg_insights_coverage`: % of vital insights captured (0-100%)

**SECONDARY METRICS:**
- `faithfulness/v1/mean`: Factual accuracy score (1-5)
- `conciseness/v1/mean`: Efficiency score (1-5)
- `readability/v1/mean`: Clarity score (1-5)

## Quick Start

### 1. Run experiments on evaluation dataset

Experiments now run on the curated evaluation dataset:

```bash
python experiments/summarization_experiments.py
```

This will:
- Load curated content from `eval_dataset/`
- Run all experiments defined in `prompts.yaml`
- Evaluate summaries using insights-based metrics
- Log results to MLflow (metrics, summaries, evaluation scores)

### 2. View results

Launch the MLflow UI:

```bash
mlflow ui
```

Then open http://localhost:5000 in your browser to compare experiments.

## Configuration

### Using prompts.yaml

Edit `experiments/prompts.yaml` to define your experiments:

```yaml
experiments:
  - name: "my_experiment"
    system_message: |
      Your system prompt here
    user_template: |
      Your user prompt template here
      Use {title}, {content_type}, and {content} placeholders
    model: "openai/gpt-4o"
    temperature: 0.7
    max_tokens: 1000
```

### Environment Variables

The script uses the same environment variables as your Dagster pipeline:

- `OPENAI_API_KEY` - Your OpenRouter API key
- `OPENAI_BASE_URL` - API base URL (default: https://openrouter.ai/api/v1)

These are loaded from your `.env` file.

## Evaluation Dataset

### Structure

```
experiments/eval_dataset/
├── example_001.json           # Content file
└── example_001.insights.json  # Insights for example_001
```

### Content Files

Regular JSON files containing extracted content (same format as `artifacts/html/*.json`):

```json
{
  "url": "https://example.com/article",
  "title": "Article Title",
  "text": "Full article content...",
  "content_type": "html",
  ...
}
```

### Insights Files

For each content file, create a matching `.insights.json` file:

**Format: `{filename}.insights.json`** (e.g., `example_001.insights.json`)

```json
[
  {
    "insight": "Main fact or key point from the article",
    "vitality": "vital"
  },
  {
    "insight": "Supporting detail or secondary information",
    "vitality": "okay"
  }
]
```

### Creating Insights Files

**Guidelines:**

1. **Atomic Facts**: Each insight should be a single, clear fact
2. **Self-Contained**: Insight makes sense on its own
3. **Verifiable**: Can check if it appears in the summary

**Vitality Levels:**

- **"vital"**: MUST be in the summary (core information)
  - Main topic or thesis
  - Key conclusions or findings
  - Critical facts

- **"okay"**: Nice to have (supporting details)
  - Background information
  - Examples or illustrations
  - Additional context

**Example Process:**

1. Read the content file
2. Extract 5-10 key insights
3. Mark 3-5 as "vital", rest as "okay"
4. Save as `{filename}.insights.json`

**Example from `example_001`:**

Content: Article about father building HTML app to teach kids about investing

Insights:
```json
[
  {
    "insight": "Author created an HTML app to teach kids about investing",
    "vitality": "vital"
  },
  {
    "insight": "App is a single HTML file that works as a PWA",
    "vitality": "vital"
  },
  {
    "insight": "Son asked for money instead of birthday gifts to start investing",
    "vitality": "vital"
  },
  {
    "insight": "App shows investment growing daily on smartphone attached to fridge",
    "vitality": "vital"
  },
  {
    "insight": "Purpose is teaching compound interest concepts",
    "vitality": "vital"
  },
  {
    "insight": "App is called D-iNvestments",
    "vitality": "okay"
  },
  {
    "insight": "Uses affordable materials (old phone + $0.90 mount)",
    "vitality": "okay"
  }
]
```

### Adding New Examples

1. Copy a content file to `eval_dataset/`:
   ```bash
   cp artifacts/html/somefile.json eval_dataset/example_002.json
   ```

2. Create insights file:
   ```bash
   # Read example_002.json
   # Extract key insights
   # Save as example_002.insights.json
   ```

3. Run experiments - new example is automatically included!

## Experiment Types

The default experiments include:

### 1. baseline_current
- Matches your current production prompt
- GPT-4o, temperature 0.7
- Balanced summary style

### 2. concise_bullets
- Short, scannable bullet points
- Lower temperature (0.5) for consistency
- Fewer tokens (500 max)

### 3. detailed_analytical
- Comprehensive, nuanced summaries
- Captures context and supporting details
- More tokens (1500 max)

### 4. gpt4o_mini_baseline
- Same prompt as baseline
- Uses GPT-4o-mini instead of GPT-4o
- Compare cost vs quality tradeoff

### 5. action_oriented
- Focuses on practical takeaways
- Actionable insights and recommendations

### 6. technical_academic
- Formal, precise language
- Lower temperature (0.4)
- Academic/research style

## Metrics Tracked

For each experiment, MLflow tracks:

### Parameters
- `experiment_name` - Name of the experiment
- `model` - Model used
- `temperature` - Temperature setting
- `max_tokens` - Max tokens limit
- `content_count` - Number of items processed

### Evaluation Metrics (PRIMARY)
- `avg_insights_coverage` - **PRIMARY METRIC**: % of vital insights preserved (0-100%)
- `avg_all_insights_coverage` - % of all insights (vital + okay) preserved
- `item_N_insights_coverage` - Insights coverage for item N

### Quality Metrics (SECONDARY)
- `faithfulness/v1/mean` - Factual accuracy score (1-5)
- `faithfulness/v1/variance` - Consistency of faithfulness scores
- `conciseness/v1/mean` - Efficiency score (1-5)
- `conciseness/v1/variance` - Consistency of conciseness scores
- `readability/v1/mean` - Clarity score (1-5)
- `readability/v1/variance` - Consistency of readability scores

### Performance Metrics
- `item_N_tokens` - Tokens used for item N
- `item_N_latency_ms` - Latency for item N
- `item_N_compression_ratio` - Summary length / original length
- `avg_tokens_per_summary` - Average tokens across all summaries
- `avg_latency_ms` - Average API latency
- `avg_compression_ratio` - Average compression ratio
- `total_tokens` - Total tokens consumed
- `successful_summaries` - Count of successful summaries
- `failed_summaries` - Count of failures

### Artifacts
- `system_prompt.txt` - System message used
- `user_prompt_template.txt` - User prompt template
- `summary_00_*.txt`, `summary_01_*.txt`, ... - All individual summaries
- `all_summaries_report.md` - Consolidated report with all summaries
- `dataset_contents.csv` - Dataset used for evaluation

## Comparing Results in MLflow UI

### 1. Select experiments

In the MLflow UI:
- Check the boxes next to experiments you want to compare
- Click "Compare" button

### 2. View metrics side-by-side

**PRIMARY**: Compare insights coverage
- `avg_insights_coverage` - How well summaries preserve vital facts

**SECONDARY**: Compare quality scores
- `faithfulness/v1/mean` - Factual accuracy
- `conciseness/v1/mean` - Efficiency
- `readability/v1/mean` - Clarity

**PERFORMANCE**: Compare efficiency
- `avg_tokens_per_summary` - Cost proxy
- `avg_latency_ms` - Speed
- `avg_compression_ratio` - Conciseness

### 3. Read summaries and evaluation details

Click on a run, then:
- **Artifacts tab** → Read `all_summaries_report.md` for all summaries
- **Metrics tab** → See insights coverage per item
- **Datasets tab** → View content used

### 4. Find the best configuration

Look for experiments that:
- **High insights coverage** (>80%) - Preserves key information
- **High quality scores** (>4.0) - Faithful, concise, readable
- **Efficient performance** - Lower tokens/latency when possible
- **Read actual summaries** - Subjective quality check

## Adding New Experiments

### Option 1: Edit prompts.yaml

Add a new entry to `prompts.yaml`:

```yaml
experiments:
  - name: "my_new_experiment"
    system_message: "Your system prompt"
    user_template: "Your user prompt with {placeholders}"
    model: "openai/gpt-4o"
    temperature: 0.7
    max_tokens: 1000
```

### Option 2: Modify the script

Edit `summarization_experiments.py` and add to `get_default_experiments()`:

```python
ExperimentConfig(
    name="my_experiment",
    system_message="...",
    user_template="...",
    model="openai/gpt-4o",
    temperature=0.7,
    max_tokens=1000,
)
```

## Advanced Usage

### Limit content for faster testing

Edit `main()` in `summarization_experiments.py`:

```python
# Only use 5 content items
content_list = load_content_files(artifacts_dir, limit=5)
```

Or modify the sample_size parameter:

```python
run_experiment(
    config=config,
    content_list=content_list,
    sample_size=5,  # Only process 5 items
)
```

### Test a single experiment

Comment out experiments in `prompts.yaml` or modify the script:

```python
experiments = [get_default_experiments()[0]]  # Only run first experiment
```

### Change MLflow experiment name

```python
run_experiment(
    config=config,
    content_list=content_list,
    experiment_name="my_custom_experiment",
)
```

## Workflow Examples

### Iterative Prompt Improvement

1. Start with baseline
2. Run experiment, view results
3. Tweak prompt in `prompts.yaml`
4. Run again with new name
5. Compare in MLflow UI
6. Iterate until satisfied

### Model Cost Comparison

1. Create two experiments with identical prompts
2. Use different models (gpt-4o vs gpt-4o-mini)
3. Compare `avg_tokens` and read sample summaries
4. Calculate cost difference
5. Choose based on quality/cost tradeoff

### A/B Testing Prompt Styles

1. Create variations (concise vs detailed)
2. Run all experiments
3. Compare `compression_ratio` metrics
4. Read sample artifacts
5. Pick style that fits your use case

## Troubleshooting

### No content files found

Run the Dagster pipeline first:
```bash
dagster job execute -f manual_pipeline -c manual_links.txt
```

### API key errors

Check your `.env` file has:
```
OPENAI_API_KEY=your_key_here
OPENAI_BASE_URL=https://openrouter.ai/api/v1
```

### MLflow UI not starting

Ensure MLflow is installed:
```bash
uv sync
```

### Experiments not appearing in UI

Check you're in the project root when running `mlflow ui`.

MLflow stores data in `./mlruns/` by default.

## Files

- `summarization_experiments.py` - Main experiment runner
- `evaluator.py` - Insights-based evaluation logic
- `prompts.yaml` - Experiment configurations
- `eval_dataset/` - Curated evaluation examples
  - `example_001.json` - Content file
  - `example_001.insights.json` - Ground truth insights
- `README.md` - This file

## Next Steps

After finding your best prompt:

1. Note the experiment name and configuration
2. Update `dagster_project/assets/summarization.py` with the winning prompt
3. Deploy to production

Or keep both:
- Production: stable, proven prompt
- Experiments: continuous testing and improvement
