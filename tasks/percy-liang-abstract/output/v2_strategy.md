# Abstract Generation Strategy

## Content Selection Rules
- Follow the introduction in order; map intro ¶1 to the opener, then give each later major result paragraph at most one sentence.
- Include the operating regime, default pipeline, or central constraint from the first intro paragraph in sentence 1.
- Include the baseline role of the key ingredient or the main failure mode of the default recipe in one sentence before or alongside the contribution.
- State the main intervention and the top-line result in the same sentence; make the contrast explicit when the result is surprising or counter to standard intuition.
- Keep only the strongest quantitative evidence from each major result paragraph; include only the minimal setup scale numbers needed to interpret the claim.
- End with downstream, large-scale, or practical validation, and add one broad takeaway sentence only if the introduction clearly supports it.
- Drop citations, section references, related-work framing, open-source notes, most dataset and benchmark proper names, and implementation details unless a detail is itself a headline result.

## Structural Template
1. **Move 1**
   - **What this move does:** State the operating regime and the default recipe, constraint, or question.
   - **How to fill it from the introduction:** Lightly rewrite the first setup sentence from intro ¶1; keep the core regime and remove extra examples or background detail.

2. **Move 2**
   - **What this move does:** Make the baseline legible by stating the standard role of the key ingredient or the baseline failure mode.
   - **How to fill it from the introduction:** Extract the sentence in intro ¶2 that says what is normally done or what breaks in the default approach, and compress it to one sentence.

3. **Move 3**
   - **What this move does:** Introduce the paper’s main intervention and immediate top-line claim.
   - **How to fill it from the introduction:** Combine the intervention statement and its main directional result from intro ¶2–¶3 into one sentence; keep any surprise or contrast language.

4. **Move 4**
   - **What this move does:** Anchor the main claim with the paper’s canonical evidence frame.
   - **How to fill it from the introduction:** Add either the essential controlled-setup numbers or the core evaluation lens from the next result paragraph, and include the single strongest headline number.

5. **Move 5**
   - **What this move does:** Extend the abstract through the remaining major result paragraphs in order.
   - **How to fill it from the introduction:** For each later major intro paragraph, write one sentence with the new variant, analysis, or extension plus its strongest finding, moderator, or headline number.

6. **Move 6**
   - **What this move does:** Show external validity beyond the narrow core setup.
   - **How to fill it from the introduction:** Use the downstream, large-scale, or practical result paragraph near the end of the introduction; generalize benchmark names to task categories unless the names are essential.

7. **Move 7**
   - **What this move does:** Close with a broad take-home implication when the introduction supports one.
   - **How to fill it from the introduction:** Synthesize one future-facing or big-picture sentence from the paper’s overall thesis; omit this move if the introduction does not support a clear concluding claim.

## Style Markers
- Start with a lightly rewritten version of the introduction’s first sentence; do not invent a separate hook.
- Write each result sentence as one claim plus one headline number.
- Use light progression markers to preserve intro order: “Concretely,” “We further analyze,” “We then identify,” “Finally,”
- Replace dataset and benchmark proper names with task-category labels unless the proper name is essential to the claim.
- Keep regime-defining qualifiers and moderator conditions; remove generic hedges, caveats, and method minutiae.

## Reference Abstracts

**Paper 1 — “Replaying pre-training data improves fine-tuning”**

To obtain a language model for a target domain (e.g. math), the current paradigm is to pre-train on a vast amount of generic web text and then fine-tune on the relatively limited amount of target data. Typically, generic data is only mixed in during fine-tuning to prevent catastrophic forgetting of the generic domain. We surprisingly find that replaying the generic data during fine-tuning can actually improve performance on the (less related) target task. Concretely, in a controlled pre-training environment with 4M target tokens, 4B total tokens, and 150M parameter models, generic replay increases target data efficiency by up to $1.87\times$ for fine-tuning and $2.06\times$ for mid-training. We further analyze data schedules that introduce target data during pre-training and find that replay helps more when there is less target data present in pre-training. We demonstrate the success of replay in practice for fine-tuning 8B parameter models, improving agentic web navigation success by $4.5\%$ and Basque question-answering accuracy by $2\%$.

**Paper 2 — “Pre-training under infinite compute”**

Since compute grows much faster than web text available for language model pre-training, we ask how one should approach pre-training under fixed data and no compute constraints. We first show that existing data-constrained approaches of increasing epoch count and parameter count eventually overfit, and we significantly improve upon such recipes by properly tuning regularization, finding that the optimal weight decay is $30\times$ larger than standard practice. Since our regularized recipe monotonically decreases loss following a simple power law in parameter count, we estimate its best possible performance via the asymptote of its scaling law rather than the performance at a fixed compute budget. We then identify that ensembling independently trained models achieves a significantly lower loss asymptote than the regularized recipe. Our best intervention combining epoching, regularization, parameter scaling, and ensemble scaling achieves an asymptote at 200M tokens using $5.17\times$ less data than our baseline, and our data scaling laws predict that this improvement persists at higher token budgets. We find that our data efficiency gains can be realized at much smaller parameter counts as we can distill an ensemble into a student model that is $8\times$ smaller and retains $83\%$ of the ensembling benefit. Finally, our interventions designed for validation loss generalize to downstream benchmarks, achieving a $9\%$ improvement for pre-training evals and a $17.5\times$ data efficiency improvement over continued pre-training on math mid-training data. Our results show that simple algorithmic improvements can enable significantly more data-efficient pre-training in a compute-rich future.

## Generation Process
When given an introduction, follow these steps:
1. Read the introduction and identify: the operating regime or setup, the default pipeline or baseline, the main intervention, the baseline failure mode or standard role of the key ingredient, each later major result paragraph, the strongest number from each paragraph, any essential setup scale numbers, any downstream or practical validation, and any broad concluding claim supported by the introduction.
2. Plan content: select one opener from intro ¶1, one sentence for the baseline or failure mode, one sentence for the main intervention plus top-line result, one anchor sentence with minimal scale or evaluation framing, one sentence for each remaining major result paragraph, one closing downstream-validation sentence, and an optional final takeaway sentence; drop everything excluded by the content rules.
3. Fill the structural template move by move, preserving introduction order and compressing each major result paragraph to one sentence.
4. Check against reference abstracts for length and style calibration; target 6–8 sentences, roughly one-third of the introduction’s length, with generalized proper names, minimal setup detail, and only headline numbers.
5. Output only the abstract text.