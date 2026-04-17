# Assembler

Assemble a taste model into a complete, deployable skill file. Produces either a discriminative skill (scoring, classification, filtering) or a generative skill (style-matched content generation).

**Input:** Taste model from labeled-inducer or unlabeled-inducer + output type (`discriminative` or `generative`)  
**Output:** Skill file draft (markdown, ready to use as system prompt)

---

## Three Required Ingredients

Every skill file — discriminative or generative — must contain all three:

| Ingredient | What it provides |
|------------|-----------------|
| **Features** | Explicit criteria or style patterns the model uses to reason |
| **Prototypes** | Annotated examples that ground abstract criteria in concrete text |
| **Tools** | Step-by-step instructions, output format, computation rules, parsing |

Do not omit any ingredient. Prototypes without Features leave the model without criteria. Features without Prototypes leave criteria unanchored. Tools without the other two leave the model without judgment.

---

## Discriminative Skill Template

Use when: `output_type = discriminative` (scoring, classification, filtering, ranking)

```markdown
# [Task Name] Evaluation Skill

[1-line evaluator identity + task definition]
[e.g., "You are evaluating essay quality on a 0–1 scale according to the criteria below."]

## Criteria / Rubric                          ← FEATURES
[From S1 rubric or E2 fingerprint adapted for classification]
[Dimension-by-dimension; Excellent / Adequate / Weak descriptions for scoring tasks]
[Per-category distinguishing features for classification tasks]

## Score / Label Distribution                 ← TOOLS (anchor)
[Include only if N ≥ 15; skip entirely for sparse settings]
- Mean: X | Std: Y | Range: [min, max]
- Q10: A | Q25: B | Q50: C | Q75: D | Q90: E
- [Per sub-group stats if multi-population]
- Calibration note: "A score of [Q50] is the median for this population."

## Calibration Examples                       ← PROTOTYPES
[Sorted low → high for scoring / grouped by class for classification]
[Full text — never truncate]

### Example N — [score or label] | [sub-group if applicable]
[FULL input text]
**Why [score/label]:** [2–3 sentence diagnostic annotation citing rubric vocabulary]

## Scoring Instructions                       ← TOOLS (computation + format)
1. Assess the input against each criterion in the rubric above.
2. Compare against calibration examples to anchor your judgment relative to the population.
3. [For multi-dimensional scoring: score each dimension separately, then aggregate.]
4. Output ONLY the following JSON, nothing else:
   {"score": 0.XX}          [for continuous scoring]
   {"category": "LABEL"}    [for classification]

## Response Parsing Notes                     ← TOOLS (parsing)
If the model returns unquoted JSON keys, use regex fallback:
Extract content matching `\{[^}]+\}`, then parse key-value pairs with:
`key\s*[:\s]+([^\s,}]+)` for each expected key.
```

**Prototype simplification:** If N > 15, annotations may be shortened to 1–2 sentences to reduce token consumption. Do not shorten the example text itself — only the annotation.

---

## Generative Skill Template

Use when: `output_type = generative` (style-matched content generation)

```markdown
# [Style Name] Generation Skill

[1-line identity: "You are generating [content type] in the style of [source]."]
[Most distinctive quality of this style in one sentence — grounded in unique mechanisms]

## Style Fingerprint                          ← FEATURES
**Vocabulary and diction:** [5+ specific examples]
**Structure and form:** [sentence rhythm, parallelism, transitions]
  - Opening sentence subject: [e.g., "The task name", "We", "In this paper"]
**Themes and imagery:** [recurring content clusters, cross-line chains]
**Stance and expression:** [how emotion is carried by objects, not stated]
**Unique mechanisms:**
  - [Mechanism A name]: [quote] → [effect]
  - [Mechanism B name]: [quote] → [effect]
  - [Mechanism C name]: [quote] → [effect]
**What this style avoids:** [specific avoidances]

## Reference Examples                         ← PROTOTYPES
[Full text — never truncate]

### Example N
[FULL text]
**Style features present:** [annotation citing specific mechanisms by name]

## Counter-examples                           ← PROTOTYPES (contrast)
[Include if negatives were collected]

### Counter-example K
[FULL text]
**What it lacks:** [annotation — which mechanism is absent, what the author did instead]

## Generation Instructions                    ← TOOLS
1. Study the fingerprint, especially the unique mechanisms.
2. Before writing, choose one mechanism from section 5 to anchor your piece.
3. Draw on *patterns* from the reference examples, not specific words — invent new content.
4. Emotion is always carried by objects. Never state it directly.
5. Check your draft against the counter-examples: if your draft could appear there, revise.
[6. Target length: ~[N] words.]  ← Include ONLY if induction/eval length difference < 20%.
    Omit if lengths differ by more — wrong anchor causes systematic ROUGE drop (~0.038).
7. Output only the generated content, no explanation or preamble.
```

---

## Routing Decision

```
output_type = discriminative  →  use Discriminative Skill Template
output_type = generative      →  use Generative Skill Template

Signal S always → discriminative
Signal E → discriminative or generative (from config.md)
```

---

## Output

Write the assembled skill to `output/<task-name>-skill.md` and pass the path to the evaluator (if dev set exists).
