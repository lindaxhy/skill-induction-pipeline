# Skill Induction — User Guide

This guide explains how to prepare your data and invoke the skill induction pipeline.

## What You'll Get

A skill file (`output/<task-name>-skill.md`) ready to use as a system prompt. The skill encodes your examples' judgment criteria, annotated calibration examples, and step-by-step task instructions — no fine-tuning required.

---

## Step 1: Determine Your Signal Type

| I have... | Signal type |
|-----------|-------------|
| Examples with explicit scores or category labels (essays + grades, resumes + ratings) | **S** |
| A collection of examples I consider "good" — no numeric label | **E** |
| Preference pairs — A was better than B (A/B tests, arena battles) | **E** (treat as curated demonstrations) |
| Behavioral logs (clicks, engagement, accepts) | Convert to **E** (treat top-K engaged items as curated examples) |

## Step 2: Determine Your Output Type

| I want the skill to... | Output type |
|------------------------|-------------|
| Score, classify, filter, or rank new items | **discriminative** |
| Generate new content matching the style or quality | **generative** |

Signal S always produces a discriminative skill.  
Signal E can produce either type.

---

## Step 3: Prepare Your Data Directory

```
my-task/
  config.md          ← Required (see template below)
  examples.csv       ← Your labeled examples (Signal S) or curated examples (Signal E)
  dev.csv            ← Optional: held-out examples for evaluation
```

### Data Format

**Signal S (`examples.csv`):**
```
input_text,score,domain
"The essay text...",0.82,science
"Another essay...",0.41,history
```

**Signal E (`examples.csv` or individual files in `examples/`):**
```
text
"A strong example of the target style..."
"Another example of the target style..."
```
Or: one `.txt` file per example in `examples/`.

---

## Step 4: Write config.md

```markdown
# Task Config

**Signal type**: S
**Output type**: discriminative

## Signal S fields
- Input columns: [input_text]
- Label column: score
- Group column: domain   ← omit if no sub-groups

## Task description
Evaluate essay quality on a 0–1 scale. Higher scores indicate stronger argumentation,
evidence use, and clarity of expression.
```

```markdown
# Task Config

**Signal type**: E
**Output type**: generative

## Signal E fields
- Style name: "Yejin Choi abstract style"
- Paper type: empirical   ← position | empirical | benchmark | training (optional)
- Temporal period: 2020-2024   ← optional

## Task description
Generate NLP paper abstracts in the style of Yejin Choi.
```

---

## Step 5: Invoke the Skill

Point Claude Code at your data directory:

```
Use the skill-induction skill on my-task/
```

The pipeline will:
1. Read `config.md` and your examples
2. Run induction (S or E path)
3. Assemble the skill file
4. Evaluate against baseline if `dev.csv` is present
5. Write the final skill file to `output/<task-name>-skill.md`

---

## Common Pitfalls

| Pitfall | Symptom | Fix |
|---------|---------|-----|
| Truncating examples | Skill underperforms baseline | Never truncate — the pipeline handles full text automatically |
| Global quintile with multi-population data | One group's metric collapses | Set `Group column` in config.md |
| Abstract section 5 mechanisms | Outputs generic; model reverts to direct statements | Re-run on a tighter / more consistent subset of examples so the LLM has a clearer common signal to extract |
| Too many near-duplicate examples | All outputs feel the same | Curate for variety before invoking the pipeline |
| Length anchor mismatch | Systematic ROUGE drop | Leave length unconfigured unless induction/eval examples are closely matched in length |

---

## Validated Results

| Task | Signal | Output | Dataset | Zero-shot | Skill | Metric |
|------|--------|--------|---------|-----------|-------|--------|
| Essay scoring (content) | S | Discriminative | DREsS n=228 | 0.150 | 0.229 | QWK |
| Essay scoring (total) | S | Discriminative | DREsS n=228 | 0.188 | 0.280 | Pearson |
| Resume quality scoring | S | Discriminative | CareerCorpus n=61 | 0.551 | 0.752 | Pearson |
| Resume classification | S | Discriminative | opensporks n=200 | 0.695 | 0.740 | Accuracy |
