# Schema Optimization Analysis

## Current Schema (schemas.py)

### Field Description Analysis

| Field | Current Description | Guidance Level | Optimization Opportunity |
|-------|-------------------|----------------|-------------------------|
| `core_answer` | "One clear sentence..." | ✅ Clear | Could add "synthesizing main thesis" |
| `unique_insights` | "Novel insights..." | ⚠️ Generic | Could specify what makes insight "novel" |
| `CoreInsight.insight` | "Main insight statement" | ❌ Minimal | No extraction guidance |
| `CoreInsight.supporting_facts` | "Supporting evidence with **exact details**" | ✅ Good | Already emphasizes specifics |
| `CoreInsight.quantitative_data` | "**Exact** numbers, formulas..." | ✅ Good | Emphasizes precision |
| `people` | "with **full quote context** (who, when, why)" | ✅ Excellent | Already instructs context capture |
| `formulas_data` | "**Exact** metrics/formulas with numbers..." | ✅ Good | Clear precision requirement |
| `examples_analogies` | "with **specific numbers**..." | ✅ Good | Emphasizes specifics |
| `forward_looking` | "Mentions of future posts..." | ✅ Clear | Good examples |

## Key Findings

### Strengths
1. **Entity fields** have excellent guidance (people, formulas_data, examples_analogies)
2. **Quantitative fields** emphasize "exact", "specific" - aligns with V1 prompt
3. **Bold emphasis** on critical requirements

### Gaps
1. **CoreInsight.insight** - Too generic, no extraction guidance
2. **unique_insights** - Doesn't specify how to identify novelty
3. **No cross-paragraph synthesis guidance** in any field
4. **Missing**: Guidance on connecting related information

## Schema Optimization Strategies

### Strategy S1: Enhanced Field Descriptions
Move V1 prompt instructions INTO schema field descriptions

**Example:**
```python
core_insights: list[CoreInsight] = Field(
    description="Key insights with memory aids, supporting facts with exact numbers, "
                "quantitative data, and connections. Include ALL insights, even supporting ones. "
                "Connect related details mentioned in different parts of content "
                "(e.g., a principle and its numeric specification)."
)
```

**Benefit:** Reduces prompt size, guidance at field level

### Strategy S2: Add Synthesis Fields
Create dedicated fields for cross-content synthesis

**Example:**
```python
class Entity(BaseModel):
    name: str = Field(description="Entity name or principle")
    context: str = Field(description="Context, role, or relevance")
    numeric_specs: str | None = Field(
        None,
        description="If this is a rule/principle, include exact numbers or specifications "
                    "mentioned elsewhere in content (e.g., 'two-pizza rule' → '6-8 members')"
    )
```

**Benefit:** Explicit synthesis instruction without changing extraction strategy

### Strategy S3: Example-Driven Descriptions
Add concrete examples to field descriptions

**Example:**
```python
examples_analogies: list[Entity] = Field(
    default_factory=list,
    description="Examples/cases with specific numbers and what they illustrate. "
                "Example: 'Navy Seals: Work in combat teams of 4 people' "
                "Include BOTH the example AND its numeric specification."
)
```

**Benefit:** Shows model exactly what to capture

### Strategy S4: Minimal Schema (Control)
Strip all descriptions to bare minimum, test if prompt can compensate

**Benefit:** Tests hypothesis that rich schema > rich prompt

## Proposed Experiments

### Experiment Set 2: Schema Variations

Test 4 schema variations with **simplified prompts**:

1. **S1: Rich Descriptions** - Move V1 instructions into field descriptions
2. **S2: Synthesis Fields** - Add `numeric_specs` to Entity, synthesis notes to CoreInsight
3. **S3: Example-Driven** - Add concrete examples to all field descriptions
4. **S4: Minimal Schema** - Bare descriptions + V1 prompt (control)

Each with **3 prompt levels**:
- Ultra-minimal: "Extract information per schema"
- Minimal: V3 minimal prompt
- V1: Current winner prompt

**Total:** 4 schemas × 3 prompts = 12 experiments

### Success Criteria
- Achieve ≥91.7% coverage (match/beat V1)
- Prompt size <500 chars (35% smaller than V1)
- Capture the missing two-pizza insight

## Recommended Approach

**Phase 2A: Quick Win Test (2 experiments)**
1. S2 (Synthesis Fields) + V3 Minimal prompt
2. S1 (Rich Descriptions) + Ultra-minimal prompt

**If either hits 100%:** Ship it
**If not:** Run full 12-experiment matrix

**Phase 2B: Full Matrix** (if needed)
All 12 combinations to find optimal schema + prompt pairing

## Next Step

Create `schema_variations.py` with 4 schema alternatives and run Phase 2A quick tests.
