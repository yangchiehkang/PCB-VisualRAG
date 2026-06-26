from pathlib import Path
import argparse
import base64
import csv
import json
import time
import requests


PROJECT_ROOT = Path(r"E:\Working\PCB_VisualRAG_Project")

INPUT_CSV = PROJECT_ROOT / "results" / "week8" / "visual_rag" / "qa_inputs.csv"
OUT_JSONL = PROJECT_ROOT / "results" / "week8" / "visual_rag" / "qa_outputs_ollama.jsonl"
OUT_CSV = PROJECT_ROOT / "results" / "week8" / "visual_rag" / "qa_outputs_ollama.csv"
OUT_FILLED_CSV = PROJECT_ROOT / "results" / "week8" / "visual_rag" / "qa_outputs_manual_filled.csv"

OLLAMA_URL = "http://localhost:11434/api/generate"

DEFAULT_SETTINGS = [
    "Gold Evidence",
    "BM25",
    "Full MV",
    "Hybrid Fusion",
    "Budgeted MV",
    "Gold Masked",
    "Random Masked",
]


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


def encode_image(path):
    with path.open("rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def call_ollama(model, prompt, image_path, temperature=0.0, timeout=180):
    image_b64 = encode_image(image_path)

    payload = {
        "model": model,
        "prompt": prompt,
        "images": [image_b64],
        "stream": False,
        "options": {
            "temperature": temperature,
        },
    }

    resp = requests.post(
        OLLAMA_URL,
        json=payload,
        timeout=timeout,
    )

    resp.raise_for_status()
    data = resp.json()

    return data.get("response", "").strip(), data


def parse_answer(text):
    short_answer = ""
    evidence_description = ""
    confidence = ""

    for line in text.splitlines():
        line_strip = line.strip()

        low = line_strip.lower()

        if low.startswith("short answer:"):
            short_answer = line_strip.split(":", 1)[1].strip()

        elif low.startswith("evidence description:"):
            evidence_description = line_strip.split(":", 1)[1].strip()

        elif low.startswith("confidence:"):
            confidence = line_strip.split(":", 1)[1].strip()

    if not short_answer:
        short_answer = text.strip()

    return short_answer, evidence_description, confidence


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=str, default="llama3.2-vision")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--settings", type=str, default="")
    parser.add_argument("--sleep", type=float, default=0.2)
    parser.add_argument("--temperature", type=float, default=0.0)
    args = parser.parse_args()

    if args.settings.strip():
        selected_settings = [x.strip() for x in args.settings.split(",") if x.strip()]
    else:
        selected_settings = DEFAULT_SETTINGS

    rows = list(csv.DictReader(INPUT_CSV.open("r", encoding="utf-8-sig", newline="")))

    rows = [r for r in rows if r["setting"] in selected_settings]
    rows = [r for r in rows if r.get("image_path", "").strip()]

    if args.limit and args.limit > 0:
        rows = rows[:args.limit]

    OUT_JSONL.parent.mkdir(parents=True, exist_ok=True)

    out_rows = []

    with OUT_JSONL.open("w", encoding="utf-8") as jf:
        for i, r in enumerate(rows, start=1):
            query_id = r["query_id"]
            setting = r["setting"]
            case_id = f"{query_id}__{setting.replace(' ', '_')}"

            rel_image_path = r["image_path"]
            image_path = PROJECT_ROOT / rel_image_path

            prompt = PROMPT_TEMPLATE.format(query=r["query"])

            print(f"[{i}/{len(rows)}] {case_id}")
            print("Image:", image_path)

            if not image_path.exists():
                print("SKIP: image missing")
                continue

            try:
                raw_answer, raw_json = call_ollama(
                    model=args.model,
                    prompt=prompt,
                    image_path=image_path,
                    temperature=args.temperature,
                )

                short_answer, evidence_description, confidence = parse_answer(raw_answer)

                out = {
                    "case_id": case_id,
                    "query_id": query_id,
                    "setting": setting,
                    "query": r["query"],
                    "gold_page_id": r["gold_page_id"],
                    "page_id": r["page_id"],
                    "rank": r.get("rank", ""),
                    "retrieval_score": r.get("retrieval_score", ""),
                    "is_gold_page": r.get("is_gold_page", ""),
                    "image_path": rel_image_path,
                    "model": args.model,
                    "prompt": prompt,
                    "vlm_answer": short_answer,
                    "evidence_description": evidence_description,
                    "confidence": confidence,
                    "raw_response": raw_answer,
                    "status": "OK",
                    "error": "",
                }

            except Exception as e:
                out = {
                    "case_id": case_id,
                    "query_id": query_id,
                    "setting": setting,
                    "query": r["query"],
                    "gold_page_id": r["gold_page_id"],
                    "page_id": r["page_id"],
                    "rank": r.get("rank", ""),
                    "retrieval_score": r.get("retrieval_score", ""),
                    "is_gold_page": r.get("is_gold_page", ""),
                    "image_path": rel_image_path,
                    "model": args.model,
                    "prompt": prompt,
                    "vlm_answer": "",
                    "evidence_description": "",
                    "confidence": "",
                    "raw_response": "",
                    "status": "ERROR",
                    "error": str(e),
                }

                print("ERROR:", e)

            jf.write(json.dumps(out, ensure_ascii=False) + "\n")
            jf.flush()

            out_rows.append(out)

            time.sleep(args.sleep)

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

    with OUT_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(out_rows)

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

    for r in out_rows:
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
            "notes": r["status"] if r["status"] != "OK" else "",
        })

    with OUT_FILLED_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=filled_fields)
        writer.writeheader()
        writer.writerows(filled_rows)

    print()
    print("[Week8] Ollama VLM QA finished.")
    print("Cases:", len(out_rows))
    print("Wrote:", OUT_JSONL)
    print("Wrote:", OUT_CSV)
    print("Wrote:", OUT_FILLED_CSV)


if __name__ == "__main__":
    main()
