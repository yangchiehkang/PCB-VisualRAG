from pathlib import Path
import json
import re
from collections import defaultdict

PROJECT_ROOT = Path(__file__).resolve().parents[2]
INPUT_PATH = PROJECT_ROOT / "data" / "metadata" / "corpus.jsonl"
OUTPUT_PATH = PROJECT_ROOT / "data" / "metadata" / "queries.auto.jsonl"


def load_jsonl(path: Path):
    data = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            data.append(json.loads(line))
    return data


def save_jsonl(path: Path, rows):
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def normalize_text(text):
    if not text:
        return ""
    return str(text).lower().strip()


def infer_difficulty(query_type, note, doc_page_count):
    note = normalize_text(note)

    if query_type == "similarity_based_interference":
        return "hard"
    if query_type == "cross_page_consistency":
        return "hard"
    if query_type == "component_localization":
        return "medium" if doc_page_count > 3 else "easy"
    if query_type == "structure_legend_interpretation":
        return "medium"
    if query_type == "parameter_lookup":
        if any(k in note for k in ["table", "bom", "material", "drill"]):
            return "easy"
        return "medium"
    return "medium"


def build_query(query_id, query_text, query_type, difficulty, page_id, doc_id, note):
    return {
        "query_id": query_id,
        "query_text": query_text,
        "query_type": query_type,
        "difficulty": difficulty,
        "gold_page_ids": [page_id],
        "gold_doc_ids": [doc_id],
        "note": note
    }


def extract_queries_from_page(page, doc_page_count):
    page_id = page["page_id"]
    doc_id = page["doc_id"]
    page_type = normalize_text(page.get("page_type", ""))
    note = page.get("note", "") or page.get("label_notes", "") or ""
    note_l = normalize_text(note)

    queries = []

    if page_type in ["fabrication", "bom"] or any(
        k in note_l for k in ["table", "material", "panel", "drill", "thickness", "dimension", "bom"]
    ):
        qtext = "Which page contains the engineering table or specification block for this parameter set?"
        if "material" in note_l or "panel" in note_l:
            qtext = "Which page contains the fabrication requirements table with material and panel specifications?"
        elif "drill" in note_l:
            qtext = "Which page contains the drill specification table with hole size information?"
        elif "thickness" in note_l or "stackup" in note_l:
            qtext = "Which page contains the board thickness or stackup parameter information?"
        elif "bom" in page_type or "bom" in note_l:
            qtext = "Which page lists the component entries and values in the bill of materials?"
        elif "dimension" in note_l:
            qtext = "Which page contains the dimensional requirements or size annotations?"
        queries.append(("parameter_lookup", qtext))

    if page_type in ["fabrication", "schematic"] or any(
        k in note_l for k in ["legend", "stackup", "cross-section", "cross section", "bevel", "breakaway", "diagram"]
    ):
        qtext = "Which page shows the engineering structure or legend relevant to this design?"
        if "stackup" in note_l:
            qtext = "Which page shows the PCB layer stack and thickness structure?"
        elif "legend" in note_l:
            qtext = "Which page contains the legend explaining the engineering symbols or markings?"
        elif "bevel" in note_l or "breakaway" in note_l:
            qtext = "Which page explains the breakaway or bevel structure with dimensional annotations?"
        elif "cross-section" in note_l or "cross section" in note_l:
            qtext = "Which page shows the cross-sectional structure of the board?"
        queries.append(("structure_legend_interpretation", qtext))

    if page_type in ["assembly", "layout"] or any(
        k in note_l for k in ["placement", "callout", "reference designator", "board view", "designator"]
    ):
        qtext = "Which page shows the placement of a component in the board view?"
        if "top" in note_l:
            qtext = "Which page shows the top-side board view with labeled component placement?"
        elif "bottom" in note_l:
            qtext = "Which page shows the bottom-side board view with labeled component placement?"
        elif "designator" in note_l:
            qtext = "Which page contains the board view with visible reference designators?"
        queries.append(("component_localization", qtext))

    output = []
    for query_type, qtext in queries:
        difficulty = infer_difficulty(query_type, note, doc_page_count)
        output.append((query_type, qtext, difficulty, page_id, doc_id, note))

    return output


def generate_cross_page_queries(doc_pages):
    queries = []
    by_type = defaultdict(list)
    for p in doc_pages:
        by_type[normalize_text(p.get("page_type", ""))].append(p)

    if by_type["bom"] and by_type["assembly"]:
        bom_page = by_type["bom"][0]
        asm_page = by_type["assembly"][0]
        queries.append({
            "query_type": "cross_page_consistency",
            "query_text": "Which pages can be used together to match BOM entries with assembly reference designators?",
            "difficulty": "hard",
            "gold_page_ids": [bom_page["page_id"], asm_page["page_id"]],
            "gold_doc_ids": [bom_page["doc_id"]],
            "note": "cross-page mapping between BOM and assembly views"
        })

    if by_type["layout"] and by_type["fabrication"]:
        layout_page = by_type["layout"][0]
        fab_page = by_type["fabrication"][0]
        queries.append({
            "query_type": "cross_page_consistency",
            "query_text": "Which pages can be used together to verify the design in both layout and fabrication views?",
            "difficulty": "hard",
            "gold_page_ids": [layout_page["page_id"], fab_page["page_id"]],
            "gold_doc_ids": [layout_page["doc_id"]],
            "note": "cross-page mapping between layout and fabrication pages"
        })

    return queries


def generate_similarity_queries(grouped_pages):
    queries = []
    for doc_id, pages in grouped_pages.items():
        if len(pages) >= 8:
            target_page = pages[-1]
            queries.append({
                "query_type": "similarity_based_interference",
                "query_text": "Which page corresponds to the correct design variant among several visually similar pages in this document?",
                "difficulty": "hard",
                "gold_page_ids": [target_page["page_id"]],
                "gold_doc_ids": [doc_id],
                "note": "heuristic similarity-based query for a multi-page document with repeated technical page patterns"
            })
    return queries


def main():
    if not INPUT_PATH.exists():
        raise FileNotFoundError(f"Input corpus not found: {INPUT_PATH}")

    pages = load_jsonl(INPUT_PATH)

    candidate_pages = [
        p for p in pages
        if normalize_text(str(p.get("is_candidate_page", ""))) in ["yes", "true", "1"]
    ]
    if not candidate_pages:
        candidate_pages = pages

    grouped_pages = defaultdict(list)
    for p in candidate_pages:
        grouped_pages[p["doc_id"]].append(p)

    all_queries = []
    qid = 1

    for doc_id, doc_pages in grouped_pages.items():
        doc_page_count = len(doc_pages)

        for page in doc_pages:
            extracted = extract_queries_from_page(page, doc_page_count)
            for query_type, query_text, difficulty, page_id, doc_id_, note in extracted:
                all_queries.append(
                    build_query(
                        query_id=f"q{qid:03d}",
                        query_text=query_text,
                        query_type=query_type,
                        difficulty=difficulty,
                        page_id=page_id,
                        doc_id=doc_id_,
                        note=note,
                    )
                )
                qid += 1

        cross_page = generate_cross_page_queries(doc_pages)
        for item in cross_page:
            item["query_id"] = f"q{qid:03d}"
            all_queries.append(item)
            qid += 1

    for item in generate_similarity_queries(grouped_pages):
        item["query_id"] = f"q{qid:03d}"
        all_queries.append(item)
        qid += 1

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    save_jsonl(OUTPUT_PATH, all_queries)

    print(f"[INFO] Candidate pages: {len(candidate_pages)}")
    print(f"[INFO] Generated queries: {len(all_queries)}")
    print(f"[INFO] Output: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
