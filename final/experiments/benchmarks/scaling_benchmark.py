"""
scaling_benchmark.py — Performance Profiling & Complexity Benchmarks
====================================================================
Empirically verify theoretical complexity of Baswana-Sen.
  - Run on graphs of n = 1K, 5K, 10K, 50K, 100K
  - Fit empirical curve vs theoretical O(km)
  - Compare: Union-Find with vs without path compression
  - Compare: adjacency list vs adjacency matrix (small n)

Output: CSV tables + matplotlib plots for Person B's analysis.

Part of t-Spanner project — Person A (Implementation & Engineering)
"""

import os
import sys
import time
import json
import csv
import random
import math

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from src.python.spanner.graph import Graph
from src.python.spanner.baswana_sen import baswana_sen_spanner, theoretical_max_edges
from src.python.spanner.greedy_spanner import greedy_bfs_spanner
from src.python.spanner.union_find import UnionFind, UnionFindNoCompression
from src.python.data.graph_loader import GraphLoader, RESULTS_DIR, FIGURES_DIR

import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import numpy as np


def run_scaling_benchmark(
    sizes=None,
    k_values=None,
    edge_probability=0.01,
    seed=42,
):
    """
    Run Baswana-Sen on increasing graph sizes to profile time complexity.
    """
    if sizes is None:
        sizes = [500, 1000, 2000, 5000, 10000]
    if k_values is None:
        k_values = [2, 3]
    
    loader = GraphLoader()
    results = []
    
    print("=" * 70)
    print("SCALING BENCHMARK: Baswana-Sen Time Complexity")
    print("=" * 70)
    
    for n in sizes:
        # Adjust edge probability to maintain reasonable density
        p = min(edge_probability, 10.0 / n)  # ~10*n edges
        if n <= 1000:
            p = max(p, 0.02)
        
        print(f"\n--- n = {n}, p = {p:.4f} ---")
        g = loader.generate_erdos_renyi(n, p, seed=seed)
        print(f"  Graph: {g.num_nodes} nodes, {g.num_edges} edges")
        
        for k in k_values:
            t = 2 * k - 1
            
            # Baswana-Sen
            bs_result = baswana_sen_spanner(g, k=k, seed=seed)
            
            # Greedy (only for smaller graphs — too slow for large)
            greedy_time = None
            if n <= 2000:
                gr_result = greedy_bfs_spanner(g, t=t)
                greedy_time = gr_result["construction_time_ms"]
            
            result = {
                "n": g.num_nodes,
                "m": g.num_edges,
                "k": k,
                "t": t,
                "bs_time_ms": bs_result["construction_time_ms"],
                "bs_edges": bs_result["num_spanner_edges"],
                "bs_sparseness": round(bs_result["sparseness_ratio"], 4),
                "theoretical_max_edges": round(theoretical_max_edges(g.num_nodes, k), 0),
                "greedy_time_ms": greedy_time,
            }
            results.append(result)
            
            print(f"  k={k}: BS={bs_result['construction_time_ms']:.1f}ms, "
                  f"edges={bs_result['num_spanner_edges']}, "
                  f"ratio={bs_result['sparseness_ratio']:.3f}", end="")
            if greedy_time:
                print(f", Greedy={greedy_time:.1f}ms", end="")
            print()
    
    # Save results
    save_results(results, "scaling_benchmark")
    
    # Plot
    plot_scaling(results)
    
    return results


def run_union_find_benchmark(sizes=None, seed=42):
    """
    Compare Union-Find with vs without path compression.
    """
    if sizes is None:
        sizes = [1000, 5000, 10000, 50000]
    
    results = []
    
    print("\n" + "=" * 70)
    print("UNION-FIND BENCHMARK: Path Compression Impact")
    print("=" * 70)
    
    for n in sizes:
        random.seed(seed)
        
        # Generate random union/find operations
        ops = [(random.randint(0, n-1), random.randint(0, n-1)) for _ in range(n * 5)]
        
        # With compression
        uf_comp = UnionFind(n)
        t1 = time.perf_counter()
        for a, b in ops:
            uf_comp.union(a, b)
        for a, b in ops[:n*2]:
            uf_comp.find(a)
        comp_time = (time.perf_counter() - t1) * 1000
        
        # Without compression
        uf_nocomp = UnionFindNoCompression(n)
        t2 = time.perf_counter()
        for a, b in ops:
            uf_nocomp.union(a, b)
        for a, b in ops[:n*2]:
            uf_nocomp.find(a)
        nocomp_time = (time.perf_counter() - t2) * 1000
        
        speedup = nocomp_time / max(comp_time, 0.001)
        
        result = {
            "n": n,
            "operations": len(ops) + n*2,
            "with_compression_ms": round(comp_time, 2),
            "without_compression_ms": round(nocomp_time, 2),
            "speedup": round(speedup, 2),
            "path_compressions": uf_comp.profiling_stats()["path_compressions"],
        }
        results.append(result)
        
        print(f"  n={n:>6d}: with={comp_time:8.2f}ms, "
              f"without={nocomp_time:8.2f}ms, speedup={speedup:.2f}x")
    
    save_results(results, "union_find_benchmark")
    plot_union_find(results)
    
    return results


def run_data_structure_benchmark(sizes=None, seed=42):
    """
    Compare adjacency list vs adjacency matrix for spanner construction.
    Only feasible for small graphs (matrix = O(n^2) memory).
    """
    if sizes is None:
        sizes = [100, 200, 500, 1000]
    
    results = []
    loader = GraphLoader()
    
    print("\n" + "=" * 70)
    print("DATA STRUCTURE BENCHMARK: Adjacency List vs Matrix")
    print("=" * 70)
    
    for n in sizes:
        p = max(0.02, 5.0 / n)
        g = loader.generate_erdos_renyi(n, p, seed=seed)
        
        # Adjacency list (standard)
        t1 = time.perf_counter()
        bs_list = baswana_sen_spanner(g, k=2, seed=seed)
        list_time = (time.perf_counter() - t1) * 1000
        list_memory = g.memory_bytes()
        
        # Adjacency matrix (convert graph)
        t2 = time.perf_counter()
        # Build matrix representation
        nodes = sorted(g.nodes)
        node_to_idx = {v: i for i, v in enumerate(nodes)}
        matrix = [[float('inf')] * len(nodes) for _ in range(len(nodes))]
        for u, v, w in g.edges():
            i, j = node_to_idx[u], node_to_idx[v]
            matrix[i][j] = w
            matrix[j][i] = w
        matrix_build_time = (time.perf_counter() - t2) * 1000
        matrix_memory = sys.getsizeof(matrix) + sum(sys.getsizeof(row) for row in matrix)
        
        result = {
            "n": g.num_nodes,
            "m": g.num_edges,
            "list_time_ms": round(list_time, 2),
            "list_memory_bytes": list_memory,
            "matrix_build_time_ms": round(matrix_build_time, 2),
            "matrix_memory_bytes": matrix_memory,
            "memory_ratio": round(matrix_memory / max(list_memory, 1), 2),
        }
        results.append(result)
        
        print(f"  n={n:>5d}: list={list_time:8.2f}ms/{list_memory:>10d}B, "
              f"matrix_build={matrix_build_time:8.2f}ms/{matrix_memory:>10d}B, "
              f"memory_ratio={result['memory_ratio']:.1f}x")
    
    save_results(results, "data_structure_benchmark")
    
    return results


# ─── Plotting ──────────────────────────────────────────────────

def plot_scaling(results):
    """Plot scaling benchmark: time vs n (log-log)."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    
    # Group by k
    k_values = sorted(set(r["k"] for r in results))
    colors = ['#2196F3', '#FF5722', '#4CAF50', '#9C27B0']
    
    # Plot 1: Construction time vs nodes
    ax = axes[0]
    for i, k in enumerate(k_values):
        data = [r for r in results if r["k"] == k]
        ns = [r["n"] for r in data]
        times = [r["bs_time_ms"] for r in data]
        ax.plot(ns, times, 'o-', color=colors[i], linewidth=2, markersize=8,
                label=f'Baswana-Sen k={k}')
        
        # Greedy comparison
        greedy_data = [(r["n"], r["greedy_time_ms"]) for r in data if r["greedy_time_ms"]]
        if greedy_data:
            gns, gtimes = zip(*greedy_data)
            ax.plot(gns, gtimes, 's--', color=colors[i], alpha=0.5, markersize=6,
                    label=f'Greedy t={2*k-1}')
    
    ax.set_xlabel('Number of Nodes (n)', fontsize=12)
    ax.set_ylabel('Construction Time (ms)', fontsize=12)
    ax.set_title('Spanner Construction Time vs Graph Size', fontsize=14, fontweight='bold')
    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)
    
    # Plot 2: Spanner edges vs n (with theoretical bound)
    ax = axes[1]
    for i, k in enumerate(k_values):
        data = [r for r in results if r["k"] == k]
        ns = [r["n"] for r in data]
        edges = [r["bs_edges"] for r in data]
        ax.plot(ns, edges, 'o-', color=colors[i], linewidth=2, markersize=8,
                label=f'Baswana-Sen k={k}')
        
        # Theoretical bound
        ns_theory = np.linspace(min(ns), max(ns), 100)
        theory = [theoretical_max_edges(n, k) for n in ns_theory]
        ax.plot(ns_theory, theory, '--', color=colors[i], alpha=0.4,
                label=f'Theoretical O(k*n^{{1+1/k}}) k={k}')
    
    ax.set_xlabel('Number of Nodes (n)', fontsize=12)
    ax.set_ylabel('Spanner Edges', fontsize=12)
    ax.set_title('Spanner Size vs Graph Size', fontsize=14, fontweight='bold')
    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    plt.savefig(FIGURES_DIR / 'scaling_benchmark.png', dpi=150, bbox_inches='tight')
    plt.savefig(FIGURES_DIR / 'scaling_benchmark.pdf', bbox_inches='tight')
    plt.close()
    print(f"\n  Plot saved to {FIGURES_DIR / 'scaling_benchmark.png'}")


def plot_union_find(results):
    """Plot Union-Find benchmark."""
    fig, ax = plt.subplots(figsize=(8, 5))
    
    ns = [r["n"] for r in results]
    comp = [r["with_compression_ms"] for r in results]
    nocomp = [r["without_compression_ms"] for r in results]
    
    x = np.arange(len(ns))
    width = 0.35
    
    bars1 = ax.bar(x - width/2, comp, width, label='With Path Compression', color='#2196F3')
    bars2 = ax.bar(x + width/2, nocomp, width, label='Without Path Compression', color='#FF5722')
    
    ax.set_xlabel('Number of Elements (n)', fontsize=12)
    ax.set_ylabel('Time (ms)', fontsize=12)
    ax.set_title('Union-Find: Path Compression Impact', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels([str(n) for n in ns])
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3, axis='y')
    
    # Add speedup labels
    for i, r in enumerate(results):
        ax.annotate(f'{r["speedup"]:.1f}x', xy=(x[i], max(comp[i], nocomp[i])),
                   ha='center', va='bottom', fontsize=10, fontweight='bold', color='#333')
    
    plt.tight_layout()
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    plt.savefig(FIGURES_DIR / 'union_find_benchmark.png', dpi=150, bbox_inches='tight')
    plt.savefig(FIGURES_DIR / 'union_find_benchmark.pdf', bbox_inches='tight')
    plt.close()
    print(f"  Plot saved to {FIGURES_DIR / 'union_find_benchmark.png'}")


# ─── Utility ──────────────────────────────────────────────────

def save_results(results, name):
    """Save results as CSV and JSON."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    
    # JSON
    with open(RESULTS_DIR / f"{name}.json", 'w') as f:
        json.dump(results, f, indent=2)
    
    # CSV
    if results:
        with open(RESULTS_DIR / f"{name}.csv", 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)
    
    print(f"  Results saved to {RESULTS_DIR / name}.[json|csv]")


# ─── Main ──────────────────────────────────────────────────────

if __name__ == "__main__":
    print("t-Spanner Performance Profiling")
    print("=" * 70)
    
    # Run all benchmarks
    scaling_results = run_scaling_benchmark()
    uf_results = run_union_find_benchmark()
    ds_results = run_data_structure_benchmark()
    
    print("\n" + "=" * 70)
    print("ALL BENCHMARKS COMPLETE")
    print("=" * 70)
