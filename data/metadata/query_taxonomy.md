# Query Taxonomy

This document defines the first-round query taxonomy for the PCB VisualRAG Project.

The taxonomy is designed for **page-level retrieval evaluation** on engineering PDF documents rendered as page images. Its main purpose is to support the construction of a query set that can meaningfully distinguish:

- shallow text matching
- OCR-assisted text retrieval
- visually grounded page retrieval
- retrieval requiring cross-page consistency or fine-grained discrimination

The current taxonomy is built based on the existing project corpus, including:

- fabrication documents
- assembly drawings
- layout pages
- schematic pages
- BOM-oriented files
- evaluation board manuals and mixed technical documentation

The current corpus metadata is defined mainly through:

- `document_inventory.csv`
- `page_inventory.csv`
- `corpus.jsonl`
- `data_schema.md`

---

## 1. Design Goal

The query taxonomy is intended to guide the first-round construction of `queries.jsonl`.

The query set should not be dominated by shallow keyword prompts such as:

- `BOM`
- `drill table`
- `U3`

Instead, it should contain queries that reflect realistic engineering information needs and that can expose the difference between text-oriented retrieval and visual page retrieval.

A useful query in this project should ideally require one or more of the following:

- spatial localization on a page
- identification of a structured table or engineering block
- interpretation of diagrams, legends, or layered structures
- linking information across pages or views
- distinguishing among visually similar but semantically different pages

---

## 2. Scope of the Current Taxonomy

This first-round taxonomy is designed for the current page-level corpus.

### Current document families
The existing corpus includes document families such as:

- fabrication
- assembly
- manual
- eval
- bom

### Current page types
The current labeled page types include:

- `fabrication`
- `assembly`
- `layout`
- `schematic`
- `bom`
- `other`

Because the corpus contains both highly structured pages and visually rich engineering pages, the taxonomy is designed to cover both:

- text-heavy retrieval needs
- visually grounded retrieval needs

---

## 3. Query Type Overview

The first-round taxonomy includes five query types.

| query_type | Chinese name | Core retrieval ability |
|---|---|---|
| `component_localization` | 元件定位类 | locate a component or board element in a visual page |
| `parameter_lookup` | 参数查表类 | find a page containing a specific parameter or tabular value |
| `structure_legend_interpretation` | 结构/图例解释类 | find structural diagrams, legends, symbols, or layer explanations |
| `cross_page_consistency` | 跨页一致性类 | connect related information across pages or views |
| `similarity_based_interference` | 相似干扰类 | distinguish among highly similar pages or variants |

These five categories are intended to cover the major retrieval challenges observed in the current corpus.

---

## 4. Query Type Definitions

### 4.1 component_localization

This category covers queries asking where a component, reference designator, board region, or visually marked element is located.

These queries usually depend on page regions such as:

- assembly views
- board placement drawings
- layout pages
- zoomed views
- callout-annotated figures

#### What this type tests
This type tests whether the retriever can identify pages based on **spatially grounded engineering content**, rather than only matching visible text tokens.

#### Typical evidence sources
- assembly pages with top/bottom views
- layout pages with component or board regions
- pages containing callouts for designators
- visual placement diagrams

#### Why this matters
Many component-location queries cannot be robustly solved by pure keyword matching alone, especially when:
- the reference designator text is small
- the page is visually dense
- the answer depends on spatial arrangement rather than isolated text

#### Example query patterns
- Which page shows the placement of component U3 in the board assembly view?
- Where can the location of R17 near the connector area be identified?
- Which page contains the top view with labeled component placement?
- On which page can the placement of a specific board-side component be verified?

#### Typical good-query characteristics
A strong query in this category:
- refers to a component or board element
- implies a location or spatial relation
- requires finding the right visual page rather than only a literal token

---

### 4.2 parameter_lookup

This category covers queries asking for the page containing a specific engineering parameter, value, size, thickness, drill specification, BOM field, or tabular item.

These queries usually depend on:

- BOM tables
- drill tables
- fabrication requirement tables
- stackup tables
- dimension blocks
- specification notes

#### What this type tests
This type tests whether the retriever can locate **high-density answer-bearing pages**, especially those dominated by tables or structured text blocks.

#### Typical evidence sources
- fabrication pages with tables
- BOM pages
- parameter summary pages
- stackup pages with thickness/material values
- pages with dimensional notes

#### Why this matters
This category helps evaluate retrieval over structured technical content. Some of these queries may be partially answerable through OCR or text retrieval, but page retrieval still matters because:
- values may appear inside dense tables
- the relevant content may be embedded in engineering layout blocks
- multiple parameters may be visually grouped on the same page

#### Example query patterns
- Which page contains the drill diameter specifications?
- Where is the board thickness specified?
- Which page lists component values in the BOM?
- On which page can material or panel requirements be found?
- Which page contains bevel or dimensional requirement annotations?

#### Typical good-query characteristics
A strong query in this category:
- asks for a concrete parameter or field
- refers to engineering values, sizes, materials, or tabular entries
- points toward a structured answer-bearing page

---

### 4.3 structure_legend_interpretation

This category covers queries asking for the location or interpretation of engineering structure diagrams, legends, symbols, stackup figures, cross-sections, or explanatory figure blocks.

These queries usually depend on:

- stackup diagrams
- fabrication legends
- drill legends
- symbol explanation areas
- cross-sectional views
- layered or annotated engineering figures

#### What this type tests
This type tests whether the retriever can locate pages whose meaning comes from a **combination of diagram structure and nearby explanatory text**, rather than from keywords alone.

#### Typical evidence sources
- fabrication detail pages
- pages with cross-sectional board views
- pages showing legend-symbol correspondence
- schematic pages with explanatory symbol regions
- layered structure diagrams

#### Why this matters
These queries are important because they often rely on visual organization:
- legends are often small but semantically important
- symbols may be ambiguous without nearby explanatory text
- structural meaning may come from figure layout, not isolated words

#### Example query patterns
- Which page shows the PCB stackup and layer structure?
- Where is the legend for fabrication or drill symbols shown?
- Which page explains the cross-sectional structure of the board?
- On which page can the layer thickness diagram be found?
- Which page contains the annotated breakaway or bevel structure figure?

#### Typical good-query characteristics
A strong query in this category:
- asks for a structure, legend, or symbol explanation
- depends on visual or diagrammatic organization
- cannot be reduced to a single obvious keyword

---

### 4.4 cross_page_consistency

This category covers queries that require relating the same entity, identifier, parameter, or design element across multiple pages or multiple views.

These queries usually depend on relationships such as:

- BOM ↔ assembly correspondence
- schematic ↔ assembly correspondence
- fabrication ↔ layout correspondence
- manual explanation ↔ figure page correspondence
- same board or circuit shown in different representational forms

#### What this type tests
This type tests whether the retrieval setup can support **document-level reasoning** and **multi-page evidence gathering**, instead of only ranking isolated pages.

#### Typical evidence sources
- BOM page and assembly page
- layout page and fabrication page
- schematic page and related board or package page
- multiple pages within the same manual that describe the same circuit variant

#### Why this matters
This category is especially important for VisualRAG-style retrieval because many engineering tasks involve:
- matching labels across views
- verifying consistency across representations
- identifying where the same object is described in different formats

#### Example query patterns
- Which pages can be used to match BOM entries with assembly reference designators?
- Where can a design element be verified in both a fabrication page and a layout page?
- Which pages describe the same board structure in different views?
- On which pages can a component identifier and its BOM record be checked together?

#### Typical good-query characteristics
A strong query in this category:
- implies more than one relevant page or view
- asks for correspondence, mapping, or consistency
- is difficult to satisfy through single-page keyword retrieval alone

#### Note
In the first-round query set, some queries in this category may still have only one strong gold page if the relevant correspondence is co-located on a single page. This is acceptable as long as the query intent is clearly cross-view or cross-representation in nature.

---

### 4.5 similarity_based_interference

This category covers queries designed to distinguish between pages that are visually, structurally, or semantically similar but not equivalent.

These queries usually arise from situations such as:

- nearby pages with similar layout templates
- repeated assembly pages for different variants
- similar schematic pages with small circuit differences
- package-specific pages with only subtle differences
- BOM or manual sections that use repeated formatting

#### What this type tests
This type tests **fine-grained retrieval discrimination**. It is meant to expose false positives that look plausible but are not actually correct.

#### Typical evidence sources
- manual pages for similar variants
- package comparison pages
- repeated document templates
- similar engineering pages differing only in a few labels, component names, or structure details

#### Why this matters
This category is highly valuable for research because a retriever may appear strong when evaluated on coarse page categories, but fail when several pages look almost the same.

This query type helps reveal whether the system can:
- distinguish variants
- avoid near-miss retrieval
- use subtle page-specific signals correctly

#### Example query patterns
- Which page shows the emitter degeneration variant rather than the grounded emitter variant?
- Which page corresponds to the SOT143X package instead of the SOT143 package?
- Which page contains the correct board variant among several visually similar pages?
- Which page shows the assembly drawing for the correct evaluation board revision?

#### Typical good-query characteristics
A strong query in this category:
- includes an explicit contrast or exclusion
- depends on subtle distinctions
- is vulnerable to visually plausible false positives

---

## 5. Taxonomy-to-Corpus Mapping

This taxonomy is grounded in the current corpus composition.

### Likely sources for `component_localization`
Common candidate pages include:
- assembly drawings
- layout pages
- visually annotated board pages

### Likely sources for `parameter_lookup`
Common candidate pages include:
- fabrication pages
- BOM pages
- table-heavy notes pages
- pages containing material, dimension, or drill information

### Likely sources for `structure_legend_interpretation`
Common candidate pages include:
- fabrication detail pages
- stackup pages
- symbol or legend-bearing pages
- annotated diagram pages

### Likely sources for `cross_page_consistency`
Common candidate page pairs or groups include:
- BOM + assembly
- layout + fabrication
- schematic + assembly
- manual explanation + figure page

### Likely sources for `similarity_based_interference`
Common candidate pages include:
- repeated variant pages in manuals
- similar assembly or schematic pages
- visually similar board pages with subtle labeling differences

---

## 6. Query Writing Principles

The first-round query set should follow the principles below.

### 6.1 Avoid shallow keyword-only prompts
Avoid queries that are essentially label lookup rather than information-seeking retrieval.

Examples of weak queries:
- `BOM`
- `drill table`
- `U3`
- `stackup`

These prompts are too shallow and may overestimate retrieval quality.

### 6.2 Prefer realistic engineering information needs
A query should resemble something a user might genuinely ask while navigating PCB-related technical documents.

Better patterns include:
- Where is a specific component placed?
- Which page contains the relevant drill specification?
- Where is the board stack structure explained?
- Which pages can verify the mapping between a BOM entry and an assembly designator?

### 6.3 Encourage structural and visual dependence
A strong query should ideally depend on one or more of:
- page layout
- visual grouping
- tables
- figures
- legends
- cross-view correspondence
- subtle contrast between similar pages

### 6.4 Keep query wording answerable at the page level
The current corpus is page-level. Therefore, the query should be phrased so that a correct answer can reasonably be expressed as:
- one correct page
- multiple relevant pages
- one document with one or more clearly relevant pages

### 6.5 Avoid unnecessary ambiguity
Queries should avoid being so broad that many unrelated pages could be counted as correct.

For example:
- Weak: `Where is the circuit shown?`
- Better: `Which page shows the grounded emitter amplifier schematic with labeled matching network elements?`

### 6.6 Preserve difficulty diversity
The first-round query set should include:
- easy queries: obvious page-type match
- medium queries: requires locating the correct page among several plausible candidates
- hard queries: requires cross-page mapping or distinguishing near-duplicate pages

---

## 7. Difficulty Guideline

The `difficulty` field in `queries.jsonl` may use:

- `easy`
- `medium`
- `hard`

### easy
The target page has a clear dominant content type and limited confusion.

Typical cases:
- a clearly identifiable BOM page
- a single fabrication page with obvious drill or material tables

### medium
The target page must be selected from several plausible pages within a document family.

Typical cases:
- choosing the correct assembly page among several board views
- selecting the page containing the right parameter block rather than a general note page

### hard
The query requires fine-grained discrimination, cross-page consistency, or distinguishing similar variants.

Typical cases:
- linking BOM and assembly references
- distinguishing two similar schematic variants
- separating visually similar package-specific pages

---

## 8. Recommended Query Fields

The first-round query file should be stored as `queries.jsonl`.

Recommended fields:

| field | meaning |
|---|---|
| `query_id` | unique query identifier |
| `query_text` | natural-language query text |
| `query_type` | one of the five taxonomy types |
| `difficulty` | easy / medium / hard |
| `gold_page_ids` | one or more gold target page IDs |
| `gold_doc_ids` | one or more gold target document IDs |
| `note` | annotation note explaining the intent |

### Example
```json
{
  "query_id": "q001",
  "query_text": "Which page shows the placement of component U3 in the board assembly view?",
  "query_type": "component_localization",
  "difficulty": "easy",
  "gold_page_ids": ["doc002_p001"],
  "gold_doc_ids": ["doc002"],
  "note": "assembly page with labeled placement view"
}
