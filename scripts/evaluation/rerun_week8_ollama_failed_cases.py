from pathlib import Path
import base64
import csv
import json
import time
import requests


PROJECT_ROOT = Path(r"E:\Working\PCB_VisualRAG_Project")

QA_INPUTS = PROJECT_ROOT / "results" / "week8" / "visual_rag" / "qa_inputs.csv"
OLD_OUTPUTS = PROJECT_ROOT / "results" / "week8" / "visual_rag" / "qa_outputs_ollama.csv"

OUT_JSONL = PROJECT_ROOT / "results" / "week8" / "visual_rag" / "qa_outputs_ollama_rerun.jsonl"
OUT_CSV = PROJECT_ROOT / "results" / "week8" / "visual_rag" / "qa_outputs_ollama_rerun.csv"
OUT_MERGED_CSV = PROJECT_ROOT / "results" / "week8" / "visual_rag" / "qa_outputs_ollama_merged.csv"
OUT_FILLED = PROJECT_ROOT / "results" / "week8" / "visual_rag" / "qa_outputs_manual_filled.csv"

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.2-vision"


PROMPT_TEMPLATE = """You are answering a question about a PCB engineering document page.

Use only the provided page image as evidence.
If the page does not contain enough information, answer exactly:
Not enough evidence.

Question:
{query}

Return your answer in this exact format:
Short answer: <one concise answer>
Evidence description: <what visible evidence supports the answer>
Confidence: high / medium / low
"""


def read_csv(path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path, rows, fieldnames):
    path.parent.mkdir(parents=True, exist_ok=True)
    clean = [{k: r.get(k, "") for k in fieldnames} for r in rows]

    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(clean)


def encode_image(path):
    with path.open("rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def parse_answer(text):
    short_answer = ""
    evidence_description = ""
    confidence = ""

    for line in text.splitlines():
        s = line.strip()
        low = s.lower()

        if low.startswith("short answer:"):
            short_answer = s.split(":", 1)[1].strip()
        elif low.startswith("evidence description:"):
            evidence_description = s.split(":", 1)[1].strip()
        elif low.startswith("confidence:"):
            confidence = s.split(":", 1)[1].strip()

    if not short_answer:
        short_answer = text.strip()

    return short_answer, evidence_description, confidence


def call_ollama(prompt, image_path, timeout=420):
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "images": [encode_image(image_path)],
        "stream": False,
        "options": {
            "temperature": 0.0,
            "num_predict": 128,
        },
    }

    r = requests.post(OLLAMA_URL, json=payload, timeout=timeout)
    r.raise_for_status()
    data = r.json()
    return data.get("response", "").strip()


def case_id_from_input(r):
    return f"{r['query_id']}__{r['setting'].replace(' ', '_')}"


def main():
    input_rows = read_csv(QA_INPUTS)
    old_rows = read_csv(OLD_OUTPUTS)

    old_by_case = {r["case_id"]: r for r in old_rows}

    failed_case_ids = set()

    for r in old_rows:
        if r.get("status") != "OK" or not r.get("vlm_answer", "").strip():
            failed_case_ids.add(r["case_id"])

    print("Failed / blank cases:", len(failed_case_ids))
    for cid in sorted(failed_case_ids):
        print(cid)

    rerun_rows = []

    with OUT_JSONL.open("w", encoding="utf-8") as jf:
        for i, r in enumerate(input_rows, start=1):
            case_id = case_id_from_input(r)

            if case_id not in failed_case_ids:
                continue

            image_path = PROJECT_ROOT / r["image_path"]
            prompt = PROMPT_TEMPLATE.format(query=r["query"])

            print("RERUN:", case_id)
            print("Image:", image_path)

            try:
                raw = call_ollama(prompt, image_path)
                short, evidence, confidence = parse_answer(raw)

                out = {
                    "case_id": case_id,
                    "query_id": r["query_id"],
                    "setting": r["setting"],
                    "query": r["query"],
                    "gold_page_id": r["gold_page_id"],
                    "page_id": r["page_id"],
                    "rank": r.get("rank", ""),
                    "retrieval_score": r.get("retrieval_score", ""),
                    "is_gold_page": r.get("is_gold_page", ""),
                    "image_path": r["image_path"],
                    "model": MODEL,
                    "prompt": prompt,
                    "vlm_answer": short,
                    "evidence_description": evidence,
                    "confidence": confidence,
                    "raw_response": raw,
                    "status": "OK",
                    "error": "",
                }

            except Exception as e:
                old = old_by_case.get(case_id, {})
                out = {
                    "case_id": case_id,
                    "query_id": r["query_id"],
                    "setting": r["setting"],
                    "query": r["query"],
                    "gold_page_id": r["gold_page_id"],
                    "page_id": r["page_id"],
                    "rank": r.get("rank", ""),
                    "retrieval_score": r.get("retrieval_score", ""),
                    "is_gold_page": r.get("is_gold_page", ""),
                    "image_path": r["image_path"],
                    "model": MODEL,
                    "prompt": prompt,
                    "vlm_answer": old.get("vlm_answer", ""),
                    "evidence_description": old.get("evidence_description", ""),
                    "confidence": old.get("confidence", ""),
                    "raw_response": old.get("raw_response", ""),
                    "status": "ERROR",
                    "error": str(e),
                }

                print("ERROR:", e)

            rerun_rows.append(out)
            jf.write(json.dumps(out, ensure_ascii=False) + "\n")
            jf.flush()

            time.sleep(0.5)

    fieldnames = [
        "case_id",
        "query_id",
        "setting",
        "query",
        "gold_page_id",
        "page_id",
        "rank",
        "retrieval_score",
        "is_gold_page",
        "image_path",
        "model",
        "prompt",
        "vlm_answer",
        "evidence_description",
        "confidence",
        "raw_response",
        "status",
        "error",
    ]

    write_csv(OUT_CSV, rerun_rows, fieldnames)

    rerun_by_case = {r["case_id"]: r for r in rerun_rows if r.get("status") == "OK" and r.get("vlm_answer", "").strip()}

    merged = []

    for r in old_rows:
        cid = r["case_id"]
        if cid in rerun_by_case:
            merged.append(rerun_by_case[cid])
        else:
            merged.append(r)

    write_csv(OUT_MERGED_CSV, merged, fieldnames)

    filled_fields = [
        "case_id",
        "query_id",
        "setting",
        "query",
        "gold_page_id",
        "page_id",
        "is_gold_page",
        "image_path",
        "vlm_answer",
        "evidence_description",
        "confidence",
        "notes",
    ]

    filled_rows = []

    for r in merged:
        filled_rows.append({
            "case_id": r["case_id"],
            "query_id": r["query_id"],
            "setting": r["setting"],
            "query": r["query"],
            "gold_page_id": r["gold_page_id"],
            "page_id": r["page_id"],
            "is_gold_page": r["is_gold_page"],
            "image_path": r["image_path"],
            "vlm_answer": r["vlm_answer"],
            "evidence_description": r["evidence_description"],
            "confidence": r["confidence"],
            "notes": "" if r.get("status") == "OK" else r.get("error", "ERROR"),
        })

    write_csv(OUT_FILLED, filled_rows, filled_fields)

    print()
    print("[Week8] Rerun finished.")
    print("Rerun cases:", len(rerun_rows))
    print("Merged outputs:", len(merged))
    print("Wrote:", OUT_JSONL)
    print("Wrote:", OUT_CSV)
    print("Wrote:", OUT_MERGED_CSV)
    print("Updated:", OUT_FILLED)


if __name__ == "__main__":
    main()
