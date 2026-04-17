I’ll use **¶x.sy** = paragraph x, sentence y of the Introduction.

## Paper 1: *Replaying pre-training data improves fine-tuning*

### High-level pattern
The abstract follows the introduction almost **in order**:
- intro ¶1 → abstract setup sentence
- intro ¶2 → abstract problem + main replay result + controlled-scale number sentence
- intro ¶3 → abstract interaction analysis sentence
- intro ¶4 → abstract practical/downstream sentence  
Only the open-source paragraph is dropped.

### Sentence-by-sentence analysis

1. **Abstract:**  
   > “To obtain a language model for a target domain (e.g. math), the current paradigm is to pre-train on a vast amount of generic web text and then fine-tune on the relatively limited amount of target data.”

   - **Draws from:** **¶1.s1**
     - “To obtain a language model for a target domain … current practice often pre-trains … on a vast amount of generic web text before fine-tuning on the relatively limited amount of target data.”
   - **Transformation:** **VERBATIM**
   - **How:** Very light editing only:
     - “current practice often” → “the current paradigm”
     - trims examples from “math, code, instruction following” to just “math”
     - “before” → “and then”

2. **Abstract:**  
   > “Typically, generic data is only mixed in during fine-tuning to prevent catastrophic forgetting of the generic domain.”

   - **Draws from:** mainly **¶2.s4**, with support from **¶1.s2**
     - ¶2.s4: generic data is mixed at the end of training to prevent catastrophic forgetting
     - ¶1.s2: standard schedule is generic data first, then target data
   - **Transformation:** **REFRAMED**
   - **How:** The intro presents this as something that happens “in this setting” / “sometimes”; the abstract generalizes it into the typical role of generic data during fine-tuning.

3. **Abstract:**  
   > “We surprisingly find that replaying the generic data during fine-tuning can actually improve performance on the (less related) target task.”

   - **Draws from:** **¶2.s1** and **¶2.s5**
     - ¶2.s1: asks whether introducing generic data at the end can improve target performance
     - ¶2.s5: replaying generic data improves target performance even though distribution is further from target
   - **Transformation:** **SYNTHESIZED**
   - **How:** Combines the intervention location (“at the end of training” / during fine-tuning) with the surprising result.  
     The phrase **“(less related) target task”** is a compressed restatement of “the fine-tuning distribution is now further from the target distribution.”

4. **Abstract:**  
   > “Concretely, in a controlled pre-training environment with 4M target tokens, 4B total tokens, and 150M parameter models, generic replay increases target data efficiency by up to $1.87\\times$ for fine-tuning and $2.06\\times$ for mid-training.”

   - **Draws from:** **¶2.s2**, **¶2.s5**, **¶3.s3**
     - ¶2.s2: 150M models, 4M target tokens, up to 4B generic tokens
     - ¶2.s5: up to 1.87× data efficiency for fine-tuning
     - ¶3.s3: up to 2.06× for mid-training
   - **Transformation:** **SYNTHESIZED**
   - **How:** This is a classic abstract move:
     - compress setup to only the key scale numbers
     - merge two separate result paragraphs into one “Concretely…” sentence
     - omit dataset names, baseline details, and optimizer/schedule details

5. **Abstract:**  
   > “We further analyze data schedules that introduce target data during pre-training and find that replay helps more when there is less target data present in pre-training.”

   - **Draws from:** **¶3.s1**, **¶3.s5**, **¶3.s6**
     - moving target data earlier in training
     - two-stage schedules that use target data earlier
     - replay fraction matters more when there is less target data in stage 1
   - **Transformation:** **SYNTHESIZED**
   - **How:** The abstract drops the baseline/schedule implementation details and keeps only the conceptual finding:
     - target can be introduced earlier
     - replay matters more when pre-training contains less target data

6. **Abstract:**  
   > “We demonstrate the success of replay in practice for fine-tuning 8B parameter models, improving agentic web navigation success by $4.5\\%$ and Basque question-answering accuracy by $2\\%$.”

   - **Draws from:** **¶4.s2–s3**
     - 8B Llama 3 fine-tuning at scale
     - +4.5% web navigation success
     - +2% Basque QA accuracy
   - **Transformation:** **SYNTHESIZED**
   - **How:** Combines the scale sentence and the downstream-results sentence into one clean closing sentence.

---

## Paper 2: *Pre-training under infinite compute*

### High-level pattern
This abstract is also built almost paragraph-by-paragraph:
- intro ¶1 → motivation/regime
- ¶2–¶3 → baseline failure + regularization fix
- ¶4 → asymptote-based evaluation
- ¶5 → ensembling result
- ¶6 → data-scaling extrapolation
- ¶7 → distillation
- ¶8 → downstream validation
- final abstract sentence = broad take-home summary  
Again, citations/open-source/details are dropped.

### Sentence-by-sentence analysis

1. **Abstract:**  
   > “Since compute grows much faster than web text available for language model pre-training, we ask how one should approach pre-training under fixed data and no compute constraints.”

   - **Draws from:** **¶1.s2–s3** (with background from **¶1.s1**)
     - web data grows 1.03×/year, compute 4×/year
     - question: how to pre-train when constrained by data and unconstrained by compute
   - **Transformation:** **SYNTHESIZED**
   - **How:** The exact growth numbers are dropped and replaced by the qualitative summary “compute grows much faster.”

2. **Abstract:**  
   > “We first show that existing data-constrained approaches of increasing epoch count and parameter count eventually overfit, and we significantly improve upon such recipes by properly tuning regularization, finding that the optimal weight decay is $30\\times$ larger than standard practice.”

   - **Draws from:** **¶2.s1–s3** and **¶3.s1–s3**
     - baseline: repeat data and increase parameter count
     - too many epochs/parameters overfit
     - regularized recipe improves things
     - optimal weight decay is 30× larger than standard practice
   - **Transformation:** **SYNTHESIZED**
   - **How:** Merges the “problem with standard recipe” paragraph and the “fix via regularization” paragraph into one sentence.  
     Keeps the **30×** number because it is a headline finding.

3. **Abstract:**  
   > “Since our regularized recipe monotonically decreases loss following a simple power law in parameter count, we estimate its best possible performance via the asymptote of its scaling law rather than the performance at a fixed compute budget.”

   - **Draws from:** **¶3.s1**, **¶3.s4**, **¶4.s1–s4**
     - monotone scaling
     - power law in parameter count
     - evaluate by asymptote instead of fixed compute budget
   - **Transformation:** **SYNTHESIZED**
   - **How:** Compresses several sentences of methodological justification into one sentence.  
     This sentence preserves the paper’s central conceptual framing: **asymptote**, not finite-budget comparison.

4. **Abstract:**  
   > “We then identify that ensembling independently trained models achieves a significantly lower loss asymptote than the regularized recipe.”

   - **Draws from:** **¶5.s2–s3**
     - alternative ensembling recipe
     - ensembling yields lower loss asymptote than regularized parameter scaling
   - **Transformation:** **COMPRESSED**
   - **How:** Drops the recipe details (“average logits of K models”) and keeps just the comparative result.

5. **Abstract:**  
   > “Our best intervention combining epoching, regularization, parameter scaling, and ensemble scaling achieves an asymptote at 200M tokens using $5.17\\times$ less data than our baseline, and our data scaling laws predict that this improvement persists at higher token budgets.”

   - **Draws from:** **¶5.s5** and **¶6.s1–s3**
     - joint scaling recipe
     - asymptotes themselves scale with data
     - 5.17× less data than standard recipe
     - improvement persists at higher token counts
   - **Transformation:** **SYNTHESIZED**
   - **How:** This sentence bundles together:
     - the combined intervention
     - the main 200M-token data-efficiency number
     - the extrapolation claim

6. **Abstract:**  
   > “We find that our data efficiency gains can be realized at much smaller parameter counts as we can distill an ensemble into a student model that is $8\\times$ smaller and retains $83\\%$ of the ensembling benefit.”

   - **Draws from:** **¶7.s1–s2**
     - distillation retains most gains without increasing inference parameter count
     - distilling an 8-ensemble into a single 300M model retains 83% of the improvement
   - **Transformation:** **REFRAMED**
   - **How:** “8× smaller” is not stated that way in the intro, but is an arithmetic restatement of “8-ensemble → single model.”  
     So the abstract makes the same point in a more impact-oriented form.

7. **Abstract:**  
   > “Finally, our interventions designed for validation loss generalize to downstream benchmarks, achieving a $9\\%$ improvement for pre-training evals and a $17.5\\times$ data efficiency improvement over continued pre-training on math mid-training data.”

   - **Draws from:** **¶8.s1–s4**
     - validation loss improvements transfer downstream
     - 9% average benchmark improvement
     - 17.5× data efficiency improvement over CPT on MegaMath-Web-Pro
   - **Transformation:** **SYNTHESIZED**
   - **How:** Generalizes benchmark names (“PIQA, SciQ, ARC Easy”) into “pre-training evals,” and generalizes “MegaMath-Web-Pro” into “math mid-training data.”

8. **Abstract:**  
   > “Our results show that simple algorithmic improvements can enable significantly more data-efficient pre-training in a compute-rich future.”

   - **Draws from:** the **overall argument** of **¶1–¶8**, especially **¶1.s3**
   - **Transformation:** **NOVEL**
   - **How:** This is not stated as a single sentence in the intro. It is a high-level concluding claim synthesized from the whole paper.

---

# General patterns across both papers

## A. Content Selection Rules

### What is consistently included
1. **Opening motivation/regime**
   - Both abstracts begin with the first-paragraph setup:
     - Paper 1: target-domain LM pipeline
     - Paper 2: compute-rich, data-limited future

2. **The baseline/current practice**
   - Not in full detail, but enough to define what the paper is improving on:
     - Paper 1: generic then target; generic replay is usually for catastrophic forgetting
     - Paper 2: increase epochs/params; compare under fixed compute budgets

3. **Core intervention + main finding**
   - This is the most reliably preserved content.
   - Usually one sentence per major result paragraph.

4. **Headline quantitative metrics**
   - Strongest numbers are kept:
     - 1.87×, 2.06×, 4.5%, 2%
     - 30×, 5.17×, 83%, 9%, 17.5×

5. **Minimal experimental scale needed to interpret the result**
   - Kept when useful:
     - 4M / 4B / 150M / 8B
     - 200M tokens

6. **Practical/downstream validation**
   - Both abstracts end with evidence that the method matters beyond the narrow core setup.

### What is consistently excluded
1. **Citations**
   - Always dropped.

2. **Section references**
   - Always dropped.

3. **Implementation details unless they are themselves a result**
   - Dropped:
     - separate LR schedules / optimizer states
     - WSD schedule
     - exact ensembling mechanics
   - Kept only if central:
     - “optimal weight decay is 30× larger”

4. **Dataset/benchmark names are often generalized away**
   - FineMath / StarCoder / Flan / C4 → omitted
   - PIQA / SciQ / ARC Easy → “pre-training evals”
   - MegaMath-Web-Pro → “math mid-training data”

5. **Definitions/terminology digressions**
   - Example: “distributional replay” explanation is omitted.

6. **Open-source statement**
   - Always omitted.

### Are specific numbers always kept?
Not all numbers. They keep only numbers that are:
- **headline effect sizes**
- **core setup scale**
- **central conceptual evidence**
- **surprising comparisons**

They drop numbers that are merely illustrative or secondary:
- 1.03×/year and 4×/year become “much faster”
- 140× Chinchilla is dropped
- 4B vs 73B CPT comparison details are collapsed into 17.5×

### How are caveats/limitations handled?
- Formal limitations/uncertainty are mostly **not** foregrounded.
- What *is* kept are **scope conditions** that sharpen the claim:
  - “when there is less target data present in pre-training”
  - “under fixed data and no compute constraints”
  - “at 200M tokens”
- So they keep **regime-defining caveats**, not methodological caution.

---

## B. Compression Ratios

### Sentence-level compression
- **Paper 1:** 20 intro sentences → 6 abstract sentences = **30%**
- **Paper 2:** 31 intro sentences → 8 abstract sentences = **26%**

### Word-level compression
Roughly, the abstracts are about **one-third of the intro length**.

### Content survival
A useful way to describe it:
- **Most major intro paragraphs survive**
- **Only the top 1 claim + top 1 number from each paragraph survive**
- Fine detail survival is much lower than paragraph-level survival

So:
- **major rhetorical units retained:** high
- **specific details retained:** low

---

## C. Information Priority Ranking

Most reliably included → least reliably included:

1. **Problem framing / regime**
2. **Main intervention**
3. **Main result**
4. **Strongest quantitative evidence**
5. **Central conceptual lens or moderator**
   - Paper 1: replay helps more when pre-training has less target data
   - Paper 2: asymptote as evaluation object
6. **Experimental scale**
7. **Practical/downstream validation**
8. **Big-picture conclusion**
9. **Implementation details / related work / citations / open-source**
   - almost always excluded

---

## D. Cross-paper Consistency: strongest reusable rules

These decisions are essentially identical across both papers:

1. **The abstract follows intro order.**
   - It is not a free reorganization.
   - It is a sequential condensation of intro paragraphs.

2. **One abstract sentence roughly corresponds to one major intro paragraph.**
   - Often with 2–4 intro sentences fused together.

3. **The first abstract sentence is very close to the intro’s first paragraph.**
   - Usually compressed, sometimes near-verbatim.

4. **Each major result paragraph contributes one sentence with:**
   - the intervention/result
   - the strongest number

5. **Citations, section references, and open-source notes are always removed.**

6. **Benchmark/dataset names are generalized unless directly important to the claim.**
   - Task categories are preferred over proper names.

7. **Technical detail is included only if it is itself a contribution.**
   - Example kept: “30× larger weight decay”
   - Example dropped: exact optimizer/schedule setup

8. **The ending emphasizes external validity.**
   - either downstream/practical performance
   - or a broad take-home implication

9. **Most abstract sentences are SYNTHESIZED, not copied.**
   - These abstracts are built by compressing multiple intro sentences into one claim sentence.

---

If you want, I can turn this into a **concrete recipe/template for generating new abstracts from introductions in this group’s style**.