from pathlib import Path
import pandas as pd
import json

PROJECT_ROOT = Path(__file__).resolve().parents[2]

PAGE_CSV = PROJECT_ROOT / "data" / "metadata" / "page_inventory.csv"
ANNOTATION_DIR = PROJECT_ROOT / "data" / "annotations"
LABELS_CSV = ANNOTATION_DIR / "page_labels_updates.csv"
LABELS_JSONL = ANNOTATION_DIR / "page_labels_updates.jsonl"

TARGET_COLS = [
    "page_type",
    "has_table",
    "has_diagram",
    "has_designators",
    "has_dimensions",
    "has_dense_text",
    "is_candidate_page",
    "label_notes",
]

# 内置标签作为回退方案。
# 如果存在 data/annotations/page_labels_updates.csv 或 jsonl，则优先使用外部文件。
LABELS = [
    {
        "page_id": "doc007_p001",
        "page_type": "other",
        "has_table": "yes",
        "has_diagram": "yes",
        "has_designators": "yes",
        "has_dimensions": "no",
        "has_dense_text": "yes",
        "is_candidate_page": "yes",
        "label_notes": "overview page containing schematic layout top view parts list and power supply table for adis1620x pcb",
    },
    {
        "page_id": "doc007_p002",
        "page_type": "assembly",
        "has_table": "yes",
        "has_diagram": "yes",
        "has_designators": "yes",
        "has_dimensions": "yes",
        "has_dense_text": "yes",
        "is_candidate_page": "yes",
        "label_notes": "mechanical drawing page with ordering guide esd caution and board outline dimensions for adis1620x pcb",
    },
    {
        "page_id": "doc008_p001",
        "page_type": "bom",
        "has_table": "yes",
        "has_diagram": "no",
        "has_designators": "yes",
        "has_dimensions": "no",
        "has_dense_text": "yes",
        "is_candidate_page": "yes",
        "label_notes": "bill of materials page 1 for mcp6n11 wheatstone bridge reference design including document entries capacitors and connectors",
    },
    {
        "page_id": "doc008_p002",
        "page_type": "bom",
        "has_table": "yes",
        "has_diagram": "no",
        "has_designators": "yes",
        "has_dimensions": "no",
        "has_dense_text": "yes",
        "is_candidate_page": "yes",
        "label_notes": "bill of materials page 2 for mcp6n11 wheatstone bridge reference design listing headers inductors and resistors",
    },
    {
        "page_id": "doc008_p003",
        "page_type": "bom",
        "has_table": "yes",
        "has_diagram": "no",
        "has_designators": "yes",
        "has_dimensions": "no",
        "has_dense_text": "yes",
        "is_candidate_page": "yes",
        "label_notes": "bill of materials page 3 for mcp6n11 wheatstone bridge reference design listing remaining resistors ics switch resonator and not installed parts",
    },
    {
        "page_id": "doc009_p001",
        "page_type": "bom",
        "has_table": "yes",
        "has_diagram": "no",
        "has_designators": "yes",
        "has_dimensions": "no",
        "has_dense_text": "yes",
        "is_candidate_page": "yes",
        "label_notes": "bill of materials page 1 for ti designs tida00440 leakage current measurement reference design main board",
    },
    {
        "page_id": "doc009_p002",
        "page_type": "bom",
        "has_table": "yes",
        "has_diagram": "no",
        "has_designators": "yes",
        "has_dimensions": "yes",
        "has_dense_text": "yes",
        "is_candidate_page": "yes",
        "label_notes": "bill of materials page 2 for tida00440 including remaining main board entries and daughter board items",
    },
    {
        "page_id": "doc009_p003",
        "page_type": "other",
        "has_table": "no",
        "has_diagram": "no",
        "has_designators": "no",
        "has_dimensions": "no",
        "has_dense_text": "yes",
        "is_candidate_page": "no",
        "label_notes": "important notice for ti reference designs legal disclaimer page with dense text",
    },
    {
        "page_id": "doc010_p001",
        "page_type": "other",
        "has_table": "yes",
        "has_diagram": "yes",
        "has_designators": "yes",
        "has_dimensions": "no",
        "has_dense_text": "yes",
        "is_candidate_page": "yes",
        "label_notes": "overview page containing schematic layout top view parts list power supply table and ordering guide for adis16006 pcb",
    },
    {
        "page_id": "doc010_p002",
        "page_type": "assembly",
        "has_table": "no",
        "has_diagram": "yes",
        "has_designators": "yes",
        "has_dimensions": "yes",
        "has_dense_text": "no",
        "is_candidate_page": "yes",
        "label_notes": "mechanical drawing page with board outline hole pattern connector locations and dimensions for adis16006 pcb",
    },
]


def load_labels_from_csv(path: Path):
    df = pd.read_csv(path, dtype=str).fillna("")
    records = df.to_dict(orient="records")
    return records


def load_labels_from_jsonl(path: Path):
    rows = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def choose_label_source():
    if LABELS_CSV.exists():
        print(f"[INFO] Using external labels CSV: {LABELS_CSV}")
        return load_labels_from_csv(LABELS_CSV), f"csv:{LABELS_CSV}"
    if LABELS_JSONL.exists():
        print(f"[INFO] Using external labels JSONL: {LABELS_JSONL}")
        return load_labels_from_jsonl(LABELS_JSONL), f"jsonl:{LABELS_JSONL}"

    print("[INFO] No external label file found. Using built-in LABELS.")
    return LABELS, "builtin:LABELS"


def normalize_value(v):
    if pd.isna(v):
        return ""
    return str(v).strip()


def validate_labels(labels):
    required_keys = {"page_id", *TARGET_COLS}
    seen = set()
    duplicates = []

    for item in labels:
        keys = set(item.keys())
        missing = required_keys - keys
        extra = keys - required_keys

        if missing:
            raise ValueError(
                f"Label for page_id={item.get('page_id', '<missing>')} missing keys: {sorted(missing)}"
            )

        if extra:
            raise ValueError(
                f"Label for page_id={item.get('page_id', '<missing>')} has unexpected keys: {sorted(extra)}"
            )

        page_id = normalize_value(item["page_id"])
        if not page_id:
            raise ValueError("Found label with empty page_id")

        if page_id in seen:
            duplicates.append(page_id)
        seen.add(page_id)

    if duplicates:
        raise ValueError(f"Duplicate page_id entries found in labels: {sorted(set(duplicates))}")


def ensure_target_columns(df):
    for col in TARGET_COLS:
        if col not in df.columns:
            df[col] = ""
        df[col] = df[col].fillna("").astype(str)
    return df


def apply_labels(df, labels):
    label_df = pd.DataFrame(labels).copy()

    for col in ["page_id", *TARGET_COLS]:
        if col not in label_df.columns:
            label_df[col] = ""
        label_df[col] = label_df[col].map(normalize_value)

    label_map = label_df.set_index("page_id").to_dict(orient="index")

    updated_rows = 0
    missing_page_ids = []
    changed_cell_count = 0

    df["page_id"] = df["page_id"].fillna("").astype(str)

    for page_id, values in label_map.items():
        mask = df["page_id"] == page_id

        if mask.any():
            for col in TARGET_COLS:
                old_vals = df.loc[mask, col].astype(str)
                new_val = str(values[col])
                changed_cell_count += int((old_vals != new_val).sum())
                df.loc[mask, col] = new_val
            updated_rows += int(mask.sum())
        else:
            missing_page_ids.append(page_id)

    return df, updated_rows, missing_page_ids, label_map, changed_cell_count


def print_summary(df, label_map, updated_rows, missing_page_ids, changed_cell_count, label_source):
    print(f"[INFO] Label source: {label_source}")
    print(f"[INFO] Requested labels: {len(label_map)}")
    print(f"[INFO] Updated rows: {updated_rows}")
    print(f"[INFO] Changed cells: {changed_cell_count}")
    print(f"[INFO] Missing page_ids in inventory: {len(missing_page_ids)}")

    if missing_page_ids:
        print("[WARN] Missing page_ids:")
        for pid in missing_page_ids[:20]:
            print(f"  - {pid}")
        if len(missing_page_ids) > 20:
            print(f"  ... and {len(missing_page_ids) - 20} more")

    print("\n[INFO] page_type distribution:")
    if "page_type" in df.columns:
        print(df["page_type"].fillna("").value_counts(dropna=False).to_string())

    print("\n[INFO] is_candidate_page distribution:")
    if "is_candidate_page" in df.columns:
        print(df["is_candidate_page"].fillna("").value_counts(dropna=False).to_string())


def maybe_export_template(df: pd.DataFrame):
    ANNOTATION_DIR.mkdir(parents=True, exist_ok=True)
    template_path = ANNOTATION_DIR / "page_labels_updates.template.csv"

    export_cols = ["page_id", *TARGET_COLS]
    template_df = df.copy()

    for col in export_cols:
        if col not in template_df.columns:
            template_df[col] = ""

    template_df = template_df[export_cols]
    template_df.to_csv(template_path, index=False, encoding="utf-8-sig")
    print(f"[INFO] Exported label template: {template_path}")


def main():
    if not PAGE_CSV.exists():
        raise FileNotFoundError(f"Page inventory not found: {PAGE_CSV}")

    labels, label_source = choose_label_source()
    validate_labels(labels)

    df = pd.read_csv(PAGE_CSV, dtype=str).fillna("")
    df = ensure_target_columns(df)

    df, updated_rows, missing_page_ids, label_map, changed_cell_count = apply_labels(df, labels)

    df.to_csv(PAGE_CSV, index=False, encoding="utf-8-sig")

    print(f"[INFO] Updated page inventory saved to: {PAGE_CSV}")
    print_summary(df, label_map, updated_rows, missing_page_ids, changed_cell_count, label_source)
    maybe_export_template(df)


if __name__ == "__main__":
    main()
