#!/usr/bin/env python3
"""Build a public read-only index from the reviewed CSVs already in the repository."""
import argparse
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "site" / "data" / "experiments.json"
WALKS = {"ball", "dikin", "coordinate_hit_run", "random_hit_run", "john"}
CHECKPOINTS_N20 = {"ball": 128, "dikin": 1024, "coordinate_hit_run": 64, "random_hit_run": 32, "john": 2048}

def rows(path):
    with (ROOT / path).open(newline="", encoding="utf-8") as f:
        yield from csv.DictReader(f)

def val(s, cast=float):
    return None if s in ("", None) else cast(s)

def record(source, file, walk, n, language, stage, checkpoint=None, us_per_step=None, runtime_s=None,
           steps=None, chains=None, seed=None, repeats=1, threads=None, exact_tv=None, notes=""):
    if walk not in WALKS or n < 1:
        raise ValueError(f"Invalid result: {walk}, {n}")
    return dict(id=f"{source}:{stage}:{language}:{walk}:n{n}", source=source, source_file=file, walk=walk,
                n=n, language=language, stage=stage, checkpoint=checkpoint, us_per_step=us_per_step,
                runtime_s=runtime_s, steps=steps, chains=chains, seed=seed, repeats=repeats,
                threads=threads, exact_tv_10pct_steps=exact_tv, notes=notes)

def build():
    out = []
    file = "results/reported_mac_results/n1_to_n10_transcribed.csv"
    for r in rows(file):
        for lang in ("python", "cpp"):
            out.append(record("mac_dimension_sweep", file, r["walk"], int(r["dimension"]), lang, "explicit",
                checkpoint=val(r[f"baseline_{lang}_empirical_checkpoint"], int),
                us_per_step=val(r[f"baseline_{lang}_us_per_step"]),
                steps=2560, chains=3000, seed=2026, threads=1,
                notes="Mac screenshot transcription (rounded); study protocol supplied dimensions/steps/chains/seed. Not an imported raw run."))

    file = "results/reported_mac_results/n20_elapsed_seconds_transcribed.csv"
    for r in rows(file):
        for lang in ("python", "cpp"):
            for stage in ("explicit", "optimized"):
                field = f"{'baseline' if stage == 'explicit' else 'optimized'}_{lang}"
                field += "_four_threads_seconds" if lang == "cpp" and stage == "optimized" else "_seconds"
                seconds = float(r[field])
                steps, chains = int(r["steps"]), int(r["chains"])
                out.append(record("mac_n20", file, r["walk"], int(r["dimension"]), lang, stage,
                    checkpoint=CHECKPOINTS_N20[r["walk"]], runtime_s=seconds,
                    us_per_step=round(seconds * 1e6 / (steps * chains), 6),
                    steps=steps, chains=chains, seed=int(r["seed"]),
                    threads=4 if lang == "cpp" and stage == "optimized" else 1,
                    exact_tv=103 if r["walk"] == "coordinate_hit_run" else None,
                    notes="Mac Terminal/Jupyter transcription. Per-step cost derived from full-run elapsed time. Checkpoint is an empirical proxy, not a TV mixing time."))

    file = "results/example_development_n1_to_n10/combined_results.csv"
    for r in rows(file):
        for lang in ("python", "cpp"):
            out.append(record("development_dimension_pilot", file, r["walk"], int(r["n"]), lang, "explicit",
                checkpoint=val(r[f"{lang}_proxy_steps"], int), us_per_step=val(r[f"{lang}_us_per_step"]),
                exact_tv=val(r["exact_coordinate_tv_10pct_steps"], int), repeats=None,
                notes="Development pilot with unknown run budget, chains and seed in the published summary; not a Mac benchmark."))

    file = "results/example_development_n20/tables/combined_results.csv"
    for r in rows(file):
        for lang in ("python", "cpp"):
            out.append(record("development_n20", file, r["walk"], int(r["n"]), lang, "optimized",
                checkpoint=val(r[f"{lang}_proxy_steps"], int), us_per_step=val(r[f"{lang}_us_per_step"]),
                exact_tv=val(r["exact_coordinate_tv_10pct_steps"], int),
                steps=2560, chains=3000, seed=2026, threads=4 if lang == "cpp" else 1,
                notes="Linux development example; not a timing measured on the owner's Mac. See archived parameters.json."))

    ids = [r["id"] for r in out]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate experiment IDs")
    return {"schema_version": 1,
            "criterion": "Maximum marginal and pairwise-sum KS <= 0.15; relative second moment error <= 0.25; two consecutive recorded positive checkpoints. Not full-law TV.",
            "records": sorted(out, key=lambda x: (x["n"], x["walk"], x["source"], x["stage"], x["language"]))}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--check", action="store_true")
    args = p.parse_args()
    data = build()
    content = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    if args.check:
        if not OUTPUT.exists() or OUTPUT.read_text(encoding="utf-8") != content:
            raise SystemExit("Stale public index: run python tools/build_public_index.py")
        print("Public experiment index matches the curated source CSVs")
    else:
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT.write_text(content, encoding="utf-8")
        print(f"Wrote {len(data['records'])} curated records to {OUTPUT}")
if __name__ == "__main__":
    main()
