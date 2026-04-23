---
name: skill-induction  
description: Build a reusable LLM skill file (system prompt) from a collection of example inputs/outputs. Trigger phrases include "induce a skill from these examples", "build a scorer for [domain]", "create a style-matched generator", "turn this rubric into a skill", "distill scoring criteria from examples", or when the user provides a data directory containing config.md + example CSV / JSON / text files. Input is a data directory with config.md and example files; output is a deployable skill file under the output/ directory, plus (optionally, when dev.csv is provided) an evaluation report comparing the skill against a zero-shot baseline.  
metadata:  
  author: skill-induction-pipeline
---

# Skill Induction

Build a reusable LLM skill file from examples by distilling the task's judgment criteria into a compact, inspectable system prompt.

## Overview

The pipeline follows two axes:

- **Signal type**: what your examples contain — explicit scores/labels (S) or curated demonstrations (E)
- **Output type**: what the induced skill will do — **discriminative** (score, classify, filter) or **generative** (produce style-matched content)

Each induced skill contains three ingredients: **Features** (explicit criteria or style patterns), **Prototypes** (annotated calibration examples), and **Tools** (step-by-step instructions, output format, parsing rules).

## User Data Convention

The user prepares a directory containing:

```
my-task/
  config.md          ← Required: task description and routing parameters
  examples.csv / examples.json / examples/   ← Example data
  dev.csv            ← Optional: dev set for evaluation
```

### config.md format

```markdown
# Task Config

**Signal type**: S  # S = scored/labeled, E = examples-only
**Output type**: discriminative  # discriminative or generative

## Signal S fields (if Signal S)
- Input columns: [col1, col2]
- Label column: score
- Group column: domain  # optional, for multi-population data
- Rubric file: rubric.md  # optional, if annotation guide exists

## Signal E fields (if Signal E)
- Style name: "Yejin Choi abstract style"
- Paper type: empirical  # optional: position, empirical, benchmark, training

## Task description
[Free-text description of the task for context]
```

## Routing Logic

```
Read config.md + data files
  │
  ├─ Signal S → invoke agents/labeled-inducer.md
  │             (rubric + distribution + calibration examples + diagnostic annotations)
  │
  └─ Signal E → invoke agents/unlabeled-inducer.md
  |            (style fingerprint extracted from examples + annotated reference examples)
  └─ invoke agents/assembler.md → output/<task-name>-skill.md
  │
  └─ If dev.csv exists → invoke agents/evaluator.md:
       - Phase 1: compare against zero-shot baseline on dev
       - Phase 2: (optional) ≤3 rounds of targeted refinement
```

**No dev.csv? That's fine.** Skip the evaluator; the assembled skill is the deliverable. Many tasks don't come with a gold-labeled evaluation set, and that's normal.

## Data Scale Awareness


| N     | Regime       | Adaptation                                           |
| ----- | ------------ | ---------------------------------------------------- |
| ≥ 30  | Rich         | Embed full distribution stats (mean, std, Q10–Q90)   |
| 15–29 | Moderate     | Embed simple range statement                         |
| 5–14  | Sparse       | Skip stats; use all examples directly                |
| < 5   | Ultra-sparse | Fingerprint/criteria only; all examples as reference |


## Output

The final skill file is written to `output/<task-name>-skill.md` and is ready to use as a system prompt with no modification.

## Sub-agents


| Agent                         | When to invoke          | Reference                                    |
| ----------------------------- | ----------------------- | -------------------------------------------- |
| `agents/labeled-inducer.md`   | Signal S                | Steps S1–S4                                  |
| `agents/unlabeled-inducer.md` | Signal E                | Steps E1–E4                                  |
| `agents/assembler.md`         | Always, after induction | Skill file assembly                          |
| `agents/evaluator.md`         | Only if `dev.csv` given | Phase 1 (baseline) + Phase 2 (refinement)    |

## Examples

### Example 1 — Essay scoring (Signal S, discriminative)

**User provides:** `my-task/` directory containing:

- `config.md` declaring `Signal: S`, `Output: discriminative`, label column `total_score`, group column `prompt_id`
- `examples.csv` with 228 graded ESL essays (Content, Organization, Language scored 1.0–5.0)
- `dev.csv` with 100 held-out essays (optional)

**User says:** "Induce a scoring skill from these essays"

**What the pipeline does:**

1. Reads config.md, detects Signal S + discriminative.
2. Invokes `agents/labeled-inducer.md` → produces a rubric (from per-group extremes), distribution stats, calibration examples per quintile, and diagnostic annotations.
3. Invokes `agents/assembler.md` → writes `output/essay-scoring-skill.md`.
4. If `dev.csv` present: invokes `agents/evaluator.md` → compares against zero-shot baseline on dev, optionally runs up to 3 rounds of refinement.

**Result:** Deployable system prompt that outputs `{"content": X, "organization": Y, "language": Z}` per new essay.

### Example 2 — Abstract style generation (Signal E, generative)

**User provides:** `my-task/` directory containing:

- `config.md` declaring `Signal: E`, `Output: generative`, style name "Yejin Choi abstract style"
- `examples/` directory with 15 abstracts from target author

**User says:** "Build a style-matched abstract generator from these examples"

**What the pipeline does:**

1. Reads config.md, detects Signal E + generative.
2. Invokes `agents/unlabeled-inducer.md` — extracts a style fingerprint from the examples and selects/annotates reference examples.
3. Invokes `agents/assembler.md` → writes `output/abstract-style-skill.md`.
4. No `dev.csv` is typical for style tasks → skip evaluator.

**Result:** Deployable system prompt that generates style-matched abstracts when given a new paper title + introduction.
