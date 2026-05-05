"""
seed_variance.py — Random Seed Sensitivity Analysis
=====================================================
Run 50 different random seeds on the same graph.
Plot variance in |E_spanner| and average stretch.
Answers Person B's Q2: "Does the choice of random seed matter?"

Part of t-Spanner project — Person A (Implementation & Engineering)
"""

import os
import sys
import json
import csv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from src.python.spanner.baswana_sen import baswana_sen_spanner
from src.python.spanner.metrics import compute_stretch 
from src.python.data.graph_loader import GraphLoader, RESULTS_DIR, FIGURES_DIR

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np


def run_seed_variance(num_seeds=50, num_pairs=200):
    """Analyze impact of random seed on spanner quality."""
    
    loader = GraphLoader()
    
    graphs = {
        "Erdos-Renyi (500)": loader.generate_erdos_renyi(500, 0.03, seed=0),
        "Barabasi-Albert (500)": loader.generate_barabasi_albert(500, 3, seed=0),
    }
    
    results = []
    
    print("=" * 70)
    print(f"SEED VARIANCE ANALYSIS ({num_seeds} seeds)")
    print("=" * 70)
    
    for graph_name, g in graphs.items():
        print(f"\n{graph_name}: n={g.num_nodes}, m={g.num_edges}")
        
        for k in [2, 3]:
            edge_counts = []
            avg_stretches = []
            max_stretches = []
            times = []
            
            for seed in range(num_seeds):
                r = baswana_sen_spanner(g, k=k, seed=seed)
                stretch = compute_stretch(g, r["spanner"], num_pairs=num_pairs, seed=seed)
                
                edge_counts.append(r["num_spanner_edges"])
                avg_stretches.append(stretch["avg_stretch"])
                max_stretches.append(stretch["max_stretch"])
                times.append(r["construction_time_ms"])
            
            result = {
                "dataset": graph_name,
                "k": k,
                "t": 2 * k - 1,
                "num_seeds": num_seeds,
                "edge_count_mean": round(np.mean(edge_counts), 2),
                "edge_count_std": round(np.std(edge_counts), 2),
                "edge_count_min": min(edge_counts),
                "edge_count_max": max(edge_counts),
                "edge_count_cv": round(np.std(edge_counts) / np.mean(edge_counts), 4),
                "avg_stretch_mean": round(np.mean(avg_stretches), 4),
                "avg_stretch_std": round(np.std(avg_stretches), 4),
                "max_stretch_mean": round(np.mean(max_stretches), 4),
                "max_stretch_std": round(np.std(max_stretches), 4),
                "time_mean_ms": round(np.mean(times), 2),
                "all_edge_counts": edge_counts,
                "all_avg_stretches": avg_stretches,
            }
            results.append(result)
            
            print(f"  k={k}: edges={np.mean(edge_counts):.0f} +/- {np.std(edge_counts):.1f} "
                  f"(CV={result['edge_count_cv']:.4f}), "
                  f"avg_stretch={np.mean(avg_stretches):.4f} +/- {np.std(avg_stretches):.4f}")
    
    # Save (without the large lists)
    save_data = []
    for r in results:
        d = {k: v for k, v in r.items() if k not in ['all_edge_counts', 'all_avg_stretches']}
        save_data.append(d)
    save_results(save_data, "seed_variance")
    
    plot_seed_variance(results)
    
    return results


def plot_seed_variance(results):
    """Plot seed variance as box plots and histograms."""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    colors = ['#2196F3', '#FF5722', '#4CAF50', '#9C27B0']
    
    # Edges box plot
    ax = axes[0][0]
    data_labels = []
    data_values = []
    for r in results:
        label = f"{r['dataset'].split('(')[0].strip()}\nk={r['k']}"
        data_labels.append(label)
        data_values.append(r['all_edge_counts'])
    
    bp = ax.boxplot(data_values, labels=data_labels, patch_artist=True)
    for i, patch in enumerate(bp['boxes']):
        patch.set_facecolor(colors[i % len(colors)])
        patch.set_alpha(0.7)
    ax.set_ylabel('Spanner Edge Count', fontsize=12)
    ax.set_title('Edge Count Variance Across Seeds', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3, axis='y')
    
    # Stretch box plot
    ax = axes[0][1]
    stretch_values = [r['all_avg_stretches'] for r in results]
    bp = ax.boxplot(stretch_values, labels=data_labels, patch_artist=True)
    for i, patch in enumerate(bp['boxes']):
        patch.set_facecolor(colors[i % len(colors)])
        patch.set_alpha(0.7)
    ax.set_ylabel('Average Stretch', fontsize=12)
    ax.set_title('Stretch Variance Across Seeds', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3, axis='y')
    
    # Histograms
    for plot_idx, (data_key, ylabel, title) in enumerate([
        ('all_edge_counts', 'Frequency', 'Edge Count Distribution'),
        ('all_avg_stretches', 'Frequency', 'Avg Stretch Distribution')
    ]):
        ax = axes[1][plot_idx]
        for i, r in enumerate(results):
            label = f"{r['dataset'].split('(')[0].strip()} k={r['k']}"
            ax.hist(r[data_key], bins=15, alpha=0.5, color=colors[i], label=label)
        ax.set_xlabel(ylabel if data_key == 'all_edge_counts' else 'Average Stretch', fontsize=12)
        ax.set_ylabel('Frequency', fontsize=12)
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.legend(fontsize=9)
        ax.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    plt.savefig(FIGURES_DIR / 'seed_variance.png', dpi=150, bbox_inches='tight')
    plt.savefig(FIGURES_DIR / 'seed_variance.pdf', bbox_inches='tight')
    plt.close()
    print(f"\n  Plot saved to {FIGURES_DIR / 'seed_variance.png'}")


def save_results(results, name):
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
    run_seed_variance()
