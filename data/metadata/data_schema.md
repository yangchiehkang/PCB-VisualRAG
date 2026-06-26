# PCB VisualRAG Project Data Schema

This document defines the data schema, field meanings, allowed values, and labeling conventions used in the PCB VisualRAG Project.

The current focus is **page-level metadata** for technical PDF documents, especially PCB-related materials such as schematics, assembly drawings, fabrication packages, bills of materials, manuals, datasheets, and reference designs.

---

## 1. Scope

This schema currently covers:

- document-level identity through `doc_id`
- page-level identity through `page_id`
- file linkage between source PDF files and rendered page images
- page-level structural and semantic labels
- retrieval candidate selection fields
- dataset management fields such as split and inclusion flags

This schema is primarily implemented in:

- `data/metadata/page_inventory.csv`

Each row in `page_inventory.csv` represents **one page** from one source PDF document.

---

## 2. Core Entity: Page Inventory

The core dataset entity is the **page**.

A page is the basic unit for:

- visual retrieval
- metadata filtering
- page-type classification
- retrieval candidate selection
- train/validation/test splitting
- downstream multimodal indexing

Because the project is page-centric, all important engineering and retrieval annotations are attached at the page level.

---

## 3. Primary Keys

### `doc_id`

Document identifier.

- Type: `string`
- Example: `doc001`, `doc009`, `doc010`

Rules:

- unique at the document level
- recommended format: `doc` + zero-padded numeric index

Examples:

- `doc001`
- `doc002`
- `doc010`

### `page_id`

Unique page identifier.

- Type: `string`
- Example: `doc009_p001`

Rules:

- unique across the entire dataset
- recommended format: `{doc_id}_p{page_number_3digits}`

Examples:

- `doc001_p001`
- `doc009_p003`
- `doc010_p002`

---

## 4. Current Columns in `page_inventory.csv`

The following table reflects the **actual current columns** used in the dataset.

| Field | Type | Example | Description |
|---|---|---|---|
| `page_id` | string | `doc010_p002` | Unique page identifier |
| `doc_id` | string | `doc010` | Document identifier |
| `page_num` | integer | `2` | Original page number within the source document |
| `file_name` | string | `ADIS16006_PCB.pdf` | Original PDF filename |
| `document_family` | string | `assembly` | High-level document family or document category |
| `experiment_tier` | string | `core` | Dataset tier such as `core` or `extended` |
| `pdf_path` | string | `E:\Working\PCB_VisualRAG_Project\data\raw_pdfs\...` | Full path to the source PDF |
| `image_path` | string | `E:\Working\PCB_VisualRAG_Project\data\images\doc010\doc010_p002.png` | Full path to the rendered page image |
| `image_name` | string | `doc010_p002.png` | Rendered page image filename |
| `width` | integer | `1582` | Rendered page image width in pixels |
| `height` | integer | `2450` | Rendered page image height in pixels |
| `page_type` | string | `assembly` | Manual page category label |
| `has_table` | string | `yes` | Whether the page contains a meaningful table |
| `has_diagram` | string | `yes` | Whether the page contains a meaningful technical diagram |
| `has_designators` | string | `yes` | Whether the page contains component or connector designators |
| `has_dimensions` | string | `yes` | Whether the page contains explicit dimensions |
| `has_dense_text` | string | `no` | Whether the page contains dense paragraph or table text |
| `is_candidate_page` | string | `yes` | Whether the page is useful as a retrieval candidate |
| `include_flag` | string | `yes` | Whether the page is currently included in the active processing scope |
| `split` | string | `train` | Dataset split such as `train`, `val`, or `test` |
| `notes` | string | `` | General-purpose note field |
| `label_notes` | string | `mechanical drawing page with board outline and dimensions` | Manual labeling note explaining the assigned labels |

---

## 5. Field Definitions

This section defines the meaning and expected usage of each field.

### 5.1 Identity Fields

#### `doc_id`

Document identifier.

- Type: `string`
- Required: yes

Purpose:

- groups pages belonging to the same source document
- supports document-level filtering and grouping

#### `page_id`

Unique page identifier.

- Type: `string`
- Required: yes

Purpose:

- uniquely identifies a single page across the whole dataset
- serves as the main join key for page-level operations

#### `page_num`

Original page number in the source PDF.

- Type: `integer`
- Required: yes

Purpose:

- preserves original page ordering
- supports reconstruction of page position inside the document

---

### 5.2 File Linkage Fields

#### `file_name`

Original PDF filename.

- Type: `string`
- Required: yes

Examples:

- `doc001_fabrication_slu-sf05b.pdf`
- `ADIS16006_PCB.pdf`

#### `pdf_path`

Full filesystem path to the source PDF.

- Type: `string`
- Required: yes

Purpose:

- links metadata rows to original source documents
- supports reprocessing and traceability

#### `image_path`

Full filesystem path to the rendered page image.

- Type: `string`
- Required: yes

Purpose:

- links each row to the rendered image used for visual retrieval or analysis

#### `image_name`

Rendered image filename.

- Type: `string`
- Required: yes

Examples:

- `doc010_p002.png`

---

### 5.3 Dataset Organization Fields

#### `document_family`

High-level document family or source category.

- Type: `string`
- Required: yes

Observed examples:

- `fabrication`
- `assembly`
- `manual`

Purpose:

- groups source documents by broad engineering category
- supports sampling and experiment organization

#### `experiment_tier`

Dataset experiment tier.

- Type: `string`
- Required: yes

Observed examples:

- `core`
- `extended`

Purpose:

- identifies whether a document belongs to the main experimental subset or an extended subset

#### `split`

Dataset split assignment.

- Type: `string`
- Required: yes

Typical values:

- `train`
- `val`
- `test`

Purpose:

- controls experimental partitioning
- supports reproducible evaluation

#### `include_flag`

Operational inclusion flag for the current processing or experiment pipeline.

- Type: `string`
- Required: yes
- Recommended values: `yes`, `no`

Purpose:

- indicates whether the row is currently active in the working dataset
- supports filtering pages in or out without deleting records

Important distinction:

- `is_candidate_page` describes **retrieval usefulness**
- `include_flag` describes **operational inclusion in the current workflow**

A page may be a useful retrieval candidate in principle, but still be excluded operationally for a specific experiment.

---

### 5.4 Image Size Fields

#### `width`

Rendered page image width in pixels.

- Type: `integer`
- Required: yes

Purpose:

- supports image preprocessing
- supports aspect-ratio analysis
- supports vision model input handling

#### `height`

Rendered page image height in pixels.

- Type: `integer`
- Required: yes

Purpose:

- supports image preprocessing
- supports aspect-ratio analysis
- supports vision model input handling

---

### 5.5 Manual Label Fields

#### `page_type`

Human-assigned page category describing the dominant engineering function of the page.

- Type: `string`
- Required: yes

#### Allowed values

- `schematic`
- `assembly`
- `bom`
- `fabrication`
- `layout`
- `other`

#### Definitions

##### `schematic`

Use when the page is primarily an electrical schematic.

Typical characteristics:

- nets and signal connections
- circuit symbols
- ICs, passives, connectors
- reference designators such as `R1`, `C5`, `U2`

Examples:

- circuit diagram pages
- multi-block electrical schematic pages

##### `assembly`

Use when the page is primarily about physical board realization, placement, or mechanical structure.

Typical characteristics:

- assembly drawing
- top or bottom component placement
- board outline
- hole pattern
- connector locations
- mechanical dimensions

Examples:

- mechanical drawing pages
- placement drawing pages
- board outline pages

##### `bom`

Use when the page is primarily a bill of materials or parts list.

Typical characteristics:

- large component tables
- quantity columns
- manufacturer and part number columns
- long designator lists

Examples:

- bill of materials
- parts list
- installed / not installed parts pages

##### `fabrication`

Use when the page is primarily about PCB fabrication requirements or manufacturing details.

Typical characteristics:

- fabrication notes
- drill table
- material requirements
- stackup information
- process instructions
- panel details
- manufacturing constraints

Examples:

- fabrication instruction pages
- drill and stackup pages
- process requirement pages

##### `layout`

Use when the page is primarily about PCB artwork or routed board views.

Typical characteristics:

- layer artwork
- routed copper views
- top or bottom layer board views
- physical board representation without being mainly a placement sheet
- routing-focused board graphics

Examples:

- layer view pages
- copper artwork pages
- routing pages

##### `other`

Use when the page does not fit the main engineering classes above, or when it is a mixed-content page whose dominant purpose is not clearly one of them.

Typical characteristics:

- overview pages
- hybrid summary pages
- ordering guide pages
- legal notices
- introductory pages
- mixed-content evaluation-board pages

Examples:

- overview page containing schematic, layout, text, and parts list
- legal disclaimer page
- title or intro page

#### Dominant-content rule

Assign `page_type` based on the **dominant purpose of the page**, not every element present.

Examples:

- a BOM page containing package sizes is still `bom`
- a mixed overview page with schematic, layout, and text may still be `other`
- a drill and stackup manufacturing page is `fabrication`
- a layer artwork page is `layout`

---

#### `has_table`

Whether the page contains a meaningful table.

- Type: `string`
- Required: yes
- Allowed values: `yes`, `no`

Use `yes` when:

- there is a structured row/column table
- the table has engineering or metadata value
- examples include BOM tables, ordering tables, drill tables, spec tables

Use `no` when:

- there is no clear tabular structure
- only loose text alignment is present

---

#### `has_diagram`

Whether the page contains a meaningful technical diagram.

- Type: `string`
- Required: yes
- Allowed values: `yes`, `no`

Use `yes` for:

- schematics
- board drawings
- mechanical drawings
- layout views
- drill graphics
- block diagrams
- connector illustrations

Use `no` for:

- pure text pages
- pure tabular pages without meaningful graphics
- legal notice pages

Small legends or logos do not count as diagrams.

---

#### `has_designators`

Whether the page contains component or connector designators.

- Type: `string`
- Required: yes
- Allowed values: `yes`, `no`

Use `yes` when the page includes identifiers such as:

- `R1`
- `C5`
- `U1`
- `J1`
- `TP1`
- `SW1`
- `D3`
- `L1`

Designators may appear in:

- schematics
- BOM tables
- layout views
- assembly drawings
- callout annotations

---

#### `has_dimensions`

Whether the page contains explicit dimensional information.

- Type: `string`
- Required: yes
- Allowed values: `yes`, `no`

Use `yes` when the page includes:

- dimension callouts
- board width or height
- hole diameters
- distances or spacing values
- package or physical size values such as `20.3x14.3x17.96mm`

Use `no` when:

- no explicit dimensions are shown
- graphics are present but not dimensioned

Important note:

A BOM page may still have `has_dimensions = yes` if the table includes explicit physical size values.

---

#### `has_dense_text`

Whether the page contains high textual density.

- Type: `string`
- Required: yes
- Allowed values: `yes`, `no`

Use `yes` when:

- the page contains long paragraphs
- the page contains dense legal text
- the page contains large tables
- the page contains many annotations or descriptive sections

Use `no` when:

- the page is mostly visual
- only sparse labels are present
- text is limited and lightweight

This field describes **textual density**, not whether the content is prose only.

---

#### `is_candidate_page`

Whether the page should be retained as a retrieval candidate for downstream VisualRAG tasks.

- Type: `string`
- Required: yes
- Allowed values: `yes`, `no`

Use `yes` for pages with engineering retrieval value, such as:

- schematics
- assembly pages
- fabrication pages
- layout pages
- BOM pages
- mixed technical overview pages

Use `no` for pages with low retrieval value, such as:

- legal disclaimers
- administrative pages
- blank or separator pages
- pages with minimal engineering content

This is a retrieval-oriented field and may evolve as the retrieval pipeline changes.

---

#### `label_notes`

Free-text annotation explaining the page label.

- Type: `string`
- Required: yes

Purpose:

- documents why the page received its labels
- supports QA and relabeling
- improves consistency across annotation passes

Recommended style:

- concise
- descriptive
- lowercase English text is preferred
- focus on dominant content

Examples:

- `bill of materials page 2 with resistors inductors and connectors`
- `mechanical drawing page with board outline and mounting hole dimensions`
- `important notice legal disclaimer page with dense text`
- `overview page containing schematic layout parts list and ordering guide`

---

### 5.6 General Notes Fields

#### `notes`

General-purpose note field.

- Type: `string`
- Required: no

Purpose:

- stores miscellaneous notes not specific to labeling logic
- can remain empty

This field is distinct from `label_notes`.

---

## 6. Labeling Rules

This section defines the practical rules used during manual annotation.

### Rule 1: Label by dominant page purpose

If a page contains multiple content types, assign `page_type` according to the main engineering function of the page.

Examples:

- mixed intro page with schematic, layout, and parts list → often `other`
- mechanical drawing with dimensions → `assembly`
- BOM table with some footprint sizes → `bom`
- drill and stackup page → `fabrication`
- routed copper artwork page → `layout`

### Rule 2: Do not overreact to small visual elements

Small legends, logos, simple headers, decorative boxes, or page furniture do not determine `has_diagram`.

### Rule 3: BOM remains BOM

If a page is structurally a bill of materials, keep `page_type = bom` even if some rows describe:

- documents
- labels
- bare PCBs
- not installed parts
- package size information

### Rule 4: Dimensions are content-level, not type-level

A page may be:

- `bom` and `has_dimensions = yes`
- `assembly` and `has_dimensions = yes`
- `fabrication` and `has_dimensions = yes`
- `other` and `has_dimensions = no`

Dimension presence does not determine `page_type` by itself.

### Rule 5: Candidate pages are usefulness-driven

`is_candidate_page` reflects retrieval usefulness, not just page category.

Examples:

- a mixed technical overview page can be `other` and still `is_candidate_page = yes`
- a legal notice page is usually `other` and `is_candidate_page = no`

### Rule 6: `include_flag` is operational

`include_flag` is not the same as `is_candidate_page`.

Use `include_flag` to control whether a row is actively used in a given workflow, experiment, or export step.

---

## 7. Recommended Value Conventions

To keep the dataset machine-friendly and consistent:

### Binary-style fields

Use exactly:

- `yes`
- `no`

Fields following this convention include:

- `has_table`
- `has_diagram`
- `has_designators`
- `has_dimensions`
- `has_dense_text`
- `is_candidate_page`
- `include_flag`

Do not use:

- `Yes`
- `No`
- `Y`
- `N`
- `true`
- `false`
- `1`
- `0`

### Text normalization

Recommended conventions:

- lowercase values for `page_type`
- lowercase values for binary fields
- lowercase descriptive text for `label_notes`
- keep path fields exactly as stored on disk

---

## 8. Example Rows

### Example 1: fabrication page

| Field | Value |
|---|---|
| `page_id` | `doc001_p001` |
| `doc_id` | `doc001` |
| `page_num` | `1` |
| `document_family` | `fabrication` |
| `experiment_tier` | `core` |
| `page_type` | `fabrication` |
| `has_table` | `yes` |
| `has_diagram` | `no` |
| `has_designators` | `no` |
| `has_dimensions` | `no` |
| `has_dense_text` | `yes` |
| `is_candidate_page` | `yes` |
| `include_flag` | `yes` |
| `split` | `train` |
| `label_notes` | `fabrication requirements page with material panel and special requirement tables` |

### Example 2: BOM page

| Field | Value |
|---|---|
| `page_id` | `doc009_p001` |
| `page_type` | `bom` |
| `has_table` | `yes` |
| `has_diagram` | `no` |
| `has_designators` | `yes` |
| `has_dimensions` | `no` |
| `has_dense_text` | `yes` |
| `is_candidate_page` | `yes` |
| `label_notes` | `bill of materials page 1 for ti designs tida00440 leakage current measurement reference design main board` |

### Example 3: legal notice page

| Field | Value |
|---|---|
| `page_id` | `doc009_p003` |
| `page_type` | `other` |
| `has_table` | `no` |
| `has_diagram` | `no` |
| `has_designators` | `no` |
| `has_dimensions` | `no` |
| `has_dense_text` | `yes` |
| `is_candidate_page` | `no` |
| `label_notes` | `important notice for ti reference designs legal disclaimer page with dense text` |

### Example 4: layout page

| Field | Value |
|---|---|
| `page_id` | `doc001_p005` |
| `page_type` | `layout` |
| `has_table` | `no` |
| `has_diagram` | `yes` |
| `has_designators` | `no` |
| `has_dimensions` | `no` |
| `has_dense_text` | `no` |
| `is_candidate_page` | `yes` |
| `label_notes` | `layer view page showing board artwork and copper routing` |

### Example 5: mechanical drawing page

| Field | Value |
|---|---|
| `page_id` | `doc010_p002` |
| `page_type` | `assembly` |
| `has_table` | `no` |
| `has_diagram` | `yes` |
| `has_designators` | `yes` |
| `has_dimensions` | `yes` |
| `has_dense_text` | `no` |
| `is_candidate_page` | `yes` |
| `label_notes` | `mechanical drawing page with board outline hole pattern connector locations and dimensions for adis16006 pcb` |

---

## 9. Validation Recommendations

Before writing updated labels into `page_inventory.csv`, validate the following:

- all `page_id` values are unique in label definitions
- all required columns exist
- all binary fields use only `yes` or `no`
- all `page_type` values are within the allowed set
- all labeled `page_id` values exist in `page_inventory.csv`
- `width` and `height` are positive integers
- `split` values follow the expected experiment convention
- `label_notes` is not empty for manually labeled pages

Recommended validation checks:

- duplicate `page_id`
- missing required keys
- unexpected field names
- empty `label_notes`
- invalid `page_type`
- invalid binary value
- missing file paths
- invalid image dimension values

---

## 10. Current Operational Files

The schema is currently used with the following project assets:

- `data/metadata/page_inventory.csv`
- `data/metadata/data_schema.md`
- `scripts/update_page_labels_all.py`

Older per-document label update scripts may still exist, but the preferred workflow is to maintain a consolidated label update script.

---

## 11. Future Extensions

This schema is intentionally compact enough for current VisualRAG development, while remaining extensible.

Possible future fields include:

- `doc_title`
- `vendor`
- `document_type`
- `language`
- `ocr_text`
- `contains_block_diagram`
- `contains_connector_pinout`
- `contains_pcb_layout`
- `contains_footprint`
- `candidate_score`
- `chunk_id`
- `embedding_status`

If new fields are introduced, update this document and keep the schema synchronized with the CSV.

---

## 12. Changelog

### v2

- aligned schema with actual `page_inventory.csv` columns
- replaced abstract file field names with actual field names
- added `document_family`
- added `experiment_tier`
- added `pdf_path`
- added `image_path`
- added `image_name`
- added `width`
- added `height`
- added `include_flag`
- added `split`
- added `notes`
- expanded `page_type` allowed values to include `fabrication` and `layout`
- clarified the distinction between `is_candidate_page` and `include_flag`

### v1

- established page-level schema
- defined core manual labeling fields
- standardized basic page types and binary label conventions

---

## 13. Summary

The PCB VisualRAG Project uses a **page-centric metadata schema** built around `page_inventory.csv`.

The most important field groups are:

- identity fields:
  - `doc_id`
  - `page_id`
  - `page_num`

- file linkage fields:
  - `file_name`
  - `pdf_path`
  - `image_path`
  - `image_name`

- dataset organization fields:
  - `document_family`
  - `experiment_tier`
  - `split`
  - `include_flag`

- image metadata fields:
  - `width`
  - `height`

- page labeling fields:
  - `page_type`
  - `has_table`
  - `has_diagram`
  - `has_designators`
  - `has_dimensions`
  - `has_dense_text`
  - `is_candidate_page`
  - `label_notes`

- general note field:
  - `notes`

These fields should be maintained consistently using the dominant-content rule, retrieval usefulness, and operational inclusion logic.
