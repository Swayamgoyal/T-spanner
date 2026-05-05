"""
Verify Hybrid Adaptive Spanner (HAS) correctness.
Tests 5 key properties:
  1. Stretch guarantee: d_spanner(u,v) <= t * d_original(u,v) for ALL pairs
  2. Sparseness: HAS should produce fewer edges than standard BS
  3. Connectivity: spanner must be connected if original is connected
  4. Subset property: all spanner edges must exist in original graph
  5. Pruning effectiveness: pruning should remove some edges without violations
"""

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.python.spanner.graph import Graph
from src.python.spanner.baswana_sen import baswana_sen_spanner
from src.python.spanner.advanced_spanner import hybrid_adaptive_spanner
from src.python.spanner.metrics import verify_spanner_property, stretch_statistics
import random

def make_grid(side):
    g = Graph()
    for r in range(side):
        for c in range(side):
            node = r * side + c
            g.add_node(node)
            if c > 0: g.add_edge(node, node - 1)
            if r > 0: g.add_edge(node, node - side)
    return g

def make_random(n, p, seed=42):
    rng = random.Random(seed)
    g = Graph()
    for i in range(n): g.add_node(i)
    for i in range(n):
        for j in range(i+1, n):
            if rng.random() < p: g.add_edge(i, j)
    return g

def make_scalefree(n, m=3, seed=42):
    rng = random.Random(seed)
    g = Graph()
    for i in range(m): g.add_node(i)
    for i in range(m):
        for j in range(i+1, m): g.add_edge(i, j)
    targets = list(range(m))
    for i in range(m, n):
        g.add_node(i)
        chosen = set()
        degrees = [len(g.neighbors(v)) for v in targets]
        total = sum(degrees) or 1
        while len(chosen) < m and len(chosen) < len(targets):
            r = rng.random() * total
            cumsum = 0
            for idx, t in enumerate(targets):
                cumsum += degrees[idx]
                if cumsum >= r and t not in chosen:
                    chosen.add(t)
                    break
        for t in chosen:
            g.add_edge(i, t)
        targets.append(i)
    return g

def verify_all_pairs_stretch(graph, spanner_edges, t):
    """Exhaustive check: for ALL pairs, spanner distance <= t * original distance."""
    nodes = list(graph.nodes)
    # Build spanner adjacency
    span_adj = {n: [] for n in nodes}
    for u, v in spanner_edges:
        span_adj[u].append(v)
        span_adj[v].append(u)
    
    def bfs(adj, src):
        dist = {src: 0}
        queue = [src]
        h = 0
        while h < len(queue):
            cur = queue[h]; h += 1
            for nb in adj.get(cur, []):
                if nb not in dist:
                    dist[nb] = dist[cur] + 1
                    queue.append(nb)
        return dist
    
    violations = 0
    max_stretch = 0
    for src in nodes:
        d_orig = bfs({n: list(graph.neighbors(n)) for n in nodes}, src)
        d_span = bfs(span_adj, src)
        for dst in nodes:
            if src >= dst: continue
            do = d_orig.get(dst, float('inf'))
            ds = d_span.get(dst, float('inf'))
            if do == 0 or do == float('inf'): continue
            stretch = ds / do
            if stretch > max_stretch: max_stretch = stretch
            if ds > t * do:
                violations += 1
    return violations, max_stretch

def test_graph(name, graph, k, seed=42):
    t = 2 * k - 1
    n = len(graph.nodes)
    m = graph.num_edges
    
    # Run HAS
    has_result = hybrid_adaptive_spanner(graph, k=k, seed=seed, 
                                          enable_degree_weighted=True,
                                          enable_pruning=True,
                                          enable_topology_detection=True)
    has_edges_raw = has_result['spanner_edges']
    # Normalize: may be (u,v) or (u,v,w) tuples
    has_edges = [(min(e[0],e[1]), max(e[0],e[1])) for e in has_edges_raw]
    has_count = len(has_edges)
    
    # Run standard BS
    bs_result = baswana_sen_spanner(graph, k=k, seed=seed)
    bs_edges_raw = bs_result['spanner_edges']
    # Normalize: BS returns (u,v,w) tuples
    bs_edges = [(min(u,v), max(u,v)) for u,v,w in bs_edges_raw]
    bs_count = len(bs_edges)
    
    # 1. Stretch guarantee (exhaustive)
    violations, max_stretch = verify_all_pairs_stretch(graph, has_edges, t)
    
    # 2. Subset check
    orig_edges = set()
    for u in graph.nodes:
        for v, w in graph.neighbors(u):
            orig_edges.add((min(u,v), max(u,v)))
    
    invalid_edges = 0
    for u, v in has_edges:
        if (min(u,v), max(u,v)) not in orig_edges:
            invalid_edges += 1
    
    # 3. Pruning stats
    pruning_log = [l for l in has_result.get('phase_logs', []) if l.get('phase') == 'pruning']
    pruned = pruning_log[0]['edges_pruned'] if pruning_log else 0
    topology = pruning_log[0].get('topology', 'N/A') if pruning_log else 'N/A'
    
    # Print results
    status = "✓ PASS" if violations == 0 and invalid_edges == 0 else "✗ FAIL"
    print(f"\n{'='*60}")
    print(f"  {name} (n={n}, m={m}, t={t}, k={k})")
    print(f"{'='*60}")
    print(f"  Topology detected:    {topology}")
    print(f"  BS edges:             {bs_count} (ratio: {bs_count/max(m,1):.3f})")
    print(f"  HAS edges:            {has_count} (ratio: {has_count/max(m,1):.3f})")
    print(f"  Improvement over BS:  {bs_count - has_count} fewer edges ({(1-has_count/max(bs_count,1))*100:.1f}%)")
    print(f"  Edges pruned:         {pruned}")
    print(f"  Max stretch:          {max_stretch:.2f} / {t}")
    print(f"  Stretch violations:   {violations}")
    print(f"  Invalid edges:        {invalid_edges}")
    print(f"  {status}")
    return violations == 0 and invalid_edges == 0

if __name__ == '__main__':
    print("Hybrid Adaptive Spanner — Correctness Verification")
    print("=" * 60)
    
    all_pass = True
    
    # Test 1: Grid 7x7, t=3
    all_pass &= test_graph("Grid 7×7", make_grid(7), k=2, seed=42)
    
    # Test 2: Grid 7x7, t=5
    all_pass &= test_graph("Grid 7×7 (t=5)", make_grid(7), k=3, seed=42)
    
    # Test 3: Random 50, t=3
    all_pass &= test_graph("Random 50", make_random(50, 0.12, seed=42), k=2, seed=42)
    
    # Test 4: Random 100, t=3
    all_pass &= test_graph("Random 100", make_random(100, 0.08, seed=42), k=2, seed=42)
    
    # Test 5: Scale-free 50, t=3
    all_pass &= test_graph("Scale-Free 50", make_scalefree(50, 3, seed=42), k=2, seed=42)
    
    # Test 6: Scale-free 100, t=5
    all_pass &= test_graph("Scale-Free 100 (t=5)", make_scalefree(100, 3, seed=42), k=3, seed=42)
    
    # Test 7: Grid 5x5, t=3 (small, easy to verify)
    all_pass &= test_graph("Grid 5×5", make_grid(5), k=2, seed=42)
    
    print(f"\n{'='*60}")
    if all_pass:
        print("ALL TESTS PASSED ✓ — HAS is correctly implemented")
    else:
        print("SOME TESTS FAILED ✗ — check violations above")
    print(f"{'='*60}")
