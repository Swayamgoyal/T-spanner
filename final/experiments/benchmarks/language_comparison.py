"""
language_comparison.py — Python vs C++ Cross-Language Benchmark
==============================================================
Runs both Python and C++ implementations of Baswana-Sen on the same graphs.
Compares wall-clock time, spanner edge count, and sparseness.

Prerequisites:
  - C++ binary compiled: cd src/cpp && make all
  - Python spanner modules available

Part of t-Spanner project — Person A (Implementation & Engineering)
"""

import os
import sys
import json
import csv
import time
import subprocess
import tempfile
import random

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from src.python.spanner.graph import Graph
from src.python.spanner.baswana_sen import baswana_sen_spanner
from src.python.spanner.greedy_spanner import greedy_bfs_spanner
from src.python.data.graph_loader import GraphLoader, RESULTS_DIR, FIGURES_DIR, PROJECT_ROOT

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np


CPP_BINARY = PROJECT_ROOT / "src" / "cpp" / "spanner_cpp"
if sys.platform == "win32":
    CPP_BINARY = PROJECT_ROOT / "src" / "cpp" / "spanner_cpp.exe"


def write_graph_to_file(graph: Graph, filepath: str):
    """Write graph in C++ input format: first line 'n m', then edges 'u v w'."""
    edges = graph.edges()
    with open(filepath, 'w') as f:
        f.write(f"{graph.num_nodes} {graph.num_edges}\n")
        for u, v, w in edges:
            f.write(f"{u} {v} {w}\n")


def run_cpp_spanner(graph: Graph, algo: str = "baswana", k: int = 2, t: int = 3, seed: int = 42):
    """Run the C++ spanner binary and capture output."""
    if not CPP_BINARY.exists():
        return None  # C++ not compiled

    # Write graph to temp file
    input_file = str(PROJECT_ROOT / "data" / "temp_graph_input.txt")
    output_file = str(PROJECT_ROOT / "data" / "temp_graph_output.txt")

    write_graph_to_file(graph, input_file)

    cmd = [
        str(CPP_BINARY),
        "--algo", algo,
        "--k", str(k),
        "--t", str(t),
        "--seed", str(seed),
        "--input", input_file,
        "--output", output_file,
    ]

    try:
        start = time.perf_counter()
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        total_time = (time.perf_counter() - start) * 1000

        stderr = result.stderr

        # Parse construction time from stderr
        construction_time = None
        spanner_edges = None
        for line in stderr.split('\n'):
            if 'Time:' in line:
                try:
                    construction_time = float(line.split('Time:')[1].strip().replace('ms', '').strip())
                except:
                    pass

        # Parse output file for edge count
        if os.path.exists(output_file):
            with open(output_file, 'r') as f:
                for line in f:
                    if line.startswith('#'):
                        if 'Spanner edges:' in line:
                            try:
                                spanner_edges = int(line.split(':')[1].strip())
                            except:
                                pass
                        elif 'Sparseness ratio:' in line:
                            try:
                                sparseness = float(line.split(':')[1].strip())
                            except:
                                sparseness = None

        # Cleanup
        for f in [input_file, output_file]:
            if os.path.exists(f):
                os.remove(f)

        return {
            "time_ms": construction_time or total_time,
            "spanner_edges": spanner_edges,
            "return_code": result.returncode,
        }

    except subprocess.TimeoutExpired:
        return {"time_ms": 120000, "spanner_edges": None, "return_code": -1}
    except Exception as e:
        return {"time_ms": None, "spanner_edges": None, "error": str(e)}


def run_language_comparison(sizes=None, seed=42):
    """Run Python vs C++ comparison."""

    if sizes is None:
        sizes = [500, 1000, 2000, 5000]

    loader = GraphLoader()
    results = []

    cpp_available = CPP_BINARY.exists()

    print("=" * 70)
    print("LANGUAGE COMPARISON: Python vs C++")
    print("=" * 70)

    if not cpp_available:
        print(f"\n  WARNING: C++ binary not found at {CPP_BINARY}")
        print("  To compile: cd src/cpp && make all")
        print("  Running Python-only benchmarks...\n")

    for n in sizes:
        p = max(0.005, 5.0 / n)
        g = loader.generate_erdos_renyi(n, p, seed=seed)

        print(f"\n--- n={g.num_nodes}, m={g.num_edges} ---")

        for k in [2, 3]:
            t = 2 * k - 1

            # Python Baswana-Sen
            py_start = time.perf_counter()
            py_result = baswana_sen_spanner(g, k=k, seed=seed)
            py_time = (time.perf_counter() - py_start) * 1000

            # C++ Baswana-Sen
            cpp_result_data = None
            cpp_time = None
            cpp_edges = None
            speedup = None

            if cpp_available:
                cpp_result_data = run_cpp_spanner(g, algo="baswana", k=k, seed=seed)
                if cpp_result_data and cpp_result_data.get("time_ms"):
                    cpp_time = cpp_result_data["time_ms"]
                    cpp_edges = cpp_result_data.get("spanner_edges")
                    speedup = py_time / max(cpp_time, 0.001)

            result = {
                "n": g.num_nodes,
                "m": g.num_edges,
                "k": k,
                "t": t,
                "python_time_ms": round(py_time, 2),
                "python_edges": py_result["num_spanner_edges"],
                "cpp_time_ms": round(cpp_time, 2) if cpp_time else None,
                "cpp_edges": cpp_edges,
                "speedup": round(speedup, 2) if speedup else None,
            }
            results.append(result)

            msg = f"  k={k}: Python={py_time:.1f}ms ({py_result['num_spanner_edges']} edges)"
            if cpp_time:
                msg += f", C++={cpp_time:.1f}ms ({cpp_edges} edges), speedup={speedup:.1f}x"
            else:
                msg += f", C++=[not compiled]"
            print(msg)

    # Save results
    save_results(results, "language_comparison")
    plot_language_comparison(results)

    return results


def plot_language_comparison(results):
    """Plot Python vs C++ benchmark."""
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))

    k_values = sorted(set(r["k"] for r in results))
    colors_py = ['#2196F3', '#4CAF50']
    colors_cpp = ['#FF5722', '#FF9800']

    # Plot 1: Time comparison
    ax = axes[0]
    for i, k in enumerate(k_values):
        data = [r for r in results if r["k"] == k]
        ns = [r["n"] for r in data]
        py_times = [r["python_time_ms"] for r in data]
        ax.plot(ns, py_times, 'o-', color=colors_py[i], linewidth=2, markersize=8,
                label=f'Python k={k}')
        cpp_times = [r["cpp_time_ms"] for r in data if r["cpp_time_ms"]]
        if cpp_times:
            cpp_ns = [r["n"] for r in data if r["cpp_time_ms"]]
            ax.plot(cpp_ns, cpp_times, 's--', color=colors_cpp[i], linewidth=2, markersize=8,
                    label=f'C++ k={k}')

    ax.set_xlabel('Number of Nodes (n)', fontsize=12)
    ax.set_ylabel('Construction Time (ms)', fontsize=12)
    ax.set_title('Python vs C++ Construction Time', fontsize=14, fontweight='bold')
    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)

    # Plot 2: Speedup
    ax = axes[1]
    for i, k in enumerate(k_values):
        data = [r for r in results if r["k"] == k and r["speedup"]]
        if data:
            ns = [r["n"] for r in data]
            speedups = [r["speedup"] for r in data]
            ax.bar([x + i * 0.35 for x in range(len(ns))], speedups, 0.35,
                   label=f'k={k}', color=colors_cpp[i], alpha=0.85)
            ax.set_xticks(range(len(ns)))
            ax.set_xticklabels([str(n) for n in ns])
        else:
            ax.text(0.5, 0.5, 'C++ not compiled\nRun: cd src/cpp && make all',
                    transform=ax.transAxes, ha='center', va='center',
                    fontsize=12, color='#666')

    ax.set_xlabel('Number of Nodes (n)', fontsize=12)
    ax.set_ylabel('Speedup (C++ vs Python)', fontsize=12)
    ax.set_title('C++ Speedup Over Python', fontsize=14, fontweight='bold')
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3, axis='y')
    ax.axhline(y=1.0, color='gray', linestyle=':', alpha=0.5)

    plt.tight_layout()
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    plt.savefig(FIGURES_DIR / 'language_comparison.png', dpi=150, bbox_inches='tight')
    plt.savefig(FIGURES_DIR / 'language_comparison.pdf', bbox_inches='tight')
    plt.close()
    print(f"\n  Plot saved to {FIGURES_DIR / 'language_comparison.png'}")


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
    run_language_comparison()
