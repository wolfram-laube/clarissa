#!/usr/bin/env python3
"""Merge OPM Flow and MRST results into unified spe_benchmarks.json.

Usage:
    python3 merge_results.py \\
        --opm  ~/projects/results/clarissa-benchmarks/spe_benchmarks.json \\
        --mrst ~/mrst_results/ \\
        --output spe_benchmarks_final.json

The MRST dir should contain files like spe1_mrst.json, spe5_mrst.json, etc.
"""
import argparse
import json
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--opm", required=True, help="OPM benchmarks JSON")
    parser.add_argument("--mrst", required=True, help="MRST results directory")
    parser.add_argument("--output", required=True, help="Output merged JSON")
    args = parser.parse_args()

    # Load OPM
    with open(args.opm) as f:
        data = json.load(f)

    mrst_dir = Path(args.mrst)
    merged = 0

    for bm_key, bm_data in data["benchmarks"].items():
        # Try to find matching MRST result
        for pattern in [
            mrst_dir / f"{bm_key.lower()}_mrst.json",
            mrst_dir / f"{bm_key}_mrst.json",
        ]:
            if pattern.exists():
                print(f"  Merging MRST for {bm_key}: {pattern}")
                with open(pattern) as f:
                    mrst = json.load(f)
                bm_data["mrst"] = mrst
                merged += 1
                break

    with open(args.output, "w") as f:
        json.dump(data, f, separators=(",", ":"))

    size_mb = Path(args.output).stat().st_size / 1e6
    print(f"\nMerged {merged} MRST results → {args.output} ({size_mb:.1f} MB)")


if __name__ == "__main__":
    main()
