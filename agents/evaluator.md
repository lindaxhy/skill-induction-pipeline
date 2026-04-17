# Evaluator

Evaluate an induced skill against a baseline and apply targeted iterative refinement.

**Input:** Skill file path + dev set (`dev.csv`) + signal type + output type  
**Output:** Refined skill file (same path, updated in place; max 3 refinement rounds)

---

## Baseline Comparison

Always compare the induced skill against a zero-shot baseline using the same dev set.

| Signal / Output | Baseline | Test |
|-----------------|----------|------|
| Signal S → Discriminative | Zero-shot (task instruction only, no system prompt) | Skill system prompt |
| Signal E → Generative | Zero-shot generation | Skill-guided generation |
| Signal E → Discriminative | Zero-shot (task instruction only) | Skill system prompt |

Run both conditions on the dev set before examining any outputs. Report:
- **Discriminative:** primary metric (see table below) + secondary metric
- **Generative:** human judgment on 5–10 outputs (yes/partially/no) + optional blind comparison

### Metric Selection (Discriminative, Signal S)

| Output type | Primary metric | Secondary |
|-------------|---------------|-----------|
| Continuous (0–1, 0–100) | Pearson r | MAE |
| Ordinal (1–5 with half steps) | QWK | Pearson |
| Multi-dimensional ordinal | Per-dimension QWK | Total Pearson |
| Binary | F1 | Accuracy, Precision, Recall |
| Multi-class | Macro-F1 | Per-class F1, Accuracy |

---

## Discriminative Skill — Diagnosis and Fix Table

When the skill underperforms the baseline, diagnose using this table (one fix per round):

| Observation | Diagnosis | Fix |
|-------------|-----------|-----|
| Primary metric improves | Skill is effective | Ship it |
| pred_mean systematically off | Reference frame mismatch | Strengthen distribution stats; add extreme calibration examples |
| pred_std too narrow (hedging) | Model averages toward midpoint | Add more examples at both ends of the score range |
| One sub-group metric drops | Group bias in rubric or examples | Per-group stratified examples; add domain note to rubric clarifying group norms |
| One class consistently worse | Rubric gap for that class | Add 1–2 targeted examples for the underperforming class |
| Skill hurts on all metrics | Wrong examples or rubric | Re-induce from scratch; check domain mismatch between examples and dev set |

---

## Generative Skill — Refinement Triggers

**Level 1 (required): Human judgment**

Generate 5–10 outputs with the skill. For each output, rate:
- **Yes** — feels like it belongs alongside the reference examples
- **Partially** — some mechanisms present, but misses depth or avoidances
- **No** — generic; missing the style entirely

Collect specific observations on what is missing.

**Level 2 (recommended for version comparison): Blind comparison**

Save outputs from the current skill version and the previous version (or zero-shot) to separate files. Compare blindly (without knowing which version produced which output) using these rubric dimensions:
- Does it use the unique mechanisms from section 5?
- Does it observe the avoidances?
- Does it avoid direct emotional statements?
- Does it avoid recycled phrases from the reference examples?

**Refinement triggers:**

| Observation | Fix |
|-------------|-----|
| "Generic" — sounds like any [domain] content | Strengthen fingerprint section 5; add contrasting negatives |
| "Missing [specific characteristic]" | Add one targeted example that exemplifies it |
| "Mimics surface but misses depth" | Add a counter-example of surface mimicry specifically |
| "All outputs feel like each other" | Increase example variety; remove near-duplicate positives |
| "Wrong dimension prioritized" | Revise fingerprint section 5 weighting; rephrase mechanism descriptions |

---

## Iteration Loop

```
Round 1:
  Evaluate skill on dev set
  If primary metric improves (discriminative) or ≥60% "yes/partially" (generative): STOP
  Apply most impactful fix from diagnosis table / refinement triggers (1 LLM call)
  Update skill file

Round 2:
  Re-evaluate
  If gain < 0.02 on primary metric (discriminative) or qualitative plateau (generative): STOP
  Apply next most impactful fix (1 LLM call)
  Update skill file

Round 3:
  Re-evaluate
  Report final metrics regardless of gain
  STOP — do not exceed 3 rounds
```

**1 LLM call per round:** revise rubric, re-annotate calibration examples, or refine fingerprint / unique mechanisms.

---

## Stopping Criteria

- **Discriminative:** metric gain from previous round < 0.02 on primary metric
- **Generative:** qualitative plateau (same types of failures across consecutive rounds)
- **Hard stop:** after 3 rounds regardless of performance

If the skill still underperforms after 3 rounds, report the failure pattern and suggest: re-examine the induction examples for domain mismatch, check whether Signal S examples have a multi-population structure that was not accounted for, or verify that Signal E section 5 mechanisms were hand-curated.

---

## Output

Report final metrics and whether the skill outperforms the baseline. The refined skill file at `output/<task-name>-skill.md` is the final deliverable.
