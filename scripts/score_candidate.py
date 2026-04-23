#!/usr/bin/env python3
"""Score a skill file on a dev set, with optional zero-shot baseline comparison.

Runs the skill (as system prompt) on every dev example, computes the
task-native metric (Pearson / QWK / F1 / ROUGE) appropriate for the task's
output type, and writes a score.json. Used by the evaluator agent for
Phase 1 baseline comparison.

Usage
-----
    python -m scripts.score_candidate \\
        --skill      output/my-task-skill.md \\
        --dev        my-task/dev.csv \\
        --output-type continuous \\
        --input-cols title,body \\
        --label-col  score \\
        --task-user-template my-task/task_user_template.txt \\
        --score-out  output/my-task-eval.score.json \\
        --baseline

`--task-user-template` is a text file containing the user-message template
used at inference. It should contain `{input_text}` placeholder which gets
filled with the concatenated input columns.

If `--baseline` is passed, the zero-shot condition (no system prompt) is also
evaluated on the same dev set, and `lift = metric(skill) - metric(baseline)`
is reported.

Output (JSON)
-------------
    {
      "candidate_path":   "...",
      "metric_name":      "pearson_r" | "qwk" | "macro_f1" | "rouge1_f",
      "metric_value":     0.752,
      "baseline_metric":  0.551,        # only if --baseline
      "lift":             0.201,        # only if --baseline
      "n_dev":            100,
      "predictions":      [ {"gold": ..., "pred": ..., "raw": "..."} , ...]
    }
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Add parent directory to path so we can import lib.py as a sibling module
_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from lib import (  # type: ignore
    chat,
    compute_metric,
    extract_json,
    load_dev_set,
    read_json,
    write_json,
)


OUTPUT_TYPES = {
    "continuous",
    "ordinal",
    "multidim-ordinal",
    "binary",
    "multiclass",
    "generative",
}


def parse_candidate_metadata(skill_text: str) -> dict:
    """Extract the HTML-comment metadata block at the top of a candidate file."""
    m = re.search(
        r"<!--\s*candidate_metadata\s*\n(.*?)\n-->",
        skill_text,
        re.DOTALL,
    )
    if not m:
        return {}
    block = m.group(1)
    meta: dict = {}
    for line in block.splitlines():
        line = line.strip()
        if not line or ":" not in line:
            continue
        k, v = line.split(":", 1)
        meta[k.strip()] = v.strip()
    return meta


def strip_candidate_metadata(skill_text: str) -> str:
    """Remove the HTML comment metadata so it doesn't pollute the system prompt."""
    return re.sub(
        r"<!--\s*candidate_metadata.*?-->\s*\n?",
        "",
        skill_text,
        count=1,
        flags=re.DOTALL,
    )


def parse_prediction(
    raw: str,
    output_type: str,
    expected_keys: list[str] | None = None,
):
    """Convert a model response into a typed prediction for the metric."""
    if output_type == "generative":
        # Strip any meta-commentary; the raw text IS the prediction
        return raw.strip()

    if output_type == "multidim-ordinal":
        return extract_json(raw, expected_keys=expected_keys or [])

    # single-value outputs: expect {"score": X} or {"label": "..."} / {"category": "..."}
    obj = extract_json(raw, expected_keys=expected_keys or ["score", "label", "category"])
    if not obj:
        return None
    # Return the single value by priority order
    for key in ("score", "label", "category", "value"):
        if key in obj:
            return obj[key]
    # Fallback: return first value
    return next(iter(obj.values()), None)


def run_on_dev(
    system_prompt: str | None,
    examples: list[dict],
    user_template: str,
    output_type: str,
    expected_keys: list[str] | None,
    model: str | None,
    temperature: float,
    max_tokens: int,
) -> list[dict]:
    """Run either the skill (system_prompt) or zero-shot (system_prompt=None)."""
    records: list[dict] = []
    for ex in examples:
        # Use plain string replace rather than .format() — task templates often
        # contain literal "{...}" fragments (e.g. JSON output schemas) that
        # .format() would misinterpret as placeholders.
        if "{input_text}" in user_template:
            user_msg = user_template.replace("{input_text}", ex["input_text"])
        else:
            user_msg = user_template.rstrip() + "\n" + ex["input_text"]
        raw = chat(
            system=system_prompt,
            user=user_msg,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        pred = parse_prediction(raw, output_type, expected_keys=expected_keys)
        records.append({
            "gold": ex.get("gold"),
            "pred": pred,
            "raw": raw,
        })
    return records


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--skill", type=Path, required=True,
                    help="Path to candidate skill .md file")
    ap.add_argument("--dev", type=Path, required=True,
                    help="Dev set path (.csv or .json)")
    ap.add_argument("--output-type", choices=sorted(OUTPUT_TYPES), required=True)
    ap.add_argument("--input-cols", required=True,
                    help="Comma-separated input column names")
    ap.add_argument("--label-col", default=None,
                    help="Gold label column (omit for generative tasks where "
                         "the whole row IS the gold output)")
    ap.add_argument("--label-cols", default=None,
                    help="Comma-separated gold label columns for multi-dim "
                         "ordinal tasks (e.g. 'content,organization,language'). "
                         "Mutually exclusive with --label-col.")
    ap.add_argument("--task-user-template", type=Path, required=True,
                    help="Text file with the user-message template "
                         "(must contain {input_text})")
    ap.add_argument("--expected-keys", default="",
                    help="Comma-separated keys for multidim-ordinal parsing")
    ap.add_argument("--score-out", type=Path, required=True,
                    help="Where to write the score.json")
    ap.add_argument("--baseline", action="store_true",
                    help="Also run zero-shot baseline, report lift")
    ap.add_argument("--model", default=None,
                    help="Override model id (default: env SKILL_SCORE_MODEL)")
    ap.add_argument("--temperature", type=float, default=0.0)
    ap.add_argument("--max-tokens", type=int, default=1024)
    ap.add_argument("--max-dev", type=int, default=None,
                    help="Subsample dev set to this many examples (for debugging)")
    args = ap.parse_args()

    if not args.skill.exists():
        print(f"ERROR: skill file not found: {args.skill}", file=sys.stderr)
        return 2
    if not args.dev.exists():
        print(f"ERROR: dev set not found: {args.dev}", file=sys.stderr)
        return 2

    skill_text = args.skill.read_text()
    metadata = parse_candidate_metadata(skill_text)
    system_prompt = strip_candidate_metadata(skill_text).strip()

    input_cols = [c.strip() for c in args.input_cols.split(",") if c.strip()]
    expected_keys = (
        [c.strip() for c in args.expected_keys.split(",") if c.strip()]
        or None
    )
    user_template = args.task_user_template.read_text()
    if "{input_text}" not in user_template:
        print(
            "WARNING: --task-user-template does not contain {input_text}; "
            "using template verbatim as the user message.",
            file=sys.stderr,
        )

    label_cols_list = None
    if args.label_cols:
        label_cols_list = [c.strip() for c in args.label_cols.split(",") if c.strip()]
        if args.label_col:
            print("ERROR: pass either --label-col or --label-cols, not both", file=sys.stderr)
            return 2

    examples = load_dev_set(
        args.dev,
        input_cols=input_cols,
        label_col=args.label_col,
        label_cols=label_cols_list,
    )
    if args.max_dev:
        examples = examples[: args.max_dev]
    print(f"Loaded {len(examples)} dev examples from {args.dev}", file=sys.stderr)

    print(f"Running skill on {len(examples)} examples...", file=sys.stderr)
    skill_preds = run_on_dev(
        system_prompt=system_prompt,
        examples=examples,
        user_template=user_template,
        output_type=args.output_type,
        expected_keys=expected_keys,
        model=args.model,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
    )

    gold = [ex.get("gold") for ex in examples]
    preds = [r["pred"] for r in skill_preds]
    skill_metric = compute_metric(
        output_type=args.output_type,
        predictions=preds,
        gold=gold,
        label_column=args.label_col,
    )

    result: dict = {
        "candidate_path": str(args.skill),
        "dev_path": str(args.dev),
        "output_type": args.output_type,
        "metric_name": skill_metric.name,
        "metric_value": skill_metric.value,
        "n_dev": len(examples),
        "predictions": skill_preds,
        "candidate_metadata": metadata,
    }
    if hasattr(skill_metric, "per_dim"):
        result["per_dim_metric"] = skill_metric.per_dim

    if args.baseline:
        print(f"Running zero-shot baseline on {len(examples)} examples...",
              file=sys.stderr)
        base_preds = run_on_dev(
            system_prompt=None,
            examples=examples,
            user_template=user_template,
            output_type=args.output_type,
            expected_keys=expected_keys,
            model=args.model,
            temperature=args.temperature,
            max_tokens=args.max_tokens,
        )
        base_metric = compute_metric(
            output_type=args.output_type,
            predictions=[r["pred"] for r in base_preds],
            gold=gold,
            label_column=args.label_col,
        )
        result["baseline_metric"] = base_metric.value
        result["lift"] = skill_metric.value - base_metric.value
        result["baseline_predictions"] = base_preds
        if hasattr(base_metric, "per_dim"):
            result["baseline_per_dim_metric"] = base_metric.per_dim
            result["per_dim_lift"] = {
                d: skill_metric.per_dim[d] - base_metric.per_dim[d]
                for d in skill_metric.per_dim
            }

    write_json(args.score_out, result)
    print(
        f"Wrote {args.score_out}: {skill_metric.name}={skill_metric.value:.4f}"
        + (
            f"  (baseline={result.get('baseline_metric', 0):.4f}, "
            f"lift={result.get('lift', 0):+.4f})"
            if args.baseline else ""
        ),
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
