from pathlib import Path
import argparse
import json
import csv


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_metric_csv(path: Path):
    data = {}
    with path.open("r", encoding="utf-8") as in_f:
        reader = csv.reader(in_f)
        next(reader)
        for row in reader:
            if len(row) >= 2:
                data[row[0]] = row[1]
    return data


def to_float(x):
    return float(x)


def safe_ratio(a, b):
    if b == 0:
        return ""
    return a / b


def main():
    parser = argparse.ArgumentParser(description="Build performance-cost comparison table with ratios.")
    parser.add_argument("--full-metrics", type=str, default=str(PROJECT_ROOT / "results" / "full_multivector" / "full_mv_metrics.json"))
    parser.add_argument("--single-metrics", type=str, default=str(PROJECT_ROOT / "results" / "single_vector" / "single_vector_metrics.json"))
    parser.add_argument("--full-cost", type=str, default=str(PROJECT_ROOT / "results" / "analysis" / "full_mv_cost_stats.csv"))
    parser.add_argument("--single-cost", type=str, default=str(PROJECT_ROOT / "results" / "analysis" / "single_vector_cost_stats.csv"))
    parser.add_argument("--output", type=str, default=str(PROJECT_ROOT / "results" / "analysis" / "perf_cost_comparison_with_ratio.csv"))
    args = parser.parse_args()

    full_metrics = load_json(Path(args.full_metrics))
    single_metrics = load_json(Path(args.single_metrics))
    full_cost = load_metric_csv(Path(args.full_cost))
    single_cost = load_metric_csv(Path(args.single_cost))

    single_vectors = to_float(single_cost["vectors_per_page"])
    full_vectors = to_float(full_cost["vectors_per_page"])
    single_index = to_float(single_cost["estimated_raw_index_size_mb"])
    full_index = to_float(full_cost["estimated_raw_index_size_mb"])
    single_latency = to_float(single_cost["avg_query_latency_ms"])
    full_latency = to_float(full_cost["avg_query_latency_ms"])

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)

    rows = [
        ["category", "metric", "full_multivector", "single_vector", "ratio_full_over_single"],
        ["effectiveness", "Recall@10", full_metrics.get("Recall@10", ""), single_metrics.get("Recall@10", ""), ""],
        ["effectiveness", "MRR", full_metrics.get("MRR", ""), single_metrics.get("MRR", ""), ""],
        ["effectiveness", "nDCG@10", full_metrics.get("nDCG@10", ""), single_metrics.get("nDCG@10", ""), ""],
        ["cost", "vectors_per_page", full_vectors, single_vectors, round(safe_ratio(full_vectors, single_vectors), 6)],
        ["cost", "estimated_raw_index_size_mb", full_index, single_index, round(safe_ratio(full_index, single_index), 6)],
        ["cost", "avg_query_latency_ms", full_latency, single_latency, round(safe_ratio(full_latency, single_latency), 6)],
    ]

    with output.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(rows)

    print(f"Wrote performance-cost comparison with ratios to: {output}")


if __name__ == "__main__":
    main()
