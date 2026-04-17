Below is a mechanical template for this group’s abstract style.

**Mapping rule:** intro ¶1 usually becomes Move 1; intro ¶2 becomes Moves 2–3; each later major result paragraph becomes one iteration of Move 5; the final intro paragraph or overall thesis becomes Move 6.

```text
Move 1: State the operating regime and the default recipe / core question (1 sentence)
  Paper 1: "To obtain a language model for a target domain (e.g. math), the current paradigm is to pre-train on a vast amount of generic web text and then fine-tune on the relatively limited amount of target data."
  Paper 2: "Since compute grows much faster than web text available for language model pre-training, we ask how one should approach pre-training under fixed data and no compute constraints."
  Pattern: Open with a lightly compressed version of intro ¶1 that defines the setting, names the standard pipeline or constraint, and frames the paper’s question.

Move 2: State the standard role of the key ingredient, or the failure mode of the baseline in that regime (1 sentence; can be merged with Move 3)
  Paper 1: "Typically, generic data is only mixed in during fine-tuning to prevent catastrophic forgetting of the generic domain."
  Paper 2: "We first show that existing data-constrained approaches of increasing epoch count and parameter count eventually overfit..."
  Pattern: Before giving the contribution, make the baseline legible in one sentence by saying either what people currently use the ingredient for or what breaks in the default recipe.

Move 3: Introduce the paper’s main intervention and immediate top-line claim (1 sentence; often contrastive/surprising)
  Paper 1: "We surprisingly find that replaying the generic data during fine-tuning can actually improve performance on the (less related) target task."
  Paper 2: "...and we significantly improve upon such recipes by properly tuning regularization, finding that the optimal weight decay is 30× larger than standard practice."
  Pattern: Put the intervention and the main directional result in the same sentence; if the claim is counter to standard intuition, make that contrast explicit.

Move 4: Anchor the main claim with the paper’s canonical evidence frame—either a controlled setup with essential scale numbers, or the specific evaluation lens used to judge success (1 sentence)
  Paper 1: "Concretely, in a controlled pre-training environment with 4M target tokens, 4B total tokens, and 150M parameter models, generic replay increases target data efficiency by up to 1.87× for fine-tuning and 2.06× for mid-training."
  Paper 2: "Since our regularized recipe monotonically decreases loss following a simple power law in parameter count, we estimate its best possible performance via the asymptote of its scaling law rather than the performance at a fixed compute budget."
  Pattern: Right after the headline claim, tell the reader how to read it: give only the minimum setup numbers or conceptual measurement frame needed to interpret the result.

Move 5: Sequential result-extension loop: for each remaining major intro result paragraph, write one sentence with [new variant / analysis / extension] + [single strongest finding or condition] (1–4 sentences, repeated as needed)
  Paper 1: "We further analyze data schedules that introduce target data during pre-training and find that replay helps more when there is less target data present in pre-training."
  Paper 2: "We then identify that ensembling independently trained models achieves a significantly lower loss asymptote than the regularized recipe." / "We find that our data efficiency gains can be realized at much smaller parameter counts as we can distill an ensemble into a student model that is 8× smaller and retains 83% of the ensembling benefit."
  Pattern: Walk through the remaining intro paragraphs in order; compress each one to a single sentence containing just the new idea plus its best number/moderator, while dropping implementation detail and usually generalizing benchmark names.

Move 6: Close on external validity and overall stakes (1–2 sentences)
  Paper 1: "We demonstrate the success of replay in practice for fine-tuning 8B parameter models, improving agentic web navigation success by 4.5% and Basque question-answering accuracy by 2%."
  Paper 2: "Finally, our interventions designed for validation loss generalize to downstream benchmarks, achieving a 9% improvement for pre-training evals and a 17.5× data efficiency improvement over continued pre-training on math mid-training data." / "Our results show that simple algorithmic improvements can enable significantly more data-efficient pre-training in a compute-rich future."
  Pattern: End by proving the method matters beyond the core setup—usually with downstream or large-scale evidence—and, if there is room, append one broad future-facing takeaway sentence.
```

## 2. LIGHTWEIGHT STYLE MARKERS

1. **Near-verbatim regime opener**  
   Example: “To obtain a language model for a target domain…”  
   Rule: Start by lightly rewriting the introduction’s first setup sentence rather than inventing a new abstract hook.

2. **One result sentence = one claim + one headline number**  
   Example: “generic replay increases target data efficiency by up to 1.87× for fine-tuning and 2.06× for mid-training.”  
   Rule: Each result sentence should carry a single main point and only its strongest quantitative support.

3. **Proper-name abstraction**  
   Example: “pre-training evals” and “math mid-training data” instead of named benchmarks/datasets.  
   Rule: Replace benchmark and dataset names with task-category labels unless the proper name is itself essential to the claim.

4. **Regime-defining qualifiers, not methodological hedges**  
   Example: “under fixed data and no compute constraints”; “when there is less target data present in pre-training.”  
   Rule: Keep qualifiers that specify the operating regime or when the effect is strongest, but omit generic cautionary detail.

5. **Stepwise discourse markers for ordered accumulation**  
   Example: “Concretely, … We further analyze … We then identify … Finally, …”  
   Rule: Use light sentence-initial markers to walk through results in intro order, instead of citations, section references, or heavy signposting.

If you want, I can also convert this into a **fill-in-the-blanks abstract generator** for a new introduction from this group.