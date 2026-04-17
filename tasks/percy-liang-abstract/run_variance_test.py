"""
Variance test: run each condition 3 times with different seeds,
report mean ± std to distinguish real regression from sampling noise.
"""
import os, re, json, time
import requests
from rouge_score import rouge_scorer

API_KEY = os.environ["OPENROUTER_API_KEY"]
MODEL   = "anthropic/claude-sonnet-4.6"
BASE    = os.path.dirname(os.path.abspath(__file__))
N_RUNS  = 3

def llm_multi(messages, temperature=0.3, retries=2, seed=None):
    for attempt in range(retries + 1):
        try:
            payload = {"model": MODEL, "temperature": temperature, "messages": messages}
            if seed is not None:
                payload["seed"] = seed
            resp = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
                json=payload, timeout=180,
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"].strip()
        except Exception as e:
            print(f"     [Attempt {attempt+1}/{retries+1}] Error: {e}")
            if attempt == retries: raise
            time.sleep(5)

def llm(system, user, temperature=0.3, seed=None):
    return llm_multi([{"role":"system","content":system},{"role":"user","content":user}],
                     temperature=temperature, seed=seed)

def load(p):
    with open(p) as f: return f.read()

def strip_latex(text):
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

intro    = load(f"{BASE}/test/paper3_megadocs_intro.md")
gold_raw = load(f"{BASE}/test/paper3_megadocs_abstract_gold.md")
strategy = load(f"{BASE}/output/v2_strategy.md")
content_mapping = load(f"{BASE}/output/v2_content_mapping.md")
v1_skill = load(f"{BASE}/output/percy-liang-abstract-skill.md")

task_inst = """Given the Introduction section of an ML research paper on data-efficient
language model pre-training, write an abstract for this paper.

Output ONLY the abstract text. No preamble, no explanation."""

def gen_zeroshot(seed):
    return llm("You are an expert ML researcher writing paper abstracts.",
               f"{task_inst}\n\n{intro}", seed=seed)

def gen_v1(seed):
    return llm(v1_skill, f"{task_inst}\n\n{intro}", seed=seed)

def gen_v2_simple(seed):
    """v2 original: strategy + plan → draft (no explicit mapping)."""
    plan = llm_multi([
        {"role":"system","content":strategy},
        {"role":"user","content":f"""Step 1: Content Planning.

Read the introduction below and identify the key information for the abstract.
List as bullet points. Do NOT write the abstract yet.

Introduction:
{intro}"""}
    ], temperature=0.2, seed=seed)
    return llm_multi([
        {"role":"system","content":strategy},
        {"role":"user","content":f"Step 1: Content Planning.\n\nIntroduction:\n{intro}"},
        {"role":"assistant","content":plan},
        {"role":"user","content":"""Step 2: Write the abstract.

Using the content plan and the structural template, write the abstract.
Target: 180-220 words.

Output ONLY the abstract text."""}
    ], temperature=0.3, seed=seed)

def gen_v2_mapping(seed):
    """v2 mapping-driven: strategy + content_mapping + explicit sentence mapping."""
    v2_sys = f"{strategy}\n\n---\n\n## Training Sentence-Level Mapping (reference)\n\n{content_mapping}"
    step1 = llm_multi([
        {"role":"system","content":v2_sys},
        {"role":"user","content":f"""Step 1 — Structural Analysis.

Analyze the introduction paragraph-by-paragraph. For each paragraph:
- One-line summary
- Specific numbers/concepts
- Role label

Introduction:
{intro}"""}
    ], temperature=0.2, seed=seed)
    step2 = llm_multi([
        {"role":"system","content":v2_sys},
        {"role":"user","content":f"Step 1.\n{intro}"},
        {"role":"assistant","content":step1},
        {"role":"user","content":"""Step 2 — Sentence Mapping Plan.

Produce a table:
| Abstract Sentence # | Source intro paragraph(s) | Transformation | Content to preserve |

Aim for 7-9 sentences. Follow training mapping patterns but match the density of
the training abstracts. Output ONLY the table."""}
    ], temperature=0.2, seed=seed)
    return llm_multi([
        {"role":"system","content":v2_sys},
        {"role":"user","content":f"Step 1.\n{intro}"},
        {"role":"assistant","content":step1},
        {"role":"user","content":"Step 2."},
        {"role":"assistant","content":step2},
        {"role":"user","content":"""Step 3 — Write the abstract.

For each row of your mapping plan, write the corresponding abstract sentence.
Target: 180-220 words.

Output ONLY the abstract text."""}
    ], temperature=0.3, seed=seed)

scorer = rouge_scorer.RougeScorer(['rouge1','rouge2','rougeL'], use_stemmer=True)
gold = strip_latex(gold_raw)

results = {name: {"rouge1":[], "rouge2":[], "rougeL":[], "words":[]}
           for name in ["zeroshot","v1","v2_simple","v2_mapping"]}

for run_idx in range(N_RUNS):
    seed = 42 + run_idx * 1000
    print(f"\n=== Run {run_idx+1}/{N_RUNS} (seed={seed}) ===")

    for cond_name, gen_fn in [
        ("zeroshot", gen_zeroshot),
        ("v1", gen_v1),
        ("v2_simple", gen_v2_simple),
        ("v2_mapping", gen_v2_mapping),
    ]:
        print(f"  [{cond_name}] generating...")
        text = gen_fn(seed)
        cleaned = strip_latex(text)
        sc = scorer.score(gold, cleaned)
        results[cond_name]["rouge1"].append(sc["rouge1"].fmeasure)
        results[cond_name]["rouge2"].append(sc["rouge2"].fmeasure)
        results[cond_name]["rougeL"].append(sc["rougeL"].fmeasure)
        results[cond_name]["words"].append(len(cleaned.split()))
        print(f"    R1={sc['rouge1'].fmeasure:.4f} R2={sc['rouge2'].fmeasure:.4f} RL={sc['rougeL'].fmeasure:.4f} ({len(cleaned.split())}w)")
        with open(f"{BASE}/output/variance_{cond_name}_run{run_idx+1}.txt", "w") as f:
            f.write(text)

import statistics
print("\n" + "="*80)
print("  Variance Report (N=3 runs each)")
print("="*80)
print(f"\n{'Condition':<14} {'ROUGE-1':>18} {'ROUGE-2':>18} {'ROUGE-L':>18} {'Words':>8}")
print("-"*80)
for name in ["zeroshot","v1","v2_simple","v2_mapping"]:
    r = results[name]
    def fmt(xs):
        return f"{statistics.mean(xs):.4f}±{statistics.stdev(xs):.4f}" if len(xs)>1 else f"{xs[0]:.4f}"
    print(f"{name:<14} {fmt(r['rouge1']):>18} {fmt(r['rouge2']):>18} {fmt(r['rougeL']):>18} "
          f"{int(statistics.mean(r['words'])):>8}")

# save json for further analysis
with open(f"{BASE}/output/variance_results.json", "w") as f:
    json.dump(results, f, indent=2)
print("\nFull results saved to output/variance_results.json")
