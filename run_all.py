"""
run_all.py — Unified Experiment Runner
=======================================
CLI interface to run all t-Spanner experiments.

Usage:
    python run_all.py --experiment scaling      # Performance benchmarks
    python run_all.py --experiment stretch       # Stretch factor analysis
    python run_all.py --experiment fault         # Fault tolerance
    python run_all.py --experiment routing       # Hyderabad routing simulation
    python run_all.py --experiment seeds         # Seed variance analysis
    python run_all.py --experiment all           # Run everything
    python run_all.py --quick                    # Quick test run (small graphs)

Part of t-Spanner project — Person A (Implementation & Engineering)
"""

import argparse
import os
import sys
import json
import time

sys.path.insert(0, os.path.dirname(__file__))


def run_scaling(quick=False):
    from src.python.experiments.scaling_benchmark import (
        run_scaling_benchmark, run_union_find_benchmark, run_data_structure_benchmark
    )
    sizes = [200, 500, 1000] if quick else [500, 1000, 2000, 5000, 10000]
    uf_sizes = [500, 1000] if quick else [1000, 5000, 10000, 50000]
    ds_sizes = [50, 100] if quick else [100, 200, 500, 1000]
    
    run_scaling_benchmark(sizes=sizes)
    run_union_find_benchmark(sizes=uf_sizes)
    run_data_structure_benchmark(sizes=ds_sizes)


def run_stretch(quick=False):
    from src.python.experiments.stretch_experiment import run_stretch_experiment
    num_pairs = 100 if quick else 500
    run_stretch_experiment(num_pairs=num_pairs)


def run_fault(quick=False):
    from src.python.experiments.fault_tolerance import run_fault_tolerance_experiment
    num_pairs = 100 if quick else 300
    run_fault_tolerance_experiment(num_pairs=num_pairs)


def run_routing(quick=False):
    from src.python.experiments.routing_simulation import run_routing_simulation
    num_queries = 50 if quick else 500
    run_routing_simulation(num_queries=num_queries)


def run_seeds(quick=False):
    from src.python.experiments.seed_variance import run_seed_variance
    num_seeds = 10 if quick else 50
    run_seed_variance(num_seeds=num_seeds)


EXPERIMENTS = {
    "scaling": run_scaling,
    "stretch": run_stretch,
    "fault": run_fault,
    "routing": run_routing,
    "seeds": run_seeds,
}


def main():
    parser = argparse.ArgumentParser(
        description="t-Spanner Unified Experiment Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Experiments available:
  scaling   — Performance benchmarks (BS vs Greedy, Union-Find, data structures)
  stretch   — Stretch factor & sparseness analysis across datasets
  fault     — Fault-tolerant spanner experiments with repair heuristic
  routing   — Real-world Hyderabad routing simulation
  seeds     — Random seed sensitivity analysis (50 seeds)
  all       — Run all experiments

Examples:
  python run_all.py --experiment stretch
  python run_all.py --experiment all --quick
  python run_all.py --experiment scaling stretch
        """
    )
    parser.add_argument(
        "--experiment", "-e", nargs="+",
        choices=list(EXPERIMENTS.keys()) + ["all"],
        default=["all"],
        help="Which experiments to run"
    )
    parser.add_argument(
        "--quick", "-q", action="store_true",
        help="Quick mode: smaller graphs and fewer samples"
    )
    
    args = parser.parse_args()
    
    experiments_to_run = list(EXPERIMENTS.keys()) if "all" in args.experiment else args.experiment
    
    start = time.time()
    
    print("=" * 70)
    print("t-SPANNER EXPERIMENT SUITE")
    print(f"Mode: {'QUICK' if args.quick else 'FULL'}")
    print(f"Experiments: {', '.join(experiments_to_run)}")
    print("=" * 70)
    
    for exp_name in experiments_to_run:
        print(f"\n{'#' * 70}")
        print(f"# Running: {exp_name}")
        print(f"{'#' * 70}")
        
        try:
            EXPERIMENTS[exp_name](quick=args.quick)
            print(f"\n>>> {exp_name} COMPLETED")
        except Exception as e:
            print(f"\n>>> {exp_name} FAILED: {e}")
            import traceback
            traceback.print_exc()
    
    total_time = time.time() - start
    print(f"\n{'=' * 70}")
    print(f"ALL EXPERIMENTS COMPLETE in {total_time:.1f}s")
    print(f"Results saved to: data/results/")
    print(f"Figures saved to: data/figures/")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
