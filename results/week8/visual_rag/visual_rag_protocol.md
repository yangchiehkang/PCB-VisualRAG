# Week 8 Day 1: Lightweight Visual RAG Protocol

## Goal

Build a lightweight downstream Visual RAG / QA validation pipeline.

```text
Query
↓
Retrieval Result
↓
Evidence Page / Page Subset
↓
VLM Answer
↓
Answer Evaluation
```

## Validation Questions

- Does retrieval evidence quality affect answer quality?
- Can Budgeted Retrieval still support Visual QA / RAG?
- Does Evidence Occlusion affect downstream answers?

## QA Input Settings

| Setting | Source | Purpose | Required |
|---|---|---|---|
| Gold Evidence | gold evidence page | QA upper bound | yes |
| BM25 | BM25 top retrieval result | strong OCR/text baseline | yes |
| Full MV | Full multi-vector retrieval result | visual retrieval baseline | recommended |
| Hybrid Fusion | hybrid BM25 + MV retrieval result | text-visual fusion validation | yes |
| Budgeted MV | budgeted multi-vector retrieval result | budgeted retrieval downstream validation | optional |
| Gold Masked | gold evidence region masked page | test evidence occlusion effect | yes |
| Random Masked | random region masked page | occlusion control | yes |

## Evaluation Metrics

| Metric | Type | Values | Description |
|---|---|---|---|
| Answer Correctness | binary | 0/1 | Whether the answer is correct. |
| Evidence Supported | binary | 0/1 | Whether the answer is supported by visible page evidence. |
| Unknown Rate | binary | 0/1 | Whether the model answers not enough evidence / unknown. |
| Answer Consistency | categorical | same/changed | Whether the answer changes across input settings. |
| Error Type | categorical | wrong_page/masked_evidence/hallucination/insufficient_info/ocr_error/none | Manual error category. |

## Fixed Prompt Template

```text
You are answering a question about a PCB engineering document page.
Use only the provided page image as evidence.
If the page does not contain enough information, answer "Not enough evidence".

Question:
{query}

Return:
1. Short answer
2. Evidence description
3. Confidence: high / medium / low
```

## Planned Outputs

```text
results/week8/visual_rag/qa_inputs.jsonl
results/week8/visual_rag/qa_outputs_all.jsonl
results/week8/visual_rag/qa_evaluation.csv
results/week8/visual_rag/tables/table19_visual_rag_main_results.csv
results/week8/visual_rag/tables/table20_occlusion_downstream_results.csv
```