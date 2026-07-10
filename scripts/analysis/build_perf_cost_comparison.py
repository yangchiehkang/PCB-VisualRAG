from pathlib import Path
import argparse
import json
import csv


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_metric_csv(path: Path):
    data = {}
    with path.open("r", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            if len(row) >= 2:
                data[row[0]] = row[1]
    return data


def main():
    parser = argparse.ArgumentParser(description="Build performance-cost comparison table.")
    parser.add_argument("--full-metrics", type=str, default=str(PROJECT_ROOT / "results" / "full_multivector" / "full_mv_metrics.json"))
    parser.add_argument("--single-metrics", type=str, default=str(PROJECT_ROOT / "results" / "single_vector" / "single_vector_metrics.json"))
    parser.add_argument("--full-cost", type=str, default=str(PROJECT_ROOT / "results" / "analysis" / "full_mv_cost_stats.csv"))
    parser.add_argument("--single-cost", type=str, default=str(PROJECT_ROOT / "results" / "analysis" / "single_vector_cost_stats.csv"))
    parser.add_argument("--output", type=str, default=str(PROJECT_ROOT / "results" / "analysis" / "perf_cost_comparison.csv"))
    args = parser.parse_args()

    full_metrics = load_json(Path(args.full_metrics))
    single_metrics = load_json(Path(args.single_metrics))

    full_cost = load_metric_csv(Path(args.full_cost))
    single_cost = load_metric_csv(Path(args.single_cost))

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)

    rows = [
        ["category", "metric", "full_multivector", "single_vector"],
        ["effectiveness", "Recall@10", full_metrics.get("Recall@10", ""), single_metrics.get("Recall@10", "")],
        ["effectiveness", "MRR", full_metrics.get("MRR", ""), single_metrics.get("MRR", "")],
        ["effectiveness", "nDCG@10", full_metrics.get("nDCG@10", ""), single_metrics.get("nDCG@10", "")],
        ["cost", "vectors_per_page", full_cost.get("vectors_per_page", ""), single_cost.get("vectors_per_page", "")],
        ["cost", "estimated_raw_index_size_mb", full_cost.get("estimated_raw_index_size_mb", ""), single_cost.get("estimated_raw_index_size_mb", "")],
        ["cost", "avg_query_latency_ms", full_cost.get("avg_query_latency_ms", ""), single_cost.get("avg_query_latency_ms", "")],
    ]

    with output.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(rows)

    print(f"Wrote performance-cost comparison to: {output}")


if __name__ == "__main__":
    main()
