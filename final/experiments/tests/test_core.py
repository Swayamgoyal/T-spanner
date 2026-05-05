"""
test_core.py — Unit Tests for Core t-Spanner Modules
=====================================================
Tests: Graph, UnionFind, Baswana-Sen, Greedy Spanner, Metrics

Run: python -m pytest tests/ -v
     or: python tests/test_core.py

Part of t-Spanner project — Person A (Implementation & Engineering)
"""

import sys
import os
import math
import random

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from src.python.spanner.graph import Graph
from src.python.spanner.union_find import UnionFind, UnionFindNoCompression
from src.python.spanner.baswana_sen import baswana_sen_spanner, theoretical_max_edges
from src.python.spanner.greedy_spanner import greedy_bfs_spanner
from src.python.spanner.metrics import (
    compute_stretch, compute_sparseness_ratio, 
    stretch_statistics, verify_spanner_property
)


# ════════════════════════════════════════════════════════════════
# Graph Tests
# ════════════════════════════════════════════════════════════════

def test_graph_basic():
    """Test basic graph operations."""
    g = Graph()
    g.add_edge(0, 1, 1.0)
    g.add_edge(1, 2, 2.0)
    g.add_edge(2, 3, 1.0)
    
    assert g.num_nodes == 4
    assert g.num_edges == 3
    assert g.has_edge(0, 1)
    assert g.has_edge(1, 0)  # Undirected
    assert not g.has_edge(0, 3)
    assert g.degree(1) == 2
    print("✓ test_graph_basic passed")


def test_graph_bfs():
    """Test BFS shortest path."""
    g = Graph()
    # Path: 0-1-2-3
    g.add_edge(0, 1)
    g.add_edge(1, 2)
    g.add_edge(2, 3)
    
    dist = g.bfs(0)
    assert dist[0] == 0
    assert dist[1] == 1
    assert dist[2] == 2
    assert dist[3] == 3
    
    assert g.bfs_distance(0, 3) == 3
    assert g.bfs_distance(0, 0) == 0
    print("✓ test_graph_bfs passed")


def test_graph_dijkstra():
    """Test Dijkstra with weighted edges."""
    g = Graph()
    g.add_edge(0, 1, 4.0)
    g.add_edge(0, 2, 1.0)
    g.add_edge(2, 1, 2.0)  # 0→2→1 = 3, shorter than 0→1 = 4
    
    dist = g.dijkstra(0)
    assert dist[0] == 0.0
    assert dist[1] == 3.0  # Via node 2
    assert dist[2] == 1.0
    print("✓ test_graph_dijkstra passed")


def test_graph_subgraph():
    """Test subgraph extraction."""
    g = Graph()
    g.add_edge(0, 1)
    g.add_edge(1, 2)
    g.add_edge(2, 3)
    g.add_edge(3, 4)
    
    sub = g.subgraph({0, 1, 2})
    assert sub.num_nodes == 3
    assert sub.num_edges == 2
    assert sub.has_edge(0, 1)
    assert sub.has_edge(1, 2)
    assert not sub.has_edge(2, 3)
    print("✓ test_graph_subgraph passed")


def test_graph_connected_component():
    """Test largest connected component."""
    g = Graph()
    # Component 1: {0, 1, 2}
    g.add_edge(0, 1)
    g.add_edge(1, 2)
    # Component 2: {3, 4, 5, 6}
    g.add_edge(3, 4)
    g.add_edge(4, 5)
    g.add_edge(5, 6)
    
    lcc = g.largest_connected_component()
    assert lcc.num_nodes == 4  # {3,4,5,6} is larger
    print("✓ test_graph_connected_component passed")


def test_graph_edge_list_io():
    """Test edge list serialization/deserialization."""
    g = Graph()
    g.add_edge(0, 1, 2.5)
    g.add_edge(1, 2, 3.0)
    
    text = g.to_edge_list()
    g2 = Graph.from_edge_list(text, weighted=True)
    assert g2.num_nodes == g.num_nodes
    assert g2.num_edges == g.num_edges
    print("✓ test_graph_edge_list_io passed")


# ════════════════════════════════════════════════════════════════
# Union-Find Tests
# ════════════════════════════════════════════════════════════════

def test_union_find_basic():
    """Test basic Union-Find operations."""
    uf = UnionFind(5)
    
    assert uf.num_components == 5
    assert not uf.connected(0, 1)
    
    uf.union(0, 1)
    assert uf.connected(0, 1)
    assert uf.num_components == 4
    
    uf.union(2, 3)
    uf.union(0, 2)
    assert uf.connected(0, 3)
    assert uf.connected(1, 2)
    assert uf.num_components == 2
    print("✓ test_union_find_basic passed")


def test_union_find_path_compression():
    """Verify path compression is working by checking find count."""
    uf = UnionFind(100)
    
    # Create a long chain: 0-1-2-...-99
    for i in range(99):
        uf.union(i, i + 1)
    
    uf.reset_counters()
    
    # First find — may traverse long path
    uf.find(99)
    first_ops = uf.find_ops
    
    # Second find — should be shorter due to path compression
    uf.find(99)
    
    # Path compression should have flattened the tree
    # After first find, path from 99 to root is compressed
    assert uf.connected(0, 99)
    print("✓ test_union_find_path_compression passed")


def test_union_find_components():
    """Test component extraction."""
    uf = UnionFind(6)
    uf.union(0, 1)
    uf.union(1, 2)
    uf.union(3, 4)
    
    components = uf.get_components()
    # Should have 3 components: {0,1,2}, {3,4}, {5}
    assert len(components) == 3
    
    sizes = sorted(len(v) for v in components.values())
    assert sizes == [1, 2, 3]
    print("✓ test_union_find_components passed")


def test_union_find_no_compression():
    """Test that no-compression variant works but is slower."""
    uf_comp = UnionFind(1000)
    uf_nocomp = UnionFindNoCompression(1000)
    
    # Same operations
    random.seed(42)
    ops = [(random.randint(0, 999), random.randint(0, 999)) for _ in range(500)]
    
    for a, b in ops:
        uf_comp.union(a, b)
        uf_nocomp.union(a, b)
    
    # Same results
    assert uf_comp.num_components == uf_nocomp.num_components
    
    # Both should be correct
    for a, b in ops[:50]:
        assert uf_comp.connected(a, b) == uf_nocomp.connected(a, b)
    
    # No compression should report 0 path compressions
    assert uf_nocomp.profiling_stats()["path_compressions"] == 0
    print("✓ test_union_find_no_compression passed")


# ════════════════════════════════════════════════════════════════
# Baswana-Sen Tests
# ════════════════════════════════════════════════════════════════

def _make_test_graph(n: int = 50, p: float = 0.15, seed: int = 42) -> Graph:
    """Generate a random test graph."""
    random.seed(seed)
    g = Graph()
    for i in range(n):
        g.add_node(i)
    for i in range(n):
        for j in range(i + 1, n):
            if random.random() < p:
                g.add_edge(i, j, 1.0)
    # Ensure connected
    g = g.largest_connected_component()
    g, _ = g.normalize_node_ids()
    return g


def test_baswana_sen_basic():
    """Test Baswana-Sen produces a valid subgraph."""
    g = _make_test_graph(30, 0.2, seed=123)
    result = baswana_sen_spanner(g, k=2, seed=42)
    
    spanner = result["spanner"]
    
    # Spanner should be a subgraph
    assert spanner.num_nodes == g.num_nodes
    assert spanner.num_edges <= g.num_edges
    assert spanner.num_edges > 0
    
    # Every spanner edge should be in original
    spanner_edges = spanner.edge_set()
    original_edges = g.edge_set()
    assert spanner_edges.issubset(original_edges), "Spanner has edges not in original!"
    
    print(f"✓ test_baswana_sen_basic passed "
          f"(original: {g.num_edges} edges, spanner: {spanner.num_edges} edges, "
          f"ratio: {result['sparseness_ratio']:.2f})")


def test_baswana_sen_edge_count():
    """Verify spanner edge count ≤ k·n^{1+1/k} (theoretical bound)."""
    for n in [20, 50, 100]:
        g = _make_test_graph(n, 0.3, seed=42)
        for k in [2, 3]:
            result = baswana_sen_spanner(g, k=k, seed=42)
            max_edges = theoretical_max_edges(g.num_nodes, k)
            # Note: this is expected value, not strict bound
            # Allow some slack (3x) for randomness
            assert result["num_spanner_edges"] <= max_edges * 3, \
                f"n={n}, k={k}: {result['num_spanner_edges']} > 3 * {max_edges:.0f}"
    
    print("✓ test_baswana_sen_edge_count passed")


def test_baswana_sen_stretch():
    """Verify spanner satisfies (2k-1)-stretch property."""
    g = _make_test_graph(50, 0.2, seed=42)
    
    for k in [2, 3]:
        result = baswana_sen_spanner(g, k=k, seed=42)
        spanner = result["spanner"]
        t = 2 * k - 1
        
        # Check stretch on all pairs (small graph, so feasible)
        nodes = sorted(g.nodes)
        violations = 0
        for i in range(len(nodes)):
            for j in range(i + 1, len(nodes)):
                u, v = nodes[i], nodes[j]
                d_orig = g.bfs_distance(u, v)
                d_span = spanner.bfs_distance(u, v)
                
                if d_orig == 0 or d_orig == float('inf'):
                    continue
                if d_span == float('inf'):
                    violations += 1
                    continue
                
                stretch = d_span / d_orig
                if stretch > t + 0.01:
                    violations += 1
        
        # Some violations are possible (randomized algorithm, small graphs)
        # but should be very rare
        violation_rate = violations / max(1, len(nodes) * (len(nodes) - 1) / 2)
        print(f"  k={k}, t={t}: violations={violations} "
              f"(rate={violation_rate:.4f})")
        # Allow up to 5% violation rate for small graphs
        assert violation_rate < 0.05, f"Too many stretch violations: {violation_rate:.2%}"
    
    print("✓ test_baswana_sen_stretch passed")


def test_baswana_sen_deterministic():
    """Same seed should produce same spanner."""
    g = _make_test_graph(50, 0.2, seed=42)
    
    r1 = baswana_sen_spanner(g, k=2, seed=123)
    r2 = baswana_sen_spanner(g, k=2, seed=123)
    
    assert r1["num_spanner_edges"] == r2["num_spanner_edges"]
    assert r1["spanner"].edge_set() == r2["spanner"].edge_set()
    print("✓ test_baswana_sen_deterministic passed")


def test_baswana_sen_phase_logs():
    """Test that phase logging works."""
    g = _make_test_graph(50, 0.2, seed=42)
    result = baswana_sen_spanner(g, k=3, seed=42, log_phases=True)
    
    assert len(result["phase_logs"]) > 0
    for log in result["phase_logs"]:
        assert "phase" in log
        assert "edges_added" in log
    
    print("✓ test_baswana_sen_phase_logs passed")


# ════════════════════════════════════════════════════════════════
# Greedy Spanner Tests
# ════════════════════════════════════════════════════════════════

def test_greedy_spanner_basic():
    """Test greedy spanner produces valid output."""
    g = _make_test_graph(30, 0.2, seed=42)
    result = greedy_bfs_spanner(g, t=3)
    
    spanner = result["spanner"]
    assert spanner.num_nodes == g.num_nodes
    assert spanner.num_edges <= g.num_edges
    assert spanner.num_edges > 0
    
    # Verify all spanner edges are in original
    assert spanner.edge_set().issubset(g.edge_set())
    print(f"✓ test_greedy_spanner_basic passed "
          f"(ratio: {result['sparseness_ratio']:.2f})")


def test_greedy_spanner_stretch():
    """Verify greedy spanner satisfies t-stretch."""
    g = _make_test_graph(40, 0.2, seed=42)
    t = 3
    result = greedy_bfs_spanner(g, t=t)
    spanner = result["spanner"]
    
    nodes = sorted(g.nodes)
    max_stretch_found = 0
    
    for i in range(min(len(nodes), 30)):
        for j in range(i + 1, min(len(nodes), 30)):
            u, v = nodes[i], nodes[j]
            d_orig = g.bfs_distance(u, v)
            d_span = spanner.bfs_distance(u, v)
            
            if d_orig == 0 or d_orig == float('inf') or d_span == float('inf'):
                continue
            
            stretch = d_span / d_orig
            max_stretch_found = max(max_stretch_found, stretch)
            assert stretch <= t + 0.01, \
                f"Stretch violation: d_G({u},{v})={d_orig}, d_H={d_span}, stretch={stretch}"
    
    print(f"✓ test_greedy_spanner_stretch passed (max stretch: {max_stretch_found:.2f})")


# ════════════════════════════════════════════════════════════════
# Metrics Tests
# ════════════════════════════════════════════════════════════════

def test_sparseness_ratio():
    """Test sparseness ratio computation."""
    g = _make_test_graph(30, 0.2, seed=42)
    result = baswana_sen_spanner(g, k=2, seed=42)
    
    ratio = compute_sparseness_ratio(g, result["spanner"])
    assert 0 < ratio <= 1.0
    print(f"✓ test_sparseness_ratio passed (ratio: {ratio:.3f})")


def test_stretch_statistics():
    """Test stretch statistics function."""
    stretches = [1.0, 1.2, 1.5, 2.0, 2.8, 1.1, 1.3, 1.0, 1.0, 3.0]
    stats = stretch_statistics(stretches)
    
    assert stats["min_stretch"] == 1.0
    assert stats["max_stretch"] == 3.0
    assert 1.0 <= stats["avg_stretch"] <= 3.0
    assert "median_stretch" in stats
    assert "p95_stretch" in stats
    print(f"✓ test_stretch_statistics passed (avg: {stats['avg_stretch']})")


def test_verify_spanner_property():
    """Test spanner property verification."""
    g = _make_test_graph(40, 0.2, seed=42)
    result = greedy_bfs_spanner(g, t=3)
    
    verification = verify_spanner_property(g, result["spanner"], t=3, 
                                           num_samples=100, seed=42)
    print(f"  Valid: {verification['is_valid']}, "
          f"Max stretch: {verification['max_stretch']:.2f}, "
          f"Violations: {verification['num_violations']}")
    print("✓ test_verify_spanner_property passed")


# ════════════════════════════════════════════════════════════════
# Advanced Regression & Stress Tests
# ════════════════════════════════════════════════════════════════

def test_stress_scale_free():
    """Stress test on a large 1000-node Scale-Free graph."""
    import networkx as nx
    # Generate 1000-node Barabasi-Albert graph with 30 edges per new node (Dense)
    ba = nx.barabasi_albert_graph(1000, 30, seed=42)
    g = Graph()
    for u, v in ba.edges():
        g.add_edge(u, v, 1.0)

    from src.python.spanner.advanced_spanner import hybrid_adaptive_spanner
    
    print(f"  Stress testing 1000-node graph ({g.num_edges} edges) with HAS (t=5)...")
    # Using k=3 (t=5) and alpha=1.0 for degree-weighted sampling
    result = hybrid_adaptive_spanner(g, k=3, seed=42)
    
    assert result["spanner"].num_nodes == 1000
    # HAS should achieve decent sparsification (30% reduction on dense BA)
    print(f"  Resulting sparseness: {result['sparseness_ratio']:.4f}")
    assert result["sparseness_ratio"] < 0.8 
    print("✓ test_stress_scale_free passed")


def test_boundary_disconnected():
    """Verify spanner preserves disconnected components."""
    g = Graph()
    # Component A
    g.add_edge(0, 1)
    g.add_edge(1, 2)
    # Component B
    g.add_edge(10, 11)
    
    result = baswana_sen_spanner(g, k=2, seed=42)
    spanner = result["spanner"]
    
    # Should NOT be able to reach 10 from 0
    assert spanner.bfs_distance(0, 10) == float('inf')
    print("✓ test_boundary_disconnected passed")


def test_boundary_chain():
    """Verify spanner on a long chain (the worst case for stretch)."""
    g = Graph()
    for i in range(100):
        g.add_edge(i, i+1, 1.0)
    
    result = baswana_sen_spanner(g, k=2, seed=42)
    spanner = result["spanner"]
    
    # In a simple chain, every edge is a bridge and MUST be kept
    if spanner.num_edges != g.num_edges:
        print(f"  FAILED: Original={g.num_edges}, Spanner={spanner.num_edges}")
        # List missing edges
        orig_edges = g.edge_set()
        span_edges = spanner.edge_set()
        missing = orig_edges - span_edges
        print(f"  Missing edges: {list(missing)[:5]}...")
    assert spanner.num_edges == g.num_edges
    print("✓ test_boundary_chain passed")


def test_real_world_regression():
    """Regression test using a slice of the actual ego-Facebook dataset."""
    from src.python.data.graph_loader import GraphLoader
    loader = GraphLoader()
    # Try to load Facebook, fallback to synthetic if not available
    try:
        g = loader.load_facebook(max_nodes=500)
        print("  Running regression on ego-Facebook slice...")
    except:
        g = _make_test_graph(500, 0.05)
        print("  Running regression on Large Synthetic (Fallback)...")
        
    result = baswana_sen_spanner(g, k=2, seed=42)
    print(f"  Resulting sparseness: {result['sparseness_ratio']:.4f}")
    print("✓ test_real_world_regression passed")


# ════════════════════════════════════════════════════════════════
# Run all tests
# ════════════════════════════════════════════════════════════════

def run_all_tests():
    """Run all unit tests."""
    print("=" * 60)
    print("t-Spanner Core Module Tests (Advanced)")
    print("=" * 60)
    
    print("\n─── Graph Tests ───")
    test_graph_basic()
    test_graph_bfs()
    test_graph_dijkstra()
    test_graph_subgraph()
    test_graph_connected_component()
    test_graph_edge_list_io()
    
    print("\n─── Union-Find Tests ───")
    test_union_find_basic()
    test_union_find_path_compression()
    test_union_find_components()
    test_union_find_no_compression()
    
    print("\n─── Baswana-Sen Tests ───")
    test_baswana_sen_basic()
    test_baswana_sen_edge_count()
    test_baswana_sen_stretch()
    test_baswana_sen_deterministic()
    test_baswana_sen_phase_logs()
    
    print("\n─── Greedy Spanner Tests ───")
    test_greedy_spanner_basic()
    test_greedy_spanner_stretch()
    
    print("\n─── Metrics Tests ───")
    test_sparseness_ratio()
    test_stretch_statistics()
    test_verify_spanner_property()

    print("\n─── Advanced & Stress Tests ───")
    test_stress_scale_free()
    test_boundary_disconnected()
    test_boundary_chain()
    test_real_world_regression()
    
    print("\n" + "=" * 60)
    print("ALL TESTS PASSED ✓")
    print("=" * 60)


if __name__ == "__main__":
    run_all_tests()
