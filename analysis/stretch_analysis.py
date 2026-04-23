"""
stretch_analysis.py — Stretch Factor & Sparseness Ratio Analysis
=================================================================
Reads Person A's experimental CSVs and computes comprehensive stretch
metrics, sparseness ratios, and statistical analysis for the report.

Part of t-Spanner project — Person B (Research, Analysis & Writing)
"""

import os
import sys
import csv
import math
from collections import defaultdict

RESULTS_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'results')
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'results')


def load_csv(filename):
    """Load a CSV file and return list of dicts."""
    filepath = os.path.join(RESULTS_DIR, filename)
    if not os.path.exists(filepath):
        print(f"[WARN] File not found: {filepath}")
        return []
    with open(filepath, 'r') as f:
        reader = csv.DictReader(f)
        return list(reader)


def analyze_stretch_experiment():
    """
    Compute and display comprehensive stretch metrics from stretch_experiment.csv.
    Reports: avg stretch, max stretch, p95 stretch, sparseness ratio
    for each (dataset, t) combination, for both BS and Greedy algorithms.
    """
    print("\n" + "=" * 80)
    print("STRETCH FACTOR & SPARSENESS RATIO ANALYSIS")
    print("=" * 80)

    rows = load_csv('stretch_experiment.csv')
    if not rows:
        return

    # ── Table 1: Baswana-Sen Metrics ──
    print("\n── Table 1: Baswana-Sen Spanner Metrics ──")
    print(f"{'Dataset':<25} {'t':>3} {'Edges':>7} {'Sparseness':>11} {'Avg Str':>9} {'Max Str':>9} {'P95 Str':>9} {'Time(ms)':>10}")
    print("-" * 95)
    for r in rows:
        print(f"{r['dataset']:<25} {r['t']:>3} {r['bs_edges']:>7} {float(r['bs_sparseness']):>11.4f} "
              f"{float(r['bs_avg_stretch']):>9.4f} {float(r['bs_max_stretch']):>9.4f} "
              f"{float(r['bs_p95_stretch']):>9.4f} {float(r['bs_time_ms']):>10.2f}")

    # ── Table 2: Greedy Spanner Metrics ──
    print("\n── Table 2: Greedy Spanner Metrics ──")
    print(f"{'Dataset':<25} {'t':>3} {'Edges':>7} {'Sparseness':>11} {'Avg Str':>9} {'Max Str':>9} {'Time(ms)':>10}")
    print("-" * 80)
    for r in rows:
        print(f"{r['dataset']:<25} {r['t']:>3} {r['gr_edges']:>7} {float(r['gr_sparseness']):>11.4f} "
              f"{float(r['gr_avg_stretch']):>9.4f} {float(r['gr_max_stretch']):>9.4f} "
              f"{float(r['gr_time_ms']):>10.2f}")

    # ── Key Findings ──
    print("\n── KEY FINDINGS ──")

    # Finding 1: Average stretch is much lower than theoretical max
    avg_stretches = [float(r['gr_avg_stretch']) for r in rows if float(r['t']) == 3]
    if avg_stretches:
        mean_avg = sum(avg_stretches) / len(avg_stretches)
        print(f"  [1] At t=3, average stretch across all topologies: {mean_avg:.4f}")
        print(f"      Theoretical max = 3.0, actual avg = {mean_avg:.4f} → {mean_avg/3*100:.1f}% of theoretical")

    # Finding 2: Topology with best/worst sparseness
    if rows:
        t3_rows = [r for r in rows if int(r['t']) == 3]
        if t3_rows:
            best = min(t3_rows, key=lambda r: float(r['gr_sparseness']))
            worst = max(t3_rows, key=lambda r: float(r['gr_sparseness']))
            print(f"  [2] Best sparseness at t=3: {best['dataset']} ({float(best['gr_sparseness']):.4f})")
            print(f"      Worst sparseness at t=3: {worst['dataset']} ({float(worst['gr_sparseness']):.4f})")

    # Finding 3: Greedy vs BS speedup
    speedups = []
    for r in rows:
        bs_t = float(r['bs_time_ms'])
        gr_t = float(r['gr_time_ms'])
        if bs_t > 0:
            speedups.append(gr_t / bs_t)
    if speedups:
        avg_speedup = sum(speedups) / len(speedups)
        print(f"  [3] Greedy is {avg_speedup:.1f}x slower than Baswana-Sen on average")


def analyze_advanced_experiment():
    """
    Analyze the HAS vs BS vs Greedy comparison data.
    """
    print("\n" + "=" * 80)
    print("HYBRID ADAPTIVE SPANNER (HAS) COMPARISON ANALYSIS")
    print("=" * 80)

    rows = load_csv('advanced_experiment.csv')
    if not rows:
        return

    print(f"\n{'Dataset':<30} {'t':>3} {'BS':>7} {'HAS':>7} {'Greedy':>7} {'HAS Improv':>11} {'HAS Valid':>10}")
    print("-" * 90)
    for r in rows:
        print(f"{r['dataset']:<30} {r['t']:>3} {r['bs_edges']:>7} {r['has_edges']:>7} "
              f"{r['gr_edges']:>7} {r['has_improvement_pct']:>10}% {r['has_valid']:>10}")

    # Compute averages
    improvements = [float(r['has_improvement_pct']) for r in rows]
    if improvements:
        print(f"\n  Average HAS improvement over BS: {sum(improvements)/len(improvements):.1f}%")
        print(f"  Min improvement: {min(improvements):.1f}%")
        print(f"  Max improvement: {max(improvements):.1f}%")
        print(f"  All stretch-valid: {all(r['has_valid'] == 'True' for r in rows)}")


def analyze_fault_tolerance():
    """
    Analyze fault tolerance data by topology.
    """
    print("\n" + "=" * 80)
    print("FAULT TOLERANCE ANALYSIS")
    print("=" * 80)

    rows = load_csv('fault_tolerance.csv')
    if not rows:
        return

    # Group by dataset
    datasets = defaultdict(list)
    for r in rows:
        datasets[r['dataset']].append(r)

    for dataset, data in datasets.items():
        print(f"\n  {dataset}:")
        for r in data:
            conn = float(r['connectivity_ratio'])
            stretch = float(r['damaged_avg_stretch'])
            print(f"    Failure {float(r['failure_rate'])*100:>5.1f}% | "
                  f"Connectivity: {conn*100:>6.1f}% | "
                  f"Avg Stretch: {stretch:.4f} | "
                  f"Max Stretch: {r['damaged_max_stretch']}")


def analyze_seed_variance():
    """
    Analyze random seed sensitivity.
    """
    print("\n" + "=" * 80)
    print("RANDOM SEED SENSITIVITY ANALYSIS")
    print("=" * 80)

    rows = load_csv('seed_variance.csv')
    if not rows:
        return

    print(f"\n{'Dataset':<25} {'k':>3} {'CV(Edges)':>12} {'CV(Stretch)':>13} {'Assessment':>15}")
    print("-" * 75)
    for r in rows:
        cv_edges = float(r['edge_count_cv'])
        cv_stretch = float(r['avg_stretch_std']) if float(r['avg_stretch_mean']) > 0 else 0
        assessment = "Stable" if cv_edges < 0.01 else "Moderate" if cv_edges < 0.05 else "Unstable"
        print(f"{r['dataset']:<25} {r['k']:>3} {cv_edges:>12.6f} {cv_stretch:>13.6f} {assessment:>15}")

    print("\n  Interpretation: CV < 0.01 → algorithm is extremely stable across seeds.")
    print("  This is expected: with p = n^{-1/k} and n ≥ 500, concentration inequalities apply.")


def generate_report_tables():
    """
    Generate formatted markdown tables for the report.
    """
    print("\n" + "=" * 80)
    print("MARKDOWN TABLES FOR REPORT")
    print("=" * 80)

    rows = load_csv('stretch_experiment.csv')
    if not rows:
        return

    # Table: Greedy spanner metrics
    print("\n### Greedy Spanner: Stretch and Sparseness")
    print("| Dataset | t | Edges | Sparseness | Avg Stretch | Max Stretch | P95 Stretch |")
    print("|:--------|:-:|------:|-----------:|------------:|------------:|------------:|")
    for r in rows:
        print(f"| {r['dataset']} | {r['t']} | {r['gr_edges']} | "
              f"{float(r['gr_sparseness']):.4f} | {float(r['gr_avg_stretch']):.4f} | "
              f"{float(r['gr_max_stretch']):.4f} | — |")


if __name__ == "__main__":
    print("t-Spanner Stretch & Sparseness Analysis (Person B)")
    print("=" * 60)

    analyze_stretch_experiment()
    analyze_advanced_experiment()
    analyze_fault_tolerance()
    analyze_seed_variance()
    generate_report_tables()

    print("\n[DONE] All analyses complete.")
