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

The multi-vector retrieval branch represents each page as multiple visual tokens and uses late-interaction scoring between query tokens and page tokens.

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

| Method | Recall@10 | nDCG@10 |
|---|---:|---:|
| OCR + BM25 | 0.8833 | 0.5241 |
| OCR + Dense Text | 0.8000 | 0.4420 |
| Full MV Standalone | 0.1333 | 0.0807 |

BM25 is the strongest overall baseline in this corpus. This shows that OCR text remains highly useful for PCB document retrieval because many relevant pages contain exact technical terms.

---

### Token Budget Retrieval

| Method | Visual Tokens/Page | Recall@10 | nDCG@10 | Vector Payload |
|---|---:|---:|---:|---:|
| Full MV Standalone | Full | 0.1333 | 0.0807 | 9.6660 MB |
| C2F-Budgeted N10 M8 | 8 | 0.2667 | 0.1249 | 1.5781 MB |
| C2F-Budgeted N10 M16 | 16 | 0.2667 | 0.1242 | 3.1563 MB |
| C2F-Budgeted N10 M24 | 24 | 0.2667 | 0.1145 | 4.7344 MB |
| C2F-Full N10 M49 | 49 | 0.2667 | 0.1033 | 9.6660 MB |

The results show that many visual tokens are redundant. Keeping only 8 visual tokens per page preserves comparable retrieval quality while greatly reducing storage cost.

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
| Full MV | 0.1000 | 0.1000 | 4 |
| Hybrid Fusion | 0.4000 | 0.4000 | 1 |
| Budgeted MV | 0.1000 | 0.1000 | 6 |

The Visual RAG results show that downstream answer quality is strongly controlled by retrieval quality. When the correct page is retrieved, the VLM can answer correctly. When retrieval fails, the model is more likely to produce wrong or hallucinated answers.

---

## Key Findings

- OCR BM25 remains the strongest page-level retrieval baseline.
- Dense text retrieval also performs well but does not outperform BM25.
- Full multi-vector visual retrieval does not outperform BM25 in the current setup.
- Coarse-to-fine and token-budgeted retrieval improve the visual retrieval branch.
- Retaining only a small number of visual tokens can preserve useful retrieval quality.
- Product quantization greatly reduces visual vector payload size.
- Evidence-region occlusion confirms that annotated visual regions can be important for retrieval scoring.
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

Full multi-vector retrieval:

```bash
python scripts/retrieval/run_full_multivector_retrieval.py
```

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
- FAISS-style vector compression
- Product Quantization
- Visual RAG
- VLM-based QA evaluation

---

## Author

**Jiekang Yang**

Major: Computer and Information Engineering

Project completed in May 2026.
