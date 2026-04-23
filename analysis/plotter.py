"""
plotter.py — Publication-Quality Plotting for t-Spanner Analysis
=================================================================
Generates Pareto frontier, stretch distribution, energy proxy,
and topology comparison plots from Person A's experimental data.

Part of t-Spanner project — Person B (Research, Analysis & Writing)
"""

import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for headless environments
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import pandas as pd
import numpy as np
import os
import sys

# ── Configure matplotlib for publication quality ──
plt.rcParams.update({
    'font.size': 12,
    'font.family': 'serif',
    'axes.labelsize': 14,
    'axes.titlesize': 16,
    'legend.fontsize': 10,
    'xtick.labelsize': 11,
    'ytick.labelsize': 11,
    'figure.dpi': 150,
    'savefig.dpi': 300,
    'savefig.bbox': 'tight',
})

# Color palette for topologies
TOPOLOGY_COLORS = {
    'Erdos-Renyi': '#2196F3',
    'Grid': '#4CAF50',
    'Barabasi-Albert': '#FF5722',
    'Small-World': '#9C27B0',
    'Dense Random': '#FF9800',
}

RESULTS_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'results')
FIGURES_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'figures')


def _ensure_dirs():
    os.makedirs(FIGURES_DIR, exist_ok=True)


def _classify_topology(dataset_name):
    """Map dataset names to topology categories."""
    name = dataset_name.lower()
    if 'erdos' in name or 'random' in name:
        return 'Erdos-Renyi'
    elif 'grid' in name:
        return 'Grid'
    elif 'barabasi' in name or 'scale' in name:
        return 'Barabasi-Albert'
    elif 'small' in name or 'watts' in name:
        return 'Small-World'
    return 'Other'


def plot_pareto_frontier(csv_path=None, output_prefix='pareto_frontier_pub'):
    """
    Publication-quality Pareto frontier: Sparseness Ratio vs Average Stretch.
    One curve per topology, annotated key points, operating region shading.
    """
    _ensure_dirs()
    if csv_path is None:
        csv_path = os.path.join(RESULTS_DIR, 'stretch_experiment.csv')
    if not os.path.exists(csv_path):
        print(f"[WARN] {csv_path} not found, skipping Pareto plot.")
        return

    df = pd.read_csv(csv_path)
    df['topology'] = df['dataset'].apply(_classify_topology)

    fig, ax = plt.subplots(figsize=(10, 7))

    # Plot Greedy results (the interesting Pareto points)
    for topo, group in df.groupby('topology'):
        color = TOPOLOGY_COLORS.get(topo, '#607D8B')
        sorted_g = group.sort_values('gr_sparseness')
        ax.plot(sorted_g['gr_sparseness'], sorted_g['gr_avg_stretch'],
                'o-', color=color, label=topo, markersize=8, linewidth=2, zorder=5)
        # Annotate each point with t value
        for _, row in sorted_g.iterrows():
            ax.annotate(f"t={int(row['t'])}",
                        (row['gr_sparseness'], row['gr_avg_stretch']),
                        textcoords="offset points", xytext=(8, 5),
                        fontsize=8, color=color, fontweight='bold')

    # Operating region shading
    ax.axvspan(0, 0.3, alpha=0.08, color='red', label='Impractical (too sparse)')
    ax.axvspan(0.8, 1.05, alpha=0.08, color='blue', label='Wasteful (too dense)')
    ax.axvspan(0.3, 0.8, alpha=0.06, color='green')
    ax.annotate('Sweet Spot', xy=(0.55, 1.05), fontsize=11,
                fontstyle='italic', color='green', fontweight='bold', ha='center')

    ax.set_xlabel('Sparseness Ratio ($|E_{spanner}| / |E_{original}|$)')
    ax.set_ylabel('Average Stretch')
    ax.set_title('Pareto Frontier: Sparseness vs. Stretch (Greedy Spanner)')
    ax.legend(loc='upper left', framealpha=0.9)
    ax.grid(True, linestyle='--', alpha=0.4)
    ax.set_xlim(-0.02, 1.05)
    ax.set_ylim(0.95, max(df['gr_avg_stretch'].max() * 1.1, 2.0))

    for fmt in ['png', 'pdf']:
        fig.savefig(os.path.join(FIGURES_DIR, f'{output_prefix}.{fmt}'))
    plt.close(fig)
    print(f"[OK] Pareto frontier saved to {FIGURES_DIR}/{output_prefix}.png/pdf")


def plot_energy_proxy(csv_path=None, output_prefix='energy_proxy'):
    """
    Secondary plot: Edge count (energy/interference proxy) vs Stretch.
    Framed for wireless sensor network applications.
    """
    _ensure_dirs()
    if csv_path is None:
        csv_path = os.path.join(RESULTS_DIR, 'stretch_experiment.csv')
    if not os.path.exists(csv_path):
        print(f"[WARN] {csv_path} not found, skipping energy proxy plot.")
        return

    df = pd.read_csv(csv_path)
    df['topology'] = df['dataset'].apply(_classify_topology)

    fig, ax = plt.subplots(figsize=(10, 7))

    for topo, group in df.groupby('topology'):
        color = TOPOLOGY_COLORS.get(topo, '#607D8B')
        sorted_g = group.sort_values('gr_edges')
        ax.plot(sorted_g['gr_edges'], sorted_g['gr_avg_stretch'],
                's-', color=color, label=topo, markersize=8, linewidth=2)

    ax.set_xlabel('Edge Count (∝ Energy / Interference)')
    ax.set_ylabel('Average Stretch')
    ax.set_title('Energy-Interference Proxy: Edge Count vs. Stretch')
    ax.legend(loc='upper right', framealpha=0.9)
    ax.grid(True, linestyle='--', alpha=0.4)

    for fmt in ['png', 'pdf']:
        fig.savefig(os.path.join(FIGURES_DIR, f'{output_prefix}.{fmt}'))
    plt.close(fig)
    print(f"[OK] Energy proxy plot saved to {FIGURES_DIR}/{output_prefix}.png/pdf")


def plot_stretch_distribution_from_csv(csv_path=None, output_prefix='stretch_overview'):
    """
    Bar chart overview: avg, max, p95 stretch per topology and t value.
    """
    _ensure_dirs()
    if csv_path is None:
        csv_path = os.path.join(RESULTS_DIR, 'stretch_experiment.csv')
    if not os.path.exists(csv_path):
        print(f"[WARN] {csv_path} not found, skipping stretch overview.")
        return

    df = pd.read_csv(csv_path)

    fig, axes = plt.subplots(1, 3, figsize=(18, 6), sharey=False)
    metrics = [
        ('gr_avg_stretch', 'Average Stretch'),
        ('gr_max_stretch', 'Maximum Stretch'),
        ('gr_sparseness', 'Sparseness Ratio'),
    ]

    for ax, (col, title) in zip(axes, metrics):
        pivot = df.pivot_table(values=col, index='dataset', columns='t')
        pivot.plot(kind='bar', ax=ax, colormap='viridis', edgecolor='black', linewidth=0.5)
        ax.set_title(title)
        ax.set_xlabel('')
        ax.set_ylabel(title)
        ax.legend(title='t', fontsize=9)
        ax.tick_params(axis='x', rotation=30)
        ax.grid(axis='y', linestyle='--', alpha=0.4)

    fig.suptitle('Greedy Spanner Metrics Across Topologies and Stretch Factors', fontsize=16, y=1.02)
    fig.tight_layout()

    for fmt in ['png', 'pdf']:
        fig.savefig(os.path.join(FIGURES_DIR, f'{output_prefix}.{fmt}'))
    plt.close(fig)
    print(f"[OK] Stretch overview saved to {FIGURES_DIR}/{output_prefix}.png/pdf")


def plot_has_comparison(csv_path=None, output_prefix='has_vs_bs_analysis'):
    """
    3-way comparison: BS vs HAS vs Greedy — edge count and stretch.
    """
    _ensure_dirs()
    if csv_path is None:
        csv_path = os.path.join(RESULTS_DIR, 'advanced_experiment.csv')
    if not os.path.exists(csv_path):
        print(f"[WARN] {csv_path} not found, skipping HAS comparison.")
        return

    df = pd.read_csv(csv_path)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7))

    x = np.arange(len(df))
    width = 0.25

    # Edge count comparison
    ax1.bar(x - width, df['bs_edges'], width, label='Baswana-Sen', color='#2196F3', edgecolor='black', linewidth=0.5)
    ax1.bar(x, df['has_edges'], width, label='Hybrid Adaptive (HAS)', color='#4CAF50', edgecolor='black', linewidth=0.5)
    ax1.bar(x + width, df['gr_edges'], width, label='Greedy', color='#FF5722', edgecolor='black', linewidth=0.5)
    ax1.set_xlabel('Dataset')
    ax1.set_ylabel('Edge Count')
    ax1.set_title('Edge Count: BS vs HAS vs Greedy')
    ax1.set_xticks(x)
    ax1.set_xticklabels([f"{r['dataset']}\nt={int(r['t'])}" for _, r in df.iterrows()],
                        fontsize=8, rotation=30, ha='right')
    ax1.legend()
    ax1.grid(axis='y', linestyle='--', alpha=0.4)

    # Stretch comparison
    ax2.bar(x - width, df['bs_avg_stretch'], width, label='Baswana-Sen', color='#2196F3', edgecolor='black', linewidth=0.5)
    ax2.bar(x, df['has_avg_stretch'], width, label='Hybrid Adaptive (HAS)', color='#4CAF50', edgecolor='black', linewidth=0.5)
    ax2.bar(x + width, df['gr_avg_stretch'], width, label='Greedy', color='#FF5722', edgecolor='black', linewidth=0.5)
    ax2.set_xlabel('Dataset')
    ax2.set_ylabel('Average Stretch')
    ax2.set_title('Average Stretch: BS vs HAS vs Greedy')
    ax2.set_xticks(x)
    ax2.set_xticklabels([f"{r['dataset']}\nt={int(r['t'])}" for _, r in df.iterrows()],
                        fontsize=8, rotation=30, ha='right')
    ax2.legend()
    ax2.grid(axis='y', linestyle='--', alpha=0.4)

    fig.suptitle('Algorithm Comparison: Baswana-Sen vs Hybrid Adaptive vs Greedy', fontsize=16, y=1.02)
    fig.tight_layout()

    for fmt in ['png', 'pdf']:
        fig.savefig(os.path.join(FIGURES_DIR, f'{output_prefix}.{fmt}'))
    plt.close(fig)
    print(f"[OK] HAS comparison saved to {FIGURES_DIR}/{output_prefix}.png/pdf")


if __name__ == "__main__":
    print("=" * 60)
    print("t-Spanner Publication-Quality Plot Generator (Person B)")
    print("=" * 60)

    plot_pareto_frontier()
    plot_energy_proxy()
    plot_stretch_distribution_from_csv()
    plot_has_comparison()

    //print("\n[DONE] All Person B plots generated.")
