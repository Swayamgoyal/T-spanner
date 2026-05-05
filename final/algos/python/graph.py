"""
graph.py — Weighted/Unweighted Graph Abstraction
=================================================
Adjacency list representation for O(n+m) memory.
Provides BFS, Dijkstra, subgraph extraction, and export utilities.

Part of t-Spanner project — Person A (Implementation & Engineering)
"""

import heapq
import random
import sys
from collections import defaultdict, deque
from typing import Dict, List, Optional, Set, Tuple


class Graph:
    """
    Weighted undirected graph using adjacency list representation.
    
    Internal storage: dict[int, list[tuple[int, float]]]
    - Keys are node IDs (integers)
    - Values are lists of (neighbor_id, weight) tuples
    
    Why adjacency list over adjacency matrix:
    - Memory: O(n + m) vs O(n²) — critical for sparse graphs (spanners are sparse)
    - Iteration: O(deg(v)) to iterate neighbors vs O(n) 
    - For road networks with ~2M nodes, matrix would need ~4TB; list needs ~50MB
    """

    def __init__(self, directed: bool = False):
        self._adj: Dict[int, List[Tuple[int, float]]] = defaultdict(list)
        self._nodes: Set[int] = set()
        self._edge_count: int = 0
        self._directed: bool = directed

    # ─── Construction ──────────────────────────────────────────────

    def add_node(self, u: int) -> None:
        """Add a node (no-op if already exists)."""
        self._nodes.add(u)
        if u not in self._adj:
            self._adj[u] = []

    def add_edge(self, u: int, v: int, weight: float = 1.0) -> None:
        """Add an undirected edge (u, v) with given weight."""
        self._nodes.add(u)
        self._nodes.add(v)
        self._adj[u].append((v, weight))
        if not self._directed:
            self._adj[v].append((u, weight))
        self._edge_count += 1

    def add_edges_from(self, edges: List[Tuple[int, int, float]]) -> None:
        """Add multiple edges. Each edge is (u, v, weight)."""
        for u, v, w in edges:
            self.add_edge(u, v, w)

    # ─── Properties ────────────────────────────────────────────────

    @property
    def num_nodes(self) -> int:
        return len(self._nodes)

    @property
    def num_edges(self) -> int:
        return self._edge_count

    @property
    def nodes(self) -> Set[int]:
        return self._nodes.copy()

    @property
    def density(self) -> float:
        """Graph density: |E| / (|V| choose 2)."""
        n = self.num_nodes
        if n < 2:
            return 0.0
        max_edges = n * (n - 1) / 2
        return self._edge_count / max_edges

    @property
    def avg_degree(self) -> float:
        """Average degree of the graph."""
        if self.num_nodes == 0:
            return 0.0
        return 2 * self._edge_count / self.num_nodes

    # ─── Access ────────────────────────────────────────────────────

    def neighbors(self, u: int) -> List[Tuple[int, float]]:
        """Return list of (neighbor, weight) for node u."""
        return self._adj.get(u, [])

    def degree(self, u: int) -> int:
        """Return degree of node u."""
        return len(self._adj.get(u, []))

    def has_node(self, u: int) -> bool:
        return u in self._nodes

    def has_edge(self, u: int, v: int) -> bool:
        """Check if edge (u,v) exists."""
        return any(nbr == v for nbr, _ in self._adj.get(u, []))

    def get_edge_weight(self, u: int, v: int) -> Optional[float]:
        """Return weight of edge (u,v) or None."""
        for nbr, w in self._adj.get(u, []):
            if nbr == v:
                return w
        return None

    def edges(self) -> List[Tuple[int, int, float]]:
        """Return all edges as list of (u, v, weight). Each edge appears once."""
        seen = set()
        result = []
        for u in self._adj:
            for v, w in self._adj[u]:
                edge_key = (min(u, v), max(u, v))
                if edge_key not in seen:
                    seen.add(edge_key)
                    result.append((u, v, w))
        return result

    def edge_set(self) -> Set[Tuple[int, int]]:
        """Return set of edges as (min_id, max_id) pairs."""
        result = set()
        for u in self._adj:
            for v, _ in self._adj[u]:
                result.add((min(u, v), max(u, v)))
        return result

    # ─── Graph Algorithms ──────────────────────────────────────────

    def bfs(self, source: int) -> Dict[int, int]:
        """
        BFS from source. Returns dict of {node: distance}.
        Distance is in hops (unweighted).
        
        Why BFS and not DFS for shortest-path/stretch checking:
        - BFS guarantees shortest unweighted path from source
        - DFS explores deep before wide → finds *a* path, not the shortest
        - For stretch verification d_H(u,v), we NEED the shortest path
        - Both are O(n + m), but BFS output is *correct* for our purpose
        - DFS would require post-processing or give wrong stretch values
        """
        dist = {source: 0}
        queue = deque([source])
        while queue:
            u = queue.popleft()
            for v, _ in self._adj.get(u, []):
                if v not in dist:
                    dist[v] = dist[u] + 1
                    queue.append(v)
        return dist

    def bfs_distance(self, source: int, target: int) -> float:
        """BFS distance from source to target. Returns float('inf') if unreachable."""
        if source == target:
            return 0
        dist = {source: 0}
        queue = deque([source])
        while queue:
            u = queue.popleft()
            for v, _ in self._adj.get(u, []):
                if v == target:
                    return dist[u] + 1
                if v not in dist:
                    dist[v] = dist[u] + 1
                    queue.append(v)
        return float('inf')

    def dijkstra(self, source: int) -> Dict[int, float]:
        """
        Dijkstra's shortest path from source. Returns dict of {node: distance}.
        Uses min-heap for O((n + m) log n) complexity.
        """
        dist = {source: 0.0}
        heap = [(0.0, source)]
        while heap:
            d, u = heapq.heappop(heap)
            if d > dist.get(u, float('inf')):
                continue
            for v, w in self._adj.get(u, []):
                nd = d + w
                if nd < dist.get(v, float('inf')):
                    dist[v] = nd
                    heapq.heappush(heap, (nd, v))
        return dist

    def dijkstra_distance(self, source: int, target: int) -> float:
        """Dijkstra distance from source to target. Returns float('inf') if unreachable."""
        if source == target:
            return 0.0
        dist = {source: 0.0}
        heap = [(0.0, source)]
        while heap:
            d, u = heapq.heappop(heap)
            if u == target:
                return d
            if d > dist.get(u, float('inf')):
                continue
            for v, w in self._adj.get(u, []):
                nd = d + w
                if nd < dist.get(v, float('inf')):
                    dist[v] = nd
                    heapq.heappush(heap, (nd, v))
        return float('inf')

    # ─── Graph Operations ──────────────────────────────────────────

    def subgraph(self, nodes: Set[int]) -> 'Graph':
        """Extract induced subgraph on given node set."""
        g = Graph(directed=self._directed)
        for u in nodes:
            g.add_node(u)
            for v, w in self._adj.get(u, []):
                if v in nodes and (self._directed or u < v):
                    g.add_edge(u, v, w)
        return g

    def largest_connected_component(self) -> 'Graph':
        """Extract the largest connected component."""
        visited = set()
        best_component = set()

        for start in self._nodes:
            if start in visited:
                continue
            component = set()
            queue = deque([start])
            while queue:
                u = queue.popleft()
                if u in component:
                    continue
                component.add(u)
                for v, _ in self._adj.get(u, []):
                    if v not in component:
                        queue.append(v)
            visited |= component
            if len(component) > len(best_component):
                best_component = component

        return self.subgraph(best_component)

    def remove_node(self, u: int) -> 'Graph':
        """Return a new graph with node u and all its edges removed."""
        remaining = self._nodes - {u}
        return self.subgraph(remaining)

    def remove_nodes(self, nodes_to_remove: Set[int]) -> 'Graph':
        """Return a new graph with given nodes removed."""
        remaining = self._nodes - nodes_to_remove
        return self.subgraph(remaining)

    # ─── Degree Analysis ───────────────────────────────────────────

    def degree_sequence(self) -> List[Tuple[int, int]]:
        """Return sorted list of (node, degree) pairs, descending by degree."""
        degs = [(u, len(self._adj.get(u, []))) for u in self._nodes]
        degs.sort(key=lambda x: -x[1])
        return degs

    def top_degree_nodes(self, fraction: float) -> Set[int]:
        """Return set of top-k% nodes by degree."""
        degs = self.degree_sequence()
        k = max(1, int(len(degs) * fraction))
        return {node for node, _ in degs[:k]}

    # ─── Utility ───────────────────────────────────────────────────

    def normalize_node_ids(self) -> Tuple['Graph', Dict[int, int]]:
        """
        Re-map node IDs to 0..n-1 contiguous integers.
        Returns (new_graph, mapping) where mapping[old_id] = new_id.
        """
        sorted_nodes = sorted(self._nodes)
        mapping = {old: new for new, old in enumerate(sorted_nodes)}
        g = Graph(directed=self._directed)
        for u, v, w in self.edges():
            g.add_edge(mapping[u], mapping[v], w)
        return g, mapping

    def memory_bytes(self) -> int:
        """Estimate memory usage in bytes."""
        size = sys.getsizeof(self._adj)
        for u in self._adj:
            size += sys.getsizeof(self._adj[u])
            for item in self._adj[u]:
                size += sys.getsizeof(item)
        size += sys.getsizeof(self._nodes)
        return size

    def info(self) -> Dict:
        """Return summary statistics."""
        return {
            "num_nodes": self.num_nodes,
            "num_edges": self.num_edges,
            "density": round(self.density, 6),
            "avg_degree": round(self.avg_degree, 2),
            "directed": self._directed,
            "memory_bytes": self.memory_bytes(),
        }

    # ─── I/O ───────────────────────────────────────────────────────

    def to_edge_list(self) -> str:
        """Export as edge list string (u v w per line)."""
        lines = []
        for u, v, w in self.edges():
            lines.append(f"{u} {v} {w}")
        return "\n".join(lines)

    @classmethod
    def from_edge_list(cls, text: str, weighted: bool = False) -> 'Graph':
        """Parse edge list from string. Lines: 'u v [w]'. Lines starting with # are comments."""
        g = cls()
        for line in text.strip().split('\n'):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.split()
            if len(parts) < 2:
                continue
            u, v = int(parts[0]), int(parts[1])
            w = float(parts[2]) if weighted and len(parts) > 2 else 1.0
            g.add_edge(u, v, w)
        return g

    @classmethod
    def from_networkx(cls, nx_graph) -> 'Graph':
        """Convert a NetworkX graph to our Graph representation."""
        g = cls()
        for u, v, data in nx_graph.edges(data=True):
            w = data.get('weight', data.get('length', 1.0))
            # Handle non-integer node IDs
            g.add_edge(u, v, float(w))
        return g

    def to_networkx(self):
        """Convert to NetworkX graph."""
        import networkx as nx
        G = nx.Graph()
        for u, v, w in self.edges():
            G.add_edge(u, v, weight=w)
        return G

    def __repr__(self) -> str:
        return f"Graph(nodes={self.num_nodes}, edges={self.num_edges}, density={self.density:.4f})"

    def __len__(self) -> int:
        return self.num_nodes
