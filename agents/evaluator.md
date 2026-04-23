# Evaluator

Compare the assembled skill against a zero-shot baseline on a dev set, and optionally apply targeted iterative refinement.

**Input:** Assembled skill file path + dev set (`dev.csv`) + signal type + output type
**Output:** Evaluation report, and optionally an in-place refined skill file (max 3 refinement rounds)

**When to skip this agent:** if the user did not provide `dev.csv`, do not run the evaluator at all — the assembled skill is the deliverable. This is a common situation for Signal E style-induction tasks and small Signal S datasets with no gold-labeled held-out set.

---

## Phase 1 — Baseline Comparison

Compare the assembled skill against a zero-shot baseline on the same dev set.

| Signal / Output | Baseline | Test |
|-----------------|----------|------|
| Signal S → Discriminative | Zero-shot (task instruction only, no system prompt) | Skill system prompt |
| Signal E → Generative | Zero-shot generation | Skill-guided generation |
| Signal E → Discriminative | Zero-shot (task instruction only) | Skill system prompt |

Run both conditions on the dev set and compute:
- **Discriminative:** primary metric (see table below) + secondary metric
- **Generative:** ROUGE-1 F1 against gold outputs in `dev.csv` (or ROUGE-L if available); additionally, the rate at which each §5 mechanism from the fingerprint appears in the generated outputs.

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

Generate 5–10 outputs with the skill on held-out inputs. Compute two automated signals:

1. **ROUGE-1 F1 against gold** (when gold outputs are in `dev.csv`): measures vocabulary and phrase-level overlap with the target style. Compare skill ROUGE vs. zero-shot ROUGE — skill should be higher.
2. **§5 mechanism usage rate**: for each unique mechanism named in fingerprint §5, compute what fraction of generated outputs contain a phrase that triggers it (regex / keyword match over the mechanism's quoted phrases). Higher rates mean the skill is actually producing the style it was induced to produce.
3. **Recycled-phrase check** (optional but recommended): compute the n-gram overlap (n≥5) between each generated output and the reference examples. High overlap (>20% of 5-grams shared verbatim) signals the skill is copying phrases rather than reproducing patterns.

**Refinement triggers (based on the signals above):**

| Observed signal | Likely diagnosis | Fix |
|---|---|---|
| ROUGE lower than zero-shot | Skill hurts style fidelity | Re-induce from scratch; check that induction examples and dev inputs come from compatible subpopulations |
| §5 mechanism usage rate near zero across all outputs | Mechanisms in fingerprint are too abstract, model can't operationalize them | Strengthen fingerprint §5 with more concrete quoted phrases; re-run induction on a tighter / more consistent subset of examples |
| §5 mechanism usage rate high but ROUGE still low | Skill learned style markers but misses content overlap | Add §1-4 tightening (vocabulary, structure, framing specifics) to fingerprint |
| Recycled-phrase overlap > 20% | Skill is copying phrases verbatim from reference examples | Add explicit "do not copy phrases from examples" instruction in generation template; reduce reference example count |
| All outputs look similar regardless of input | Prompt overrides input conditioning | Reduce fingerprint prominence in prompt; emphasize input-first framing in template |
| "Wrong dimension prioritized" | Revise fingerprint section 5 weighting; rephrase mechanism descriptions |

---

## Phase 2 — Iterative Refinement (optional)

**When to run:** only if Phase 1 shows the skill trails the zero-shot baseline on the primary task metric, OR shows a systematic failure visible in the diagnosis tables above. Often skipped entirely when Phase 1 already shows the skill beats baseline with margin.

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
- **Generative:** same failure signals (ROUGE / mechanism-usage / recycled-phrase) across consecutive rounds with no improvement
- **Hard stop:** after 3 rounds regardless of performance

If the skill still underperforms after 3 rounds, report the failure pattern and suggest: re-examine the induction examples for domain mismatch, check whether Signal S examples have a multi-population structure that was not accounted for, or (Signal E) curate a tighter subset of examples with a more consistent stylistic signature.

---

## Output

Write a short evaluation report at `output/<task-name>-eval-report.md` containing:

- Baseline (zero-shot) vs. skill metrics on dev (Phase 1)
- Refinement rounds and deltas (Phase 2, if run)
- Final metrics and whether the skill outperforms the baseline

The final skill file lives at `output/<task-name>-skill.md` — refined in place if Phase 2 ran, unchanged otherwise.

### Computing metrics

Use `scripts/score_candidate.py` with `--baseline` to compute both skill metrics and zero-shot metrics in a single pass:

```bash
python skill-induction/scripts/score_candidate.py \
    --skill              output/<task-name>-skill.md \
    --dev                <task-dir>/dev.csv \
    --output-type        <continuous|ordinal|multidim-ordinal|binary|multiclass|generative> \
    --input-cols         <comma-separated input columns> \
    --label-col          <gold label column>  # or --label-cols for multidim
    --task-user-template <task-dir>/task_user_template.txt \
    --score-out          output/<task-name>-eval.score.json \
    --baseline
```

The resulting `score.json` contains the skill metric, the zero-shot metric, and the lift (`skill − baseline`). Use these numbers in the evaluation report.

### Output-type to metric mapping

| Output type in config | `--output-type` arg | Metric computed |
|---|---|---|
| Continuous (0–1, 0–100) | `continuous` | Pearson r |
| Ordinal (1–5 with half steps) | `ordinal` | Quadratic Weighted Kappa |
| Multi-dimensional ordinal | `multidim-ordinal` | Mean per-dim QWK |
| Binary | `binary` | Macro-F1 |
| Multi-class | `multiclass` | Macro-F1 |
| Generative | `generative` | ROUGE-1 F1 against gold |
