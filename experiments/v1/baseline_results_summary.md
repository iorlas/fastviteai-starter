# Baseline Prompt Testing Results

## Objective
Test the "technical_academic" baseline prompt across 6 different models to achieve 100% insights coverage on example_002 (microservices article).

## Test Configuration
- **Temperature**: 0 (deterministic)
- **Max tokens**: 1200
- **Target example**: example_002.json (The Real Success Story of Microservices Architectures)
- **Total insights**: 12 vital insights

## Results Summary

| Model | Coverage | Found | Latency | Tokens | Status |
|-------|----------|-------|---------|--------|--------|
| **mistralai/mistral-medium-3.1** | **100.0%** ✅ | 12/12 | 13.40s | 2820 | **SUCCESS** |
| google/gemini-2.5-flash | 75.0% | 9/12 | 4.88s | 2287 | Success |
| openai/gpt-4o | 75.0% | 9/12 | 10.82s | 2028 | Success |
| z-ai/glm-4.6 | 75.0% | 9/12 | 50.61s | 3746 | Success |
| minimax/minimax-m2:free | ERROR | - | - | - | Parsing failed |
| z-ai/glm-4.6:exacto | ERROR | - | - | - | Invalid JSON |

## Key Findings

### 🎉 Achievement: 100% Coverage
**mistralai/mistral-medium-3.1** achieved perfect 100% coverage with the baseline "technical_academic" prompt - no prompt engineering required!

### Model Performance Analysis

**Top Performer: Mistral Medium 3.1**
- Only model to capture all 12 insights
- Reasonable speed (13.40s)
- Good token efficiency (2820 tokens)
- Successfully included all missing details that other models skipped

**Fast but Incomplete: Gemini 2.5 Flash**
- Fastest response (4.88s)
- 75% coverage
- Missing: Jeff Bezos quote, Navy Seals, OpenShift/fabric8io

**Balanced: GPT-4o**
- 75% coverage
- Captured OpenShift/fabric8io (which Gemini missed)
- Missing: Communication formula, Jeff Bezos quote, Navy Seals

**Slow: GLM-4.6**
- 75% coverage
- Slowest response (50.61s)
- Highest token usage (3746 tokens)
- Same missing insights as Gemini

**Failed: Minimax & GLM-4.6:exacto**
- Both failed due to structured output incompatibility
- These models don't properly support OpenAI's beta.chat.completions.parse() API
- Returned text instead of JSON, causing Pydantic validation errors

## Missing Insights Pattern (75% models)

All 75% coverage models missed similar insights:
1. **Jeff Bezos quote**: "Communication is terrible" (consistently missed)
2. **Navy Seals teams**: Work in combat teams of 4 (consistently missed)
3. **OpenShift/fabric8io**: Future tooling discussion (missed by 2/3 models)
4. **Communication formula**: (n * n-1) / 2 (missed by GPT-4o only)

These tend to be:
- Specific quotes/numbers
- Supporting examples vs. main arguments
- Forward-looking references

## Baseline Prompt Used

```
System: You are an academic researcher who creates precise, technical summaries.
Use formal language, cite specific claims, and maintain objectivity.

User: Provide a technical summary of this {content_type}:

Title: {title}

Content:
{content}

Include:
- Central hypothesis or main claim
- Key methodologies or approaches
- Primary findings or results
- Conclusions and implications
```

## Recommendations

### Option 1: Use Mistral Medium 3.1 (Current Winner)
- Already achieves 100% coverage
- No prompt engineering needed
- Good balance of speed and quality

### Option 2: Improve Other Models to 100%
If we want to improve Gemini/GPT-4o/GLM-4.6 from 75% to 100%, we could:
- Add explicit instructions to capture specific quotes and numbers
- Emphasize supporting examples and anecdotes
- Request inclusion of forward-looking statements

### Option 3: Investigate Why Mistral Succeeded
Analyze what Mistral did differently that allowed it to capture all insights while other models missed the same 3-4 items.

## Next Steps

Decision needed:
1. ✅ Accept 100% achievement with Mistral Medium 3.1 (DONE)
2. Attempt to improve other models to 100%
3. Analyze Mistral's approach for insights
4. Run full experiments with Mistral to validate consistency across more examples
