# Task Config

**Signal type**: E
**Output type**: generative

## Signal E fields
- Style name: "Wenxuan Ding and Greg Durrett abstract style"
- Paper type: empirical / benchmark / alignment
- Temporal period: 2025-2026
- Negatives available: false

## Task description
Learn the abstract writing style of Wenxuan Ding and Greg Durrett's research group at UT Austin.
The group focuses on LLM alignment, calibration, benchmark construction, and agent exploration.

Given a paper's **introduction section** as input, generate an **abstract** in this group's style.

Their abstracts characteristically:
- Open by framing a core challenge or limitation in current LLMs (not the paper's contribution)
- Name a specific problem or gap with a clear, coined term when one exists
- State contributions as a numbered or enumerated list at the end
- Provide concrete numbers/percentages anchoring results to specific models or datasets
- Maintain a measured academic tone — no hype language, no "we demonstrate state-of-the-art"
- End with either a generalization claim or a forward-looking remark

## Input format
Each positive example is a pair: (introduction text, abstract).
Math notation uses LaTeX inline style. Citations in (Author, Year) format.

## Evaluation
After induction, the induced skill will be used to generate an abstract for:
  test/paper4_calibrate_then_act_intro.md  →  compare against  test/paper4_calibrate_then_act_abstract_gold.md
Metrics: ROUGE-1, ROUGE-2, ROUGE-L (vs. zero-shot baseline).
