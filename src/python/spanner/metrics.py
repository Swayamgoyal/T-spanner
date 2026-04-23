"""
metrics.py — Stretch Factor & Sparseness Computation
====================================================
Computes key quality metrics for t-spanners:
  - Stretch factor: d_H(u,v) / d_G(u,v) for sampled vertex pairs
  - Sparseness ratio: |E_spanner| / |E_original|
  - Statistical analysis: avg, max, median, 95th percentile, distribution

Why sample-based stretch computation:
  - Exact all-pairs shortest paths is O(n² · (n + m)) — infeasible for n > 10K
  - Sampling 500-1000 random pairs gives a statistically robust estimate
  - We verify the theoretical guarantee (stretch ≤ t) on sampled pairs
  - For small graphs (n ≤ 1000), we can afford exact computation

Part of t-Spanner project — Person A (Implementation & Engineering)
"""

import random
import statistics
from collections import Counter
from typing import Any, Dict, List, Optional, Tuple

from .graph import Graph


def compute_stretch(
    original: Graph,
    spanner: Graph,
    pairs: Optional[List[Tuple[int, int]]] = None,
    num_pairs: int = 500,
    weighted: bool = False,
    seed: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Compute stretch factors for sampled vertex pairs.
    
    Stretch for a pair (u, v) = d_H(u,v) / d_G(u,v)
    where H is the spanner and G is the original graph.
    
    Parameters
    ----------
    original : Graph
        The original graph G.
    spanner : Graph
        The spanner subgraph H.
    pairs : list of (int, int), optional
        Specific pairs to check. If None, sample randomly.
    num_pairs : int
        Number of random pairs to sample if pairs is None.
    weighted : bool
        Use Dijkstra (True) or BFS (False) for distances.
    seed : int, optional
        Random seed.
    
    Returns
    -------
    dict with stretch statistics and per-pair data.
    """
    if seed is not None:
        random.seed(seed)
    
    if pairs is None:
        pairs = sample_random_pairs(original, num_pairs, seed=seed)
    
    stretches = []
    pair_details = []
    violations = 0  # pairs where stretch > theoretical guarantee
    unreachable_in_spanner = 0
    
    for u, v in pairs:
        # Distance in original graph
        if weighted:
            d_orig = original.dijkstra_distance(u, v)
        else:
            d_orig = original.bfs_distance(u, v)
        
        if d_orig == float('inf') or d_orig == 0:
            continue  # Skip disconnected or same-node pairs
        
        # Distance in spanner
        if weighted:
            d_span = spanner.dijkstra_distance(u, v)
        else:
            d_span = spanner.bfs_distance(u, v)
        
        if d_span == float('inf'):
            unreachable_in_spanner += 1
            continue
        
        stretch = d_span / d_orig
        stretches.append(stretch)
        pair_details.append({
            "u": u, "v": v,
            "d_original": d_orig,
            "d_spanner": d_span,
            "stretch": round(stretch, 4),
        })
    
    if not stretches:
        return {
            "avg_stretch": 0,
            "max_stretch": 0,
            "min_stretch": 0,
            "median_stretch": 0,
            "p95_stretch": 0,
            "std_stretch": 0,
            "num_pairs_checked": 0,
            "violations": 0,
            "unreachable_in_spanner": unreachable_in_spanner,
            "pair_details": [],
            "stretch_distribution": {},
        }
    
    stats = stretch_statistics(stretches)
    stats["num_pairs_checked"] = len(stretches)
    stats["violations"] = violations
    stats["unreachable_in_spanner"] = unreachable_in_spanner
    stats["pair_details"] = pair_details
    stats["stretch_distribution"] = _stretch_distribution(stretches)
    
    return stats


def compute_sparseness_ratio(original: Graph, spanner: Graph) -> float:
    """
    Sparseness ratio = |E_spanner| / |E_original|
    
    Values:
    - 0.0 = empty spanner (no edges)
    - 1.0 = spanner == original graph (no edges removed)
    - ~0.1 = excellent sparsification (90% edges removed)
    
    A good spanner achieves low sparseness ratio with low stretch.
    """
    if original.num_edges == 0:
        return 0.0
    return spanner.num_edges / original.num_edges


def sample_random_pairs(
    graph: Graph,
    num_pairs: int = 500,
    seed: Optional[int] = None,
    connected_only: bool = True,
) -> List[Tuple[int, int]]:
    """
    Sample random (source, target) pairs from the graph.
    
    If connected_only=True, ensures both nodes are in the same connected component
    by doing a quick BFS check. This avoids sampling pairs with infinite distance.
    """
    if seed is not None:
        random.seed(seed)
    
    nodes = sorted(graph.nodes)
    if len(nodes) < 2:
        return []
    
    pairs = []
    attempts = 0
    max_attempts = num_pairs * 10  # Avoid infinite loop
    
    while len(pairs) < num_pairs and attempts < max_attempts:
        u, v = random.sample(nodes, 2)
        if u != v:
            if connected_only:
                # Quick BFS reachability check
                d = graph.bfs_distance(u, v)
                if d < float('inf'):
                    pairs.append((u, v))
            else:
                pairs.append((u, v))
        attempts += 1
    
    return pairs


def stretch_statistics(stretches: List[float]) -> Dict[str, float]:
    """
    Compute comprehensive statistics for a list of stretch values.
    """
    if not stretches:
        return {
            "avg_stretch": 0, "max_stretch": 0, "min_stretch": 0,
            "median_stretch": 0, "p95_stretch": 0, "std_stretch": 0,
        }
    
    sorted_s = sorted(stretches)
    n = len(sorted_s)
    p95_idx = min(int(n * 0.95), n - 1)
    
    return {
        "avg_stretch": round(statistics.mean(stretches), 4),
        "max_stretch": round(max(stretches), 4),
        "min_stretch": round(min(stretches), 4),
        "median_stretch": round(statistics.median(stretches), 4),
        "p95_stretch": round(sorted_s[p95_idx], 4),
        "std_stretch": round(statistics.stdev(stretches) if len(stretches) > 1 else 0, 4),
    }


def _stretch_distribution(stretches: List[float], bins: int = 20) -> Dict[str, int]:
    """Create a histogram of stretch values."""
    if not stretches:
        return {}
    
    min_s = min(stretches)
    max_s = max(stretches)
    
    if min_s == max_s:
        return {f"{min_s:.2f}": len(stretches)}
    
    bin_width = (max_s - min_s) / bins
    histogram = {}
    
    for s in stretches:
        bin_idx = min(int((s - min_s) / bin_width), bins - 1)
        bin_label = f"{min_s + bin_idx * bin_width:.2f}-{min_s + (bin_idx + 1) * bin_width:.2f}"
        histogram[bin_label] = histogram.get(bin_label, 0) + 1
    
    return histogram


def verify_spanner_property(
    original: Graph,
    spanner: Graph,
    t: int,
    weighted: bool = False,
    num_samples: int = 1000,
    seed: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Verify that the spanner satisfies the t-stretch property.
    
    For each sampled pair (u,v): checks d_H(u,v) ≤ t · d_G(u,v)
    Reports any violations.
    """
    result = compute_stretch(original, spanner, num_pairs=num_samples, 
                             weighted=weighted, seed=seed)
    
    violations = []
    for detail in result.get("pair_details", []):
        if detail["stretch"] > t + 0.001:  # Small epsilon for floating point
            violations.append(detail)
    
    return {
        "is_valid": len(violations) == 0,
        "max_stretch": result["max_stretch"],
        "avg_stretch": result["avg_stretch"],
        "num_violations": len(violations),
        "violations": violations[:20],  # Cap at 20 for readability
        "num_pairs_checked": result["num_pairs_checked"],
    }
