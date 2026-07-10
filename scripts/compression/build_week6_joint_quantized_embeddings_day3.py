from pathlib import Path
import json
import time
import numpy as np
import pandas as pd

try:
    import faiss
except ImportError as e:
    raise ImportError("Please install faiss-cpu first: pip install faiss-cpu") from e


BUDGET_MS = [8, 16, 24]

COMPRESSIONS = [
    "PQ",
    "OPQ+PQ",
    "IVF+PQ",
    "IVF+OPQ+PQ",
]

PQ_M = 16
BITS = 4
NLIST = 8
NPROBE = 4

TOKEN_ROOT = Path("artifacts/embeddings/token_selection")
OUT_ROOT = Path("artifacts/embeddings/joint_compression")

STATS_DIR = Path("results/budgeted/joint_compression/index_stats")
DAY3_DIR = Path("results/budgeted/joint_compression/day3_main")

STATS_DIR.mkdir(parents=True, exist_ok=True)
DAY3_DIR.mkdir(parents=True, exist_ok=True)
OUT_ROOT.mkdir(parents=True, exist_ok=True)


def comp_slug(compression: str) -> str:
    return compression.lower().replace("+", "_").replace(" ", "").replace("__", "_")


def run_name_for(m: int, compression: str) -> str:
    return f"w6_N10_M{m}_{comp_slug(compression)}"


def out_dir_for(m: int, compression: str) -> Path:
    return OUT_ROOT / f"pages_M{m}_{comp_slug(compression)}"


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

    x = np.vstack(arrays).astype("float32")
    return files, meta, x


def save_reconstructed(meta, recon, out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)

    for item in meta:
        page_recon = recon[item["start"]:item["end"]]
        np.save(out_dir / item["file"], page_recon.astype("float32"))


def file_size_mb(path: Path) -> float:
    if not path.exists():
        return 0.0

    if path.is_file():
        return path.stat().st_size / 1024 / 1024

    total = 0
    for fp in path.rglob("*"):
        if fp.is_file():
            total += fp.stat().st_size

    return total / 1024 / 1024


def estimate_fp_payload_size_mb(num_vectors: int, dim: int) -> float:
    return num_vectors * dim * 4 / 1024 / 1024


def estimate_code_size_mb(num_vectors: int, pq_m: int, bits: int) -> float:
    return num_vectors * pq_m * bits / 8 / 1024 / 1024


def validate_pq_setting(x, pq_m, bits):
    d = x.shape[1]

    if d % pq_m != 0:
        raise ValueError(f"Embedding dim d={d} must be divisible by pq_m={pq_m}.")

    centroids = 2 ** bits
    if x.shape[0] < centroids:
        raise ValueError(f"Training vectors too few: num_train={x.shape[0]}, centroids={centroids}.")


def build_pq(x, pq_m, bits):
    validate_pq_setting(x, pq_m, bits)

    d = x.shape[1]
    pq = faiss.ProductQuantizer(d, pq_m, bits)
    pq.train(x)

    codes = pq.compute_codes(x)
    recon = pq.decode(codes).astype("float32")

    extra = {
        "reconstruct_mode": "pq_decode",
        "code_size_bytes_per_vector": int(pq_m * bits / 8),
        "ntotal": int(x.shape[0]),
        "is_trained": True,
    }

    return recon, extra


def build_opq_pq(x, pq_m, bits):
    validate_pq_setting(x, pq_m, bits)

    d = x.shape[1]

    opq = faiss.OPQMatrix(d, pq_m)
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

    extra = {
        "reconstruct_mode": "opq_reverse_pq_decode",
        "code_size_bytes_per_vector": int(pq_m * bits / 8),
        "ntotal": int(x.shape[0]),
        "is_trained": True,
    }

    return recon, extra


def reconstruct_ivf_index(index, x):
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
    index = faiss.IndexIVFPQ(quantizer, d, int(nlist), int(pq_m), int(bits))
    index.nprobe = int(nprobe)

    index.train(x)
    index.add(x)

    recon, reconstruct_mode = reconstruct_ivf_index(index, x)

    extra = {
        "reconstruct_mode": reconstruct_mode,
        "code_size_bytes_per_vector": int(index.code_size),
        "ntotal": int(index.ntotal),
        "is_trained": bool(index.is_trained),
    }

    return recon.astype("float32"), extra


def build_ivf_opq_pq(x, pq_m, bits, nlist, nprobe):
    validate_pq_setting(x, pq_m, bits)

    d = x.shape[1]

    opq = faiss.OPQMatrix(d, pq_m)
    opq.niter = 20
    opq.niter_pq = 20
    opq.niter_pq_0 = 10
    opq.verbose = False

    opq.train(x)
    x_opq = opq.apply_py(x).astype("float32")

    quantizer = faiss.IndexFlatL2(d)
    index = faiss.IndexIVFPQ(quantizer, d, int(nlist), int(pq_m), int(bits))
    index.nprobe = int(nprobe)

    index.train(x_opq)
    index.add(x_opq)

    recon_opq, reconstruct_mode = reconstruct_ivf_index(index, x_opq)
    recon = opq.reverse_transform(recon_opq).astype("float32")

    extra = {
        "reconstruct_mode": reconstruct_mode,
        "code_size_bytes_per_vector": int(index.code_size),
        "ntotal": int(index.ntotal),
        "is_trained": bool(index.is_trained),
    }

    return recon.astype("float32"), extra


def build_one(m: int, compression: str):
    input_dir = TOKEN_ROOT / f"pages_M{m}"
    out_dir = out_dir_for(m, compression)
    run_name = run_name_for(m, compression)

    print("=" * 80)
    print(f"[Build] {run_name}")
    print(f"[Input] {input_dir}")
    print(f"[Output] {out_dir}")

    files, meta, x = load_page_embeddings(input_dir)

    num_pages = len(files)
    total_vectors = int(x.shape[0])
    dim = int(x.shape[1])

    original_fp_file_size_mb = file_size_mb(input_dir)
    original_fp_payload_size_mb = estimate_fp_payload_size_mb(total_vectors, dim)
    estimated_code_size_mb = estimate_code_size_mb(total_vectors, PQ_M, BITS)

    t0 = time.time()

    if compression == "PQ":
        recon, extra = build_pq(x, PQ_M, BITS)
    elif compression == "OPQ+PQ":
        recon, extra = build_opq_pq(x, PQ_M, BITS)
    elif compression == "IVF+PQ":
        recon, extra = build_ivf_pq(x, PQ_M, BITS, NLIST, NPROBE)
    elif compression == "IVF+OPQ+PQ":
        recon, extra = build_ivf_opq_pq(x, PQ_M, BITS, NLIST, NPROBE)
    else:
        raise ValueError(f"Unknown compression: {compression}")

    build_time_sec = time.time() - t0

    save_reconstructed(meta, recon, out_dir)

    reconstructed_file_size_mb = file_size_mb(out_dir)

    mse = float(np.mean((x - recon) ** 2))
    mae = float(np.mean(np.abs(x - recon)))

    row = {
        "run_name": run_name,
        "N": 10,
        "M": m,
        "compression": compression,
        "input_dir": str(input_dir),
        "output_dir": str(out_dir),
        "num_pages": num_pages,
        "total_vectors": total_vectors,
        "dim": dim,
        "pq_m": PQ_M,
        "bits": BITS,
        "nlist": NLIST if "IVF" in compression else None,
        "nprobe": NPROBE if "IVF" in compression else None,
        "original_fp_file_size_mb": original_fp_file_size_mb,
        "original_fp_payload_size_mb": original_fp_payload_size_mb,
        "reconstructed_file_size_mb": reconstructed_file_size_mb,
        "estimated_code_size_mb": estimated_code_size_mb,
        "estimated_compression_ratio_vs_fp_payload": (
            original_fp_payload_size_mb / estimated_code_size_mb
            if estimated_code_size_mb > 0 else None
        ),
        "file_ratio_vs_fp_files": (
            original_fp_file_size_mb / reconstructed_file_size_mb
            if reconstructed_file_size_mb > 0 else None
        ),
        "mse": mse,
        "mae": mae,
        "build_time_sec": build_time_sec,
        "index_built": True,
    }

    row.update(extra)

    stats_path = STATS_DIR / f"{run_name}_index_stats.json"
    with stats_path.open("w", encoding="utf-8") as f:
        json.dump(row, f, indent=2, ensure_ascii=False)

    print(f"[Done] {run_name}")
    print(f"[MSE] {mse:.8f}")
    print(f"[MAE] {mae:.8f}")
    print(f"[Estimated code size MB] {estimated_code_size_mb:.6f}")
    print(f"[Build time sec] {build_time_sec:.4f}")

    return row


def main():
    rows = []

    for m in BUDGET_MS:
        for compression in COMPRESSIONS:
            row = build_one(m, compression)
            rows.append(row)

    df = pd.DataFrame(rows)

    csv_path = DAY3_DIR / "day3_quantization_build_summary.csv"
    md_path = DAY3_DIR / "day3_quantization_build_summary.md"

    df.to_csv(csv_path, index=False, encoding="utf-8-sig")

    with md_path.open("w", encoding="utf-8") as f:
        f.write("# Week 6 Day 3 Quantization Build Summary\n\n")
        try:
            f.write(df.to_markdown(index=False))
        except Exception:
            f.write(df.to_string(index=False))
        f.write("\n")

    print("=" * 80)
    print("[Done] Day 3 quantized embeddings built.")
    print(f"[Output] {csv_path}")
    print(f"[Output] {md_path}")


if __name__ == "__main__":
    main()
