# Project Structure Convention

**Project:** PCB_VisualRAG_Project  
**Purpose:** Define file organization conventions for data, artifacts, results, scripts, notes, and reports.  
**Status:** Active  

---

## 1. Root Directory

Project root:

- `E:\Working\PCB_VisualRAG_Project`

All scripts should assume this directory as the working root unless otherwise specified.

---

## 2. `data/`

The `data/` directory stores raw PDFs, rendered page images, OCR text, annotations, and metadata.

### 2.1 Standard Subdirectories

| Directory | Purpose |
|---|---|
| `data/raw_pdfs/` | Original PCB PDF documents |
| `data/images/` | Rendered page images, grouped by document |
| `data/ocr_raw/` | Raw OCR text files for each page |
| `data/annotations/` | Annotation files |
| `data/metadata/` | Corpus, queries, qrels, inventory, and schema files |

---

### 2.2 Standard Metadata Files

| File | Purpose |
|---|---|
| `data/metadata/corpus.jsonl` | Page-level corpus |
| `data/metadata/ocr_corpus.jsonl` | OCR text corpus |
| `data/metadata/queries.jsonl` | Query set |
| `data/metadata/qrels.tsv` | Page-level relevance labels |
| `data/metadata/page_inventory.csv` | Page inventory |
| `data/metadata/document_inventory.csv` | Document inventory |
| `data/metadata/query_taxonomy.md` | Query type definitions |
| `data/metadata/run_format.md` | Run file format definition |

---

## 3. `artifacts/`

The `artifacts/` directory stores intermediate assets that are not final evaluation results but are required for experiments.

### 3.1 Standard Subdirectories

| Directory | Purpose |
|---|---|
| `artifacts/embeddings/` | Page/query embeddings |
| `artifacts/indexes/` | Search indexes |
| `artifacts/quantization/` | Quantized vectors or compression artifacts |
| `artifacts/rerank_cache/` | Cached candidates and rerank scores |

---

### 3.2 Full Multi-vector Embeddings

Full MV embeddings should be stored under:

| Asset | Path |
|---|---|
| Page embeddings | `artifacts/embeddings/full_multivector/pages/` |
| Query embeddings | `artifacts/embeddings/full_multivector/queries/` |
| Page meta | `artifacts/embeddings/full_multivector/page_embedding_meta.jsonl` |
| Query meta | `artifacts/embeddings/full_multivector/query_embedding_meta.jsonl` |
| Token stats | `artifacts/embeddings/full_multivector/token_stats.csv` |

---

## 4. `results/`

The `results/` directory stores run files, metrics, comparison tables, and analysis outputs.

### 4.1 Standard Subdirectories

| Directory | Purpose |
|---|---|
| `results/baselines/` | BM25, Dense, and simple visual baseline results |
| `results/full_multivector/` | Full MV retrieval results |
| `results/single_vector/` | Single-vector results based on projected embeddings |
| `results/analysis/` | Cost, query-type, and performance analysis |
| `results/comparisons/` | Method comparison files |
| `results/budgeted/` | Budgeted retrieval experiments |

---

### 4.2 Run File Format

All retrieval run files should use TSV format with the following columns:

| Column | Meaning |
|---|---|
| `run_name` | Experiment name |
| `query_id` | Query ID |
| `page_id` | Retrieved page ID |
| `rank` | Rank position |
| `score` | Retrieval score |

---

## 5. `scripts/`

The `scripts/` directory stores executable scripts.

### 5.1 Standard Subdirectories

| Directory | Purpose |
|---|---|
| `scripts/preprocess/` | Data preparation scripts |
| `scripts/retrieval/` | Retrieval and reranking scripts |
| `scripts/eval/` | Evaluation scripts |
| `scripts/analysis/` | Result analysis scripts |
| `scripts/setup/` | Setup scripts |
| `scripts/utils/` | Debugging and helper utilities |
| `scripts/archive/` | Deprecated scripts |

---

## 6. `configs/`

The `configs/` directory stores experiment configuration files.

Standard config files:

| File | Purpose |
|---|---|
| `configs/bm25.yaml` | BM25 baseline |
| `configs/dense_text.yaml` | Dense text retrieval |
| `configs/single_vector_visual.yaml` | Single-vector visual retrieval |
| `configs/full_multivector.yaml` | Full MV retrieval |
| `configs/budgeted_retrieval.yaml` | Budgeted retrieval and reranking |

---

## 7. `notes/`

The `notes/` directory stores experiment logs, design notes, and stage summaries.

Recommended active files:

| File | Purpose |
|---|---|
| `notes/week2_baseline_experiments.md` | Week 2 merged baseline log |
| `notes/week3_full_multivector_experiments.md` | Week 3 merged Full MV log |
| `notes/project_structure_convention.md` | Project organization convention |
| `notes/template_experiment_log.md` | Experiment log template |
| `notes/README_notes_index.md` | Notes index |

Raw or outdated notes should be moved to:

- `notes/archive/`

---

## 8. `reports/`

The `reports/` directory stores formal weekly reports and milestone reports.

Examples:

| File | Purpose |
|---|---|
| `reports/weekly_report_week1.md` | Week 1 report |
| `reports/weekly_report_week2.md` | Week 2 report |
| `reports/weekly_report_week3.md` | Week 3 report |
| `reports/midterm_report.md` | Midterm report |

---

## 9. Naming Rules

### 9.1 Page ID

Page IDs should follow:

- `docXXX_pYYY`

Example:

- `doc003_p010`

---

### 9.2 Query ID

Query IDs should follow:

- `qXXX`

Example:

- `q001`

---

### 9.3 Experiment Result Files

Recommended naming format:

- `{method}_{setting}_run.tsv`
- `{method}_{setting}_metrics.json`
- `{method}_{setting}_summary.csv`

Examples:

- `bm25_run.tsv`
- `full_mv_run.tsv`
- `bm25_full_mv_top50_run.tsv`
- `token_budget_16_metrics.json`

---

## 10. Evaluation Convention

The primary evaluation unit is:

- Page-level retrieval

Doc-level metrics may be reported only as auxiliary metrics.

Primary metrics:

- `Recall@1`
- `Recall@5`
- `Recall@10`
- `MRR`
- `nDCG@10`

---

## 11. General Principles

1. Do not overwrite important raw results.
2. Keep all final run files under `results/`.
3. Keep embeddings and caches under `artifacts/`.
4. Keep raw logs under `notes/archive/` after merging.
5. Use config files instead of hard-coded paths whenever possible.
6. Always record input files, output files, metrics, and conclusions for each experiment.
