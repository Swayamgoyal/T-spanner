"""
union_find.py — Disjoint Set Union (Union-Find) Data Structure
==============================================================
Two variants:
  1. UnionFind — with path compression + union-by-rank  → O(α(n)) per op ≈ O(1)
  2. UnionFindNoCompression — without path compression  → O(log n) worst case

We implement both to empirically benchmark the difference for Person B's analysis.

Why Union-Find for Baswana-Sen:
  - Cluster membership is the core tracking structure during each phase
  - We need: "which cluster does node v belong to?" → find(v)
  - We need: "merge clusters X and Y" → union(x, y)
  - Path compression makes repeated find() nearly constant time
  - Without it, find() can degrade to O(n) on skewed trees

Part of t-Spanner project — Person A (Implementation & Engineering)
"""

from typing import Dict, List, Optional, Set


class UnionFind:
    """
    Union-Find with path compression + union-by-rank.
    
    Amortized time per operation: O(α(n)) where α is the inverse Ackermann function.
    For all practical purposes, α(n) ≤ 4 for n up to 10^80, so this is effectively O(1).
    
    Space: O(n)
    """

    def __init__(self, n: int = 0):
        """Initialize with n elements (0 to n-1)."""
        self._parent: Dict[int, int] = {}
        self._rank: Dict[int, int] = {}
        self._size: Dict[int, int] = {}
        self._num_components: int = 0
        # Operation counters for profiling
        self.find_ops: int = 0
        self.union_ops: int = 0
        self.path_compressions: int = 0

        for i in range(n):
            self.make_set(i)

    def make_set(self, x: int) -> None:
        """Create a new singleton set containing x."""
        if x in self._parent:
            return
        self._parent[x] = x
        self._rank[x] = 0
        self._size[x] = 1
        self._num_components += 1

    def find(self, x: int) -> int:
        """
        Find the representative (root) of x's set.
        Uses path compression: all nodes on path to root are directly linked to root.
        
        Path compression effect:
        - First find: O(depth) — may be up to O(log n)
        - Subsequent finds on same path: O(1) — all nodes point to root
        - Amortized over m operations: O(m · α(n)) total
        """
        self.find_ops += 1
        if x not in self._parent:
            self.make_set(x)

        # Path compression: make every node point directly to root
        if self._parent[x] != x:
            self.path_compressions += 1
            self._parent[x] = self.find(self._parent[x])
        return self._parent[x]

    def union(self, x: int, y: int) -> bool:
        """
        Merge the sets containing x and y.
        Uses union-by-rank: shorter tree is attached under taller tree's root.
        Returns True if a merge happened (x and y were in different sets).
        
        Union-by-rank guarantees tree height ≤ log₂(n):
        - A tree of rank r has at least 2^r nodes
        - So rank ≤ log₂(n)
        - Combined with path compression → O(α(n)) amortized
        """
        self.union_ops += 1
        rx, ry = self.find(x), self.find(y)
        if rx == ry:
            return False

        # Attach smaller-rank tree under larger-rank root
        if self._rank[rx] < self._rank[ry]:
            rx, ry = ry, rx
        self._parent[ry] = rx
        self._size[rx] += self._size[ry]
        if self._rank[rx] == self._rank[ry]:
            self._rank[rx] += 1

        self._num_components -= 1
        return True

    def connected(self, x: int, y: int) -> bool:
        """Check if x and y are in the same set."""
        return self.find(x) == self.find(y)

    def component_size(self, x: int) -> int:
        """Return size of the component containing x."""
        return self._size[self.find(x)]

    @property
    def num_components(self) -> int:
        return self._num_components

    def get_components(self) -> Dict[int, Set[int]]:
        """Return dict mapping root → set of members."""
        components: Dict[int, Set[int]] = {}
        for x in self._parent:
            root = self.find(x)
            if root not in components:
                components[root] = set()
            components[root].add(x)
        return components

    def profiling_stats(self) -> Dict:
        """Return profiling statistics for benchmarking."""
        return {
            "find_operations": self.find_ops,
            "union_operations": self.union_ops,
            "path_compressions": self.path_compressions,
            "num_components": self._num_components,
            "num_elements": len(self._parent),
        }

    def reset_counters(self) -> None:
        """Reset profiling counters."""
        self.find_ops = 0
        self.union_ops = 0
        self.path_compressions = 0


class UnionFindNoCompression:
    """
    Union-Find WITHOUT path compression — only union-by-rank.
    
    This exists purely to benchmark the impact of path compression.
    
    Without path compression:
    - find() is O(log n) per call (due to union-by-rank keeping height ≤ log n)
    - But without union-by-rank AND without path compression, it could be O(n)
    
    Expected benchmark result:
    - For Baswana-Sen on 100K-node graph, this should be noticeably slower
    - The difference grows with graph size (more find operations = more wasted traversal)
    """

    def __init__(self, n: int = 0):
        self._parent: Dict[int, int] = {}
        self._rank: Dict[int, int] = {}
        self._size: Dict[int, int] = {}
        self._num_components: int = 0
        self.find_ops: int = 0
        self.union_ops: int = 0

        for i in range(n):
            self.make_set(i)

    def make_set(self, x: int) -> None:
        if x in self._parent:
            return
        self._parent[x] = x
        self._rank[x] = 0
        self._size[x] = 1
        self._num_components += 1

    def find(self, x: int) -> int:
        """
        Find root WITHOUT path compression.
        Walks up the tree every time — O(log n) with union-by-rank.
        """
        self.find_ops += 1
        if x not in self._parent:
            self.make_set(x)
        while self._parent[x] != x:
            x = self._parent[x]
        return x

    def union(self, x: int, y: int) -> bool:
        """Merge sets — same as UnionFind but find() doesn't compress."""
        self.union_ops += 1
        rx, ry = self.find(x), self.find(y)
        if rx == ry:
            return False
        if self._rank[rx] < self._rank[ry]:
            rx, ry = ry, rx
        self._parent[ry] = rx
        self._size[rx] += self._size[ry]
        if self._rank[rx] == self._rank[ry]:
            self._rank[rx] += 1
        self._num_components -= 1
        return True

    def connected(self, x: int, y: int) -> bool:
        return self.find(x) == self.find(y)

    def component_size(self, x: int) -> int:
        return self._size[self.find(x)]

    @property
    def num_components(self) -> int:
        return self._num_components

    def get_components(self) -> Dict[int, Set[int]]:
        components: Dict[int, Set[int]] = {}
        for x in self._parent:
            root = self.find(x)
            if root not in components:
                components[root] = set()
            components[root].add(x)
        return components

    def profiling_stats(self) -> Dict:
        return {
            "find_operations": self.find_ops,
            "union_operations": self.union_ops,
            "path_compressions": 0,  # None — that's the point
            "num_components": self._num_components,
            "num_elements": len(self._parent),
        }
