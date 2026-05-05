"""
fault_tolerance.py — Fault-Tolerant Spanner Experiments
========================================================
Study how the spanner behaves under node failures.
  - Build t-spanner on each graph
  - Delete high-degree nodes: top 1%, 5%, 10%
  - Re-run stretch computation after each deletion
  - Implement repair heuristic
  - Compare: pre/post repair stretch, connectivity

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
from src.python.spanner.metrics import compute_stretch, compute_sparseness_ratio, sample_random_pairs
from src.python.data.graph_loader import GraphLoader, RESULTS_DIR, FIGURES_DIR

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np


def repair_spanner(original: Graph, damaged_spanner: Graph, t: int, num_checks: int = 200, seed: int = 42):
    """
    Repair heuristic: for each pair with stretch > t in damaged spanner,
    try to add edges from the original graph's remaining edges to restore stretch.
    
    Strategy:
    1. Find pairs where stretch is violated (d_H(u,v) > t * d_G(u,v))
    2. For each violated pair, find shortest path in *original subgraph* (minus deleted nodes)
    3. Add edges along this path to the spanner
    """
    repaired = Graph()
    # Copy all existing spanner edges
    for u, v, w in damaged_spanner.edges():
        repaired.add_edge(u, v, w)
    for v in damaged_spanner.nodes:
        repaired.add_node(v)
    
    edges_added = 0
    
    # Sample pairs and check stretch
    pairs = sample_random_pairs(damaged_spanner, num_checks, seed=seed)
    
    original_sub = original.subgraph(damaged_spanner.nodes)
    
    for u, v in pairs:
        d_orig = original_sub.bfs_distance(u, v)
        d_span = repaired.bfs_distance(u, v)
        
        if d_orig == 0 or d_orig == float('inf'):
            continue
        
        if d_span == float('inf') or d_span > t * d_orig:
            # Need to repair this pair
            # Find shortest path in original subgraph
            # Add edges along this path
            parent = {u: None}
            from collections import deque
            queue = deque([u])
            while queue:
                curr = queue.popleft()
                if curr == v:
                    break
                for nbr, w in original_sub.neighbors(curr):
                    if nbr not in parent:
                        parent[nbr] = (curr, w)
                        queue.append(nbr)
            
            # Reconstruct path and add edges
            if v in parent:
                curr = v
                while parent[curr] is not None:
                    prev, w = parent[curr]
                    if not repaired.has_edge(prev, curr):
                        repaired.add_edge(prev, curr, w)
                        edges_added += 1
                    curr = prev
    
    return repaired, edges_added


def run_fault_tolerance_experiment(seed=42, num_pairs=300):
    """Run fault tolerance analysis."""
    
    loader = GraphLoader()
    
    graphs = {
        "Erdos-Renyi (500)": loader.generate_erdos_renyi(500, 0.02, seed=seed),
        "Grid (20x20)": loader.generate_grid(20, 20),
        "Barabasi-Albert (500)": loader.generate_barabasi_albert(500, 3, seed=seed),
    }
    
    failure_rates = [0.01, 0.05, 0.10, 0.15, 0.20]
    t_values = [3, 5]
    
    results = []
    
    print("=" * 80)
    print("FAULT-TOLERANT SPANNER EXPERIMENTS")
    print("=" * 80)
    
    for graph_name, g in graphs.items():
        print(f"\n{'='*60}")
        print(f"Dataset: {graph_name} (n={g.num_nodes}, m={g.num_edges})")
        print(f"{'='*60}")
        
        for t in t_values:
            k = (t + 1) // 2
            
            # Build spanner
            bs_result = baswana_sen_spanner(g, k=k, seed=seed)
            spanner = bs_result["spanner"]
            
            # Baseline stretch (no failures)
            baseline_stretch = compute_stretch(g, spanner, num_pairs=num_pairs, seed=seed)
            
            print(f"\n  t={t}: Baseline avg_stretch={baseline_stretch['avg_stretch']:.4f}, "
                  f"spanner_edges={bs_result['num_spanner_edges']}")
            
            for fail_rate in failure_rates:
                # Get nodes to delete (highest degree)
                nodes_to_delete = g.top_degree_nodes(fail_rate)
                num_deleted = len(nodes_to_delete)
                
                # Damage the spanner
                damaged_spanner = spanner.remove_nodes(nodes_to_delete)
                damaged_original = g.remove_nodes(nodes_to_delete)
                
                if damaged_original.num_nodes < 10:
                    continue
                
                # Compute stretch on damaged spanner
                damaged_stretch = compute_stretch(
                    damaged_original, damaged_spanner, 
                    num_pairs=min(num_pairs, damaged_original.num_nodes * 2),
                    seed=seed
                )
                
                # Check connectivity
                lcc = damaged_spanner.largest_connected_component()
                connectivity_ratio = lcc.num_nodes / max(damaged_spanner.num_nodes, 1)
                
                # Repair
                repaired_spanner, repair_edges = repair_spanner(
                    g, damaged_spanner, t, num_checks=min(200, damaged_original.num_nodes),
                    seed=seed
                )
                repaired_stretch = compute_stretch(
                    damaged_original, repaired_spanner,
                    num_pairs=min(num_pairs, damaged_original.num_nodes * 2),
                    seed=seed
                )
                
                result = {
                    "dataset": graph_name,
                    "t": t,
                    "failure_rate": fail_rate,
                    "nodes_deleted": num_deleted,
                    "remaining_nodes": damaged_spanner.num_nodes,
                    "baseline_avg_stretch": baseline_stretch["avg_stretch"],
                    "damaged_avg_stretch": damaged_stretch["avg_stretch"],
                    "damaged_max_stretch": damaged_stretch["max_stretch"],
                    "connectivity_ratio": round(connectivity_ratio, 4),
                    "unreachable_pairs": damaged_stretch["unreachable_in_spanner"],
                    "repair_edges_added": repair_edges,
                    "repaired_avg_stretch": repaired_stretch["avg_stretch"],
                    "repaired_max_stretch": repaired_stretch["max_stretch"],
                }
                results.append(result)
                
                print(f"    fail={fail_rate:.0%}: deleted={num_deleted}, "
                      f"dmg_stretch={damaged_stretch['avg_stretch']:.3f}, "
                      f"connectivity={connectivity_ratio:.3f}, "
                      f"repair_edges=+{repair_edges}, "
                      f"repaired_stretch={repaired_stretch['avg_stretch']:.3f}")
    
    save_results(results, "fault_tolerance")
    plot_fault_tolerance(results)
    
    return results


def plot_fault_tolerance(results):
    """Plot fault tolerance: stretch degradation vs failure rate."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    
    datasets = list(dict.fromkeys(r["dataset"] for r in results))
    colors = ['#2196F3', '#4CAF50', '#FF5722', '#9C27B0']
    
    # Plot 1: Stretch degradation
    ax = axes[0]
    for i, dataset in enumerate(datasets):
        for t in [3, 5]:
            data = [r for r in results if r["dataset"] == dataset and r["t"] == t]
            if not data:
                continue
            rates = [r["failure_rate"] * 100 for r in data]
            damaged = [r["damaged_avg_stretch"] for r in data]
            repaired = [r["repaired_avg_stretch"] for r in data]
            
            style = '-' if t == 3 else '--'
            ax.plot(rates, damaged, f'o{style}', color=colors[i], linewidth=2,
                   label=f'{dataset} t={t} (damaged)', markersize=6)
            ax.plot(rates, repaired, f's{style}', color=colors[i], linewidth=1, alpha=0.6,
                   label=f'{dataset} t={t} (repaired)', markersize=5)
    
    ax.set_xlabel('Failure Rate (%)', fontsize=12)
    ax.set_ylabel('Average Stretch', fontsize=12)
    ax.set_title('Stretch Degradation Under Node Failures', fontsize=14, fontweight='bold')
    ax.legend(fontsize=7, loc='upper left')
    ax.grid(True, alpha=0.3)
    
    # Plot 2: Connectivity
    ax = axes[1]
    for i, dataset in enumerate(datasets):
        data = [r for r in results if r["dataset"] == dataset and r["t"] == 3]
        if not data:
            continue
        rates = [r["failure_rate"] * 100 for r in data]
        conn = [r["connectivity_ratio"] * 100 for r in data]
        ax.plot(rates, conn, 'o-', color=colors[i], linewidth=2, markersize=6,
               label=dataset)
    
    ax.set_xlabel('Failure Rate (%)', fontsize=12)
    ax.set_ylabel('Connectivity (%)', fontsize=12)
    ax.set_title('Spanner Connectivity Under Node Failures', fontsize=14, fontweight='bold')
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)
    ax.set_ylim(0, 105)
    
    plt.tight_layout()
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    plt.savefig(FIGURES_DIR / 'fault_tolerance.png', dpi=150, bbox_inches='tight')
    plt.savefig(FIGURES_DIR / 'fault_tolerance.pdf', bbox_inches='tight')
    plt.close()
    print(f"\n  Plot saved to {FIGURES_DIR / 'fault_tolerance.png'}")


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
    run_fault_tolerance_experiment()
