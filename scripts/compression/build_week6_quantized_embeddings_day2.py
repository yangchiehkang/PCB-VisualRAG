from pathlib import Path
import json
import time
import numpy as np
import pandas as pd

try:
    import faiss
except ImportError as e:
    raise ImportError("Please install faiss-cpu first: pip install faiss-cpu") from e


# ============================================================
# Week 6 Day 2 Quantized Embedding Builder
# Representative setting: N=10, M=16
# Input:  artifacts/embeddings/token_selection/pages_M16
# Output: artifacts/embeddings/joint_compression/*
# ============================================================

INPUT_DIR = Path("artifacts/embeddings/token_selection/pages_M16")
OUT_ROOT = Path("artifacts/embeddings/joint_compression")

STATS_DIR = Path("results/budgeted/joint_compression/index_stats")
SUMMARY_DIR = Path("results/budgeted/joint_compression/day2_validation")

STATS_DIR.mkdir(parents=True, exist_ok=True)
SUMMARY_DIR.mkdir(parents=True, exist_ok=True)
OUT_ROOT.mkdir(parents=True, exist_ok=True)


# ------------------------------------------------------------
# Important:
# Current training vectors = 101 pages * 16 tokens = 1616.
# 8-bit PQ means 256 centroids per subquantizer, which is too
# large for this small training set and produces many warnings.
#
# For Day 2 pipeline validation, use 4-bit PQ first.
# Later Day 3 batch experiments can test 4/6/8 bits separately.
# ------------------------------------------------------------

DEFAULT_PQ_M = 16
DEFAULT_BITS = 4
DEFAULT_NLIST = 8
DEFAULT_NPROBE = 4


RUNS = [
    {
        "name": "w6_N10_M16_pq",
        "compression": "PQ",
        "out_dir": OUT_ROOT / "pages_M16_pq",
        "pq_m": DEFAULT_PQ_M,
        "bits": DEFAULT_BITS,
        "use_opq": False,
        "use_ivf": False,
        "nlist": None,
        "nprobe": None,
    },
    {
        "name": "w6_N10_M16_opq_pq",
        "compression": "OPQ+PQ",
        "out_dir": OUT_ROOT / "pages_M16_opq_pq",
        "pq_m": DEFAULT_PQ_M,
        "bits": DEFAULT_BITS,
        "use_opq": True,
        "use_ivf": False,
        "nlist": None,
        "nprobe": None,
    },
    {
        "name": "w6_N10_M16_ivf_pq",
        "compression": "IVF+PQ",
        "out_dir": OUT_ROOT / "pages_M16_ivf_pq",
        "pq_m": DEFAULT_PQ_M,
        "bits": DEFAULT_BITS,
        "use_opq": False,
        "use_ivf": True,
        "nlist": DEFAULT_NLIST,
        "nprobe": DEFAULT_NPROBE,
    },
    {
        "name": "w6_N10_M16_ivf_opq_pq",
        "compression": "IVF+OPQ+PQ",
        "out_dir": OUT_ROOT / "pages_M16_ivf_opq_pq",
        "pq_m": DEFAULT_PQ_M,
        "bits": DEFAULT_BITS,
        "use_opq": True,
        "use_ivf": True,
        "nlist": DEFAULT_NLIST,
        "nprobe": DEFAULT_NPROBE,
    },
]


def load_page_embeddings(input_dir: Path):
    files = sorted(input_dir.glob("*.npy"))

    if not files:
        raise FileNotFoundError(f"No npy files found in {input_dir}")

    arrays = []
    meta = []
    offset = 0

    for fp in files:
        arr = np.load(fp).astype("float32")

        if arr.ndim != 2:
            raise ValueError(f"Invalid embedding shape: {fp}, shape={arr.shape}")

        arrays.append(arr)

        meta.append({
            "file": fp.name,
            "num_tokens": int(arr.shape[0]),
            "dim": int(arr.shape[1]),
            "start": int(offset),
            "end": int(offset + arr.shape[0]),
        })

        offset += arr.shape[0]

    all_vecs = np.vstack(arrays).astype("float32")

    return files, arrays, meta, all_vecs


def save_reconstructed(meta, recon, out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)

    for item in meta:
        page_recon = recon[item["start"]:item["end"]]
        np.save(out_dir / item["file"], page_recon.astype("float32"))


def file_size_mb(path: Path):
    if not path.exists():
        return 0.0

    if path.is_file():
        return path.stat().st_size / 1024 / 1024

    total = 0
    for fp in path.rglob("*"):
        if fp.is_file():
            total += fp.stat().st_size

    return total / 1024 / 1024


def validate_pq_setting(x, pq_m, bits):
    d = x.shape[1]

    if d % pq_m != 0:
        raise ValueError(
            f"Embedding dim d={d} must be divisible by pq_m={pq_m}."
        )

    num_train = x.shape[0]
    centroids = 2 ** bits

    if num_train < centroids:
        raise ValueError(
            f"Training vectors too few: num_train={num_train}, centroids={centroids}."
        )

    return True


def build_pq(x, pq_m, bits):
    validate_pq_setting(x, pq_m, bits)

    d = x.shape[1]

    pq = faiss.ProductQuantizer(d, pq_m, bits)
    pq.train(x)

    codes = pq.compute_codes(x)
    recon = pq.decode(codes).astype("float32")

    return recon, codes


def build_opq_pq(x, pq_m, bits):
    validate_pq_setting(x, pq_m, bits)

    d = x.shape[1]

    opq = faiss.OPQMatrix(d, pq_m)

    # Small dataset friendly settings.
    opq.niter = 20
    opq.niter_pq = 20
    opq.niter_pq_0 = 10
    opq.verbose = False

    opq.train(x)
    x_opq = opq.apply_py(x).astype("float32")

    pq = faiss.ProductQuantizer(d, pq_m, bits)
    pq.train(x_opq)

    codes = pq.compute_codes(x_opq)
    recon_opq = pq.decode(codes).astype("float32")

    recon = opq.reverse_transform(recon_opq).astype("float32")

    return recon, codes


def reconstruct_ivf_index(index, x):
    """
    Reconstruct vectors from an IVF index.

    Primary path:
        index.make_direct_map()
        index.reconstruct(i)

    Fallback path:
        search each original vector and reconstruct nearest assigned vector.

    This avoids FAISS error:
        direct map not initialized
    """

    n, d = x.shape
    recon = np.zeros((n, d), dtype="float32")

    try:
        index.make_direct_map()

        for i in range(n):
            recon[i] = index.reconstruct(i)

        return recon, "direct_map"

    except Exception as e:
        print(f"[Warn] Direct-map reconstruct failed: {repr(e)}")
        print("[Warn] Falling back to nearest-neighbor reconstruct.")

        distances, ids = index.search(x, 1)

        for i in range(n):
            rid = int(ids[i, 0])
            if rid >= 0:
                recon[i] = index.reconstruct(rid)
            else:
                recon[i] = x[i]

        return recon, "search_fallback"


def build_ivf_pq(x, pq_m, bits, nlist, nprobe):
    validate_pq_setting(x, pq_m, bits)

    d = x.shape[1]

    quantizer = faiss.IndexFlatL2(d)
    index = faiss.IndexIVFPQ(
        quantizer,
        d,
        int(nlist),
        int(pq_m),
        int(bits),
    )

    index.nprobe = int(nprobe)

    index.train(x)
    index.add(x)

    recon, reconstruct_mode = reconstruct_ivf_index(index, x)

    code_size = int(index.code_size)
    dummy_codes = np.zeros((x.shape[0], code_size), dtype="uint8")

    extra = {
        "reconstruct_mode": reconstruct_mode,
        "code_size_bytes_per_vector": code_size,
        "ntotal": int(index.ntotal),
        "is_trained": bool(index.is_trained),
    }

    return recon.astype("float32"), dummy_codes, extra


def build_ivf_opq_pq(x, pq_m, bits, nlist, nprobe):
    validate_pq_setting(x, pq_m, bits)

    d = x.shape[1]

    opq = faiss.OPQMatrix(d, pq_m)

    # Small dataset friendly settings.
    opq.niter = 20
    opq.niter_pq = 20
    opq.niter_pq_0 = 10
    opq.verbose = False

    opq.train(x)
    x_opq = opq.apply_py(x).astype("float32")

    quantizer = faiss.IndexFlatL2(d)
    index = faiss.IndexIVFPQ(
        quantizer,
        d,
        int(nlist),
        int(pq_m),
        int(bits),
    )

    index.nprobe = int(nprobe)

    index.train(x_opq)
    index.add(x_opq)

    recon_opq, reconstruct_mode = reconstruct_ivf_index(index, x_opq)
    recon = opq.reverse_transform(recon_opq).astype("float32")

    code_size = int(index.code_size)
    dummy_codes = np.zeros((x.shape[0], code_size), dtype="uint8")

    extra = {
        "reconstruct_mode": reconstruct_mode,
        "code_size_bytes_per_vector": code_size,
        "ntotal": int(index.ntotal),
        "is_trained": bool(index.is_trained),
    }

    return recon.astype("float32"), dummy_codes, extra


def estimate_code_size_mb(num_vectors, pq_m, bits):
    bytes_per_vector = pq_m * bits / 8.0
    total_bytes = num_vectors * bytes_per_vector
    return total_bytes / 1024 / 1024


def estimate_fp_payload_size_mb(num_vectors, dim):
    total_bytes = num_vectors * dim * 4
    return total_bytes / 1024 / 1024


def main():
    print("[Info] Loading input embeddings...")
    print(f"[Input] {INPUT_DIR}")

    files, arrays, meta, x = load_page_embeddings(INPUT_DIR)

    num_pages = len(files)
    total_vectors = int(x.shape[0])
    dim = int(x.shape[1])

    original_file_size_mb = file_size_mb(INPUT_DIR)
    original_payload_size_mb = estimate_fp_payload_size_mb(total_vectors, dim)

    print(f"[Info] Num pages: {num_pages}")
    print(f"[Info] Total vectors: {total_vectors}")
    print(f"[Info] Dim: {dim}")
    print(f"[Info] Original file size MB: {original_file_size_mb:.4f}")
    print(f"[Info] Original payload size MB: {original_payload_size_mb:.4f}")

    rows = []

    for cfg in RUNS:
        run_name = cfg["name"]

        print("=" * 80)
        print(f"[Run] {run_name}")
        print(f"[Compression] {cfg['compression']}")
        print(f"[pq_m] {cfg['pq_m']}")
        print(f"[bits] {cfg['bits']}")
        print(f"[nlist] {cfg['nlist']}")
        print(f"[nprobe] {cfg['nprobe']}")

        t0 = time.time()
        extra = {}

        if cfg["compression"] == "PQ":
            recon, codes = build_pq(
                x=x,
                pq_m=cfg["pq_m"],
                bits=cfg["bits"],
            )

        elif cfg["compression"] == "OPQ+PQ":
            recon, codes = build_opq_pq(
                x=x,
                pq_m=cfg["pq_m"],
                bits=cfg["bits"],
            )

        elif cfg["compression"] == "IVF+PQ":
            recon, codes, extra = build_ivf_pq(
                x=x,
                pq_m=cfg["pq_m"],
                bits=cfg["bits"],
                nlist=cfg["nlist"],
                nprobe=cfg["nprobe"],
            )

        elif cfg["compression"] == "IVF+OPQ+PQ":
            recon, codes, extra = build_ivf_opq_pq(
                x=x,
                pq_m=cfg["pq_m"],
                bits=cfg["bits"],
                nlist=cfg["nlist"],
                nprobe=cfg["nprobe"],
            )

        else:
            raise ValueError(f"Unknown compression: {cfg['compression']}")

        build_time_sec = time.time() - t0

        save_reconstructed(
            meta=meta,
            recon=recon,
            out_dir=cfg["out_dir"],
        )

        reconstructed_file_size_mb = file_size_mb(cfg["out_dir"])

        mse = float(np.mean((x - recon) ** 2))
        mae = float(np.mean(np.abs(x - recon)))

        estimated_code_size_mb = estimate_code_size_mb(
            num_vectors=total_vectors,
            pq_m=cfg["pq_m"],
            bits=cfg["bits"],
        )

        estimated_compression_ratio_vs_fp_payload = (
            original_payload_size_mb / estimated_code_size_mb
            if estimated_code_size_mb > 0
            else None
        )

        file_ratio_vs_fp_files = (
            original_file_size_mb / reconstructed_file_size_mb
            if reconstructed_file_size_mb > 0
            else None
        )

        row = {
            "run_name": run_name,
            "compression": cfg["compression"],
            "input_dir": str(INPUT_DIR),
            "output_dir": str(cfg["out_dir"]),
            "num_pages": num_pages,
            "total_vectors": total_vectors,
            "dim": dim,
            "pq_m": cfg["pq_m"],
            "bits": cfg["bits"],
            "nlist": cfg["nlist"],
            "nprobe": cfg["nprobe"],
            "original_fp_file_size_mb": original_file_size_mb,
            "original_fp_payload_size_mb": original_payload_size_mb,
            "reconstructed_file_size_mb": reconstructed_file_size_mb,
            "estimated_code_size_mb": estimated_code_size_mb,
            "estimated_compression_ratio_vs_fp_payload": estimated_compression_ratio_vs_fp_payload,
            "file_ratio_vs_fp_files": file_ratio_vs_fp_files,
            "mse": mse,
            "mae": mae,
            "build_time_sec": build_time_sec,
            "index_built": True,
        }

        row.update(extra)

        rows.append(row)

        stats_path = STATS_DIR / f"{run_name}_index_stats.json"
        with stats_path.open("w", encoding="utf-8") as f:
            json.dump(row, f, indent=2, ensure_ascii=False)

        print(f"[Done] {run_name}")
        print(f"[Output embeddings] {cfg['out_dir']}")
        print(f"[Output stats] {stats_path}")
        print(f"[MSE] {mse:.8f}")
        print(f"[MAE] {mae:.8f}")
        print(f"[Estimated code size MB] {estimated_code_size_mb:.6f}")
        print(f"[Build time sec] {build_time_sec:.4f}")

    df = pd.DataFrame(rows)

    csv_path = SUMMARY_DIR / "day2_quantization_build_summary.csv"
    md_path = SUMMARY_DIR / "day2_quantization_build_summary.md"

    df.to_csv(csv_path, index=False, encoding="utf-8-sig")

    with md_path.open("w", encoding="utf-8") as f:
        f.write("# Week 6 Day 2 Quantization Build Summary\n\n")
        f.write(df.to_markdown(index=False))
        f.write("\n")

    print("=" * 80)
    print("[Done] Day 2 quantized embeddings built.")
    print(f"[Output] {csv_path}")
    print(f"[Output] {md_path}")


if __name__ == "__main__":
    main()
