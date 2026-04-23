# Chapter 7: Topology-Specific Behavior Analysis

This chapter interprets Person A's experimental data through the lens of graph theory, explaining *why* spanner results differ by topology.

---

## Topology Report Card 1: Scale-Free Networks (Barabási-Albert)

### Structural Profile
- **Degree Distribution**: Power-law $P(k) \sim k^{-\gamma}$ ($\gamma \approx 3$ for BA model)
- **Diameter**: Ultra-small-world ($D \sim \ln \ln n$)
- **Expansion**: High; no significant bottlenecks except hubs
- **Clustering Coefficient**: Moderate (~0.01 for BA)

### Experimental Results (from Person A's data)

| Metric | t=3 (BS) | t=3 (Greedy) | t=5 (Greedy) | t=7 (Greedy) |
|:-------|:---------|:-------------|:-------------|:-------------|
| Sparseness | 0.998 | 0.777 | 0.406 | 0.334 |
| Avg Stretch | 1.0 | 1.097 | 1.301 | 1.347 |
| Max Stretch | 1.0 | 2.0 | 2.5 | 2.5 |

### Why This Happens
1. **Hub Capture**: High-degree hubs (degree > 100) are almost certainly adjacent to a sampled cluster center. A single hub sampled as a center "captures" hundreds of nodes in Phase 1.
2. **Shortcut Paths**: The ultra-small diameter means most node pairs are within 3-4 hops. Even aggressive pruning rarely increases stretch beyond 1.1.
3. **Redundancy**: Most edges are "redundant" for connectivity — removing 60-70% barely affects reachability because hubs provide alternative paths.

### HAS Improvement
| BS Edges | HAS Edges | Improvement |
|:---------|:----------|:-----------|
| 2,985 (t=3) | 2,351 | **-21.2%** |
| 2,991 (t=5) | 1,626 | **-45.6%** |

The degree-weighted sampling in HAS naturally prioritizes hubs, aligning the spanner with the graph's core hierarchy.

### Use Case Connection
Scale-free → **Social network indexing**: Facebook, LinkedIn. Spanners enable approximate distance oracles for friend recommendation and influence propagation.

---

## Topology Report Card 2: Road Networks (Grid-like / Planar)

### Structural Profile
- **Topology**: Near-planar, grid-like but irregular
- **Degree Distribution**: Very narrow; most nodes have degree 2, 3, or 4 (intersections)
- **Diameter**: Very large ($D \sim \sqrt{n}$ or higher)
- **Expansion**: Low; many cut-sets and bottlenecks (rivers, mountains)

### Experimental Results (Grid 30×30 as proxy)

| Metric | t=3 (BS) | t=3 (Greedy) | t=5 (Greedy) | t=7 (Greedy) |
|:-------|:---------|:-------------|:-------------|:-------------|
| Sparseness | 1.0 | 0.758 | 0.672 | 0.637 |
| Avg Stretch | 1.0 | 1.004 | 1.016 | 1.011 |
| Max Stretch | 1.0 | 1.25 | 2.0 | 1.286 |

### Why This Happens
1. **No Hubs**: Without high-degree nodes, clusters are small and localized (geometric disks). Sampling $n^{-1/k}$ centers creates many "holes" — unclustered nodes that must add all their edges.
2. **Low Redundancy**: Planar graphs have at most $3n - 6$ edges. Each edge is more "critical" for connectivity than in a dense graph. Removing even a few edges can force long detours.
3. **High Diameter**: Long paths mean the stretch guarantee is harder to maintain. An edge on a 50-hop path that gets removed forces a detour that may hit the $(2k-1)$ stretch limit.
4. **Baswana-Sen Conservatism**: BS retains 100% of grid edges at all $t$ values because the conservative sampling can't prune edges without risking stretch violations.

### HAS Improvement
| BS Edges | HAS Edges | Improvement |
|:---------|:----------|:-----------|
| 1,740 (t=3) | 1,202 | **-30.9%** |
| 1,740 (t=5) | 1,081 | **-37.9%** |

HAS's greedy pruning phase can identify and remove edges that BS conservatively keeps. This is where HAS provides the most value — on topologies where BS is too cautious.

### Use Case Connection
Grid/Road → **Navigation systems**: GPS, Google Maps. Spanners enable memory-efficient routing with bounded route stretch.

---

## Topology Report Card 3: Erdős-Rényi Random Graphs

### Structural Profile
- **Topology**: Uniformly random edges
- **Degree Distribution**: Poisson/Binomial; most nodes have degree close to average $\langle k \rangle$
- **Diameter**: Small ($D \sim \ln n / \ln \langle k \rangle$)
- **Expansion**: Very high; $G(n,p)$ is the archetypal expander

### Experimental Results

| Metric | t=3 (BS) | t=3 (Greedy) | t=5 (Greedy) | t=7 (Greedy) |
|:-------|:---------|:-------------|:-------------|:-------------|
| Sparseness | 0.9998 | 0.841 | 0.475 | 0.258 |
| Avg Stretch | 1.003 | 1.083 | 1.337 | 1.812 |
| Max Stretch | 1.333 | 1.667 | 2.0 | 7.0 |

### Why This Happens
1. **Uniform Clustering**: Degree uniformity → sampling is equally likely for all nodes → clusters are roughly uniform in size.
2. **High Expansion**: Many redundant paths between any two nodes → massive edge pruning is possible. Greedy achieves 74% pruning at $t=7$.
3. **Theoretical Alignment**: ER graphs most closely match the "average-case" analysis of Baswana-Sen. The sparseness follows the theoretical $O(n^{1+1/k})$ bound most precisely.
4. **Max Stretch at $t=7$**: The max stretch of 7.0 (exactly $2k-1$ for $k=4$) confirms that the theoretical worst-case is achievable even on random graphs.

### HAS Improvement
| BS Edges | HAS Edges | Improvement |
|:---------|:----------|:-----------|
| 4,984 (t=3) | 4,138 | **-17.0%** |
| 4,985 (t=5) | 2,534 | **-49.2%** |

### Use Case Connection
Random → **Benchmark/baseline**: ER graphs serve as the theoretical reference point against which all topology-specific behavior is measured.

---

## Topology Report Card 4: Small-World Networks (Watts-Strogatz)

### Structural Profile
- **Topology**: Ring lattice with random rewired edges
- **Degree Distribution**: Near-uniform (regular ring + random shortcuts)
- **Diameter**: Small ($D \sim \ln n$) due to shortcuts
- **Clustering Coefficient**: High (~0.5 for WS with low rewiring probability)

### Experimental Results

| Metric | t=3 (BS) | t=3 (Greedy) | t=5 (Greedy) | t=7 (Greedy) |
|:-------|:---------|:-------------|:-------------|:-------------|
| Sparseness | 0.999 | 0.526 | 0.460 | 0.432 |
| Avg Stretch | 1.0 | 1.116 | 1.190 | 1.271 |
| Max Stretch | 1.0 | 1.5 | 1.75 | 2.0 |

### Why This Happens
1. **Shortcut Criticality**: The random rewired edges create "shortcuts" that dramatically reduce diameter. These shortcuts are **critical** for low stretch — removing them would increase average distance significantly.
2. **Local Clustering**: The high clustering coefficient means many edges are "within triangles." Greedy can prune these safely because alternative paths through the triangle exist.
3. **Balanced Behavior**: Small-world networks sit between grid-like regularity and scale-free heterogeneity. Spanner behavior is correspondingly moderate.

### HAS Improvement
| BS Edges | HAS Edges | Improvement |
|:---------|:----------|:-----------|
| 2,998 (t=3) | 1,883 | **-37.2%** |
| 3,000 (t=5) | 1,808 | **-39.7%** |

The high clustering coefficient means HAS's pruning phase finds many redundant edges within clusters, achieving 37-40% improvement.

### Use Case Connection
Small-world → **Social network routing**, **brain connectivity modeling**: The "six degrees of separation" phenomenon is a spanner property of social networks.

---

## Summary Comparison Table

| Metric | Scale-Free | Road Network | Random (ER) | Small-World |
|:-------|:----------|:-------------|:-----------|:-----------|
| **Dominant Feature** | Hubs (Power-law) | Planarity/Bottlenecks | High Expansion | Shortcuts + Clustering |
| **Clustering Efficiency** | High (big clusters) | Low (small clusters) | Uniform | Moderate |
| **BS Sparseness (t=3)** | 0.998 | 1.0 | 0.9998 | 0.999 |
| **Greedy Sparseness (t=3)** | 0.777 | 0.758 | 0.841 | 0.526 |
| **HAS Improvement (t=3)** | -21.2% | -30.9% | -17.0% | -37.2% |
| **Vulnerability** | Hub failure | Cut-set failure | Robust | Shortcut loss |
| **Fault Tolerance (20%)** | 68.3% connected | ~100% connected | 100% connected | ~90% connected |
| **Best Use Case** | Social indexing | Navigation | Benchmark | Brain/Social models |

---

## Scientific Interpretation

**Key Finding**: Baswana-Sen is most "efficient" on **scale-free topologies** because randomized sampling naturally favors high-degree nodes critical for low-stretch connectivity. It is most "challenged" by **road/grid networks** where the lack of hubs forces conservative edge retention.

**The HAS Innovation**: Our Hybrid Adaptive Spanner provides the greatest benefit on topologies where standard BS is most conservative: **grids** (-30.9%), **small-world** (-37.2%). By combining topology detection with greedy pruning, HAS adapts to each topology's unique structure.

**Pareto Insight**: On the sparseness-vs-stretch Pareto frontier, each topology occupies a different region:
- Scale-free: **top-left** (very sparse, low stretch) — the "easy" regime
- Road: **bottom-right** (dense, but still low stretch) — the "challenging" regime
- ER/Small-world: **middle** — moderate sparseness and stretch
