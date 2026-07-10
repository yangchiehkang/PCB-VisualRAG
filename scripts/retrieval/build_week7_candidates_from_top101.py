from pathlib import Path
from collections import defaultdict

PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_FILES = {
    "bm25": PROJECT_ROOT / "results" / "baselines" / "bm25_top101_run.tsv",
    "visual": PROJECT_ROOT / "results" / "baselines" / "single_vector_top101_run.tsv",
}

OUT_DIR = PROJECT_ROOT / "artifacts" / "rerank_cache" / "week7_topN"
NS = [10, 20, 50, 100]


def load_run(path: Path):
    rows_by_qid = defaultdict(list)

    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            parts = line.split("\t")
            if len(parts) < 6:
                parts = line.split()

            qid = parts[0]
            doc_id = parts[2]
            rank = int(parts[3])
            score = float(parts[4])
            run_name = parts[5]

            rows_by_qid[qid].append((rank, doc_id, score, run_name))

    for qid in rows_by_qid:
        rows_by_qid[qid].sort(key=lambda x: x[0])

    return rows_by_qid


def write_candidates(rows_by_qid, output_path: Path, top_n: int, method_name: str):
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as out_f:
        for qid in sorted(rows_by_qid.keys()):
            rows = rows_by_qid[qid][:top_n]
            for new_rank, (_, doc_id, score, _) in enumerate(rows, start=1):
                out_f.write(
                    f"{qid}\tQ0\t{doc_id}\t{new_rank}\t{score:.6f}\t{method_name}_N{top_n}\n"
                )


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    for method, input_path in INPUT_FILES.items():
        if not input_path.exists():
            raise FileNotFoundError(f"Missing input run: {input_path}")

        rows_by_qid = load_run(input_path)

        for n in NS:
            output_path = OUT_DIR / f"candidates_{method}_N{n}.tsv"
            write_candidates(rows_by_qid, output_path, n, method)
            print(f"Wrote: {output_path}")

    print("Done.")


if __name__ == "__main__":
    main()
