import os
import sys

# Ensure repo root is on sys.path so `src` package is importable
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from src.utils.analysis import bootstrap_ci, compute_stats, detect_outliers


def main():
    sample = [100.1, 99.8, 100.5, 101.2, 99.9, 100.0, 100.3, 99.7, 100.6, 100.2, 115.0]
    print("sample:", sample)
    stats = compute_stats(sample)
    print("stats:")
    for k, v in stats.items():
        print(" ", k, ":", v)

    out_z = detect_outliers(sample, method="z", thresh=3.0)
    out_mad = detect_outliers(sample, method="mad", thresh=3.5)
    print("outliers (z):", out_z)
    print("outliers (mad):", out_mad)

    ci = bootstrap_ci([x for x in sample if x < 110], stat="mean", n_iter=1000)
    print("bootstrap CI (mean):", ci)


if __name__ == "__main__":
    main()
