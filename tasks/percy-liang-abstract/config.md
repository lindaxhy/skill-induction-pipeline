# Task Config

**Signal type**: E
**Output type**: generative

## Signal E fields
- Style name: "Kotha-Kim-Liang data-efficient pre-training abstract style"
- Paper type: empirical / scaling-law
- Temporal period: 2025-2026
- Negatives available: false

## Task description
Learn the abstract writing style of Suhas Kotha, Konwoo Kim, and Percy Liang's research line
on data-efficient language model pre-training.

Given a paper's **introduction section** as input, generate an **abstract** in this group's style.

The group focuses on:
- Data efficiency in language model pre-training (scaling laws, regularization, ensembling)
- Data scheduling and replay strategies for fine-tuning and mid-training
- Synthetic data augmentation for compute-constrained pre-training

Their abstracts characteristically:
- Open with the problem setting (data-constrained pre-training regime)
- Frame the research question explicitly ("we ask how one should...")
- Present results as concrete data efficiency multipliers (e.g., "$1.87\times$", "$5.17\times$")
- Structure findings as a progression of increasingly strong interventions
- Close with practical validation at scale or a forward-looking statement

## Input format
Each positive example is a pair: (introduction text, abstract).
Citations are in (Author, Year) format. Math notation uses LaTeX.

## Evaluation
After induction, the induced skill will be used to generate an abstract for:
  test/paper3_megadocs_intro.md  →  compare against  test/paper3_megadocs_abstract_gold.md
Metrics: ROUGE-1, ROUGE-2, ROUGE-L (vs. zero-shot baseline).
