---
name: skill-induction
description: Use when building a reusable LLM skill file from a collection of examples. Accepts scored/labeled examples (Signal S) or curated demonstrations (Signal E); produces discriminative skills (scoring, classification) or generative skills (style-matched generation). User prepares a data directory with config.md and example files.
---

# Skill Induction

Build a reusable LLM skill file from examples by distilling human judgment into a compact, inspectable system prompt — no fine-tuning required.

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
  negatives/         ← Optional (Signal E only): counter-examples
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
- Temporal period: 2020-2024  # optional
- Negatives available: true

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
                (style fingerprint + annotated reference examples)
                [PAUSE: human review of section 5 before continuing]
  │
  └─ Both paths → invoke agents/assembler.md
                  (taste model × output type → skill file draft)
  │
  └─ If dev.csv exists → invoke agents/evaluator.md
                         (baseline comparison + iterative refinement, ≤3 rounds)
  │
  └─ Write final skill file to output/<task-name>-skill.md
```

## Data Scale Awareness

| N | Regime | Adaptation |
|---|--------|------------|
| ≥ 30 | Rich | Embed full distribution stats (mean, std, Q10–Q90) |
| 15–29 | Moderate | Embed simple range statement |
| 5–14 | Sparse | Skip stats; use all examples directly |
| < 5 | Ultra-sparse | Fingerprint/criteria only; all examples as reference |

## Output

The final skill file is written to `output/<task-name>-skill.md` and is ready to use as a system prompt with no modification.

## Sub-agents

| Agent | When to invoke | Reference |
|-------|---------------|-----------|
| `agents/labeled-inducer.md` | Signal S | Steps S1–S4 |
| `agents/unlabeled-inducer.md` | Signal E | Steps E1–E4 |
| `agents/assembler.md` | Always, after induction | Skill file assembly |
| `agents/evaluator.md` | When dev.csv is present | Phase 3–4 evaluation |
