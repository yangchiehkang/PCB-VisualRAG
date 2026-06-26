from pathlib import Path
import pandas as pd

OUT_DIR = Path("results/budgeted/joint_compression/summary")
OUT_DIR.mkdir(parents=True, exist_ok=True)

configs = []

budget_points = [
    {
        "budget_level": "Low-budget",
        "N": 10,
        "M": 8,
        "note": "Extreme lightweight token budget"
    },
    {
        "budget_level": "Mid-budget",
        "N": 10,
        "M": 16,
        "note": "Best Week 5 trade-off"
    },
    {
        "budget_level": "High-budget",
        "N": 10,
        "M": 24,
        "note": "Conservative high-quality token budget"
    },
]

compressions = [
    ("None", "none", "without vector compression"),
    ("PQ", "pq", "with PQ compression"),
    ("OPQ+PQ", "opq_pq", "with OPQ plus PQ"),
    ("IVF+PQ", "ivf_pq", "with IVF plus PQ"),
    ("IVF+OPQ+PQ", "ivf_opq_pq", "with IVF plus OPQ plus PQ"),
]

for bp in budget_points:
    for comp_name, comp_slug, comp_note in compressions:
        run_name = f"w6_N{bp['N']}_M{bp['M']}_{comp_slug}"
        configs.append({
            "budget_level": bp["budget_level"],
            "N": bp["N"],
            "M": bp["M"],
            "compression": comp_name,
            "run_name": run_name,
            "role": "main",
            "notes": f"{bp['note']} {comp_note}",
        })

configs.append({
    "budget_level": "Reference",
    "N": 10,
    "M": 49,
    "compression": "None",
    "run_name": "w6_N10_M49_none",
    "role": "reference",
    "notes": "Full-token C2F reference from Week 5",
})

configs.append({
    "budget_level": "System-reference",
    "N": "N/A",
    "M": "full",
    "compression": "None",
    "run_name": "full_mv_reference",
    "role": "reference",
    "notes": "Full Multi-vector system-level reference",
})

df = pd.DataFrame(configs)

csv_path = OUT_DIR / "week6_experiment_matrix.csv"
md_path = OUT_DIR / "week6_experiment_matrix.md"

df.to_csv(csv_path, index=False, encoding="utf-8-sig")

with md_path.open("w", encoding="utf-8") as f:
    f.write("# Week 6 Joint Budget Experiment Matrix\n\n")
    f.write("This file defines the Week 6 joint budget experiment matrix.\n\n")
    f.write("The main budget is defined as:\n\n")
    f.write("```text\n")
    f.write("Budget = (N, M, Compression)\n")
    f.write("```\n\n")
    f.write("Current real constraints:\n\n")
    f.write("- N is fixed to 10 because the current coarse candidate file provides top-10 candidates.\n")
    f.write("- M must be no larger than 49 because each page has 49 visual tokens.\n")
    f.write("- Main matrix uses M8, M16, and M24 as low, mid, and high budget points.\n")
    f.write("- M49 is kept as full-token reference.\n\n")
    f.write(df.to_markdown(index=False))
    f.write("\n")

print("[Done] Week 6 experiment matrix generated.")
print(f"[Output] {csv_path}")
print(f"[Output] {md_path}")
