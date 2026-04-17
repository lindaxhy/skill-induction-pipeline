"""
Evaluation v2: Mapping-driven multi-step generation + ROUGE.

Key design: generation is explicitly grounded in the training sentence-level
intro→abstract mapping patterns. Instead of generic "plan content" step,
the model is asked to produce a SENTENCE MAPPING PLAN for the test intro:
  - For each planned abstract sentence, identify source intro paragraph(s)
  - Classify the transformation (VERBATIM/COMPRESSED/SYNTHESIZED/REFRAMED/NOVEL)
  - List specific content (numbers, phrases) to preserve
Then write each sentence following the plan.

Compares: zero-shot / v1 skill / v2 strategy-guided (mapping-driven multi-step).
"""
import os, re
import requests
from rouge_score import rouge_scorer

API_KEY = os.environ["OPENROUTER_API_KEY"]
MODEL   = "anthropic/claude-sonnet-4.6"
BASE    = os.path.dirname(os.path.abspath(__file__))

def llm_multi(messages: list, temperature: float = 0.3, retries: int = 2) -> str:
    for attempt in range(retries + 1):
        try:
            resp = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {API_KEY}",
                         "Content-Type": "application/json"},
                json={"model": MODEL,
                      "temperature": temperature,
                      "messages": messages},
                timeout=180,
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"].strip()
        except Exception as e:
            print(f"     [Attempt {attempt+1}/{retries+1}] Error: {e}")
            if attempt == retries:
                raise
            import time; time.sleep(5)

def llm(system, user, temperature=0.3):
    return llm_multi(
        [{"role": "system", "content": system},
         {"role": "user", "content": user}],
        temperature=temperature,
    )

def load(path):
    with open(path) as f: return f.read()

def strip_latex(text: str) -> str:
    text = re.sub(r'\*\*Paper:.*?\n', '', text)
    text = re.sub(r'## Gold Abstract.*?\n', '', text)
    text = re.sub(r'\$([^$]+)\$', r'\1', text)
    text = re.sub(r'\\times', '×', text)
    text = re.sub(r'\\%', '%', text)
    text = re.sub(r'\\[a-zA-Z]+\{([^}]*)\}', r'\1', text)
    text = re.sub(r'\\[a-zA-Z]+', ' ', text)
    text = re.sub(r'[{}$\\]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

# ─── Load inputs ─────────────────────────────────────────────────────────────
intro           = load(f"{BASE}/test/paper3_megadocs_intro.md")
gold_raw        = load(f"{BASE}/test/paper3_megadocs_abstract_gold.md")
strategy        = load(f"{BASE}/output/v2_strategy.md")
content_mapping = load(f"{BASE}/output/v2_content_mapping.md")
v1_skill        = load(f"{BASE}/output/percy-liang-abstract-skill.md")

task_instruction = """Given the Introduction section of an ML research paper on data-efficient
language model pre-training, write an abstract for this paper.

Output ONLY the abstract text. No preamble, no explanation."""

print(f"[Model: {MODEL}]")

# ─── Zero-shot ────────────────────────────────────────────────────────────────
print("[1/3] Generating zero-shot abstract...")
zeroshot = llm(
    system="You are an expert ML researcher writing paper abstracts.",
    user=f"{task_instruction}\n\n{intro}",
)
print(f"      {len(zeroshot.split())} words")

# ─── v1 skill-guided (single-step baseline) ─────────────────────────────────
print("[2/3] Generating v1 skill-guided abstract (single-step)...")
v1_out = llm(
    system=v1_skill,
    user=f"{task_instruction}\n\n{intro}",
)
print(f"      {len(v1_out.split())} words")

# ─── v2 mapping-driven multi-step generation ────────────────────────────────
print("[3/3] Generating v2 mapping-driven abstract (multi-step)...")

# Build a richer system prompt: strategy.md PLUS the content mapping analysis
# so the model sees actual training sentence mappings.
v2_system = f"""{strategy}

---

## Training Examples — Full Sentence-Level Mapping Analysis

Below is a detailed sentence-by-sentence mapping showing how abstracts were derived
from introductions in the training examples. Use this to understand the precise
transformation patterns this group applies.

{content_mapping}"""

# Step 1: Structural analysis of the TEST intro
step1_response = llm_multi([
    {"role": "system", "content": v2_system},
    {"role": "user", "content": f"""Step 1 — Structural Analysis of the NEW Introduction.

Analyze the introduction below paragraph-by-paragraph. For each paragraph:
- Give a one-line summary (what does this paragraph contribute?)
- List the specific quantitative claims, numbers, or named concepts in it
- Label its role (regime/setup, baseline, main finding, extension, downstream, etc.)

Do NOT write the abstract yet.

Introduction:
{intro}"""}
], temperature=0.2)

# Step 2: Sentence-level mapping plan
step2_response = llm_multi([
    {"role": "system", "content": v2_system},
    {"role": "user", "content": f"""Step 1 — Structural Analysis.
{intro}"""},
    {"role": "assistant", "content": step1_response},
    {"role": "user", "content": """Step 2 — Produce a SENTENCE MAPPING PLAN for the new abstract.

Based on:
  (a) the training examples' sentence-level mappings (in the system prompt), and
  (b) your structural analysis of the new introduction,

produce a plan in this exact table format:

| Abstract Sentence # | Source intro paragraph(s) | Transformation | Content to preserve |
|---|---|---|---|
| 1 | ¶X.sY | VERBATIM/COMPRESSED/SYNTHESIZED/REFRAMED/NOVEL | exact numbers, phrases, concepts |
| 2 | ... | ... | ... |

Requirements:
- Aim for 6–8 sentences total (matching the training abstracts' length).
- Follow the training mapping patterns: sentence 1 is typically near-verbatim from intro ¶1; each major result paragraph gets one SYNTHESIZED sentence with headline number.
- For each row, list the ACTUAL numbers/phrases to preserve (e.g. "1.48×", "3.41 vs 3.55", "32 rephrases").
- The closing sentence may be NOVEL (a broad summary not stated verbatim in the intro).

Output ONLY the table."""}
], temperature=0.2)

# Step 3: Generate abstract following the mapping plan
step3_response = llm_multi([
    {"role": "system", "content": v2_system},
    {"role": "user", "content": f"""Step 1 — Structural Analysis.
{intro}"""},
    {"role": "assistant", "content": step1_response},
    {"role": "user", "content": "Step 2 — Sentence Mapping Plan."},
    {"role": "assistant", "content": step2_response},
    {"role": "user", "content": """Step 3 — Write the Abstract.

For each row of your mapping plan, write the corresponding abstract sentence:
- Apply the transformation type you planned (VERBATIM/COMPRESSED/etc.)
- Preserve the specific numbers and phrases listed in "Content to preserve"
- Use the sentence mechanics in your instructions (one claim + one number per sentence,
  light progression markers, regime-defining qualifiers)

Target: 180-220 words total.

Output ONLY the abstract text — no preamble, no explanation, no mapping table."""}
], temperature=0.3)

# Save all intermediate outputs
for name, text in [
    ("zeroshot",        zeroshot),
    ("v1skilled",       v1_out),
    ("v2_step1_struct", step1_response),
    ("v2_step2_plan",   step2_response),
    ("v2_final",        step3_response),
]:
    with open(f"{BASE}/output/v2_{name}.txt", "w") as f:
        f.write(text)

print(f"      v2 mapping-driven: {len(step3_response.split())} words")

# ─── ROUGE ────────────────────────────────────────────────────────────────────
print("\nComputing ROUGE scores...")
gold = strip_latex(gold_raw)
scorer = rouge_scorer.RougeScorer(['rouge1', 'rouge2', 'rougeL'], use_stemmer=True)

conditions = [
    ("Zero-shot",         strip_latex(zeroshot)),
    ("v1 Skill",          strip_latex(v1_out)),
    ("v2 Mapping-driven", strip_latex(step3_response)),
]
scores = [(name, scorer.score(gold, txt), txt) for name, txt in conditions]

print("\n" + "="*80)
print("  ROUGE Evaluation: Mapping-driven v2 Pipeline")
print("="*80)
print(f"\n{'Metric':<12} {'Zero-shot':>14} {'v1 Skill':>14} {'v2 Mapping':>18}  Δ(v2-zs)")
print("-"*80)
for key, label in [('rouge1','ROUGE-1'), ('rouge2','ROUGE-2'), ('rougeL','ROUGE-L')]:
    row = f"{label:<12}"
    for _, sc, _ in scores:
        row += f" {sc[key].fmeasure:>14.4f}" if "Mapping" not in _ else f" {sc[key].fmeasure:>18.4f}"
    delta = scores[-1][1][key].fmeasure - scores[0][1][key].fmeasure
    sign = "+" if delta >= 0 else ""
    # fixed-width print regardless
    zs_f, v1_f, v2_f = [s[1][key].fmeasure for s in scores]
    print(f"{label:<12} {zs_f:>14.4f} {v1_f:>14.4f} {v2_f:>18.4f}  {sign}{delta:.4f}")
print("-"*80)
print(f"\nWord counts: Gold={len(gold.split())}", end="")
for name, _, txt in scores:
    print(f", {name}={len(txt.split())}", end="")
print("\n")

print(f"--- Gold ---\n{gold}\n")
for name, _, txt in scores:
    print(f"--- {name} ---\n{txt}\n")
