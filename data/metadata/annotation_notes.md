# Annotation Notes

## 1. Annotation Principles

This file records the annotation rationale for page-level retrieval qrels.

The current `qrels.tsv` is a first-pass relevance file derived from `queries.jsonl`.  
Each query has at least one gold page annotated as relevant.

The annotation policy used in this version is:

- `relevance = 2`: primary evidence page
- secondary evidence pages are not yet extensively added unless the query explicitly requires multiple pages
- non-relevant pages are not explicitly listed in qrels

In general, a page is marked as relevant if it directly answers the information need expressed in the query, rather than merely containing loosely related keywords.

---

## 2. Relevance Scale

### Primary relevance (`2`)
A page is assigned relevance score `2` when:

- it is the main page that directly satisfies the query
- it contains the clearest evidence for the requested structure, parameter, layout, or variant
- for multi-page queries, it is one of the necessary supporting pages

### Secondary relevance (`1`)
This level is reserved for future refinement.  
It may be used later for:

- auxiliary evidence pages
- supporting pages that are helpful but not sufficient on their own
- neighboring pages that partially answer a cross-page query

At the current stage, most annotations only use relevance score `2`.

---

## 3. Query-specific Notes

### 3.1 doc001 fabrication and board package

- **q001**: `doc001_p001` is the primary evidence page because it contains the fabrication requirements table with material, panel, and special requirements.
- **q002**: `doc001_p002` is the primary evidence page because it includes breakaway and bevel requirement diagrams with dimensional annotations.
- **q003**: `doc001_p003` is relevant because it shows the top-side board view together with board outline dimensions.
- **q004**: `doc001_p004` is relevant because it contains both drill-related fabrication details and stackup legend information.
- **q005**: `doc001_p005` is relevant because it shows board artwork and copper routing rather than a tabular fabrication description.

#### Cross-page note
- **q028** requires multiple pages:
  - `doc001_p001` provides fabrication requirements context
  - `doc001_p003` provides the board top view / layout-related evidence
- This query is intentionally cross-page and should not be treated as solvable from a single page alone.

---

### 3.2 doc002 combined assembly + BOM sheet

- **q006** and **q007** both map to `doc002_p001` because this page combines:
  - top and bottom assembly views
  - BOM table
  - component callouts
  - dimensioned component details
- Although the two queries have different information needs, the same page serves as the strongest evidence page.

#### Annotation note
- This document currently has a highly compressed one-page structure, so page-level granularity does not separate BOM and assembly evidence.

---

### 3.3 doc003 schematic, package variants, and example designs

#### Schematic interpretation
- **q008**: `doc003_p007` is the grounded emitter schematic page.
- **q009**: `doc003_p008` is the emitter degeneration schematic page.

#### Similarity-based interference
These pages are intentionally similar and should be treated as hard retrieval cases.

- **q009** is designed to distinguish the emitter degeneration schematic from the grounded emitter schematic.
- **q011** vs **q012**:
  - `doc003_p010` = SOT323 grounded emitter assembly
  - `doc003_p011` = SOT323 emitter degeneration assembly
- **q013** vs **q014**:
  - `doc003_p012` = SOT23 grounded emitter
  - `doc003_p013` = SOT23 emitter degeneration
- **q015** vs **q016**:
  - `doc003_p014` = SOT143 grounded emitter
  - `doc003_p015` = SOT143 emitter degeneration
- **q017** vs **q018**:
  - `doc003_p016` = SOT143X grounded emitter
  - `doc003_p017` = SOT143X emitter degeneration
- **q020** vs **q021**:
  - `doc003_p019` = SOT143XR grounded emitter
  - `doc003_p020` = SOT143XR emitter degeneration

These query pairs should be used in later error analysis to study failures caused by:
- package-name similarity
- circuit-variant similarity
- highly repeated page layout patterns

#### Structure / stack interpretation
- **q010**: `doc003_p009` is relevant because it shows board cross section and stack dimensions.
- **q019**: `doc003_p018` is relevant because it contains the generic SOT143XR schematic including multiple related variants.

#### Frequency / transistor family interference
The example design pages in the later part of `doc003` are also strong hard-negative cases.

- **q022** vs **q023**:
  - BFU520A, 433 MHz vs 866 MHz
- **q024** vs **q025**:
  - BFU530A, 433 MHz vs 866 MHz
- **q026** vs **q027**:
  - BFU550W, 433 MHz vs 866 MHz

These pages are relevant test cases for distinguishing:
- same transistor family, different frequency
- same frequency, different transistor family
- visually similar schematic/example page layouts

---

### 3.4 Cross-page consistency cases

- **q029** requires connecting:
  - `doc003_p007` = grounded emitter schematic
  - `doc003_p010` = SOT323 grounded emitter assembly
- **q030** requires connecting:
  - `doc003_p008` = emitter degeneration schematic
  - `doc003_p011` = SOT323 emitter degeneration assembly

#### Annotation note
For cross-page queries, all required evidence pages are marked with relevance `2` in the current qrels file.  
In a future refined version, one page could be marked as primary (`2`) and the other as secondary (`1`) if a more graded relevance setup is desired.

---

## 4. Known Limitations of This Annotation Round

This is an initial annotation pass and has several limitations:

- most queries currently only include primary relevant pages
- secondary relevant pages have not yet been exhaustively annotated
- hard negative pages are described in notes but not explicitly stored in a separate file
- some query types, especially cross-page queries, may later benefit from more fine-grained graded relevance

---

## 5. Planned Refinement

In the next annotation refinement round, the following improvements may be added:

1. add secondary evidence pages with `relevance = 1`
2. create a separate hard-negative record file for similarity-based queries
3. further refine cross-page annotation for multi-hop retrieval analysis
4. expand notes for borderline pages that are partially relevant but not fully sufficient
