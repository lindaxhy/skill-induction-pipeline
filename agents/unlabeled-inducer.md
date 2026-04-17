# Signal E Inducer

Induce a taste model from curated demonstrations without explicit labels. Implements Steps E1–E4 of the skill induction pipeline.

**Input:** Positive examples (text files, directory, or JSON), optional negative counter-examples, config.md metadata  
**Output:** Taste model `{fingerprint, examples, negatives, annotations}`

---

## E1 — Gather and Organize Examples

**Positive examples:** 5–30 pieces representing the target style or quality. Maximize variety over volume — different topics, moods, and lengths that all clearly belong to the style.

**Negative examples (optional, high value):** 3–10 near-misses from the same domain. Most useful when the style is defined partly by what it *does not* do.

**Ultra-sparse (N < 5 positives):** Proceed, but state in the final skill file that the induced pattern may be narrow.

### Academic / Long-form Style Tasks (Signal E + Generative)

Three additional checks before proceeding:

1. **Input length for generation:**
   - Technical / empirical papers: use full introduction text (method details in the intro are essential for accurate abstract writing)
   - Position / survey / high-level papers: trim to ~400 words (full intro reduces task to compression; zero-shot dominates)

2. **Paper type before authorship:** Same authors write differently across paper types (position, empirical, benchmark, training paper). Group induction examples by paper type first. Mixing types produces a fingerprint that averages incompatible styles.

3. **Temporal alignment:** Style evolves. Ensure induction examples come from a similar period as the eval target. Examples from 5+ years earlier often reflect outdated research patterns.

---

## E2 — Extract Style Fingerprint (1 LLM call)

```
User:   [N positive examples, labeled "Positive Example N"]
        [K counter-examples if available, labeled "Counter-example K"]

        Extract a structured style fingerprint. Each dimension must be specific enough
        for another writer to reproduce — cite original phrases, name syntactic patterns,
        do not use vague adjectives like "poetic" or "professional".

        1. Vocabulary and diction (5+ specific word/phrase examples)
        2. Structure and form (sentence rhythm, parallelism, line breaks, transitions)
           2b. Opening sentence: what is the grammatical subject of the first sentence?
               (e.g., the task name, a model name, "We", "In this paper" — this is a
               highly operational style signal)
        3. Imagery / content system (recurring clusters, cross-line thematic chains)
        4. Stance and expression (3+ examples of how emotion is carried by objects,
           not stated directly)
        5. MOST IMPORTANT — unique mechanisms: 3–5 constructions that appear in these
           examples but NOT in generic content from the same domain.
           For each mechanism: name it, quote ≥2 source lines, explain the effect.
        6. What this style conspicuously avoids
```

**Sparse (N < 8):** Note that the fingerprint may be narrower than ideal; expect refinement after seeing initial outputs.

---

## E3 — Select Reference Examples

Pick examples that maximize **stylistic variety** within the style — different topics, moods, or structural approaches that all clearly exhibit the target style.

- Rich (N ≥ 10): select 5–10 positives; 2–5 negatives if available
- Sparse (N < 10): use all examples

> **NEVER truncate examples.** Full text is required — rhythm, structure, and closure patterns break with truncation.

---

## E4 — Generate Style Annotations (1 LLM call)

```
System: You are annotating examples to teach a language model a specific writing style.
        For each example, identify concrete style evidence — quote phrases,
        name patterns, point to structural choices.
        Focus especially on the unique mechanisms from section 5 of the fingerprint.
User:   [full fingerprint]

        [Selected positive examples:]
        Positive Example N:
        [full text]

        [Selected negative examples if available:]
        Counter-example K:
        [full text]

        For each positive: which mechanisms from section 5 appear? Quote the specific line.
        For each negative: which mechanism is absent or violated? What did the author do instead?
```

---

## Output Format

Return a structured taste model to the assembler:

```
TASTE MODEL (Signal E)
fingerprint:
  vocabulary: [...]
  structure: [...]
  opening_sentence_subject: [...]
  imagery: [...]
  stance: [...]
  unique_mechanisms:
    - name: [...]
      quotes: [line1, line2]
      effect: [...]
  avoidances: [...]
examples: [list of selected positive examples with full text]
negatives: [list of selected negative examples with full text]
annotations:
  positives: {"N": "annotation citing mechanisms"}
  negatives: {"K": "annotation citing what is absent"}
data_scale: rich | sparse | ultra-sparse
output_type: discriminative | generative  [from config.md]
```
