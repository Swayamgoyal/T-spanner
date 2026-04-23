"""
routing_simulation.py — Real-World Routing Simulation (Hyderabad)
================================================================
Apply the spanner to a city road network; simulate Dijkstra on spanner vs full graph.
  - Extract ~5,000-node subgraph using osmnx or synthetic fallback
  - Run Dijkstra for 500 random source-dest pairs on full graph and spanners
  - Metrics: query time (ms), path length ratio (stretch), memory usage
  - Key output: "Google Maps on 3-spanner uses X% less memory with Y% longer routes"

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
from src.python.spanner.metrics import sample_random_pairs
from src.python.data.graph_loader import GraphLoader, RESULTS_DIR, FIGURES_DIR

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np


def run_routing_simulation(num_queries=500, seed=42):
    """Run routing simulation on road network."""
    
    loader = GraphLoader()
    
    print("=" * 80)
    print("REAL-WORLD ROUTING SIMULATION — Hyderabad Road Network")
    print("=" * 80)
    
    # Load road network
    print("\nLoading road network...")
    road_graph = loader.load_osm_city("Hyderabad, India", radius=3000, max_nodes=3000)
    print(f"  Road network: {road_graph.info()}")
    
    # Build spanners
    t_values = [3, 5, 7]
    spanners = {}
    
    for t in t_values:
        k = (t + 1) // 2
        result = baswana_sen_spanner(road_graph, k=k, seed=seed)
        spanners[t] = result
        print(f"  t={t} spanner: {result['num_spanner_edges']} edges "
              f"(ratio={result['sparseness_ratio']:.4f})")
    
    # Sample query pairs
    print(f"\nSampling {num_queries} random source-destination pairs...")
    pairs = sample_random_pairs(road_graph, num_queries, seed=seed)
    print(f"  Got {len(pairs)} valid pairs")
    
    # Run Dijkstra on full graph
    print("\nRunning Dijkstra queries...")
    results_per_t = {}
    
    # Full graph queries
    full_times = []
    full_dists = {}
    
    for i, (src, dst) in enumerate(pairs):
        t_start = time.perf_counter()
        d = road_graph.dijkstra_distance(src, dst)
        elapsed = (time.perf_counter() - t_start) * 1000
        full_times.append(elapsed)
        full_dists[(src, dst)] = d
    
    avg_full_time = np.mean(full_times)
    full_memory = road_graph.memory_bytes()
    
    print(f"\n  Full graph: avg query time = {avg_full_time:.3f} ms, "
          f"memory = {full_memory / 1024:.1f} KB")
    
    all_results = []
    
    for t in t_values:
        spanner = spanners[t]["spanner"]
        spanner_times = []
        stretches = []
        unreachable = 0
        
        for src, dst in pairs:
            t_start = time.perf_counter()
            d_spanner = spanner.dijkstra_distance(src, dst)
            elapsed = (time.perf_counter() - t_start) * 1000
            spanner_times.append(elapsed)
            
            d_full = full_dists[(src, dst)]
            
            if d_full == float('inf') or d_full == 0:
                continue
            if d_spanner == float('inf'):
                unreachable += 1
                continue
            
            stretches.append(d_spanner / d_full)
        
        avg_spanner_time = np.mean(spanner_times)
        spanner_memory = spanner.memory_bytes()
        memory_saved = (1 - spanner_memory / full_memory) * 100
        avg_stretch = np.mean(stretches) if stretches else float('inf')
        route_increase = (avg_stretch - 1) * 100
        speedup = avg_full_time / max(avg_spanner_time, 0.001)
        
        result = {
            "t": t,
            "full_edges": road_graph.num_edges,
            "spanner_edges": spanners[t]["num_spanner_edges"],
            "sparseness_ratio": round(spanners[t]["sparseness_ratio"], 4),
            "full_memory_kb": round(full_memory / 1024, 1),
            "spanner_memory_kb": round(spanner_memory / 1024, 1),
            "memory_saved_pct": round(memory_saved, 1),
            "avg_full_query_ms": round(avg_full_time, 3),
            "avg_spanner_query_ms": round(avg_spanner_time, 3),
            "query_speedup": round(speedup, 2),
            "avg_stretch": round(avg_stretch, 4),
            "max_stretch": round(max(stretches) if stretches else 0, 4),
            "route_increase_pct": round(route_increase, 2),
            "unreachable_queries": unreachable,
            "num_queries": len(pairs),
        }
        all_results.append(result)
        
        print(f"\n  t={t} Spanner:")
        print(f"    Memory: {spanner_memory/1024:.1f} KB ({memory_saved:.1f}% saved)")
        print(f"    Query time: {avg_spanner_time:.3f} ms ({speedup:.2f}x speedup)")
        print(f"    Avg stretch: {avg_stretch:.4f} ({route_increase:.2f}% longer routes)")
        print(f"    Unreachable: {unreachable}/{len(pairs)}")
        
        # The headline result
        print(f"    >> Google Maps on {t}-spanner: {memory_saved:.1f}% less memory, "
              f"{route_increase:.1f}% longer routes")
    
    save_results(all_results, "routing_simulation")
    plot_routing_results(all_results)
    
    return all_results


def plot_routing_results(results):
    """Plot routing simulation results."""
    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    
    ts = [r["t"] for r in results]
    colors = ['#2196F3', '#FF9800', '#4CAF50']
    
    # Plot 1: Memory savings
    ax = axes[0]
    memory_saved = [r["memory_saved_pct"] for r in results]
    bars = ax.bar(range(len(ts)), memory_saved, color=colors, edgecolor='white', linewidth=1.5)
    ax.set_xticks(range(len(ts)))
    ax.set_xticklabels([f't={t}' for t in ts], fontsize=12)
    ax.set_ylabel('Memory Saved (%)', fontsize=12)
    ax.set_title('Memory Savings', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3, axis='y')
    for bar, val in zip(bars, memory_saved):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                f'{val:.1f}%', ha='center', fontsize=11, fontweight='bold')
    
    # Plot 2: Route increase
    ax = axes[1]
    route_inc = [r["route_increase_pct"] for r in results]
    bars = ax.bar(range(len(ts)), route_inc, color=colors, edgecolor='white', linewidth=1.5)
    ax.set_xticks(range(len(ts)))
    ax.set_xticklabels([f't={t}' for t in ts], fontsize=12)
    ax.set_ylabel('Route Length Increase (%)', fontsize=12)
    ax.set_title('Route Detour Cost', fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3, axis='y')
    for bar, val in zip(bars, route_inc):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                f'{val:.1f}%', ha='center', fontsize=11, fontweight='bold')
    
    # Plot 3: Memory vs Stretch (Pareto)
    ax = axes[2]
    memory_kb = [r["spanner_memory_kb"] for r in results]
    stretches = [r["avg_stretch"] for r in results]
    
    # Add full graph point
    full_mem = results[0]["full_memory_kb"]
    ax.scatter([full_mem], [1.0], s=200, c='red', marker='*', zorder=5, label='Full Graph')
    
    for i, (m, s, t) in enumerate(zip(memory_kb, stretches, ts)):
        ax.scatter([m], [s], s=150, c=colors[i], zorder=5, label=f't={t} spanner')
        ax.annotate(f't={t}', (m, s), textcoords="offset points", xytext=(10, 5), fontsize=10)
    
    ax.set_xlabel('Memory (KB)', fontsize=12)
    ax.set_ylabel('Average Stretch', fontsize=12)
    ax.set_title('Memory vs Stretch Tradeoff', fontsize=14, fontweight='bold')
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    plt.savefig(FIGURES_DIR / 'routing_simulation.png', dpi=150, bbox_inches='tight')
    plt.savefig(FIGURES_DIR / 'routing_simulation.pdf', bbox_inches='tight')
    plt.close()
    print(f"\n  Plot saved to {FIGURES_DIR / 'routing_simulation.png'}")


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
    run_routing_simulation()
