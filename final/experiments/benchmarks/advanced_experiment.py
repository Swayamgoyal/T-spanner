"""
advanced_experiment.py — Hybrid Adaptive Spanner vs Baswana-Sen vs Greedy
==========================================================================
Head-to-head comparison of all three algorithms across multiple graph types.

Key Question: Does the Hybrid Adaptive Spanner (HAS) produce sparser 
spanners than standard Baswana-Sen while maintaining the stretch guarantee?

Metrics compared:
  - Spanner edge count (sparsity)
  - Average / max stretch
  - Construction time
  - Edges pruned by HAS
  - Topology detection accuracy

Part of t-Spanner project — Person A (Implementation & Engineering)
"""

import os
import sys
import json
import csv
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from src.python.spanner.graph import Graph
from src.python.spanner.baswana_sen import baswana_sen_spanner
from src.python.spanner.greedy_spanner import greedy_bfs_spanner
from src.python.spanner.advanced_spanner import hybrid_adaptive_spanner
from src.python.spanner.metrics import compute_stretch, verify_spanner_property
from src.python.data.graph_loader import GraphLoader, RESULTS_DIR, FIGURES_DIR

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np


def run_advanced_experiment(num_pairs=300, seed=42):
    """Run the 3-way algorithm comparison."""

    loader = GraphLoader()

    # Test across diverse topologies to show HAS's adaptive behavior
    graphs = {
        "Erdos-Renyi (1K)": loader.generate_erdos_renyi(1000, 0.01, seed=seed),
        "Grid (30x30)": loader.generate_grid(30, 30),
        "Barabasi-Albert (1K)": loader.generate_barabasi_albert(1000, 3, seed=seed),
        "Small-World (1K)": loader.generate_watts_strogatz(1000, 6, 0.1, seed=seed),
        "Erdos-Renyi (500, dense)": loader.generate_erdos_renyi(500, 0.05, seed=seed),
    }

    t_values = [3, 5]
    results = []

    print("=" * 90)
    print("ADVANCED EXPERIMENT: Hybrid Adaptive Spanner vs Baswana-Sen vs Greedy")
    print("=" * 90)

    for graph_name, g in graphs.items():
        print(f"\n{'='*70}")
        print(f"Dataset: {graph_name}")
        print(f"  Nodes: {g.num_nodes}, Edges: {g.num_edges}, "
              f"Density: {g.density:.6f}, Avg degree: {g.avg_degree:.2f}")
        print(f"{'='*70}")

        for t in t_values:
            k = (t + 1) // 2

            print(f"\n  t = {t} (k = {k}):")

            # ─── 1. Standard Baswana-Sen ───
            bs_result = baswana_sen_spanner(g, k=k, seed=seed)
            bs_stretch = compute_stretch(g, bs_result["spanner"], num_pairs=num_pairs, seed=seed)
            bs_valid = verify_spanner_property(g, bs_result["spanner"], t=t, num_samples=num_pairs, seed=seed)

            print(f"    Baswana-Sen:       edges={bs_result['num_spanner_edges']:>5d}, "
                  f"ratio={bs_result['sparseness_ratio']:.4f}, "
                  f"avg_stretch={bs_stretch['avg_stretch']:.4f}, "
                  f"max_stretch={bs_stretch['max_stretch']:.4f}, "
                  f"time={bs_result['construction_time_ms']:.1f}ms, "
                  f"valid={'YES' if bs_valid['is_valid'] else 'NO'}")

            # ─── 2. Hybrid Adaptive Spanner (HAS) ───
            has_result = hybrid_adaptive_spanner(g, k=k, seed=seed, pruning_sample_ratio=0.5)
            has_stretch = compute_stretch(g, has_result["spanner"], num_pairs=num_pairs, seed=seed)
            has_valid = verify_spanner_property(g, has_result["spanner"], t=t, num_samples=num_pairs, seed=seed)

            improvement = (1 - has_result['num_spanner_edges'] / max(bs_result['num_spanner_edges'], 1)) * 100

            print(f"    Hybrid Adaptive:   edges={has_result['num_spanner_edges']:>5d}, "
                  f"ratio={has_result['sparseness_ratio']:.4f}, "
                  f"avg_stretch={has_stretch['avg_stretch']:.4f}, "
                  f"max_stretch={has_stretch['max_stretch']:.4f}, "
                  f"time={has_result['construction_time_ms']:.1f}ms, "
                  f"valid={'YES' if has_valid['is_valid'] else 'NO'}")
            print(f"                       topology={has_result['topology_detected']}, "
                  f"pruned={has_result['edges_pruned']} edges, "
                  f"improvement={improvement:+.1f}% vs BS")

            # ─── 3. Greedy (baseline — only for smaller graphs) ───
            gr_result = None
            gr_stretch = None
            gr_valid = None
            if g.num_nodes <= 1500:
                gr_result = greedy_bfs_spanner(g, t=t)
                gr_stretch = compute_stretch(g, gr_result["spanner"], num_pairs=num_pairs, seed=seed)
                gr_valid = verify_spanner_property(g, gr_result["spanner"], t=t, num_samples=num_pairs, seed=seed)

                print(f"    Greedy:            edges={gr_result['num_spanner_edges']:>5d}, "
                      f"ratio={gr_result['sparseness_ratio']:.4f}, "
                      f"avg_stretch={gr_stretch['avg_stretch']:.4f}, "
                      f"max_stretch={gr_stretch['max_stretch']:.4f}, "
                      f"time={gr_result['construction_time_ms']:.1f}ms, "
                      f"valid={'YES' if gr_valid['is_valid'] else 'NO'}")

            # ─── Store result ───
            result = {
                "dataset": graph_name,
                "n": g.num_nodes,
                "m": g.num_edges,
                "t": t,
                "k": k,
                "topology": has_result["topology_detected"],
                # Baswana-Sen
                "bs_edges": bs_result["num_spanner_edges"],
                "bs_ratio": round(bs_result["sparseness_ratio"], 4),
                "bs_avg_stretch": bs_stretch["avg_stretch"],
                "bs_max_stretch": bs_stretch["max_stretch"],
                "bs_time_ms": bs_result["construction_time_ms"],
                "bs_valid": bs_valid["is_valid"],
                # HAS
                "has_edges": has_result["num_spanner_edges"],
                "has_ratio": round(has_result["sparseness_ratio"], 4),
                "has_avg_stretch": has_stretch["avg_stretch"],
                "has_max_stretch": has_stretch["max_stretch"],
                "has_time_ms": has_result["construction_time_ms"],
                "has_valid": has_valid["is_valid"],
                "has_pruned": has_result["edges_pruned"],
                "has_improvement_pct": round(improvement, 2),
                # Greedy
                "gr_edges": gr_result["num_spanner_edges"] if gr_result else None,
                "gr_ratio": round(gr_result["sparseness_ratio"], 4) if gr_result else None,
                "gr_avg_stretch": gr_stretch["avg_stretch"] if gr_stretch else None,
                "gr_time_ms": gr_result["construction_time_ms"] if gr_result else None,
                "gr_valid": gr_valid["is_valid"] if gr_valid else None,
            }
            results.append(result)

    # ─── Summary ───
    print("\n" + "=" * 90)
    print("SUMMARY: HAS Improvement Over Baswana-Sen")
    print("=" * 90)
    for r in results:
        sign = "+" if r["has_improvement_pct"] < 0 else "-"
        print(f"  {r['dataset']:>30s} t={r['t']}: "
              f"BS={r['bs_edges']} -> HAS={r['has_edges']} "
              f"({r['has_improvement_pct']:+.1f}%), "
              f"topology={r['topology']}, pruned={r['has_pruned']}")

    # Save & plot
    save_results(results, "advanced_experiment")
    plot_three_way_comparison(results)
    plot_improvement_chart(results)

    return results


def plot_three_way_comparison(results):
    """Plot 3-way algorithm comparison: edge count and stretch."""
    fig, axes = plt.subplots(1, 2, figsize=(16, 7))

    datasets = list(dict.fromkeys(r["dataset"] for r in results))
    t_values = sorted(set(r["t"] for r in results))

    # Colors
    c_bs = '#2196F3'
    c_has = '#4CAF50'
    c_gr = '#FF9800'

    # Plot 1: Edge count comparison
    ax = axes[0]
    x_positions = []
    x_labels = []
    group_width = 3.5
    pos = 0

    for d_idx, dataset in enumerate(datasets):
        for t in t_values:
            data = [r for r in results if r["dataset"] == dataset and r["t"] == t]
            if not data:
                continue
            r = data[0]

            label_bs = 'Baswana-Sen' if pos == 0 else None
            label_has = 'Hybrid Adaptive' if pos == 0 else None
            label_gr = 'Greedy' if pos == 0 else None

            ax.bar(pos - 0.75, r["bs_edges"], 0.7, color=c_bs, alpha=0.85, label=label_bs)
            ax.bar(pos, r["has_edges"], 0.7, color=c_has, alpha=0.85, label=label_has)
            if r["gr_edges"]:
                ax.bar(pos + 0.75, r["gr_edges"], 0.7, color=c_gr, alpha=0.85, label=label_gr)

            # Improvement annotation
            if r["has_improvement_pct"] > 0:
                ax.annotate(f'{r["has_improvement_pct"]:.0f}% fewer',
                           xy=(pos, r["has_edges"]),
                           xytext=(pos, r["has_edges"] * 1.05),
                           fontsize=7, ha='center', color='green', fontweight='bold')

            x_positions.append(pos)
            short_name = dataset.split('(')[0].strip()[:12]
            x_labels.append(f"{short_name}\nt={t}")
            pos += group_width

    ax.set_xticks(x_positions)
    ax.set_xticklabels(x_labels, fontsize=8)
    ax.set_ylabel('Spanner Edges', fontsize=12)
    ax.set_title('Edge Count: BS vs HAS vs Greedy', fontsize=14, fontweight='bold')
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3, axis='y')

    # Plot 2: Average stretch comparison
    ax = axes[1]
    pos = 0
    x_positions = []
    x_labels = []

    for d_idx, dataset in enumerate(datasets):
        for t in t_values:
            data = [r for r in results if r["dataset"] == dataset and r["t"] == t]
            if not data:
                continue
            r = data[0]

            ax.bar(pos - 0.75, r["bs_avg_stretch"], 0.7, color=c_bs, alpha=0.85)
            ax.bar(pos, r["has_avg_stretch"], 0.7, color=c_has, alpha=0.85)
            if r["gr_avg_stretch"]:
                ax.bar(pos + 0.75, r["gr_avg_stretch"], 0.7, color=c_gr, alpha=0.85)

            x_positions.append(pos)
            short_name = dataset.split('(')[0].strip()[:12]
            x_labels.append(f"{short_name}\nt={t}")
            pos += group_width

    ax.set_xticks(x_positions)
    ax.set_xticklabels(x_labels, fontsize=8)
    ax.set_ylabel('Average Stretch', fontsize=12)
    ax.set_title('Average Stretch: BS vs HAS vs Greedy', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3, axis='y')
    ax.axhline(y=1.0, color='gray', linestyle=':', alpha=0.5)

    plt.tight_layout()
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    plt.savefig(FIGURES_DIR / 'advanced_3way_comparison.png', dpi=150, bbox_inches='tight')
    plt.savefig(FIGURES_DIR / 'advanced_3way_comparison.pdf', bbox_inches='tight')
    plt.close()
    print(f"\n  Plot saved to {FIGURES_DIR / 'advanced_3way_comparison.png'}")


def plot_improvement_chart(results):
    """Plot HAS improvement over BS by topology type."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    # Group by topology
    topologies = list(dict.fromkeys(r["topology"] for r in results))
    topo_colors = {
        "scale-free": "#FF5722",
        "grid-like": "#4CAF50",
        "small-world": "#9C27B0",
        "random": "#2196F3",
        "unknown": "#607D8B",
    }

    # Plot 1: Improvement % by topology
    ax = axes[0]
    for topo in topologies:
        data = [r for r in results if r["topology"] == topo]
        improvements = [r["has_improvement_pct"] for r in data]
        labels = [f"{r['dataset'].split('(')[0].strip()}\nt={r['t']}" for r in data]

        color = topo_colors.get(topo, '#607D8B')
        bars = ax.barh(
            [f"{l} [{topo}]" for l in labels],
            improvements,
            color=color, alpha=0.85, edgecolor='white', linewidth=0.8,
        )

    ax.set_xlabel('Improvement Over Baswana-Sen (%)', fontsize=12)
    ax.set_title('HAS Edge Reduction by Topology', fontsize=14, fontweight='bold')
    ax.axvline(x=0, color='white', linewidth=1)
    ax.grid(True, alpha=0.3, axis='x')

    # Plot 2: Edges pruned vs topology
    ax = axes[1]
    for topo in topologies:
        data = [r for r in results if r["topology"] == topo]
        if not data:
            continue
        pruned = [r["has_pruned"] for r in data]
        has_edges = [r["has_edges"] for r in data]
        color = topo_colors.get(topo, '#607D8B')
        ax.scatter(has_edges, pruned, s=120, c=color, label=topo,
                  edgecolors='white', linewidth=1, zorder=5)

    ax.set_xlabel('HAS Spanner Edges', fontsize=12)
    ax.set_ylabel('Edges Pruned by HAS', fontsize=12)
    ax.set_title('Pruning Effectiveness', fontsize=14, fontweight='bold')
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(FIGURES_DIR / 'advanced_improvement.png', dpi=150, bbox_inches='tight')
    plt.savefig(FIGURES_DIR / 'advanced_improvement.pdf', bbox_inches='tight')
    plt.close()
    print(f"  Plot saved to {FIGURES_DIR / 'advanced_improvement.png'}")


def save_results(results, name):
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(RESULTS_DIR / f"{name}.json", 'w') as f:
        json.dump(results, f, indent=2, default=str)
    if results:
        with open(RESULTS_DIR / f"{name}.csv", 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)
    print(f"  Results saved to {RESULTS_DIR / name}.[json|csv]")


if __name__ == "__main__":
    run_advanced_experiment()
