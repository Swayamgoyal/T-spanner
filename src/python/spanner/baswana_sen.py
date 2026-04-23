"""
baswana_sen.py — Baswana-Sen Randomized (2k-1)-Spanner Algorithm
================================================================
Reference: S. Baswana & S. Sen, "A simple and linear time randomized algorithm 
           for computing sparse spanners in weighted graphs," 
           Random Structures & Algorithms, 2007.

Algorithm Overview:
  - Builds a (2k-1)-spanner of a weighted undirected graph G = (V, E)
  - Expected size: O(k * n^{1+1/k}) edges
  - Expected running time: O(k * m) — near-linear for fixed k
  - Uses hierarchical random clustering (k phases)

Key Idea (corrected implementation):
  The algorithm works in k-1 iterations. In each iteration i:
    1. Sample cluster centers from C_{i-1} to form C_i with probability n^{-1/k}
    2. For EVERY vertex v with a cluster in C_{i-1}:
       a. If v's cluster survived to C_i, for each neighbor u in a DIFFERENT
          cluster, add the lightest such inter-cluster edge (one per cluster).
       b. If v's cluster did NOT survive:
          - Look for a neighbor in a cluster that DID survive → attach to it
          - If found: add that attachment edge, and also add lightest inter-cluster
            edges to each other neighboring (non-surviving) cluster
          - If NOT found: v becomes unclustered; add lightest edge to each 
            neighboring cluster (of the OLD clustering)
  
  Final phase: all remaining unclustered vertices add ALL their edges.

  The critical insight is that EVERY edge crossing cluster boundaries must 
  be "covered" — either by adding the lightest edge per cluster, or by the 
  fact that both endpoints are in the same cluster and connected via the 
  cluster-center path.

Part of t-Spanner project — Person A (Implementation & Engineering)
"""

import math
import random
import time
from collections import defaultdict
from typing import Any, Dict, List, Optional, Set, Tuple

from .graph import Graph


def baswana_sen_spanner(
    graph: Graph,
    k: int = 2,
    seed: Optional[int] = None,
    log_phases: bool = True
) -> Dict[str, Any]:
    """
    Construct a (2k-1)-spanner using the Baswana-Sen randomized clustering algorithm.
    
    Parameters
    ----------
    graph : Graph
        Input weighted undirected graph.
    k : int
        Stretch parameter. The spanner guarantees distances <= (2k-1) * original.
        - k=2 -> 3-spanner (stretch <= 3)
        - k=3 -> 5-spanner (stretch <= 5)
        - k=4 -> 7-spanner (stretch <= 7)
    seed : int, optional
        Random seed for reproducibility.
    log_phases : bool
        If True, log per-phase statistics.
    
    Returns
    -------
    dict with:
        - "spanner": Graph -- the spanner subgraph
        - "spanner_edges": list of (u, v, w) edges in the spanner
        - "num_spanner_edges": int
        - "stretch_param": int -- the (2k-1) value
        - "phase_logs": list of per-phase stats (if log_phases=True)
        - "construction_time_ms": float
        - "cluster_assignments": dict -- final cluster assignment per node
    """
    if seed is not None:
        random.seed(seed)

    start_time = time.perf_counter()
    
    n = graph.num_nodes
    nodes = sorted(graph.nodes)
    
    if n == 0:
        return _empty_result(k)
    
    # Sampling probability: p = n^{-1/k}
    p = n ** (-1.0 / k) if n > 1 else 1.0
    
    # ---- Phase 0: Initialize clusters ----
    # Every vertex starts as its own cluster center
    # cluster[v] = representative (center) of v's cluster, or None if unclustered
    cluster: Dict[int, Optional[int]] = {v: v for v in nodes}
    
    # Spanner edge set (using set of sorted pairs to avoid duplicates)
    spanner_edges_set: Set[Tuple[int, int]] = set()
    spanner_edge_weights: Dict[Tuple[int, int], float] = {}
    
    phase_logs = []
    
    def add_spanner_edge(u: int, v: int, w: float):
        """Add edge to spanner (deduplicating)."""
        edge_key = (min(u, v), max(u, v))
        if edge_key not in spanner_edges_set:
            spanner_edges_set.add(edge_key)
            spanner_edge_weights[edge_key] = w
            return True
        return False
    
    # ---- Phases 1 to k-1 ----
    for phase in range(1, k):
        phase_start = time.perf_counter()
        edges_processed = 0
        edges_added = 0
        clusters_surviving = 0
        vertices_unclustered = 0
        
        # Step 1: SAMPLE -- each current cluster center survives with probability p
        sampled_centers: Set[int] = set()
        current_centers = set(c for c in cluster.values() if c is not None)
        
        for center in current_centers:
            if random.random() < p:
                sampled_centers.add(center)
                clusters_surviving += 1
        
        # Step 2: Process EVERY clustered vertex
        new_cluster: Dict[int, Optional[int]] = {}
        
        for v in nodes:
            if cluster[v] is None:
                # Already unclustered from previous phase -- stays unclustered
                new_cluster[v] = None
                continue
            
            v_old_cluster = cluster[v]
            
            # Gather neighbor information: for each neighbor, what cluster are they in?
            # Group by cluster -> lightest edge
            lightest_to_cluster: Dict[Optional[int], Tuple[int, float]] = {}
            
            for u, w in graph.neighbors(v):
                edges_processed += 1
                u_cluster = cluster[u]
                if u_cluster is None:
                    continue
                if u_cluster not in lightest_to_cluster or w < lightest_to_cluster[u_cluster][1]:
                    lightest_to_cluster[u_cluster] = (u, w)
            
            if v_old_cluster in sampled_centers:
                # Case A: v's cluster survived
                # v stays in this cluster
                new_cluster[v] = v_old_cluster
                
                # Add lightest edge to each NEIGHBORING cluster that is DIFFERENT
                # and did NOT survive (these inter-cluster edges maintain stretch)
                for nbr_cluster, (u, w) in lightest_to_cluster.items():
                    if nbr_cluster != v_old_cluster and nbr_cluster not in sampled_centers:
                        if add_spanner_edge(v, u, w):
                            edges_added += 1
            
            else:
                # Case B: v's cluster did NOT survive
                # Try to attach to a neighboring cluster that DID survive
                best_sampled_neighbor = None
                best_sampled_weight = float('inf')
                best_sampled_cluster = None
                
                for nbr_cluster, (u, w) in lightest_to_cluster.items():
                    if nbr_cluster in sampled_centers:
                        if w < best_sampled_weight:
                            best_sampled_weight = w
                            best_sampled_neighbor = u
                            best_sampled_cluster = nbr_cluster
                
                if best_sampled_neighbor is not None:
                    # Attach v to the nearest surviving cluster
                    new_cluster[v] = best_sampled_cluster
                    if add_spanner_edge(v, best_sampled_neighbor, best_sampled_weight):
                        edges_added += 1
                    
                    # Also add lightest edge to each non-surviving neighboring cluster
                    # (these clusters are "disappearing" — need coverage)
                    for nbr_cluster, (u, w) in lightest_to_cluster.items():
                        if nbr_cluster != best_sampled_cluster and nbr_cluster not in sampled_centers:
                            if add_spanner_edge(v, u, w):
                                edges_added += 1
                
                else:
                    # No neighboring cluster survived -- v becomes unclustered
                    new_cluster[v] = None
                    vertices_unclustered += 1
                    
                    # Add lightest edge to EVERY neighboring cluster (old clustering)
                    # This is CRITICAL for stretch guarantee
                    for nbr_cluster, (u, w) in lightest_to_cluster.items():
                        if add_spanner_edge(v, u, w):
                            edges_added += 1
        
        cluster = new_cluster
        
        phase_time = time.perf_counter() - phase_start
        if log_phases:
            phase_logs.append({
                "phase": phase,
                "edges_processed": edges_processed,
                "edges_added": edges_added,
                "clusters_surviving": clusters_surviving,
                "vertices_unclustered": vertices_unclustered,
                "phase_time_ms": round(phase_time * 1000, 2),
            })
    
    # ---- Final phase: handle remaining unclustered vertices ----
    # Any vertex still unclustered after phase k-1 adds ALL its remaining edges
    final_edges_added = 0
    for v in nodes:
        if cluster[v] is None:
            for u, w in graph.neighbors(v):
                if add_spanner_edge(v, u, w):
                    final_edges_added += 1
    
    if log_phases:
        phase_logs.append({
            "phase": "final",
            "edges_added": final_edges_added,
            "unclustered_vertices": sum(1 for v in cluster if cluster[v] is None),
        })
    
    # ---- Build spanner Graph object ----
    spanner = Graph()
    spanner_edges_list = []
    for (u, v), w in spanner_edge_weights.items():
        spanner.add_edge(u, v, w)
        spanner_edges_list.append((u, v, w))
    
    # Add all nodes (including isolated ones)
    for v in nodes:
        spanner.add_node(v)
    
    construction_time = (time.perf_counter() - start_time) * 1000
    
    return {
        "spanner": spanner,
        "spanner_edges": spanner_edges_list,
        "num_spanner_edges": len(spanner_edges_list),
        "stretch_param": 2 * k - 1,
        "k": k,
        "sampling_probability": p,
        "phase_logs": phase_logs,
        "construction_time_ms": round(construction_time, 2),
        "cluster_assignments": dict(cluster),
        "original_edges": graph.num_edges,
        "sparseness_ratio": len(spanner_edges_list) / max(graph.num_edges, 1),
    }


def _empty_result(k: int) -> Dict[str, Any]:
    """Return empty result for empty graph."""
    return {
        "spanner": Graph(),
        "spanner_edges": [],
        "num_spanner_edges": 0,
        "stretch_param": 2 * k - 1,
        "k": k,
        "sampling_probability": 0,
        "phase_logs": [],
        "construction_time_ms": 0,
        "cluster_assignments": {},
        "original_edges": 0,
        "sparseness_ratio": 0,
    }


def theoretical_max_edges(n: int, k: int) -> float:
    """
    Theoretical upper bound on spanner edges: k * n^{1+1/k}
    
    This comes from the Erdos girth conjecture:
    Any (2k-1)-spanner must have Omega(n^{1+1/k}) edges, and 
    Baswana-Sen achieves O(k * n^{1+1/k}) edges in expectation.
    """
    return k * (n ** (1 + 1.0 / k))
