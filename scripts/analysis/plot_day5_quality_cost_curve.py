from pathlib import Path
from collections import defaultdict
import csv
import math
import json


PROJECT_ROOT = Path(r"E:\Working\PCB_VisualRAG_Project")

QRELS_PATH = PROJECT_ROOT / "data" / "metadata" / "qrels.tsv"

SUMMARY_DIR = PROJECT_ROOT / "results" / "budgeted" / "coarse_to_fine" / "summary"
FIGURE_DIR = SUMMARY_DIR / "figures"
NOTE_DIR = PROJECT_ROOT / "notes" / "archive" / "week4_raw"

C2F_METRICS_PATH = SUMMARY_DIR / "c2f_day4_metrics_by_N.csv"
C2F_LATENCY_PATH = SUMMARY_DIR / "c2f_day4_latency_by_N.csv"

SINGLE_VECTOR_RUN_PATH = PROJECT_ROOT / "results" / "baselines" / "single_vector_visual_run.tsv"
FULL_MV_RUN_PATH = PROJECT_ROOT / "results" / "full_multivector" / "full_mv_run.tsv"
PAGE_EMB_DIR = PROJECT_ROOT / "artifacts" / "embeddings" / "full_multivector" / "pages"

OUT_CURVE_DATA = SUMMARY_DIR / "day5_quality_cost_curve_data.csv"
OUT_BEST_N_NOTE = NOTE_DIR / "2026-05-07_week4_day5_best_N_analysis.md"
OUT_JSON = SUMMARY_DIR / "day5_quality_cost_curve_summary.json"


def ensure_dirs():
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    NOTE_DIR.mkdir(parents=True, exist_ok=True)


def read_tsv_rows(path):
    if not path.exists():
        raise FileNotFoundError("Missing file: {}".format(path))

    rows = []

    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f, delimiter="\t")
        for row in reader:
            if row and any(cell.strip() for cell in row):
                rows.append(row)

    return rows


def parse_qrels(path):
    rows = read_tsv_rows(path)

    first = [x.strip() for x in rows[0]]
    lower = [x.lower() for x in first]

    has_header = (
        ("query_id" in lower or "qid" in lower)
        and ("page_id" in lower or "doc_id" in lower)
    )

    qrels = defaultdict(dict)

    if has_header:
        header = lower
        data_rows = rows[1:]

        def find_col(candidates):
            for c in candidates:
                if c in header:
                    return header.index(c)
            return None

        q_idx = find_col(["query_id", "qid"])
        p_idx = find_col(["page_id", "doc_id"])
        rel_idx = find_col(["relevance", "rel", "label"])

        if q_idx is None or p_idx is None:
            raise ValueError("Cannot identify qrels columns: {}".format(first))

        for row in data_rows:
            if len(row) <= max(q_idx, p_idx):
                continue

            qid = row[q_idx].strip()
            pid = row[p_idx].strip()

            rel = 1.0
            if rel_idx is not None and len(row) > rel_idx:
                try:
                    rel = float(row[rel_idx])
                except Exception:
                    rel = 1.0

            if rel > 0:
                qrels[qid][pid] = rel

    else:
        for row in rows:
            row = [x.strip() for x in row]

            if len(row) >= 4 and row[1] in ["0", "Q0"]:
                qid = row[0]
                pid = row[2]
                rel_raw = row[3]
            elif len(row) >= 3:
                qid = row[0]
                pid = row[1]
                rel_raw = row[2]
            elif len(row) >= 2:
                qid = row[0]
                pid = row[1]
                rel_raw = "1"
            else:
                continue

            try:
                rel = float(rel_raw)
            except Exception:
                rel = 1.0

            if rel > 0:
                qrels[qid][pid] = rel

    return qrels


def parse_run_file(path):
    rows = read_tsv_rows(path)

    first = [x.strip() for x in rows[0]]
    lower = [x.lower() for x in first]

    has_header = (
        ("query_id" in lower or "qid" in lower)
        and ("page_id" in lower or "doc_id" in lower)
    )

    by_query = defaultdict(list)

    if has_header:
        header = lower
        data_rows = rows[1:]

        def find_col(candidates):
            for c in candidates:
                if c in header:
                    return header.index(c)
            return None

        q_idx = find_col(["query_id", "qid"])
        p_idx = find_col(["page_id", "doc_id"])
        r_idx = find_col(["rank"])
        s_idx = find_col(["score"])

        if q_idx is None or p_idx is None:
            raise ValueError("Cannot identify run columns: {}".format(first))

        for row in data_rows:
            if len(row) <= max(q_idx, p_idx):
                continue

            qid = row[q_idx].strip()
            pid = row[p_idx].strip()

            rank = None
            if r_idx is not None and len(row) > r_idx:
                try:
                    rank = int(float(row[r_idx]))
                except Exception:
                    rank = None

            score = 0.0
            if s_idx is not None and len(row) > s_idx:
                try:
                    score = float(row[s_idx])
                except Exception:
                    score = 0.0

            by_query[qid].append(
                {
                    "page_id": pid,
                    "rank": rank,
                    "score": score,
                }
            )

    else:
        for row in rows:
            row = [x.strip() for x in row]

            if len(row) >= 6 and row[1].upper() == "Q0":
                qid = row[0]
                pid = row[2]
                rank = int(float(row[3]))
                score = float(row[4])
            elif len(row) >= 5:
                qid = row[1]
                pid = row[2]
                rank = int(float(row[3]))
                score = float(row[4])
            elif len(row) >= 4:
                qid = row[0]
                pid = row[1]
                rank = int(float(row[2]))
                score = float(row[3])
            else:
                continue

            by_query[qid].append(
                {
                    "page_id": pid,
                    "rank": rank,
                    "score": score,
                }
            )

    for qid in by_query:
        by_query[qid].sort(
            key=lambda x: (
                x["rank"] if x["rank"] is not None else 10**9,
                -x["score"],
            )
        )

        for idx, item in enumerate(by_query[qid], start=1):
            item["rank"] = idx

    return by_query


def dcg_at_k(relevance_list, k):
    score = 0.0

    for idx, rel in enumerate(relevance_list[:k], start=1):
        score += rel / math.log2(idx + 1)

    return score


def evaluate_run(run_by_query, qrels):
    query_ids = sorted(qrels.keys())

    evaluated = 0
    recall1_sum = 0.0
    recall5_sum = 0.0
    recall10_sum = 0.0
    mrr10_sum = 0.0
    ndcg10_sum = 0.0

    for qid in query_ids:
        rel_dict = qrels[qid]
        rel_pages = set(rel_dict.keys())

        if not rel_pages:
            continue

        evaluated += 1

        ranking = run_by_query.get(qid, [])
        ranked_pages = [x["page_id"] for x in ranking]

        hit1 = len(set(ranked_pages[:1]) & rel_pages)
        hit5 = len(set(ranked_pages[:5]) & rel_pages)
        hit10 = len(set(ranked_pages[:10]) & rel_pages)

        recall1_sum += hit1 / len(rel_pages)
        recall5_sum += hit5 / len(rel_pages)
        recall10_sum += hit10 / len(rel_pages)

        rr = 0.0
        for idx, pid in enumerate(ranked_pages[:10], start=1):
            if pid in rel_pages:
                rr = 1.0 / idx
                break

        mrr10_sum += rr

        gains = []
        for pid in ranked_pages[:10]:
            gains.append(rel_dict.get(pid, 0.0))

        dcg = dcg_at_k(gains, 10)
        ideal_gains = sorted(rel_dict.values(), reverse=True)[:10]
        idcg = dcg_at_k(ideal_gains, 10)

        ndcg = dcg / idcg if idcg > 0 else 0.0
        ndcg10_sum += ndcg

    if evaluated == 0:
        return {
            "evaluated_queries": 0,
            "Recall@1": 0.0,
            "Recall@5": 0.0,
            "Recall@10": 0.0,
            "MRR@10": 0.0,
            "nDCG@10": 0.0,
        }

    return {
        "evaluated_queries": evaluated,
        "Recall@1": recall1_sum / evaluated,
        "Recall@5": recall5_sum / evaluated,
        "Recall@10": recall10_sum / evaluated,
        "MRR@10": mrr10_sum / evaluated,
        "nDCG@10": ndcg10_sum / evaluated,
    }


def read_csv_dicts(path):
    if not path.exists():
        raise FileNotFoundError("Missing file: {}".format(path))

    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def safe_float(value, default=0.0):
    try:
        if value is None:
            return default
        value = str(value).replace("ms/query", "").strip()
        if value == "":
            return default
        return float(value)
    except Exception:
        return default


def count_full_corpus_pages():
    if not PAGE_EMB_DIR.exists():
        return ""

    return len(list(PAGE_EMB_DIR.glob("*.npy")))


def build_curve_data():
    qrels = parse_qrels(QRELS_PATH)

    rows = []

    if SINGLE_VECTOR_RUN_PATH.exists():
        single_run = parse_run_file(SINGLE_VECTOR_RUN_PATH)
        single_metrics = evaluate_run(single_run, qrels)

        rows.append(
            {
                "method": "Single-vector coarse",
                "N": "coarse",
                "point_type": "baseline",
                "Recall@1": single_metrics["Recall@1"],
                "Recall@5": single_metrics["Recall@5"],
                "Recall@10": single_metrics["Recall@10"],
                "MRR@10": single_metrics["MRR@10"],
                "nDCG@10": single_metrics["nDCG@10"],
                "latency_ms_per_query": "",
                "actual_candidates_per_query": 0.0,
                "rerank_cost_units": 0.0,
                "note": "single-vector baseline; no full MV rerank cost",
            }
        )

    if FULL_MV_RUN_PATH.exists():
        full_run = parse_run_file(FULL_MV_RUN_PATH)
        full_metrics = evaluate_run(full_run, qrels)
        full_corpus_pages = count_full_corpus_pages()

        if full_corpus_pages == "":
            full_corpus_pages = 100.0

        rows.append(
            {
                "method": "Full Multi-vector",
                "N": "full",
                "point_type": "baseline",
                "Recall@1": full_metrics["Recall@1"],
                "Recall@5": full_metrics["Recall@5"],
                "Recall@10": full_metrics["Recall@10"],
                "MRR@10": full_metrics["MRR@10"],
                "nDCG@10": full_metrics["nDCG@10"],
                "latency_ms_per_query": "",
                "actual_candidates_per_query": full_corpus_pages,
                "rerank_cost_units": full_corpus_pages,
                "note": "full corpus MV reranking; latency not available in Day 4 summary",
            }
        )

    metrics_rows = read_csv_dicts(C2F_METRICS_PATH)
    latency_rows = read_csv_dicts(C2F_LATENCY_PATH)

    latency_by_n = {}

    for row in latency_rows:
        n = str(row.get("N", "")).strip()
        latency_by_n[n] = row

    for row in metrics_rows:
        method = row.get("method", "")

        if not method.startswith("C2F"):
            continue

        n = str(row.get("N", "")).strip()
        lat = latency_by_n.get(n, {})

        actual_candidates = safe_float(lat.get("avg_candidates_per_query", ""))
        latency_ms = safe_float(lat.get("per_query_latency_ms_proxy", ""))

        rows.append(
            {
                "method": method,
                "N": n,
                "point_type": "c2f",
                "Recall@1": safe_float(row.get("Recall@1", "")),
                "Recall@5": safe_float(row.get("Recall@5", "")),
                "Recall@10": safe_float(row.get("Recall@10", "")),
                "MRR@10": safe_float(row.get("MRR@10", "")),
                "nDCG@10": safe_float(row.get("nDCG@10", "")),
                "latency_ms_per_query": latency_ms,
                "actual_candidates_per_query": actual_candidates,
                "rerank_cost_units": actual_candidates,
                "note": lat.get("note", ""),
            }
        )

    return rows


def write_curve_data(rows):
    fieldnames = [
        "method",
        "N",
        "point_type",
        "Recall@1",
        "Recall@5",
        "Recall@10",
        "MRR@10",
        "nDCG@10",
        "latency_ms_per_query",
        "actual_candidates_per_query",
        "rerank_cost_units",
        "note",
    ]

    with OUT_CURVE_DATA.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for row in rows:
            out = dict(row)

            for key in ["Recall@1", "Recall@5", "Recall@10", "MRR@10", "nDCG@10"]:
                out[key] = "{:.4f}".format(float(out[key]))

            if out["latency_ms_per_query"] != "":
                out["latency_ms_per_query"] = "{:.6f}".format(float(out["latency_ms_per_query"]))

            if out["actual_candidates_per_query"] != "":
                out["actual_candidates_per_query"] = "{:.4f}".format(float(out["actual_candidates_per_query"]))

            if out["rerank_cost_units"] != "":
                out["rerank_cost_units"] = "{:.4f}".format(float(out["rerank_cost_units"]))

            writer.writerow(out)


def group_c2f_by_cost_and_quality(c2f_rows, metric_name):
    grouped = defaultdict(list)

    for r in c2f_rows:
        x = round(float(r["rerank_cost_units"]), 6)
        y = round(float(r[metric_name]), 6)
        grouped[(x, y)].append(r)

    groups = []

    for (x, y), items in grouped.items():
        ns = [str(item["N"]) for item in items]
        ns_sorted = sorted(ns, key=lambda v: int(v) if v.isdigit() else 999999)

        groups.append(
            {
                "x": x,
                "y": y,
                "label": "C2F N=" + "/".join(ns_sorted),
                "items": items,
            }
        )

    groups.sort(key=lambda g: g["x"])
    return groups


def get_metric_ylim(rows, metric_name):
    values = [float(r[metric_name]) for r in rows]
    ymin = min(values)
    ymax = max(values)

    if abs(ymax - ymin) < 1e-9:
        pad = 0.02
    else:
        pad = max((ymax - ymin) * 0.25, 0.01)

    lower = max(0.0, ymin - pad)
    upper = min(1.0, ymax + pad)

    if upper - lower < 0.05:
        center = (upper + lower) / 2.0
        lower = max(0.0, center - 0.03)
        upper = min(1.0, center + 0.03)

    return lower, upper


def add_note_box(ax, text):
    ax.text(
        0.02,
        0.03,
        text,
        transform=ax.transAxes,
        fontsize=9,
        verticalalignment="bottom",
        bbox=dict(boxstyle="round", facecolor="white", alpha=0.85, edgecolor="gray"),
    )


def plot_curves(rows):
    import matplotlib.pyplot as plt

    plt.rcParams["font.family"] = "DejaVu Sans"
    plt.rcParams["axes.unicode_minus"] = False

    c2f_rows = [r for r in rows if r["point_type"] == "c2f"]
    baseline_rows = [r for r in rows if r["point_type"] == "baseline"]

    outputs = []

    def get_baseline(name):
        for r in baseline_rows:
            if r["method"] == name:
                return r
        return None

    single = get_baseline("Single-vector coarse")
    full = get_baseline("Full Multi-vector")

    def make_cost_plot(metric_name):
        fig, ax = plt.subplots(figsize=(9.5, 5.8))

        all_for_ylim = list(rows)

        if single is not None:
            ax.scatter(
                [float(single["rerank_cost_units"])],
                [float(single[metric_name])],
                marker="s",
                s=150,
                color="tab:green",
                label="Single-vector coarse",
                zorder=4,
            )
            ax.annotate(
                "Single-vector\ncoarse",
                (float(single["rerank_cost_units"]), float(single[metric_name])),
                textcoords="offset points",
                xytext=(8, 8),
                fontsize=9,
            )

        if full is not None:
            ax.scatter(
                [float(full["rerank_cost_units"])],
                [float(full[metric_name])],
                marker="*",
                s=220,
                color="tab:red",
                label="Full Multi-vector",
                zorder=4,
            )
            ax.annotate(
                "Full MV",
                (float(full["rerank_cost_units"]), float(full[metric_name])),
                textcoords="offset points",
                xytext=(-55, 10),
                fontsize=9,
            )

        groups = group_c2f_by_cost_and_quality(c2f_rows, metric_name)

        x_vals = [g["x"] for g in groups]
        y_vals = [g["y"] for g in groups]

        ax.plot(
            x_vals,
            y_vals,
            marker="o",
            markersize=8,
            linewidth=2.5,
            color="tab:blue",
            label="C2F",
            zorder=5,
        )

        for g in groups:
            ax.annotate(
                g["label"],
                (g["x"], g["y"]),
                textcoords="offset points",
                xytext=(8, -20),
                fontsize=9,
                bbox=dict(boxstyle="round,pad=0.2", facecolor="white", alpha=0.8, edgecolor="none"),
            )

        ymin, ymax = get_metric_ylim(all_for_ylim, metric_name)
        ax.set_ylim(ymin, ymax)

        max_x = 10.0
        for r in rows:
            if r["rerank_cost_units"] != "":
                max_x = max(max_x, float(r["rerank_cost_units"]))

        ax.set_xlim(-5, max_x * 1.12)

        ax.set_xlabel("Rerank cost units: scored pages/query")
        ax.set_ylabel(metric_name)
        ax.set_title("Coarse-to-Fine Quality-Cost Curve ({})".format(metric_name))
        ax.grid(True, linestyle="--", alpha=0.35)
        ax.legend(loc="best")

        note = "Note: C2F N=10/20/50/100 all use 10 actual candidates/query.\nSo the C2F points overlap in cost and quality."
        add_note_box(ax, note)

        fig.tight_layout()

        safe_metric = metric_name.replace("@", "").replace("/", "_")
        png_path = FIGURE_DIR / "day5_quality_rerank_cost_{}_fixed.png".format(safe_metric)
        pdf_path = FIGURE_DIR / "day5_quality_rerank_cost_{}_fixed.pdf".format(safe_metric)

        fig.savefig(png_path, dpi=300)
        fig.savefig(pdf_path)
        plt.close(fig)

        outputs.extend([png_path, pdf_path])

    def make_latency_plot(metric_name):
        fig, ax = plt.subplots(figsize=(9.5, 5.8))

        sorted_c2f = sorted(
            c2f_rows,
            key=lambda r: float(r["latency_ms_per_query"]) if r["latency_ms_per_query"] != "" else 999999.0,
        )

        x = [float(r["latency_ms_per_query"]) for r in sorted_c2f if r["latency_ms_per_query"] != ""]
        y = [float(r[metric_name]) for r in sorted_c2f if r["latency_ms_per_query"] != ""]
        labels = ["N={}".format(r["N"]) for r in sorted_c2f if r["latency_ms_per_query"] != ""]

        ax.plot(
            x,
            y,
            marker="o",
            markersize=8,
            linewidth=2.5,
            color="tab:blue",
            label="C2F",
            zorder=5,
        )

        label_offsets = [
            (6, 12),
            (6, -22),
            (6, 12),
            (6, -22),
            (6, 12),
        ]

        for idx, (xi, yi, label) in enumerate(zip(x, y, labels)):
            ox, oy = label_offsets[idx % len(label_offsets)]
            ax.annotate(
                label,
                (xi, yi),
                textcoords="offset points",
                xytext=(ox, oy),
                fontsize=9,
                bbox=dict(boxstyle="round,pad=0.2", facecolor="white", alpha=0.8, edgecolor="none"),
            )

        if full is not None:
            ax.axhline(
                float(full[metric_name]),
                linestyle="--",
                linewidth=2.0,
                color="gray",
                label="Full MV quality reference",
                zorder=3,
            )

        all_for_ylim = list(c2f_rows)
        if full is not None:
            all_for_ylim.append(full)

        ymin, ymax = get_metric_ylim(all_for_ylim, metric_name)
        ax.set_ylim(ymin, ymax)

        if x:
            xmin = min(x)
            xmax = max(x)
            xpad = max((xmax - xmin) * 0.15, 0.25)
            ax.set_xlim(xmin - xpad, xmax + xpad)

        ax.set_xlabel("Latency ms/query")
        ax.set_ylabel(metric_name)
        ax.set_title("Coarse-to-Fine Quality-Latency Curve ({})".format(metric_name))
        ax.grid(True, linestyle="--", alpha=0.35)
        ax.legend(loc="best")

        note = "Latency is cached-candidate reranking latency only.\nCoarse retrieval time is not included."
        add_note_box(ax, note)

        fig.tight_layout()

        safe_metric = metric_name.replace("@", "").replace("/", "_")
        png_path = FIGURE_DIR / "day5_quality_latency_{}_fixed.png".format(safe_metric)
        pdf_path = FIGURE_DIR / "day5_quality_latency_{}_fixed.pdf".format(safe_metric)

        fig.savefig(png_path, dpi=300)
        fig.savefig(pdf_path)
        plt.close(fig)

        outputs.extend([png_path, pdf_path])

    def make_combined_summary_plot():
        fig, axes = plt.subplots(1, 2, figsize=(14, 5.8))

        for ax, metric_name in zip(axes, ["Recall@10", "nDCG@10"]):
            if single is not None:
                ax.scatter(
                    [float(single["rerank_cost_units"])],
                    [float(single[metric_name])],
                    marker="s",
                    s=150,
                    color="tab:green",
                    label="Single-vector coarse",
                    zorder=4,
                )
                ax.annotate(
                    "Single-vector",
                    (float(single["rerank_cost_units"]), float(single[metric_name])),
                    textcoords="offset points",
                    xytext=(8, 8),
                    fontsize=9,
                )

            if full is not None:
                ax.scatter(
                    [float(full["rerank_cost_units"])],
                    [float(full[metric_name])],
                    marker="*",
                    s=220,
                    color="tab:red",
                    label="Full MV",
                    zorder=4,
                )
                ax.annotate(
                    "Full MV",
                    (float(full["rerank_cost_units"]), float(full[metric_name])),
                    textcoords="offset points",
                    xytext=(-50, 10),
                    fontsize=9,
                )

            groups = group_c2f_by_cost_and_quality(c2f_rows, metric_name)

            x_vals = [g["x"] for g in groups]
            y_vals = [g["y"] for g in groups]

            ax.plot(
                x_vals,
                y_vals,
                marker="o",
                markersize=8,
                linewidth=2.5,
                color="tab:blue",
                label="C2F",
                zorder=5,
            )

            for g in groups:
                ax.annotate(
                    g["label"],
                    (g["x"], g["y"]),
                    textcoords="offset points",
                    xytext=(8, -20),
                    fontsize=9,
                    bbox=dict(boxstyle="round,pad=0.2", facecolor="white", alpha=0.8, edgecolor="none"),
                )

            ymin, ymax = get_metric_ylim(rows, metric_name)
            ax.set_ylim(ymin, ymax)

            max_x = 10.0
            for r in rows:
                if r["rerank_cost_units"] != "":
                    max_x = max(max_x, float(r["rerank_cost_units"]))
            ax.set_xlim(-5, max_x * 1.12)

            ax.set_xlabel("Rerank cost units: scored pages/query")
            ax.set_ylabel(metric_name)
            ax.set_title(metric_name)
            ax.grid(True, linestyle="--", alpha=0.35)

        handles, labels = axes[0].get_legend_handles_labels()
        fig.legend(handles, labels, loc="upper center", ncol=3)

        fig.suptitle("Day 5 Quality-Cost Curve Summary", y=1.03, fontsize=14)

        fig.text(
            0.5,
            0.02,
            "Important: all C2F settings currently use the same actual candidate depth: 10 pages/query. "
            "Therefore, C2F N=10/20/50/100 overlap in cost-quality space.",
            ha="center",
            fontsize=10,
            bbox=dict(boxstyle="round", facecolor="white", alpha=0.9, edgecolor="gray"),
        )

        fig.tight_layout(rect=[0, 0.07, 1, 0.95])

        png_path = FIGURE_DIR / "day5_quality_cost_curve_combined_fixed.png"
        pdf_path = FIGURE_DIR / "day5_quality_cost_curve_combined_fixed.pdf"

        fig.savefig(png_path, dpi=300)
        fig.savefig(pdf_path)
        plt.close(fig)

        outputs.extend([png_path, pdf_path])

    make_cost_plot("Recall@10")
    make_cost_plot("nDCG@10")
    make_latency_plot("Recall@10")
    make_latency_plot("nDCG@10")
    make_combined_summary_plot()

    return outputs


def select_best_n(rows):
    c2f_rows = [r for r in rows if r["point_type"] == "c2f"]

    if not c2f_rows:
        return None

    max_recall = max(float(r["Recall@10"]) for r in c2f_rows)
    max_ndcg = max(float(r["nDCG@10"]) for r in c2f_rows)

    candidates = []

    for r in c2f_rows:
        recall = float(r["Recall@10"])
        ndcg = float(r["nDCG@10"])
        latency = float(r["latency_ms_per_query"]) if r["latency_ms_per_query"] != "" else 999999.0
        cost = float(r["rerank_cost_units"])

        recall_gap = max_recall - recall
        ndcg_gap = max_ndcg - ndcg

        candidates.append(
            {
                "method": r["method"],
                "N": r["N"],
                "Recall@10": recall,
                "nDCG@10": ndcg,
                "latency_ms_per_query": latency,
                "rerank_cost_units": cost,
                "recall_gap_to_best": recall_gap,
                "ndcg_gap_to_best": ndcg_gap,
            }
        )

    candidates.sort(
        key=lambda x: (
            x["recall_gap_to_best"],
            x["ndcg_gap_to_best"],
            x["rerank_cost_units"],
            int(x["N"]) if str(x["N"]).isdigit() else 999999,
            x["latency_ms_per_query"],
        )
    )

    principled_best = candidates[0]
    measured_latency_best = sorted(candidates, key=lambda x: x["latency_ms_per_query"])[0]

    return {
        "principled_best": principled_best,
        "measured_latency_best": measured_latency_best,
        "all_candidates": candidates,
    }


def write_best_n_note(rows, best_info, figure_outputs):
    c2f_rows = [r for r in rows if r["point_type"] == "c2f"]

    principled_best = best_info["principled_best"]
    measured_latency_best = best_info["measured_latency_best"]

    lines = []

    lines.append("# Week 4 Day 5 Quality-Cost Curve and Best N Analysis")
    lines.append("")
    lines.append("**Project:** PCB_VisualRAG_Project  ")
    lines.append("**Stage:** Week 4  ")
    lines.append("**Day:** Day 5  ")
    lines.append("**Date:** 2026-05-07  ")
    lines.append("**Experiment Name:** Coarse-to-Fine Quality-Cost Curve Analysis  ")
    lines.append("**Status:** Completed  ")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 1. 今日目标")
    lines.append("")
    lines.append("今日目标是将 Day 4 的效果与时延评测结果转化为第一版质量–成本曲线图，并分析当前最具性价比的候选规模 N。")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 2. 输出图文件")
    lines.append("")
    lines.append("| Figure | Path |")
    lines.append("|---|---|")

    for path in figure_outputs:
        lines.append("| Figure | `{}` |".format(path.relative_to(PROJECT_ROOT)))

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 3. Quality-Cost Curve Data")
    lines.append("")
    lines.append("| Method | N | Recall@10 | nDCG@10 | Latency ms/query | Rerank Cost |")
    lines.append("|---|---:|---:|---:|---:|---:|")

    for r in rows:
        latency = r["latency_ms_per_query"]
        if latency == "":
            latency_text = ""
        else:
            latency_text = "{:.6f}".format(float(latency))

        cost = r["rerank_cost_units"]
        if cost == "":
            cost_text = ""
        else:
            cost_text = "{:.4f}".format(float(cost))

        lines.append(
            "| {} | {} | {:.4f} | {:.4f} | {} | {} |".format(
                r["method"],
                r["N"],
                float(r["Recall@10"]),
                float(r["nDCG@10"]),
                latency_text,
                cost_text,
            )
        )

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 4. Best N 分析")
    lines.append("")
    lines.append("| Best Type | N | Recall@10 | nDCG@10 | Latency ms/query | Rerank Cost |")
    lines.append("|---|---:|---:|---:|---:|---:|")
    lines.append(
        "| Principled best trade-off | {} | {:.4f} | {:.4f} | {:.6f} | {:.4f} |".format(
            principled_best["N"],
            principled_best["Recall@10"],
            principled_best["nDCG@10"],
            principled_best["latency_ms_per_query"],
            principled_best["rerank_cost_units"],
        )
    )
    lines.append(
        "| Lowest measured latency | {} | {:.4f} | {:.4f} | {:.6f} | {:.4f} |".format(
            measured_latency_best["N"],
            measured_latency_best["Recall@10"],
            measured_latency_best["nDCG@10"],
            measured_latency_best["latency_ms_per_query"],
            measured_latency_best["rerank_cost_units"],
        )
    )
    lines.append("")
    lines.append("当前按照“效果不下降且 rerank cost 最小”的原则，N=10 是最合理的临时 best trade-off。")
    lines.append("")
    lines.append("需要注意，当前 measured latency 的最低点不一定代表真实最佳 N，因为 N=10、20、50、100 的实际候选数都为 10。")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 5. 关键观察")
    lines.append("")
    lines.append("### 5.1 当前曲线中 C2F 点重合")
    lines.append("")
    lines.append("修改后的图中已经将重合点显式标注为 `C2F N=10/20/50/100`。")
    lines.append("")
    lines.append("这说明当前不是绘图错误，而是实验数据本身具有如下特点：")
    lines.append("")
    lines.append("- N=10、20、50、100 的 actual candidates/query 均为 10；")
    lines.append("- 不同 N 的 Recall@10 完全一致；")
    lines.append("- 不同 N 的 nDCG@10 完全一致；")
    lines.append("- 原始 single-vector coarse run 很可能只保存了 top-10。")
    lines.append("")
    lines.append("因此，本轮 Day 5 图应被解释为 pipeline validation figure，而不是最终 budget-scaling figure。")
    lines.append("")
    lines.append("### 5.2 质量损失主要发生在 coarse stage")
    lines.append("")
    lines.append("Day 2 的 coarse recall 为 0.2667，而 Day 4 的 C2F Recall@10 为 0.2500。")
    lines.append("")
    lines.append("这说明 fine reranker 在候选集合内基本保留了可命中的 relevant pages，主要瓶颈仍然是 coarse retriever 的候选召回能力。")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 6. 图注草稿")
    lines.append("")
    lines.append("**Figure 1: Coarse-to-Fine Retrieval Quality-Cost Curve.** The x-axis denotes reranking cost measured by the number of scored candidate pages per query, while the y-axis denotes retrieval quality measured by Recall@10 or nDCG@10. The figure marks the single-vector coarse baseline, the full multi-vector baseline, and C2F results under different candidate budgets. In the current experiment, all C2F settings use the same actual candidate depth of 10 pages per query due to the limited depth of the coarse retrieval run; therefore, the C2F points overlap and should be interpreted as pipeline validation rather than a complete budget-scaling curve.")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## 7. 今日结论")
    lines.append("")
    lines.append("Day 5 已完成第一版质量–成本曲线绘制和 best N 分析。")
    lines.append("")
    lines.append("当前结论如下：")
    lines.append("")
    lines.append("1. 当前 limited-depth setting 下，N=10 是最合理的临时 best trade-off；")
    lines.append("2. 质量损失主要发生在 coarse stage；")
    lines.append("3. C2F pipeline 值得继续推进；")
    lines.append("4. 若要形成真实质量–成本曲线，需要重新生成 top-20、top-50、top-100 有效候选集合。")

    OUT_BEST_N_NOTE.write_text("\n".join(lines), encoding="utf-8")


def main():
    ensure_dirs()

    print("[Day5] Building quality-cost curve data...")
    rows = build_curve_data()
    write_curve_data(rows)

    print("[Day5] Plotting fixed quality-cost curves...")
    figure_outputs = plot_curves(rows)

    print("[Day5] Selecting best N...")
    best_info = select_best_n(rows)

    print("[Day5] Writing best N analysis note...")
    write_best_n_note(rows, best_info, figure_outputs)

    payload = {
        "curve_data": str(OUT_CURVE_DATA.relative_to(PROJECT_ROOT)),
        "best_n_note": str(OUT_BEST_N_NOTE.relative_to(PROJECT_ROOT)),
        "figures": [str(p.relative_to(PROJECT_ROOT)) for p in figure_outputs],
        "best_info": best_info,
    }

    with OUT_JSON.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    print("")
    print("========== Day 5 Completed ==========")
    print("Curve data: {}".format(OUT_CURVE_DATA))
    print("Best N note: {}".format(OUT_BEST_N_NOTE))
    print("Summary JSON: {}".format(OUT_JSON))
    print("")
    print("Figures:")

    for path in figure_outputs:
        print("  {}".format(path))

    print("")
    print("Best N:")
    print("  Principled best trade-off: N={}".format(best_info["principled_best"]["N"]))
    print("  Lowest measured latency:   N={}".format(best_info["measured_latency_best"]["N"]))


if __name__ == "__main__":
    main()
