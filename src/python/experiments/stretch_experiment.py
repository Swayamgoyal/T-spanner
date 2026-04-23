"""
stretch_experiment.py — Stretch Factor & Sparseness Analysis
=============================================================
For each dataset x t in {3, 5, 7}:
  - Build Baswana-Sen spanner and greedy spanner
  - Sample 500 random pairs, compute stretch
  - Record: avg stretch, max stretch, 95th percentile, sparseness ratio
  - Output: CSV tables + matplotlib plots

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
from src.python.spanner.metrics import compute_stretch, compute_sparseness_ratio
from src.python.data.graph_loader import GraphLoader, RESULTS_DIR, FIGURES_DIR

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np


def run_stretch_experiment(seed=42, num_pairs=500):
    """Run stretch analysis across all datasets and t values."""
    
    loader = GraphLoader()
    
    # Define test graphs (using synthetics — SNAP downloads handled separately)
    graphs = {
        "Erdos-Renyi (1K)": loader.generate_erdos_renyi(1000, 0.01, seed=seed),
        "Grid (30x30)": loader.generate_grid(30, 30),
        "Barabasi-Albert (1K)": loader.generate_barabasi_albert(1000, 3, seed=seed),
        "Small-World (1K)": loader.generate_watts_strogatz(1000, 6, 0.1, seed=seed),
    }
    
    # Try loading SNAP datasets if available
    try:
        fb = loader.load_snap("ego-Facebook")
        graphs["ego-Facebook"] = fb
    except FileNotFoundError:
        print("  [SKIP] ego-Facebook not downloaded")
    
    t_values = [3, 5, 7]
    results = []
    
    print("=" * 80)
    print("STRETCH FACTOR & SPARSENESS ANALYSIS")
    print("=" * 80)
    
    for graph_name, g in graphs.items():
        print(f"\n{'='*60}")
        print(f"Dataset: {graph_name}")
        print(f"  Nodes: {g.num_nodes}, Edges: {g.num_edges}, "
              f"Density: {g.density:.6f}, Avg degree: {g.avg_degree:.2f}")
        print(f"{'='*60}")
        
        for t in t_values:
            k = (t + 1) // 2  # t = 2k-1 → k = (t+1)/2
            
            print(f"\n  t = {t} (k = {k}):")
            
            # Baswana-Sen
            bs_result = baswana_sen_spanner(g, k=k, seed=seed)
            bs_spanner = bs_result["spanner"]
            
            bs_stretch = compute_stretch(g, bs_spanner, num_pairs=num_pairs, seed=seed)
            bs_sparseness = compute_sparseness_ratio(g, bs_spanner)
            
            print(f"    Baswana-Sen: edges={bs_result['num_spanner_edges']}, "
                  f"ratio={bs_sparseness:.4f}, "
                  f"avg_stretch={bs_stretch['avg_stretch']:.4f}, "
                  f"max_stretch={bs_stretch['max_stretch']:.4f}, "
                  f"p95={bs_stretch['p95_stretch']:.4f}")
            
            # Greedy (skip for large graphs)
            gr_stretch_data = None
            gr_sparseness = None
            gr_result = None
            if g.num_nodes <= 2000:
                gr_result = greedy_bfs_spanner(g, t=t)
                gr_spanner = gr_result["spanner"]
                gr_stretch = compute_stretch(g, gr_spanner, num_pairs=num_pairs, seed=seed)
                gr_sparseness = compute_sparseness_ratio(g, gr_spanner)
                gr_stretch_data = gr_stretch
                
                print(f"    Greedy:      edges={gr_result['num_spanner_edges']}, "
                      f"ratio={gr_sparseness:.4f}, "
                      f"avg_stretch={gr_stretch['avg_stretch']:.4f}, "
                      f"max_stretch={gr_stretch['max_stretch']:.4f}, "
                      f"p95={gr_stretch['p95_stretch']:.4f}")
            
            result = {
                "dataset": graph_name,
                "n": g.num_nodes,
                "m": g.num_edges,
                "t": t,
                "k": k,
                # Baswana-Sen
                "bs_edges": bs_result["num_spanner_edges"],
                "bs_sparseness": round(bs_sparseness, 4),
                "bs_avg_stretch": bs_stretch["avg_stretch"],
                "bs_max_stretch": bs_stretch["max_stretch"],
                "bs_median_stretch": bs_stretch["median_stretch"],
                "bs_p95_stretch": bs_stretch["p95_stretch"],
                "bs_std_stretch": bs_stretch["std_stretch"],
                "bs_time_ms": bs_result["construction_time_ms"],
                # Greedy
                "gr_edges": gr_result["num_spanner_edges"] if gr_result else None,
                "gr_sparseness": round(gr_sparseness, 4) if gr_sparseness else None,
                "gr_avg_stretch": gr_stretch_data["avg_stretch"] if gr_stretch_data else None,
                "gr_max_stretch": gr_stretch_data["max_stretch"] if gr_stretch_data else None,
                "gr_time_ms": gr_result["construction_time_ms"] if gr_result else None,
            }
            results.append(result)
    
    # Save results
    save_results(results, "stretch_experiment")
    
    # Plot
    plot_stretch_results(results)
    plot_sparseness_vs_stretch(results)
    
    return results


def plot_stretch_results(results):
    """Plot stretch factor comparison across datasets."""
    fig, axes = plt.subplots(1, 2, figsize=(15, 6))
    
    datasets = list(dict.fromkeys(r["dataset"] for r in results))
    t_values = sorted(set(r["t"] for r in results))
    colors = ['#2196F3', '#FF9800', '#4CAF50', '#E91E63', '#9C27B0']
    
    # Plot 1: Average stretch by dataset and t
    ax = axes[0]
    x = np.arange(len(datasets))
    width = 0.2
    
    for i, t in enumerate(t_values):
        data = [next((r["bs_avg_stretch"] for r in results 
                      if r["dataset"] == d and r["t"] == t), 0) for d in datasets]
        bars = ax.bar(x + i * width - width, data, width, 
                     label=f't={t}', color=colors[i], alpha=0.85)
    
    ax.set_xlabel('Dataset', fontsize=12)
    ax.set_ylabel('Average Stretch', fontsize=12)
    ax.set_title('Average Stretch Factor by Dataset', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels([d.replace(' (1K)', '\n(1K)').replace(' (30x30)', '\n(30x30)') 
                        for d in datasets], fontsize=9, rotation=15)
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3, axis='y')
    ax.axhline(y=1.0, color='gray', linestyle=':', alpha=0.5, label='Optimal (1.0)')
    
    # Plot 2: Sparseness ratio by dataset and t
    ax = axes[1]
    for i, t in enumerate(t_values):
        data = [next((r["bs_sparseness"] for r in results 
                      if r["dataset"] == d and r["t"] == t), 0) for d in datasets]
        bars = ax.bar(x + i * width - width, data, width, 
                     label=f't={t}', color=colors[i], alpha=0.85)
    
    ax.set_xlabel('Dataset', fontsize=12)
    ax.set_ylabel('Sparseness Ratio (|E_s|/|E|)', fontsize=12)
    ax.set_title('Sparseness Ratio by Dataset', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels([d.replace(' (1K)', '\n(1K)').replace(' (30x30)', '\n(30x30)') 
                        for d in datasets], fontsize=9, rotation=15)
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    plt.savefig(FIGURES_DIR / 'stretch_analysis.png', dpi=150, bbox_inches='tight')
    plt.savefig(FIGURES_DIR / 'stretch_analysis.pdf', bbox_inches='tight')
    plt.close()
    print(f"\n  Plot saved to {FIGURES_DIR / 'stretch_analysis.png'}")


def plot_sparseness_vs_stretch(results):
    """Plot the Pareto frontier: sparseness ratio vs average stretch."""
    fig, ax = plt.subplots(figsize=(10, 7))
    
    datasets = list(dict.fromkeys(r["dataset"] for r in results))
    markers = ['o', 's', '^', 'D', 'v', 'p']
    colors_map = {
        "Erdos-Renyi (1K)": '#2196F3',
        "Grid (30x30)": '#4CAF50',
        "Barabasi-Albert (1K)": '#FF5722',
        "Small-World (1K)": '#9C27B0',
        "ego-Facebook": '#FF9800',
    }
    
    for i, dataset in enumerate(datasets):
        data = [r for r in results if r["dataset"] == dataset]
        xs = [r["bs_sparseness"] for r in data]
        ys = [r["bs_avg_stretch"] for r in data]
        ts = [r["t"] for r in data]
        
        color = colors_map.get(dataset, f'C{i}')
        ax.scatter(xs, ys, s=120, marker=markers[i % len(markers)],
                  color=color, label=dataset, edgecolors='white', linewidth=1.5,
                  zorder=5)
        ax.plot(xs, ys, '-', color=color, alpha=0.4, linewidth=1.5)
        
        # Annotate with t values
        for x, y, t in zip(xs, ys, ts):
            ax.annotate(f't={t}', (x, y), textcoords="offset points", 
                       xytext=(8, 5), fontsize=8, color=color)
    
    # Add shading for regions
    ax.axhspan(1.0, 1.5, xmin=0, xmax=0.5, alpha=0.1, color='green', zorder=0)
    ax.text(0.15, 1.4, 'Sweet Spot', fontsize=10, color='green', alpha=0.7,
            ha='center', style='italic')
    
    ax.set_xlabel('Sparseness Ratio (|E_spanner| / |E_original|)', fontsize=13)
    ax.set_ylabel('Average Stretch Factor', fontsize=13)
    ax.set_title('Pareto Frontier: Sparseness vs Stretch', fontsize=15, fontweight='bold')
    ax.legend(fontsize=10, loc='upper left')
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / 'pareto_frontier.png', dpi=150, bbox_inches='tight')
    plt.savefig(FIGURES_DIR / 'pareto_frontier.pdf', bbox_inches='tight')
    plt.close()
    print(f"  Plot saved to {FIGURES_DIR / 'pareto_frontier.png'}")


def save_results(results, name):
    """Save results as CSV and JSON."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    with open(RESULTS_DIR / f"{name}.json", 'w') as f:
        json.dump(results, f, indent=2)
    if results:
        with open(RESULTS_DIR / f"{name}.csv", 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)
    print(f"  Results saved to {RESULTS_DIR / name}.[json|csv]")


if __name__ == "__main__":
    run_stretch_experiment()
