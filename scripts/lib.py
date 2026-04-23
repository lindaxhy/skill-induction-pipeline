"""Shared utilities for skill-induction evaluation scripts.

This module provides:
  - An OpenAI-compatible LLM adapter (works with OpenAI, OpenRouter, vLLM, etc.)
  - JSON-with-regex-fallback parsing (matches the pattern in agents/*.md)
  - Task metric functions (Pearson r, QWK, macro-F1, ROUGE-1)
  - Dev-set loading helpers for CSV / JSON / directory formats

Design note
-----------
The probabilistic formulation defines the evaluation signal via per-token
log-probabilities of gold completions. Anthropic Claude's public API does not
expose per-token logprobs, so we use a **task-native metric** (Pearson / QWK /
F1 / ROUGE) on skill predictions against gold instead. The "lift" concept is
the same: we compute

    lift(σ) = metric(σ, dev) - metric(zero_shot, dev)

which is operationally more principled — the selection metric is exactly what
downstream evaluation reports — at the cost of a coarser signal than
token-level logprobs.

If you later switch to a model that exposes logprobs (OpenAI GPT-4o, open-
weight models via vLLM), add a `logprob` metric here and use it in the same
framework.

Environment
-----------
OPENAI_API_KEY    or  OPENROUTER_API_KEY   — API key
OPENAI_BASE_URL                             — defaults to OpenRouter if OPENROUTER_API_KEY is set,
                                              else OpenAI
SKILL_SCORE_MODEL                           — model id, default "anthropic/claude-sonnet-4-6"
"""

from __future__ import annotations

import json
import os
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Sequence

try:
    from openai import OpenAI
except ImportError as e:
    raise ImportError(
        "openai package required: pip install openai"
    ) from e


# ---------------------------------------------------------------------------
# LLM adapter
# ---------------------------------------------------------------------------

def _resolve_client() -> tuple[OpenAI, str]:
    """Return (client, default_model) from environment."""
    api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError(
            "Set OPENAI_API_KEY or OPENROUTER_API_KEY in the environment."
        )
    base_url = os.environ.get("OPENAI_BASE_URL")
    if not base_url:
        base_url = (
            "https://openrouter.ai/api/v1"
            if os.environ.get("OPENROUTER_API_KEY")
            else "https://api.openai.com/v1"
        )
    client = OpenAI(base_url=base_url, api_key=api_key)
    default_model = os.environ.get("SKILL_SCORE_MODEL", "anthropic/claude-sonnet-4-6")
    return client, default_model


def chat(
    system: str | None,
    user: str,
    model: str | None = None,
    temperature: float = 0.0,
    max_tokens: int = 1024,
) -> str:
    """Single chat completion. `system=None` is the zero-shot baseline."""
    client, default_model = _resolve_client()
    messages: list[dict[str, str]] = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": user})
    response = client.chat.completions.create(
        model=model or default_model,
        temperature=temperature,
        max_tokens=max_tokens,
        messages=messages,
    )
    return response.choices[0].message.content or ""


# ---------------------------------------------------------------------------
# JSON extraction with regex fallback
# (matches the pattern documented in agents/labeled-inducer.md §S4)
# ---------------------------------------------------------------------------

def extract_json(
    response: str,
    expected_keys: Sequence[str] | None = None,
) -> dict[str, Any]:
    """Robustly extract a JSON object from a model response.

    Tries json.loads first; on failure, does regex-based key-value extraction.
    Returns an empty dict if nothing can be parsed.
    """
    match = re.search(r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", response, re.DOTALL)
    if not match:
        return {}
    blob = match.group()
    try:
        return json.loads(blob)
    except json.JSONDecodeError:
        if not expected_keys:
            return {}
        result: dict[str, Any] = {}
        for key in expected_keys:
            m = re.search(
                rf'"?{re.escape(key)}"?\s*[:\s]+"?([^",\s}}]+)', blob
            )
            if m:
                val = m.group(1).strip("\"'")
                # try numeric cast
                try:
                    val = float(val) if "." in val else int(val)
                except ValueError:
                    pass
                result[key] = val
        return result


# ---------------------------------------------------------------------------
# Metric functions
# ---------------------------------------------------------------------------

def pearson_r(x: Sequence[float], y: Sequence[float]) -> float:
    """Pearson correlation coefficient. Returns 0.0 on degenerate input."""
    if len(x) != len(y) or len(x) < 2:
        return 0.0
    n = len(x)
    mx = sum(x) / n
    my = sum(y) / n
    num = sum((xi - mx) * (yi - my) for xi, yi in zip(x, y))
    den_x = sum((xi - mx) ** 2 for xi in x) ** 0.5
    den_y = sum((yi - my) ** 2 for yi in y) ** 0.5
    if den_x == 0 or den_y == 0:
        return 0.0
    return num / (den_x * den_y)


def quadratic_weighted_kappa(
    y_true: Sequence[int], y_pred: Sequence[int]
) -> float:
    """QWK for ordinal labels. Labels must be integers."""
    if len(y_true) != len(y_pred) or len(y_true) == 0:
        return 0.0
    labels = sorted(set(list(y_true) + list(y_pred)))
    label_to_idx = {lab: i for i, lab in enumerate(labels)}
    k = len(labels)
    if k < 2:
        return 0.0
    O = [[0] * k for _ in range(k)]
    for t, p in zip(y_true, y_pred):
        O[label_to_idx[t]][label_to_idx[p]] += 1
    row_marg = [sum(row) for row in O]
    col_marg = [sum(O[i][j] for i in range(k)) for j in range(k)]
    n = sum(row_marg)
    W = [[((i - j) ** 2) / ((k - 1) ** 2) for j in range(k)] for i in range(k)]
    E = [[row_marg[i] * col_marg[j] / n for j in range(k)] for i in range(k)]
    num = sum(W[i][j] * O[i][j] for i in range(k) for j in range(k))
    den = sum(W[i][j] * E[i][j] for i in range(k) for j in range(k))
    if den == 0:
        return 0.0
    return 1.0 - num / den


def macro_f1(
    y_true: Sequence[str], y_pred: Sequence[str]
) -> float:
    """Macro-averaged F1 for multi-class labels."""
    if len(y_true) != len(y_pred) or len(y_true) == 0:
        return 0.0
    labels = sorted(set(y_true))
    f1_per_class: list[float] = []
    for lab in labels:
        tp = sum(1 for t, p in zip(y_true, y_pred) if t == lab and p == lab)
        fp = sum(1 for t, p in zip(y_true, y_pred) if t != lab and p == lab)
        fn = sum(1 for t, p in zip(y_true, y_pred) if t == lab and p != lab)
        if tp == 0 and (fp > 0 or fn > 0):
            f1_per_class.append(0.0)
            continue
        if tp + fp == 0 or tp + fn == 0:
            f1_per_class.append(0.0)
            continue
        prec = tp / (tp + fp)
        rec = tp / (tp + fn)
        f1_per_class.append(2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0.0)
    return sum(f1_per_class) / len(f1_per_class) if f1_per_class else 0.0


def _tokenize(text: str) -> list[str]:
    return re.findall(r"\w+", text.lower())


def rouge1_f(pred: str, gold: str) -> float:
    """ROUGE-1 F1 between predicted and gold text (unigram overlap)."""
    p_toks = _tokenize(pred)
    g_toks = _tokenize(gold)
    if not p_toks or not g_toks:
        return 0.0
    p_counts = Counter(p_toks)
    g_counts = Counter(g_toks)
    overlap = sum((p_counts & g_counts).values())
    if overlap == 0:
        return 0.0
    prec = overlap / len(p_toks)
    rec = overlap / len(g_toks)
    return 2 * prec * rec / (prec + rec)


# ---------------------------------------------------------------------------
# Metric dispatcher by output type
# ---------------------------------------------------------------------------

@dataclass
class MetricResult:
    name: str
    value: float
    per_example: list[float]  # per-example contribution (for diagnostics)


def compute_metric(
    output_type: str,
    predictions: list[Any],
    gold: list[Any],
    label_column: str | None = None,
) -> MetricResult:
    """Dispatch to the right metric based on output_type.

    output_type ∈ {
      "continuous", "ordinal", "multidim-ordinal",
      "binary", "multiclass", "generative"
    }
    """
    if len(predictions) != len(gold):
        raise ValueError(
            f"len(predictions)={len(predictions)} != len(gold)={len(gold)}"
        )

    if output_type == "continuous":
        pred_num = [_as_float(p) for p in predictions]
        gold_num = [_as_float(g) for g in gold]
        val = pearson_r(pred_num, gold_num)
        return MetricResult("pearson_r", val, [
            (p - g) ** 2 for p, g in zip(pred_num, gold_num)
        ])

    if output_type == "ordinal":
        # Multiply by 2 to preserve half-step resolution (1.0, 1.5, 2.0, ...)
        # before coercing to integer buckets for QWK.
        pred_i = [int(round(_as_float(p) * 2)) for p in predictions]
        gold_i = [int(round(_as_float(g) * 2)) for g in gold]
        val = quadratic_weighted_kappa(gold_i, pred_i)
        return MetricResult("qwk", val, [
            1.0 if p == g else 0.0 for p, g in zip(pred_i, gold_i)
        ])

    if output_type == "multidim-ordinal":
        # predictions and gold are dicts; compute per-dimension QWK (half-step aware)
        # and report per-dim detail + mean.
        if not predictions or not isinstance(predictions[0], dict):
            raise ValueError("multidim-ordinal expects list of dicts")
        dims = sorted(predictions[0].keys())
        dim_qwks: dict[str, float] = {}
        for d in dims:
            p_i = [int(round(_as_float(p.get(d, 0)) * 2)) for p in predictions]
            g_i = [int(round(_as_float(g.get(d, 0)) * 2)) for g in gold]
            dim_qwks[d] = quadratic_weighted_kappa(g_i, p_i)
        val = sum(dim_qwks.values()) / len(dim_qwks) if dim_qwks else 0.0
        # Compact per-example aggregate: 1.0 iff all dims match exactly
        per_ex = [
            1.0 if all(
                int(round(_as_float(p.get(d, 0)) * 2))
                == int(round(_as_float(g.get(d, 0)) * 2))
                for d in dims
            ) else 0.0
            for p, g in zip(predictions, gold)
        ]
        result = MetricResult("mean_qwk", val, per_ex)
        # Attach per-dim breakdown for the report
        result.per_dim = dim_qwks  # type: ignore[attr-defined]
        return result

    if output_type in ("binary", "multiclass"):
        pred_s = [str(p) for p in predictions]
        gold_s = [str(g) for g in gold]
        val = macro_f1(gold_s, pred_s)
        return MetricResult("macro_f1", val, [
            1.0 if p == g else 0.0 for p, g in zip(pred_s, gold_s)
        ])

    if output_type == "generative":
        pred_s = [str(p) for p in predictions]
        gold_s = [str(g) for g in gold]
        per = [rouge1_f(p, g) for p, g in zip(pred_s, gold_s)]
        val = sum(per) / len(per) if per else 0.0
        return MetricResult("rouge1_f", val, per)

    raise ValueError(f"unknown output_type: {output_type!r}")


def _as_float(x: Any) -> float:
    if isinstance(x, (int, float)):
        return float(x)
    try:
        return float(str(x).strip())
    except (TypeError, ValueError):
        return 0.0


# ---------------------------------------------------------------------------
# Dev-set loading
# ---------------------------------------------------------------------------

def load_dev_set(
    dev_path: Path,
    input_cols: list[str],
    label_col: str | None = None,
    label_cols: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Load dev examples from CSV or JSON / TSV.

    Pass `label_col` for single-label tasks, or `label_cols` (list) for
    multi-dim ordinal tasks — gold is then a dict `{col: value}`.

    Returns: list of {"input_text": str, "gold": <label value or dict>, "_row": dict}
    """
    dev_path = Path(dev_path)
    rows: list[dict[str, Any]] = []

    suffix = dev_path.suffix.lower()
    if suffix in (".csv", ".tsv"):
        import csv as _csv
        delim = "\t" if suffix == ".tsv" else ","
        with dev_path.open() as f:
            reader = _csv.DictReader(f, delimiter=delim)
            for row in reader:
                rows.append(row)
    elif suffix == ".json":
        with dev_path.open() as f:
            data = json.load(f)
        if isinstance(data, list):
            rows = data
        else:
            raise ValueError(f"JSON dev set must be a list, got {type(data)}")
    else:
        raise ValueError(
            f"Unsupported dev set format: {dev_path.suffix} "
            f"(expected .csv, .tsv, or .json)"
        )

    examples: list[dict[str, Any]] = []
    for row in rows:
        input_parts = [f"### {c}:\n{row.get(c, '')}" for c in input_cols]
        input_text = "\n\n".join(input_parts)
        ex: dict[str, Any] = {"input_text": input_text, "_row": row}
        if label_cols:
            ex["gold"] = {c: row.get(c) for c in label_cols}
        elif label_col:
            ex["gold"] = row.get(label_col)
        examples.append(ex)
    return examples


# ---------------------------------------------------------------------------
# Small convenience for scripts
# ---------------------------------------------------------------------------

def write_json(path: Path, obj: Any, indent: int = 2) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=indent, ensure_ascii=False))


def read_json(path: Path) -> Any:
    return json.loads(Path(path).read_text())
