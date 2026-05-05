"""
greedy_spanner.py — Classical Greedy BFS-based (2k-1)-Spanner
=============================================================
Reference: Althöfer et al., 1993 — "On sparse spanners of weighted graphs"

Algorithm:
  1. Sort all edges by weight (ascending)
  2. For each edge (u, v, w):
     - Run BFS/Dijkstra in the current spanner H
     - If d_H(u, v) > t · w(u,v), add edge (u,v) to H
  3. Return H

Why BFS for stretch checking (not DFS):
  - BFS finds the SHORTEST unweighted path from source to target
  - DFS finds A path, but not necessarily the shortest
  - For stretch verification, we need d_H(u,v) = shortest path distance
  - If we used DFS, we might get d_DFS(u,v) > d_BFS(u,v), causing us to add
    edges unnecessarily → spanner would be denser than optimal
  - Or worse: DFS might report a path exists but miss that the SHORTEST one
    is too long → could violate the stretch guarantee

Complexity:
  - O(m · (n + m')) per edge check, where m' is current spanner edge count
  - Total: O(m · n) for unweighted, O(m · (n + m) · log n) for weighted with Dijkstra
  - This is the baseline — Baswana-Sen is dramatically faster at O(k·m)

Part of t-Spanner project — Person A (Implementation & Engineering)
"""

import time
from typing import Any, Dict, List, Set, Tuple

from .graph import Graph


def greedy_bfs_spanner(
    graph: Graph,
    t: int = 3,
    weighted: bool = False
) -> Dict[str, Any]:
    """
    Build a t-spanner using the greedy algorithm.
    
    Parameters
    ----------
    graph : Graph
        Input undirected graph.
    t : int
        Stretch factor. For a t-spanner, d_H(u,v) ≤ t · d_G(u,v) for all u,v.
    weighted : bool
        If True, use Dijkstra for distance checks; else use BFS (unweighted).
    
    Returns
    -------
    dict with:
        - "spanner": Graph — the spanner subgraph
        - "spanner_edges": list of (u, v, w)
        - "num_spanner_edges": int
        - "stretch_param": int
        - "construction_time_ms": float
        - "edges_checked": int — total BFS/Dijkstra runs
        - "edges_rejected": int — edges NOT added (distance was OK)
    """
    start_time = time.perf_counter()
    
    n = graph.num_nodes
    nodes = graph.nodes
    
    # Initialize empty spanner with all nodes
    spanner = Graph()
    for v in nodes:
        spanner.add_node(v)
    
    # Sort edges by weight (ascending) — greedy strategy: consider cheap edges first
    # This is important: by adding lighter edges first, we establish short paths
    # that prevent heavier edges from being added → sparser spanner
    all_edges = sorted(graph.edges(), key=lambda e: e[2])
    
    edges_checked = 0
    edges_rejected = 0
    spanner_edges_list = []
    
    for u, v, w in all_edges:
        edges_checked += 1
        
        # Check current distance in spanner
        if weighted:
            # Dijkstra for weighted graphs — O((n + m') log n)
            current_dist = spanner.dijkstra_distance(u, v)
        else:
            # BFS for unweighted — O(n + m')
            # This is correct because BFS finds SHORTEST unweighted path
            # DFS would find A path but not necessarily the shortest
            #
            # Example where DFS fails:
            #   Graph: A-B (w=1), A-C (w=1), B-C (w=1), B-D (w=2)
            #   DFS from A might go A→B→D, never finding A→B→C→... 
            #   So DFS reports d(A,C) = inf when actually d(A,C) = 1 via existing edges
            #
            # BFS always reports correct shortest path → correct stretch decision
            current_dist = spanner.bfs_distance(u, v)
        
        # Add edge only if current spanner distance exceeds stretch threshold
        # This is the core greedy condition: d_H(u,v) > t · w(u,v)
        if current_dist > t * w:
            spanner.add_edge(u, v, w)
            spanner_edges_list.append((u, v, w))
        else:
            edges_rejected += 1
    
    construction_time = (time.perf_counter() - start_time) * 1000
    
    return {
        "spanner": spanner,
        "spanner_edges": spanner_edges_list,
        "num_spanner_edges": len(spanner_edges_list),
        "stretch_param": t,
        "construction_time_ms": round(construction_time, 2),
        "edges_checked": edges_checked,
        "edges_rejected": edges_rejected,
        "original_edges": graph.num_edges,
        "sparseness_ratio": len(spanner_edges_list) / max(graph.num_edges, 1),
    }


def greedy_weighted_spanner(
    graph: Graph,
    t: int = 3
) -> Dict[str, Any]:
    """Convenience wrapper for weighted greedy spanner."""
    return greedy_bfs_spanner(graph, t=t, weighted=True)
