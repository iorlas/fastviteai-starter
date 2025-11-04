# UI Testing Guide

## Changes Made

Added display of two new fields to the Streamlit UI:

### Compact View
- Added `why_this_matters` field below core answer with 💎 icon

### Detailed View
- Added `why_this_matters` with green success box (💎 icon)
- Added `expert_opinion` with italic formatting (🎓 icon)

## Testing

### 1. Test with Existing Data (Old Schema)
```bash
cd /Users/iorlas/Projects/my/ailabbrains
uv run streamlit run ui/app.py
```

**Expected:**
- ✅ UI loads without errors
- ✅ Old summaries display (without new fields)
- ✅ No crashes from null values

### 2. Generate New Summaries with Updated Schema

To see the new fields in action, we need to regenerate summaries:

```bash
# Option A: Run full pipeline
dagster dev

# Option B: Use experiment runner (faster for testing)
python experiments/v3/run.py \
  --test-case experiments/v3/test_cases/case_001.json \
  --model "mistralai/mistral-medium-3.1" \
  --system-prompt experiments/v3/prompts/system_baseline.txt \
  --user-prompt experiments/v3/prompts/user_baseline.txt

# Copy to silver layer for UI display
# (Manual step - would need to integrate with pipeline)
```

## UI Preview

### Compact Card View
```
┌─────────────────────────────────────┐
│ ### Article Title                   │
│ #Topic • Type • Depth               │
│                                     │
│ 🔗 domain.com                       │
│ 📝 Core answer sentence here...    │
│ 💎 Why: Explanation of value...    │
│                                     │
│ 💡 3 Unique Insights                │
└─────────────────────────────────────┘
```

### Detailed View
```
▼ Article Title - domain.com
──────────────────────────────────────
📝 Core Answer: One sentence summary
──────────────────────────────────────
💎 Why This Matters: 2-3 sentences...
──────────────────────────────────────
🎓 Expert Opinion: Evaluation text...
──────────────────────────────────────
[Tabs: 💡 Insights | 🎯 Details | ...]
```

## Current Status

- ✅ UI code updated
- ✅ Handles null values gracefully
- ⏳ Need new summaries to see fields in action
- ⏳ Pipeline needs to be run with updated schema

## Next Steps

1. Run UI to verify no breaking changes
2. Either:
   - Run Dagster pipeline to regenerate all summaries, OR
   - Manually create/copy a test summary with new fields
3. Verify new fields display correctly
