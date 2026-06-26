# Notes Index

**Project:** PCB_VisualRAG_Project  
**Purpose:** Index and describe active experiment notes.  

---

## 1. Active Notes

| File | Description |
|---|---|
| `week2_baseline_experiments.md` | Merged Week 2 notes for OCR, BM25, Dense Text, Single-vector Visual, and query-type analysis |
| `week3_full_multivector_experiments.md` | Merged Week 3 notes for Full MV design, embeddings, retrieval, comparison, and cost analysis |
| `project_structure_convention.md` | Project directory and file organization rules |
| `template_experiment_log.md` | Standard template for future experiment logs |

---

## 2. Archived Raw Notes

Raw notes are preserved under:

- `notes/archive/week2_raw/`
- `notes/archive/week3_raw/`

These files are kept for traceability but should not be used as the primary reference when writing reports or papers.

---

## 3. Recommended Workflow

For every new experiment:

1. Create a new experiment log using `template_experiment_log.md`.
2. Record objective, inputs, config, command, outputs, metrics, and conclusion.
3. After several daily logs accumulate, merge them into a stage-level note.
4. Move raw daily logs into `notes/archive/`.
5. Use stage-level notes when writing weekly reports or thesis sections.

---

## 4. Current Stage Summary

Completed stages:

| Stage | Main Output |
|---|---|
| Week 1 | Task setup, metadata, qrels, evaluation framework |
| Week 2 | OCR/Text baselines and Single-vector Visual baseline |
| Week 3 | Full Multi-vector Retrieval and cost analysis |

Next stage:

| Stage | Focus |
|---|---|
| Week 4 | BM25 top-N + Full MV reranking and budgeted retrieval |
