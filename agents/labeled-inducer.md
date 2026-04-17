# Signal S Inducer

Induce a taste model from scored or labeled examples. Implements Steps S1–S4 of the skill induction pipeline.

**Input:** Labeled examples (text + score or category label), optional rubric file, optional group column  
**Output:** Taste model `{rubric, stats, examples, annotations}`

---

## S1 — Rubric Extraction

**If rubric file provided in config:**
- Extract and clean: remove example-specific references, keep per-dimension criteria
- For scoring tasks: preserve Excellent / Adequate / Weak descriptions per dimension
- For classification tasks: preserve per-category distinguishing features

**If no rubric → induce from data (1 LLM call):**

```
System: You are an expert [domain] rubric writer.
User:   Here are the highest-scoring examples:
        [top quartile, labeled "High example N"]
        Here are the lowest-scoring examples:
        [bottom quartile, labeled "Low example N"]
        Identify criteria that distinguish high from low quality.
        Write a dimension-by-dimension rubric in natural language.
        For each dimension: describe what Excellent, Adequate, and Weak look like.
        Be specific — cite observable surface features, not vague adjectives.
```

For classification tasks: provide 2–3 examples per class instead of top/bottom quartile.

**Multi-population warning:** If sub-group mean score differences > 0.2, show per-group extremes separately:
```
User:   Here are the best and worst examples from Group A:
        [Group A high, Group A low]
        Here are the best and worst examples from Group B:
        [Group B high, Group B low]
        Write criteria that generalize across groups — focus on specificity, depth,
        and impact relative to group norms. Do NOT encode group-specific vocabulary as quality.
```

---

## S2 — Distribution Embedding

Compute from training set and embed in taste model:
- Overall: mean, std, range, Q10 / Q25 / Q50 / Q75 / Q90
- Per sub-group (if group column present): mean, std
- Calibration note: "A score of X is genuinely below average for this population"
- For classification: class distribution (%)

**Skip entirely if N < 15.** Use instead: "Examples in this dataset range from [min] to [max]."

---

## S3 — Calibration Example Selection

> **Critical rule: NEVER truncate examples. Use full text always.**
> Truncation breaks calibration — rhythm, closure patterns, and structural choices in the full text are essential for accurate score anchoring.

**Single-population:**
- Scoring tasks: 2–3 examples per quintile (10–15 total), sorted low → high
- Classification tasks: 1–2 examples per class

**Multi-population (sub-groups with divergent score distributions):**
- Select at Q20 and Q80 **within each group's own distribution** → `N_groups × 2` examples
- Do NOT use global quintiles: if Group A mean=0.44 and Group B mean=0.81, global bottom-20% is entirely Group A, leaving it with no high anchor

**Sparse (N < 15):** Use all examples, sorted by score or grouped by class.

---

## S4 — Diagnostic Annotation (1 LLM call)

```
System: You are an expert [domain] annotator.
        Write 2–3 sentence explanations for why each example received its label/score,
        citing specific observable features using rubric vocabulary.
        Do not use vague adjectives — name the specific evidence in the text.
User:   [rubric ≤ 1500 chars]

        [All N examples in numbered blocks:]
        Example 1 — Score: X
        [full text]

        Example 2 — Score: Y
        [full text]
        ...
Output: JSON {"1": "annotation", "2": "annotation", ..., "N": "annotation"}
```

**Response parsing fallback** (LLMs sometimes return unquoted JSON keys):
```python
match = re.search(r'\{[^}]+\}', response, re.DOTALL)
if match:
    blob = match.group()
    try:
        result = json.loads(blob)
    except json.JSONDecodeError:
        result = {}
        for key in expected_keys:
            m = re.search(rf'{key}\s*[:\s]+([^\s,}}]+)', blob)
            if m:
                result[key] = m.group(1).strip('"\'')
```

---

## Output Format

Return a structured taste model to the assembler:

```
TASTE MODEL (Signal S)
rubric: [full rubric text]
stats: {mean: X, std: Y, Q10: A, Q25: B, Q50: C, Q75: D, Q90: E, per_group: {...}}
examples: [list of selected examples with scores, full text, group label if applicable]
annotations: {"1": "...", "2": "...", ...}
data_scale: rich | moderate | sparse | ultra-sparse
output_type: discriminative  [always for Signal S]
```
