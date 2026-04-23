"""
topology_report_cards.py — Per-Topology Summary Generator
==========================================================
Reads all experimental CSVs and generates topology-specific
summary cards for the report.

Part of t-Spanner project — Person B (Research, Analysis & Writing)
"""

import os
import csv
from collections import defaultdict

RESULTS_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'results')


def load_csv(filename):
    filepath = os.path.join(RESULTS_DIR, filename)
    if not os.path.exists(filepath):
        return []
    with open(filepath, 'r') as f:
        return list(csv.DictReader(f))


def classify_topology(name):
    n = name.lower()
    if 'erdos' in n or 'random' in n:
        return 'Erdos-Renyi (Random)'
    elif 'grid' in n:
        return 'Grid (Road-like)'
    elif 'barabasi' in n:
        return 'Barabasi-Albert (Scale-Free)'
    elif 'small' in n:
        return 'Small-World (Watts-Strogatz)'
    return 'Other'


def generate_report_cards():
    """Generate comprehensive per-topology summaries."""
    stretch_data = load_csv('stretch_experiment.csv')
    fault_data = load_csv('fault_tolerance.csv')
    advanced_data = load_csv('advanced_experiment.csv')
    seed_data = load_csv('seed_variance.csv')

    # Group stretch data by topology
    topo_stretch = defaultdict(list)
    for r in stretch_data:
        topo = classify_topology(r['dataset'])
        topo_stretch[topo].append(r)

    # Group fault data by topology
    topo_fault = defaultdict(list)
    for r in fault_data:
        topo = classify_topology(r['dataset'])
        topo_fault[topo].append(r)

    # Group advanced data by topology
    topo_advanced = defaultdict(list)
    for r in advanced_data:
        topo = classify_topology(r['dataset'])
        topo_advanced[topo].append(r)

    topologies = {
        'Barabasi-Albert (Scale-Free)': {
            'use_case': 'Social network indexing, CDN overlays',
            'structure': 'Power-law degree distribution, ultra-small diameter, high-degree hubs',
            'spanner_behavior': 'Hubs captured early → very sparse spanners → low stretch',
            'vulnerability': 'Hub deletion causes rapid connectivity loss',
        },
        'Grid (Road-like)': {
            'use_case': 'GPS navigation, road routing, sensor grids',
            'structure': 'Uniform degree (~4), high diameter, planar, many bottlenecks',
            'spanner_behavior': 'No hubs → conservative pruning → denser spanners',
            'vulnerability': 'Cut-set failure causes partitioning',
        },
        'Erdos-Renyi (Random)': {
            'use_case': 'Theoretical benchmark, baseline comparison',
            'structure': 'Poisson degree distribution, high expansion, small diameter',
            'spanner_behavior': 'Uniform clustering → follows theoretical bounds most closely',
            'vulnerability': 'Highly robust; uniform redundancy',
        },
        'Small-World (Watts-Strogatz)': {
            'use_case': 'Brain connectivity, social routing, epidemic modeling',
            'structure': 'Regular ring + random shortcuts, high clustering coefficient',
            'spanner_behavior': 'Shortcuts critical for low stretch, local edges prunable',
            'vulnerability': 'Shortcut loss increases diameter significantly',
        },
    }

    for topo_name, info in topologies.items():
        print("\n" + "=" * 80)
        print(f"  TOPOLOGY REPORT CARD: {topo_name}")
        print("=" * 80)
        print(f"  Structure:  {info['structure']}")
        print(f"  Behavior:   {info['spanner_behavior']}")
        print(f"  Use Case:   {info['use_case']}")
        print(f"  Weakness:   {info['vulnerability']}")

        # Stretch metrics
        entries = topo_stretch.get(topo_name, [])
        if entries:
            print(f"\n  Stretch & Sparseness Metrics:")
            print(f"  {'t':>3} | {'BS Sparse':>10} | {'BS Avg Str':>10} | {'Gr Sparse':>10} | {'Gr Avg Str':>10} | {'Gr Max Str':>10}")
            print(f"  {'---':>3} | {'----------':>10} | {'----------':>10} | {'----------':>10} | {'----------':>10} | {'----------':>10}")
            for r in entries:
                print(f"  {r['t']:>3} | {float(r['bs_sparseness']):>10.4f} | {float(r['bs_avg_stretch']):>10.4f} | "
                      f"{float(r['gr_sparseness']):>10.4f} | {float(r['gr_avg_stretch']):>10.4f} | "
                      f"{float(r['gr_max_stretch']):>10.4f}")

        # Fault tolerance
        fault_entries = topo_fault.get(topo_name, [])
        if fault_entries:
            print(f"\n  Fault Tolerance (t=3):")
            t3_faults = [r for r in fault_entries if r['t'] == '3']
            for r in t3_faults:
                fr = float(r['failure_rate']) * 100
                conn = float(r['connectivity_ratio']) * 100
                print(f"    {fr:>5.1f}% failure → {conn:>6.1f}% connected, stretch = {r['damaged_avg_stretch']}")

        # HAS improvement
        adv_entries = topo_advanced.get(topo_name, [])
        if adv_entries:
            print(f"\n  HAS Improvement:")
            for r in adv_entries:
                print(f"    t={r['t']}: BS={r['bs_edges']} → HAS={r['has_edges']} "
                      f"(-{r['has_improvement_pct']}%), valid={r['has_valid']}")

        print()


def generate_summary_table():
    """Generate the cross-topology comparison table."""
    print("\n" + "=" * 80)
    print("CROSS-TOPOLOGY SUMMARY TABLE")
    print("=" * 80)

    print("\n| Metric | Scale-Free | Grid/Road | Random (ER) | Small-World |")
    print("|:-------|:----------|:----------|:-----------|:-----------|")
    print("| Dominant Feature | Power-law hubs | Uniform degree, planar | High expansion | Shortcuts + clustering |")
    print("| BS Behavior | Retains ~99.8% edges | Retains 100% edges | Retains ~99.98% edges | Retains ~99.9% edges |")
    print("| Greedy Sparseness (t=3) | 0.777 | 0.758 | 0.841 | 0.526 |")
    print("| Greedy Sparseness (t=7) | 0.334 | 0.637 | 0.258 | 0.432 |")
    print("| HAS Improvement (t=3) | -21.2% | -30.9% | -17.0% | -37.2% |")
    print("| Fault Tolerance (20%) | 68.3% conn | ~100% conn | 100% conn | ~90% conn |")
    print("| Best Use Case | Social indexing | Navigation | Benchmark | Brain models |")


if __name__ == "__main__":
    print("t-Spanner Topology Report Card Generator (Person B)")
    print("=" * 60)

    generate_report_cards()
    generate_summary_table()

    print("\n[DONE] All topology report cards generated.")
