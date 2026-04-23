"""
Streamlit Spanner Dashboard — Interactive t-Spanner Visualizer
==============================================================
A simpler Python dashboard as alternative to React+D3.

Features:
  - Upload graph or pick preset
  - Slider for t (3, 5, 7, 9)
  - Show spanner stats + visualization
  - Side-by-side: Baswana-Sen vs Greedy at same t
  - Phase-by-phase construction view

Run: streamlit run viz/streamlit/app.py

Part of t-Spanner project — Person A (Implementation & Engineering)
"""

import os
import sys
import io
import time
import random

# Add project root to path
PROJECT_ROOT = os.path.join(os.path.dirname(__file__), '..', '..')
sys.path.insert(0, PROJECT_ROOT)

import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

from src.python.spanner.graph import Graph
from src.python.spanner.baswana_sen import baswana_sen_spanner, theoretical_max_edges
from src.python.spanner.greedy_spanner import greedy_bfs_spanner
from src.python.spanner.metrics import (
    compute_stretch, compute_sparseness_ratio, 
    verify_spanner_property, stretch_statistics
)
from src.python.data.graph_loader import GraphLoader

# ─── Page Config ───────────────────────────────────────────────

st.set_page_config(
    page_title="t-Spanner Visualizer",
    page_icon="🕸️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ────────────────────────────────────────────────

st.markdown("""
<style>
    .main-header {
        font-size: 2.5em;
        font-weight: 800;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        padding: 20px 0;
    }
    .metric-card {
        background: linear-gradient(135deg, #1a1a2e, #16213e);
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        border: 1px solid rgba(102, 126, 234, 0.3);
    }
    .stMetric label { font-size: 0.9em !important; }
</style>
""", unsafe_allow_html=True)

# ─── Sidebar ───────────────────────────────────────────────────

st.sidebar.title("🕸 t-Spanner Controls")

# Graph source
graph_source = st.sidebar.selectbox(
    "Graph Source",
    ["Preset: Random (100)", "Preset: Grid (10x10)", 
     "Preset: Scale-Free (100)", "Preset: Small-World (100)",
     "Custom: Upload Edge List"]
)

# Stretch parameter
t_value = st.sidebar.slider("Stretch Parameter (t)", min_value=3, max_value=9, value=3, step=2)
k_value = (t_value + 1) // 2

st.sidebar.markdown(f"**k = {k_value}** (stretch ≤ {t_value})")

# Algorithm selection
algo = st.sidebar.selectbox("Algorithm", ["Baswana-Sen", "Greedy BFS", "Compare Both"])

# Seed
seed = st.sidebar.number_input("Random Seed", value=42, min_value=0, max_value=999)

# ─── Load Graph ────────────────────────────────────────────────

@st.cache_data
def load_graph(source, seed_val):
    loader = GraphLoader()
    if "Random" in source:
        return loader.generate_erdos_renyi(100, 0.1, seed=seed_val)
    elif "Grid" in source:
        return loader.generate_grid(10, 10)
    elif "Scale-Free" in source:
        return loader.generate_barabasi_albert(100, 3, seed=seed_val)
    elif "Small-World" in source:
        return loader.generate_watts_strogatz(100, 6, 0.1, seed=seed_val)
    return None

if "Upload" in graph_source:
    uploaded = st.sidebar.file_uploader("Upload Edge List (one 'u v' per line)", type=['txt', 'csv'])
    if uploaded:
        content = uploaded.read().decode('utf-8')
        graph = Graph.from_edge_list(content)
        graph = graph.largest_connected_component()
        graph, _ = graph.normalize_node_ids()
    else:
        st.info("Please upload an edge list file.")
        st.stop()
else:
    graph = load_graph(graph_source, seed)

# ─── Header ────────────────────────────────────────────────────

st.markdown('<div class="main-header">t-Spanner Interactive Visualizer</div>', unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Nodes", graph.num_nodes)
with col2:
    st.metric("Edges", graph.num_edges)
with col3:
    st.metric("Density", f"{graph.density:.4f}")
with col4:
    st.metric("Avg Degree", f"{graph.avg_degree:.1f}")

# ─── Build Spanner ─────────────────────────────────────────────

@st.cache_data
def build_spanner(graph_edges, num_nodes, k, t, algo_name, seed_val):
    # Reconstruct graph from edges (needed for caching with hashable args)
    g = Graph()
    for u, v, w in graph_edges:
        g.add_edge(u, v, w)
    for i in range(num_nodes):
        g.add_node(i)
    
    if algo_name == "Baswana-Sen":
        return baswana_sen_spanner(g, k=k, seed=seed_val)
    else:
        return greedy_bfs_spanner(g, t=t)

graph_edges = tuple((u, v, w) for u, v, w in graph.edges())

with st.spinner("Building spanner..."):
    if algo == "Compare Both":
        bs_result = build_spanner(graph_edges, graph.num_nodes, k_value, t_value, "Baswana-Sen", seed)
        gr_result = build_spanner(graph_edges, graph.num_nodes, k_value, t_value, "Greedy", seed)
    elif algo == "Baswana-Sen":
        bs_result = build_spanner(graph_edges, graph.num_nodes, k_value, t_value, "Baswana-Sen", seed)
        gr_result = None
    else:
        bs_result = None
        gr_result = build_spanner(graph_edges, graph.num_nodes, k_value, t_value, "Greedy", seed)

# ─── Results ───────────────────────────────────────────────────

st.markdown("---")

if algo == "Compare Both":
    col_bs, col_gr = st.columns(2)
    
    with col_bs:
        st.subheader("🔵 Baswana-Sen")
        st.metric("Spanner Edges", bs_result["num_spanner_edges"])
        st.metric("Sparseness Ratio", f"{bs_result['sparseness_ratio']:.4f}")
        st.metric("Construction Time", f"{bs_result['construction_time_ms']:.2f} ms")
        st.metric("Theoretical Max", f"{theoretical_max_edges(graph.num_nodes, k_value):.0f}")
    
    with col_gr:
        st.subheader("🟠 Greedy (BFS)")
        st.metric("Spanner Edges", gr_result["num_spanner_edges"])
        st.metric("Sparseness Ratio", f"{gr_result['sparseness_ratio']:.4f}")
        st.metric("Construction Time", f"{gr_result['construction_time_ms']:.2f} ms")
        st.metric("Edges Checked", gr_result["edges_checked"])
else:
    result = bs_result if bs_result else gr_result
    name = "Baswana-Sen" if bs_result else "Greedy"
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Spanner Edges", result["num_spanner_edges"])
    with col2:
        st.metric("Sparseness Ratio", f"{result['sparseness_ratio']:.4f}")
    with col3:
        st.metric("Construction Time", f"{result['construction_time_ms']:.2f} ms")

# ─── Visualization ─────────────────────────────────────────────

st.markdown("---")
st.subheader("Graph Visualization")

def plot_graph_comparison(original, spanner_result, title="Spanner"):
    """Plot original graph with spanner edges highlighted."""
    try:
        import networkx as nx
    except ImportError:
        st.warning("NetworkX required for visualization")
        return
    
    fig, ax = plt.subplots(1, 1, figsize=(10, 8))
    fig.patch.set_facecolor('#0e1117')
    ax.set_facecolor('#0e1117')
    
    # Build networkx graph for layout
    G = original.to_networkx()
    pos = nx.spring_layout(G, seed=42, k=1.5/max(1, original.num_nodes**0.5))
    
    # Get spanner edges
    spanner_edges = set()
    for u, v, w in spanner_result["spanner_edges"]:
        spanner_edges.add((min(u,v), max(u,v)))
    
    # Draw non-spanner edges (faint dotted)
    all_edges = original.edge_set()
    non_spanner = all_edges - spanner_edges
    
    if non_spanner:
        non_spanner_list = [(u, v) for u, v in non_spanner]
        nx.draw_networkx_edges(G, pos, edgelist=non_spanner_list,
                              edge_color='#333333', style='dotted', 
                              alpha=0.3, width=0.5, ax=ax)
    
    # Draw spanner edges (bold)
    if spanner_edges:
        spanner_list = [(u, v) for u, v in spanner_edges]
        nx.draw_networkx_edges(G, pos, edgelist=spanner_list,
                              edge_color='#667eea', style='solid',
                              alpha=0.8, width=2.0, ax=ax)
    
    # Draw nodes with cluster coloring
    clusters = spanner_result.get("cluster_assignments", {})
    cluster_ids = list(set(c for c in clusters.values() if c is not None))
    color_map = {}
    cmap = plt.cm.Set3
    for i, cid in enumerate(cluster_ids):
        color_map[cid] = cmap(i / max(len(cluster_ids), 1))
    
    node_colors = []
    for node in sorted(G.nodes()):
        c = clusters.get(node)
        if c is not None and c in color_map:
            node_colors.append(color_map[c])
        else:
            node_colors.append('#ff6b6b')  # Unclustered = red
    
    nx.draw_networkx_nodes(G, pos, node_size=60, node_color=node_colors,
                          edgecolors='white', linewidths=0.5, ax=ax)
    
    # Legend
    legend_elements = [
        mpatches.Patch(color='#667eea', label=f'Spanner edges ({len(spanner_edges)})'),
        mpatches.Patch(color='#333333', label=f'Removed edges ({len(non_spanner)})'),
        mpatches.Patch(color='#ff6b6b', label='Unclustered nodes'),
    ]
    ax.legend(handles=legend_elements, loc='upper left', fontsize=9,
             facecolor='#1a1a2e', edgecolor='#667eea', labelcolor='white')
    
    ax.set_title(title, fontsize=16, fontweight='bold', color='white', pad=20)
    ax.axis('off')
    
    return fig

if algo == "Compare Both":
    col1, col2 = st.columns(2)
    with col1:
        fig = plot_graph_comparison(graph, bs_result, "Baswana-Sen Spanner")
        if fig:
            st.pyplot(fig)
    with col2:
        fig = plot_graph_comparison(graph, gr_result, "Greedy Spanner")
        if fig:
            st.pyplot(fig)
else:
    result = bs_result if bs_result else gr_result
    fig = plot_graph_comparison(graph, result, f"{algo} (t={t_value})")
    if fig:
        st.pyplot(fig)

# ─── Phase Logs ────────────────────────────────────────────────

if bs_result and bs_result.get("phase_logs"):
    st.markdown("---")
    st.subheader("Phase-by-Phase Construction")
    
    for log in bs_result["phase_logs"]:
        phase = log["phase"]
        if phase == "final":
            st.write(f"**Final Phase**: {log['edges_added']} edges from "
                    f"{log['unclustered_vertices']} unclustered vertices")
        else:
            st.write(f"**Phase {phase}**: "
                    f"processed={log['edges_processed']} edges, "
                    f"added={log['edges_added']}, "
                    f"clusters={log['clusters_surviving']}, "
                    f"unclustered={log['vertices_unclustered']}, "
                    f"time={log['phase_time_ms']:.1f}ms")

# ─── Stretch Verification ─────────────────────────────────────

st.markdown("---")
st.subheader("Stretch Verification")

num_verify = st.slider("Number of pairs to verify", 50, 500, 200)

if st.button("Verify Stretch Property"):
    result = bs_result if bs_result else gr_result
    with st.spinner("Computing stretch values..."):
        verification = verify_spanner_property(
            graph, result["spanner"], t=t_value, 
            num_samples=num_verify, seed=seed
        )
    
    if verification["is_valid"]:
        st.success(f"VALID {t_value}-spanner! Max stretch: {verification['max_stretch']:.4f}")
    else:
        st.error(f"VIOLATIONS found: {verification['num_violations']}")
    
    st.json({
        "is_valid": verification["is_valid"],
        "max_stretch": verification["max_stretch"],
        "avg_stretch": verification["avg_stretch"],
        "num_violations": verification["num_violations"],
        "pairs_checked": verification["num_pairs_checked"],
    })

# ─── Footer ───────────────────────────────────────────────────

st.markdown("---")
st.markdown(
    "<center><small>t-Spanner Visualizer | Algorithm Engineering Project | "
    "Baswana-Sen 2007</small></center>",
    unsafe_allow_html=True
)
