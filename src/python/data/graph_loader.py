"""
graph_loader.py — Unified Graph Loader
=======================================
Handles loading graphs from:
  1. SNAP datasets (edge list format)
  2. Synthetic generators (Erdős–Rényi, Grid, Barabási-Albert)
  3. OpenStreetMap road networks (via osmnx)

All outputs are normalized Graph objects with contiguous 0-indexed node IDs.

Part of t-Spanner project — Person A (Implementation & Engineering)
"""

import os
import gzip
import json
import random
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from src.python.spanner.graph import Graph

logger = logging.getLogger(__name__)


# ─── Data directory paths ─────────────────────────────────────
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
RESULTS_DIR = DATA_DIR / "results"
FIGURES_DIR = DATA_DIR / "figures"


def ensure_dirs():
    """Create data directory structure."""
    for d in [RAW_DIR, PROCESSED_DIR, RESULTS_DIR, FIGURES_DIR]:
        d.mkdir(parents=True, exist_ok=True)


class GraphLoader:
    """
    Unified graph loader.
    
    Usage:
        loader = GraphLoader()
        
        # SNAP datasets
        g = loader.load_snap("ego-Facebook")
        g = loader.load_snap("roadNet-CA")
        
        # Synthetic
        g = loader.generate_erdos_renyi(n=1000, p=0.01)
        g = loader.generate_grid(rows=50, cols=50)
        g = loader.generate_barabasi_albert(n=1000, m=3)
        
        # OpenStreetMap
        g = loader.load_osm_city("Hyderabad, India", radius=3000)
    """
    
    # Known SNAP datasets with metadata
    SNAP_DATASETS = {
        "ego-Facebook": {
            "url": "https://snap.stanford.edu/data/facebook_combined.txt.gz",
            "filename": "facebook_combined.txt.gz",
            "description": "Social network (scale-free), ~4K nodes, ~88K edges",
            "directed": False,
        },
        "roadNet-CA": {
            "url": "https://snap.stanford.edu/data/roadNet-CA.txt.gz",
            "filename": "roadNet-CA.txt.gz",
            "description": "California road network (grid-like), ~2M nodes, ~2.8M edges",
            "directed": False,
        },
        "com-LiveJournal": {
            "url": "https://snap.stanford.edu/data/bigdata/communities/com-lj.ungraph.txt.gz",
            "filename": "com-lj.ungraph.txt.gz",
            "description": "LiveJournal social network, ~4M nodes, ~34M edges",
            "directed": False,
        },
    }

    def __init__(self):
        ensure_dirs()

    # ─── SNAP Dataset Loading ─────────────────────────────────

    def load_snap(
        self, 
        name: str, 
        max_nodes: Optional[int] = None
    ) -> Graph:
        """
        Load a SNAP dataset. Downloads if not cached.
        
        Parameters
        ----------
        name : str
            Dataset name (e.g., "ego-Facebook", "roadNet-CA")
        max_nodes : int, optional
            If set, extract subgraph of first max_nodes nodes only.
        """
        if name not in self.SNAP_DATASETS:
            raise ValueError(f"Unknown SNAP dataset: {name}. "
                           f"Available: {list(self.SNAP_DATASETS.keys())}")
        
        meta = self.SNAP_DATASETS[name]
        filepath = RAW_DIR / meta["filename"]
        
        # Check if already downloaded
        if not filepath.exists():
            logger.info(f"SNAP dataset {name} not found at {filepath}")
            logger.info(f"Please run download_snap.py first, or download from: {meta['url']}")
            raise FileNotFoundError(
                f"Dataset not found: {filepath}\n"
                f"Run: python src/python/data/download_snap.py --dataset {name}\n"
                f"Or download manually from: {meta['url']}"
            )
        
        logger.info(f"Loading SNAP dataset: {name} from {filepath}")
        g = self._parse_snap_file(filepath)
        
        if max_nodes is not None and g.num_nodes > max_nodes:
            logger.info(f"Extracting subgraph with {max_nodes} nodes from {g.num_nodes}")
            # Take first max_nodes nodes (sorted by ID)
            nodes = sorted(g.nodes)[:max_nodes]
            g = g.subgraph(set(nodes))
        
        # Normalize and get LCC
        g = g.largest_connected_component()
        g, mapping = g.normalize_node_ids()
        
        logger.info(f"Loaded {name}: {g.info()}")
        return g

    def _parse_snap_file(self, filepath: Path) -> Graph:
        """Parse SNAP edge list format (possibly gzipped)."""
        g = Graph()
        
        open_fn = gzip.open if str(filepath).endswith('.gz') else open
        mode = 'rt' if str(filepath).endswith('.gz') else 'r'
        
        with open_fn(filepath, mode, encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#') or line.startswith('%'):
                    continue
                parts = line.split()
                if len(parts) >= 2:
                    try:
                        u, v = int(parts[0]), int(parts[1])
                        w = float(parts[2]) if len(parts) > 2 else 1.0
                        if u != v:  # Skip self-loops
                            g.add_edge(u, v, w)
                    except ValueError:
                        continue
        
        return g

    def load_edge_list_file(self, filepath: str, weighted: bool = False) -> Graph:
        """Load any edge list file."""
        with open(filepath, 'r') as f:
            text = f.read()
        g = Graph.from_edge_list(text, weighted=weighted)
        g = g.largest_connected_component()
        g, _ = g.normalize_node_ids()
        return g

    # ─── Synthetic Graph Generators ───────────────────────────

    def generate_erdos_renyi(
        self, n: int = 1000, p: float = 0.01, seed: Optional[int] = None
    ) -> Graph:
        """
        Generate Erdős–Rényi random graph G(n, p).
        
        Each edge exists independently with probability p.
        Expected edges: n(n-1)/2 · p
        
        Properties:
        - Near-uniform degree distribution
        - Stretch values close to theoretical (2k-1) bound
        - Good baseline for testing algorithm correctness
        """
        if seed is not None:
            random.seed(seed)
        
        try:
            import networkx as nx
            nx_g = nx.erdos_renyi_graph(n, p, seed=seed)
            g = Graph.from_networkx(nx_g)
        except ImportError:
            # Fallback: manual generation
            g = Graph()
            for i in range(n):
                g.add_node(i)
            for i in range(n):
                for j in range(i + 1, n):
                    if random.random() < p:
                        g.add_edge(i, j, 1.0)
        
        g = g.largest_connected_component()
        g, _ = g.normalize_node_ids()
        logger.info(f"Generated Erdős–Rényi G({n}, {p}): {g.info()}")
        return g

    def generate_grid(self, rows: int = 50, cols: int = 50) -> Graph:
        """
        Generate grid graph G_{rows × cols}.
        
        Properties:
        - High diameter (rows + cols - 2)
        - Regular degree (2-4 depending on position)
        - Stretch hits theoretical maximum more often
        - Spanner is least sparse (needs more edges for long paths)
        - Relevant for: sensor networks, VLSI design
        """
        try:
            import networkx as nx
            nx_g = nx.grid_2d_graph(rows, cols)
            # NetworkX grid uses (row, col) tuples as node IDs — convert to ints
            mapping = {}
            g = Graph()
            for i, node in enumerate(sorted(nx_g.nodes())):
                mapping[node] = i
            for u, v in nx_g.edges():
                g.add_edge(mapping[u], mapping[v], 1.0)
        except ImportError:
            g = Graph()
            for r in range(rows):
                for c in range(cols):
                    node = r * cols + c
                    g.add_node(node)
                    if c + 1 < cols:
                        g.add_edge(node, node + 1, 1.0)
                    if r + 1 < rows:
                        g.add_edge(node, node + cols, 1.0)
        
        logger.info(f"Generated Grid({rows}x{cols}): {g.info()}")
        return g

    def generate_barabasi_albert(
        self, n: int = 1000, m: int = 3, seed: Optional[int] = None
    ) -> Graph:
        """
        Generate Barabási-Albert scale-free graph.
        
        Each new node attaches to m existing nodes with probability proportional
        to their degree (preferential attachment).
        
        Properties:
        - Power-law degree distribution
        - High-degree hubs get into clusters early → spanner very sparse around hubs
        - Relevant for: social networks, the internet, citation networks
        """
        try:
            import networkx as nx
            nx_g = nx.barabasi_albert_graph(n, m, seed=seed)
            g = Graph.from_networkx(nx_g)
        except ImportError:
            raise ImportError("NetworkX required for Barabási-Albert generation")
        
        g = g.largest_connected_component()
        g, _ = g.normalize_node_ids()
        logger.info(f"Generated Barabási-Albert({n}, {m}): {g.info()}")
        return g

    def generate_watts_strogatz(
        self, n: int = 1000, k: int = 6, p: float = 0.1, seed: Optional[int] = None
    ) -> Graph:
        """
        Generate Watts-Strogatz small-world graph.
        
        Properties:
        - High clustering coefficient
        - Low diameter (small-world property)
        - Interesting spanner behavior: clusters are "natural"
        """
        try:
            import networkx as nx
            nx_g = nx.watts_strogatz_graph(n, k, p, seed=seed)
            g = Graph.from_networkx(nx_g)
        except ImportError:
            raise ImportError("NetworkX required for Watts-Strogatz generation")
        
        g = g.largest_connected_component()
        g, _ = g.normalize_node_ids()
        logger.info(f"Generated Watts-Strogatz({n}, {k}, {p}): {g.info()}")
        return g

    # ─── OpenStreetMap / Road Network ─────────────────────────

    def load_osm_city(
        self,
        city: str = "Hyderabad, India",
        radius: int = 3000,
        max_nodes: int = 5000,
    ) -> Graph:
        """
        Load road network from OpenStreetMap using osmnx.
        
        Parameters
        ----------
        city : str
            City name for geocoding.
        radius : int
            Radius in meters around city center.
        max_nodes : int
            Max nodes to extract.
        """
        try:
            import osmnx as ox
        except ImportError:
            logger.warning("osmnx not installed. Generating synthetic road-like graph instead.")
            return self._synthetic_road_network(max_nodes)
        
        logger.info(f"Downloading OSM data for {city} (radius={radius}m)...")
        
        try:
            # Download street network
            ox_graph = ox.graph_from_place(city, network_type='drive')
            
            # Simplify and convert to undirected
            ox_graph = ox.utils_graph.get_undirected(ox_graph)
            
            # Convert to our format
            g = Graph()
            node_map = {}
            for i, (node_id, data) in enumerate(ox_graph.nodes(data=True)):
                if i >= max_nodes:
                    break
                node_map[node_id] = i
            
            for u, v, data in ox_graph.edges(data=True):
                if u in node_map and v in node_map:
                    weight = data.get('length', 1.0)  # length in meters
                    g.add_edge(node_map[u], node_map[v], weight)
            
            g = g.largest_connected_component()
            g, _ = g.normalize_node_ids()
            
            logger.info(f"Loaded OSM {city}: {g.info()}")
            return g
            
        except Exception as e:
            logger.warning(f"OSM download failed: {e}. Using synthetic road network.")
            return self._synthetic_road_network(max_nodes)

    def _synthetic_road_network(self, n: int = 5000) -> Graph:
        """
        Generate a synthetic road-like network (planar, low degree).
        
        Uses a grid with random diagonal edges + perturbation.
        Approximates real road network characteristics.
        """
        import math
        
        side = int(math.sqrt(n))
        g = self.generate_grid(side, side)
        
        # Add ~10% random shortcut edges (simulates highways)
        nodes = sorted(g.nodes)
        num_shortcuts = int(len(nodes) * 0.1)
        for _ in range(num_shortcuts):
            u, v = random.sample(nodes, 2)
            if not g.has_edge(u, v):
                # Weight proportional to "distance" in grid
                w = abs(u - v) * 0.5  # Highways are faster
                g.add_edge(u, v, max(w, 1.0))
        
        logger.info(f"Generated synthetic road network: {g.info()}")
        return g

    # ─── Utility ──────────────────────────────────────────────

    def list_available(self) -> Dict:
        """List all available dataset sources."""
        return {
            "snap_datasets": {k: v["description"] for k, v in self.SNAP_DATASETS.items()},
            "synthetic": [
                "erdos_renyi(n, p)",
                "grid(rows, cols)",
                "barabasi_albert(n, m)",
                "watts_strogatz(n, k, p)",
            ],
            "osm": "load_osm_city(city, radius)",
        }


# ─── Quick-access functions ───────────────────────────────────

def load_test_graph(graph_type: str = "small_random", **kwargs) -> Graph:
    """
    Quick graph loading for testing and experiments.
    
    graph_type options:
        "small_random" — 100-node Erdős–Rényi
        "medium_random" — 1000-node Erdős–Rényi  
        "small_grid" — 10×10 grid
        "medium_grid" — 50×50 grid
        "small_scalefree" — 100-node Barabási-Albert
        "medium_scalefree" — 1000-node Barabási-Albert
    """
    loader = GraphLoader()
    
    presets = {
        "small_random": lambda: loader.generate_erdos_renyi(100, 0.1, **kwargs),
        "medium_random": lambda: loader.generate_erdos_renyi(1000, 0.01, **kwargs),
        "large_random": lambda: loader.generate_erdos_renyi(5000, 0.005, **kwargs),
        "small_grid": lambda: loader.generate_grid(10, 10),
        "medium_grid": lambda: loader.generate_grid(50, 50),
        "large_grid": lambda: loader.generate_grid(100, 100),
        "small_scalefree": lambda: loader.generate_barabasi_albert(100, 3, **kwargs),
        "medium_scalefree": lambda: loader.generate_barabasi_albert(1000, 3, **kwargs),
        "large_scalefree": lambda: loader.generate_barabasi_albert(5000, 3, **kwargs),
    }
    
    if graph_type not in presets:
        raise ValueError(f"Unknown graph type: {graph_type}. Available: {list(presets.keys())}")
    
    return presets[graph_type]()
