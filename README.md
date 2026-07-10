# PCB-VisualRAG

Budgeted Multi-Vector Visual Retrieval and Visual RAG for PCB Engineering Documents

## Overview

PCB-VisualRAG is a multimodal retrieval and Visual RAG project for PCB engineering documents. The project focuses on retrieving useful evidence from dense technical documents such as fabrication notes, BOM tables, assembly drawings, layout diagrams, component callouts, and evaluation board manuals.

The system compares OCR-based text retrieval, dense text retrieval, visual retrieval, multi-vector retrieval, budgeted retrieval, vector compression, evidence-region attribution, occlusion evaluation, and lightweight Visual RAG validation.

The main goal is to explore whether visual multi-vector retrieval can be made accurate, interpretable, and cost-efficient for PCB document retrieval and downstream Visual RAG.

---

## Key Features

- PDF-to-page rendering and OCR preprocessing
- OCR-based BM25 retrieval baseline
- Dense text retrieval baseline
- Single-vector visual retrieval
- Full multi-vector visual retrieval
- Coarse-to-fine reranking
- Token-budgeted multi-vector retrieval
- Product quantization and compressed visual indexing
- Evidence-region annotation and evaluation
- Counterfactual occlusion analysis
- Lightweight Visual RAG question answering evaluation

---

## Dataset

The project uses a small PCB engineering document benchmark:

| Item | Value |
|---|---:|
| PDF documents | 10 |
| Rendered pages | 101 |
| Retrieval queries | 30 |
| Evidence-region queries | 10 |
| Retrieval granularity | Page-level |
| Evidence granularity | Region-level bounding box |

The documents include fabrication specifications, assembly cheatsheets, starter kit manuals, BOM documents, layout files, and evaluation board documents.

Due to redistribution and copyright concerns, the full raw PDF files are not included in the public repository.

---

## Method

The project contains two main retrieval branches:

### Text Retrieval Branch

The text branch uses OCR text extracted from rendered PCB document pages.

Methods include:

- BM25 sparse retrieval
- Dense text retrieval

BM25 is used as the main text baseline because PCB documents contain many exact textual anchors such as part numbers, table headers, component names, page titles, and specification terms.

### Visual Retrieval Branch

The visual branch uses page images for retrieval.

Methods include:

- Single-vector visual retrieval
- Full multi-vector visual retrieval
- Coarse-to-fine multi-vector reranking
- Token-budgeted visual retrieval
- Quantized visual retrieval with PQ / OPQ / IVF-style compression

The multi-vector retrieval branch represents each page as multiple visual tokens and uses late-interaction (MaxSim) scoring between query tokens and page tokens.

The visual encoder for this branch was upgraded from CLIP (`openai/clip-vit-base-patch32`) to **ColPali v1.3** (`vidore/colpali-v1.3`). CLIP is trained with a global image–text contrastive objective, so its individual patch/text tokens are not aligned at the token level; feeding raw CLIP tokens into MaxSim is a method mismatch and severely underrates the visual multi-vector branch. ColPali is trained directly with a late-interaction objective and produces token-aligned page/query multi-vectors (dim 128), which is the intended input for MaxSim scoring. The swap is zero-shot (no training/fine-tuning) and keeps the scoring, run format, qrels, and evaluation script unchanged.

---

## Pipeline

The overall pipeline is:

1. Render PCB PDF documents into page images
2. Run OCR on each page
3. Build metadata, query files, and relevance labels
4. Run text and visual retrieval baselines
5. Apply coarse-to-fine multi-vector reranking
6. Apply token budgeting and vector compression
7. Evaluate retrieval quality
8. Annotate evidence regions
9. Run occlusion experiments
10. Validate downstream Visual RAG QA performance

---

## Main Results

### Baseline Retrieval

Full corpus (101 pages, 30 queries), page-level, k = 10.

| Method | Recall@10 | nDCG@10 |
|---|---:|---:|
| OCR + BM25 | 0.8833 | 0.5241 |
| OCR + Dense Text | 0.8000 | 0.4420 |
| Full MV — CLIP (ViT-B/32) | 0.1333 | 0.0807 |
| **Full MV — ColPali v1.3** | **0.9333** | **0.6832** |

With the CLIP encoder, OCR BM25 is the strongest baseline and the visual multi-vector branch trails badly. After swapping the encoder to ColPali v1.3 (a late-interaction-native model), the visual multi-vector branch moves from far behind BM25 to on par with it on this corpus. At this pilot scale (n = 30 queries) the remaining gap falls within noise, so the robust claim is parity with BM25, not that the visual branch surpasses it.

---

### Multi-Vector Encoder Swap: CLIP → ColPali v1.3

Same evaluation script, same qrels, same MaxSim scoring, same run format; only the page/query encoder changes. Full corpus (101 pages, 30 queries), page-level, k = 10.

| Method | Recall@1 | Recall@5 | Recall@10 | MRR@10 | nDCG@10 |
|---|---:|---:|---:|---:|---:|
| Full MV — CLIP | 0.0333 | 0.1000 | 0.1333 | 0.0644 | 0.0807 |
| **Full MV — ColPali v1.3** | **0.4333** | **0.8333** | **0.9333** | **0.6228** | **0.6832** |
| BM25 (reference) | — | — | 0.8833 | — | 0.5241 |

ColPali improves Recall@10 by roughly 7× (0.1333 → 0.9333) and nDCG@10 by roughly 8× (0.0807 → 0.6832) over CLIP, reaching parity with the BM25 reference (Recall@10 0.9333 vs 0.8833, nDCG@10 0.6832 vs 0.5241). At n = 30 the Recall@10 gap (+0.05, about 1.5 queries) is within noise, and the nDCG@10 gap (+0.159), while larger, is still uncertain without confidence intervals; the robust takeaway is that the encoder swap moves the visual branch from ~7× behind BM25 to on par with it, and any claim of surpassing BM25 would need the larger qep_v1 benchmark. CLIP token vectors are L2-normalized (cosine MaxSim); ColPali vectors are stored as the model's native, un-normalized output (native dot-product MaxSim), since ColPali token norms encode learned importance. See `results/comparisons/clip_vs_colpali_multivector.md`.

---

### Token Budget Retrieval

> The token-budget, compression, and Visual RAG experiments below were run with the **CLIP** multi-vector encoder. Re-running them on ColPali v1.3 is future work.

| Method | Visual Tokens/Page | Recall@10 | nDCG@10 | Vector Payload |
|---|---:|---:|---:|---:|
| Full MV Standalone | Full | 0.1333 | 0.0807 | 9.6660 MB |
| C2F-Budgeted N10 M8 | 8 | 0.2667 | 0.1249 | 1.5781 MB |
| C2F-Budgeted N10 M16 | 16 | 0.2667 | 0.1242 | 3.1563 MB |
| C2F-Budgeted N10 M24 | 24 | 0.2667 | 0.1145 | 4.7344 MB |
| C2F-Full N10 M49 | 49 | 0.2667 | 0.1033 | 9.6660 MB |

These runs use the CLIP encoder, whose full multi-vector Recall@10 (0.1333) is already near-noise, so the apparent "budgeting matches full" effect should not be over-read as evidence of redundancy. Whether visual tokens are truly redundant, and where the optimal budget lies, must be re-verified on ColPali v1.3, where each page has ~1000+ patch tokens and the redundancy structure may differ.

---

### Joint Budget and Compression

| Setting | Recall@10 | nDCG@10 | Vector Payload |
|---|---:|---:|---:|
| N10 M8 None | 0.2667 | 0.1249 | 1.5781 MB |
| N10 M8 PQ | 0.2667 | 0.0949 | 0.0062 MB |
| N10 M16 PQ | 0.2667 | 0.1072 | 0.0123 MB |
| N10 M24 IVF+OPQ+PQ | 0.2667 | 0.1296 | 0.0185 MB |

The best compressed setting reaches nDCG@10 of 0.1296 with only 0.0185 MB visual vector payload.

---

### Visual RAG Evaluation

| Setting | Gold Page Rate | Answer Accuracy | Hallucinations |
|---|---:|---:|---:|
| Gold Evidence | 1.0000 | 1.0000 | 0 |
| BM25 | 0.4000 | 0.4000 | 1 |
| Full MV (CLIP) | 0.1000 | 0.1000 | 4 |
| Hybrid Fusion | 0.4000 | 0.4000 | 1 |
| Budgeted MV (CLIP) | 0.1000 | 0.1000 | 6 |

The Visual RAG results show that downstream answer quality is strongly controlled by retrieval quality. When the correct page is retrieved, the VLM can answer correctly. When retrieval fails, the model is more likely to produce wrong or hallucinated answers.

---

## Key Findings

- With a late-interaction-native encoder (ColPali v1.3), visual multi-vector retrieval reaches parity with OCR BM25 (Recall@10 0.9333 vs 0.8833, nDCG@10 0.6832 vs 0.5241); at n = 30 the gap is within noise, so the robust claim is parity, not surpassing BM25.
- The encoder, not the late-interaction method, was the bottleneck: raw CLIP tokens are not token-aligned, so under CLIP the multi-vector branch scored only Recall@10 0.1333; swapping to ColPali lifts it ~7× with no other changes.
- OCR BM25 remains a very strong page-level baseline and the best text-only method (Dense text retrieval performs well but does not outperform BM25).
- Coarse-to-fine and token-budgeted retrieval improve the CLIP-based visual branch and greatly reduce storage.
- Retaining only a small number of visual tokens preserved retrieval quality under the CLIP encoder, but this was measured on a near-noise CLIP baseline and must be re-verified on ColPali v1.3.
- Product quantization greatly reduces visual vector payload size.
- Evidence-region occlusion is currently a motivating illustration only, not causal evidence: the occlusion score is an edge/ink-density proxy and the gold regions are auto-generated by the same saliency, making the two circular. True retrieval-level occlusion (mask, then re-encode the page, re-run retrieval, and observe the gold-page rank change) is future work.
- Visual RAG answer accuracy closely follows retrieval gold-page hit rate.

---

## Project Structure

```text
PCB-VisualRAG/
├─ configs/              # YAML configuration files
├─ data/                 # Metadata, annotations, and sample data
├─ scripts/              # Preprocessing, retrieval, evaluation, and analysis scripts
├─ results/              # Experiment results and summary tables
├─ figures/              # Result figures and visual cases
├─ paper/                # Report tables and notes
├─ notes/                # Experiment notes
└─ reports/              # Weekly reports
```

---

## How to Run

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Prepare data

Place PCB PDF files under:

```text
data/raw_pdfs/
```

Then render pages:

```bash
python scripts/preprocess/render_pages_and_build_inventory.py
```

Run OCR:

```bash
python scripts/preprocess/run_ocr_pages.py
```

Build corpus metadata:

```bash
python scripts/preprocess/build_corpus_jsonl.py
```

### 3. Run retrieval baselines

BM25:

```bash
python scripts/retrieval/run_bm25.py
```

Dense text retrieval:

```bash
python scripts/retrieval/run_dense_text_retrieval.py
```

Single-vector visual retrieval:

```bash
python scripts/retrieval/run_single_vector_visual_retrieval.py
```

Full multi-vector retrieval (CLIP encoder):

```bash
python scripts/retrieval/run_full_multivector_retrieval.py
```

Full multi-vector retrieval (ColPali v1.3 encoder):

```bash
# 1) encode page and query multi-vectors with ColPali (writes 128-dim .npy)
python scripts/retrieval/run_colpali_page_embeddings.py   --config configs/colpali_multivector.yaml
python scripts/retrieval/run_colpali_query_embeddings.py  --config configs/colpali_multivector.yaml
# 2) reuse the same MaxSim scorer on the ColPali embeddings
python scripts/retrieval/run_full_multivector_retrieval.py --config configs/colpali_multivector.yaml
# 3) evaluate with the same eval script
python scripts/evaluation/eval_full_multivector_run.py     --config configs/colpali_multivector.yaml
```

The ColPali branch requires `colpali-engine` and a recent `transformers`; it runs on CUDA or Apple Silicon (MPS). Model weights (`vidore/colpali-v1.3`) are downloaded from the Hugging Face Hub on first run.

### 4. Run budgeted retrieval

```bash
python scripts/retrieval/run_token_budget_c2f_rerank.py
```

### 5. Run evaluation

```bash
python scripts/evaluation/eval_run_generic.py
```

---

## Notes

This repository is mainly intended as a research prototype and experiment record. The full raw PDF dataset and large generated artifacts are not included.

Large files such as embeddings, indexes, rendered full-page images, OCR backups, and intermediate caches should be regenerated locally when needed.

---

## Technologies Used

- Python
- OCR
- BM25
- Dense retrieval
- Visual retrieval
- Multi-vector retrieval
- Late interaction
- ColPali / ColQwen2 (colpali-engine)
- FAISS-style vector compression
- Product Quantization
- Visual RAG
- VLM-based QA evaluation

---

## Author

**Jiekang Yang**

Major: Computer and Information Engineering

Project completed in May 2026.
