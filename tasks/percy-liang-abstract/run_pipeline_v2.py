"""
Pipeline v2: Content-strategy-first skill induction.

Instead of extracting a style fingerprint, extracts:
  1. Content mapping (intro → abstract information flow)
  2. Compression strategy (what's kept, summarized, dropped)
  3. Structural skeleton (executable move template)
  4. Lightweight style markers (only the most distinctive 3-5 patterns)
"""
import os, re, json
import requests

API_KEY = os.environ["OPENROUTER_API_KEY"]
MODEL   = "openai/gpt-5.4-pro"
BASE    = os.path.dirname(os.path.abspath(__file__))

def llm(system: str, user: str, temperature: float = 0.2, retries: int = 2) -> str:
    for attempt in range(retries + 1):
        try:
            resp = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {API_KEY}",
                         "Content-Type": "application/json"},
                json={"model": MODEL,
                      "temperature": temperature,
                      "messages": [{"role": "system", "content": system},
                                   {"role": "user",   "content": user}]},
                timeout=300,
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"].strip()
        except Exception as e:
            print(f"     [Attempt {attempt+1}/{retries+1}] Error: {e}")
            if attempt == retries:
                raise
            import time; time.sleep(5)

def load(path):
    with open(path) as f: return f.read()

def extract_abstract(text):
    """Extract just the abstract section from an example file."""
    m = re.search(r'### Abstract.*?\n(.*?)$', text, re.DOTALL)
    return m.group(1).strip() if m else text[-1000:]

# ─── Load examples ────────────────────────────────────────────────────────────
print("[1/4] Loading examples...")
examples = {
    "paper1": load(f"{BASE}/examples/paper1_replay_finetuning.md"),
    "paper2": load(f"{BASE}/examples/paper2_infinite_compute.md"),
}

abs1 = extract_abstract(examples["paper1"])
abs2 = extract_abstract(examples["paper2"])

# ─── Phase 1a: Content Mapping ───────────────────────────────────────────────
print("[2/4] Extracting content mapping (intro → abstract information flow)...")

content_mapping_prompt = """Below are 2 examples from the same research group. Each has an Introduction
and Abstract. Your job is to analyze HOW the abstract was derived from the introduction.

{examples}

---

For EACH paper, do a sentence-by-sentence analysis of the abstract:

For each abstract sentence:
1. Quote the abstract sentence
2. Identify which paragraph(s) or sentence(s) in the Introduction it draws from
3. Classify the transformation:
   - VERBATIM: nearly identical phrasing
   - COMPRESSED: same information, fewer words
   - SYNTHESIZED: combines info from multiple intro locations
   - REFRAMED: same content but different angle/emphasis
   - NOVEL: appears in abstract but not explicitly in intro (e.g., summary claims)

After analyzing both papers, extract the GENERAL PATTERNS:

A. **Content Selection Rules**: What types of information are consistently included vs excluded?
   - Are specific numbers/metrics always kept? Which ones?
   - Are citations kept or dropped?
   - Is experimental setup detail kept or compressed?
   - How are limitations/caveats handled?

B. **Compression Ratios**: Roughly, what fraction of intro content survives into the abstract?
   What is the typical abstract length relative to intro length?

C. **Information Priority**: Rank the types of information by how reliably they appear:
   (e.g., main finding > experimental scale > downstream validation > related work context)

D. **Cross-paper Consistency**: Which content selection decisions are identical across both papers?
   These are the most reliable patterns to reproduce.
""".format(
    examples="\n\n===\n\n".join(
        f"PAPER {i+1}:\n{v}" for i, v in enumerate(examples.values())
    )
)

content_mapping = llm(
    system="You are an expert at analyzing how research paper abstracts are constructed from introductions.",
    user=content_mapping_prompt,
)

os.makedirs(f"{BASE}/output", exist_ok=True)
with open(f"{BASE}/output/v2_content_mapping.md", "w") as f:
    f.write(content_mapping)
print(f"     Content mapping saved ({len(content_mapping)} chars)")

# ─── Phase 1b: Structural Skeleton ───────────────────────────────────────────
print("[3/4] Extracting structural skeleton + style markers...")

skeleton_prompt = """Below are 2 abstracts from the same research group, plus the content mapping
analysis showing how each abstract was derived from its introduction.

=== ABSTRACTS ===
PAPER 1 Abstract:
{abs1}

PAPER 2 Abstract:
{abs2}

=== CONTENT MAPPING ANALYSIS ===
{content_mapping}

---

Extract TWO things:

## 1. EXECUTABLE STRUCTURAL SKELETON

Write a move-by-move template that someone could fill in to write a new abstract.
Each move should be:
- A slot with a clear function (not a vague description)
- With the typical sentence count for that slot
- With an example from each paper showing how they filled that slot

Format:
```
Move 1: [function] (N sentences)
  Paper 1: "[quote]"
  Paper 2: "[quote]"
  Pattern: [what's common between the two]

Move 2: ...
```

The skeleton should be specific enough that given a new introduction, someone could
fill in each slot mechanically.

## 2. LIGHTWEIGHT STYLE MARKERS (max 5)

Only the most distinctive, reproducible patterns. For each:
- Name it
- Give one example
- State the rule in one sentence

Do NOT include generic advice like "be concise" or "use formal language."
Only include patterns that distinguish THIS group from other ML paper writers.
""".format(
    abs1=abs1,
    abs2=abs2,
    content_mapping=content_mapping,
)

skeleton = llm(
    system="You are an expert at extracting reproducible structural templates from academic writing.",
    user=skeleton_prompt,
)

with open(f"{BASE}/output/v2_skeleton.md", "w") as f:
    f.write(skeleton)
print(f"     Skeleton + markers saved ({len(skeleton)} chars)")

# ─── Phase 1c: Assemble compact strategy ─────────────────────────────────────
print("[4/4] Assembling generation strategy...")

assemble_prompt = """You are creating a COMPACT generation strategy document that will be used
as a system prompt to generate paper abstracts in a specific group's style.

Here are the analysis materials:

=== CONTENT MAPPING (how intro → abstract) ===
{content_mapping}

=== STRUCTURAL SKELETON + STYLE MARKERS ===
{skeleton}

=== REFERENCE ABSTRACTS (include in full) ===
Paper 1 ("Replaying pre-training data improves fine-tuning"):
{abs1}

Paper 2 ("Pre-training under infinite compute"):
{abs2}

---

Assemble a generation strategy document with this EXACT structure:

# Abstract Generation Strategy

## Content Selection Rules
[5-7 bullet points: what to include, what to drop, what to compress.
Each rule must be actionable — "Include X" not "Consider X"]

## Structural Template
[Move-by-move template, 6-8 moves, each with:
  - What this move does (one line)
  - How to fill it from the introduction (one line)]

## Style Markers
[Max 5 distinctive patterns, one line each]

## Reference Abstracts
[Both abstracts IN FULL — these are the primary calibration anchors]

## Generation Process
When given an introduction, follow these steps:
1. Read the introduction and identify: [specific things to identify]
2. Plan content: [what to include per the content selection rules]
3. Fill the structural template move by move
4. Check against reference abstracts for length and style calibration
5. Output only the abstract text

---

IMPORTANT:
- The total document should be under 3000 words
- Every instruction must be ACTIONABLE (do X), not DESCRIPTIVE (this group tends to X)
- Do NOT truncate the reference abstracts
""".format(
    content_mapping=content_mapping,
    skeleton=skeleton,
    abs1=abs1,
    abs2=abs2,
)

strategy = llm(
    system="You are assembling a precise, actionable generation strategy for an LLM.",
    user=assemble_prompt,
    temperature=0.1,
)

# Strip markdown code fence if present
strategy = re.sub(r'^```[^\n]*\n', '', strategy.strip())
strategy = re.sub(r'\n```$', '', strategy.strip())

with open(f"{BASE}/output/v2_strategy.md", "w") as f:
    f.write(strategy)
print(f"     Strategy saved to output/v2_strategy.md")
print(f"     ({len(strategy)} chars, {len(strategy.splitlines())} lines)")
