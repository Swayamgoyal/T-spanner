# t-Spanner: Baswana-Sen Algorithm — Complete Project Guide

> **Algorithm Engineering Project [Number 7]**  
> Build a subgraph (spanner) where distances are at most *t* times the original distances, using the Baswana-Sen randomized clustering algorithm.

---

## 📌 What Is This Project?

A **t-spanner** is a sparse subgraph H of a graph G where the shortest-path distance between any two nodes in H is at most **t times** their distance in G. The parameter *t* is called the **stretch factor**.

**Why it matters**: If Google Maps stored only a 3-spanner of the full road network, it would use significantly less memory with only slightly longer routes.

### What We Implemented

| Component | What It Does |
|-----------|-------------|
| **Baswana-Sen Algorithm** | The main algorithm — builds a (2k-1)-spanner in near-linear time O(k·m) using random clustering |
| **Greedy BFS Spanner** | Classical baseline algorithm for comparison — slower O(m·n) but produces sparser spanners |
| **Multi-Language Code** | Same algorithm in Python (readable) and C++ (fast) for cross-language comparison |
| **5 Experiment Scripts** | Scaling benchmarks, stretch analysis, fault tolerance, Hyderabad routing, seed sensitivity |
| **Interactive Visualizer** | Browser-based D3.js dashboard — upload a graph, slide t, watch the spanner thin out |
| **Streamlit Dashboard** | Python-based backup visualizer with side-by-side algorithm comparison |

---

## 🗂️ Complete File Map

```
iae/
│
├── BASE_PROJECT.TXT              # Original problem statement
├── project_content.txt           # Detailed project requirements
├── person_division.txt           # Person A / Person B task split
├── README.md                     # ← YOU ARE HERE
├── requirements.txt              # Python dependencies
├── run_all.py                    # One command to run ALL experiments
│
├── src/
│   ├── python/
│   │   ├── spanner/              # 🧠 CORE ALGORITHMS (Phase 1)
│   │   │   ├── __init__.py           # Package exports
│   │   │   ├── graph.py              # Graph class — adjacency list, BFS, Dijkstra
│   │   │   ├── union_find.py         # Union-Find (2 variants for benchmarking)
│   │   │   ├── baswana_sen.py        # ⭐ Baswana-Sen (2k-1)-spanner algorithm
│   │   │   ├── greedy_spanner.py     # Greedy BFS-based baseline spanner
│   │   │   └── metrics.py            # Stretch & sparseness computation
│   │   │
│   │   ├── data/                 # 📊 DATA PIPELINE (Phase 2)
│   │   │   ├── __init__.py
│   │   │   ├── graph_loader.py       # Unified loader: SNAP + synthetic + OSM
│   │   │   └── download_snap.py      # Downloads SNAP datasets from Stanford
│   │   │
│   │   └── experiments/          # 🔬 EXPERIMENTS (Phase 4)
│   │       ├── __init__.py
│   │       ├── scaling_benchmark.py  # Time complexity profiling
│   │       ├── stretch_experiment.py # Stretch factor across topologies & t-values
│   │       ├── fault_tolerance.py    # Node failure + repair heuristic
│   │       ├── routing_simulation.py # Hyderabad road network routing
│   │       └── seed_variance.py      # Random seed sensitivity (50 seeds)
│   │
│   └── cpp/                      # ⚡ C++ IMPLEMENTATION (Phase 3)
│       ├── baswana_sen.cpp           # C++ Baswana-Sen + Greedy (single file)
│       └── Makefile                  # Build: make all / make bench / make clean
│
├── viz/
│   ├── react-d3/                 # 🎨 INTERACTIVE VISUALIZER (Phase 5)
│   │   └── index.html                # Full D3.js dashboard (dark theme, animations)
│   │
│   └── streamlit/                # 📊 STREAMLIT DASHBOARD (Phase 5)
│       └── app.py                    # Python dashboard with matplotlib plots
│
├── tests/
│   └── test_core.py              # ✅ 20 unit tests for all core modules
│
└── data/                         # 📁 OUTPUT DIRECTORY (auto-created)
    ├── raw/                          # Downloaded SNAP dataset files
    ├── results/                      # Experiment CSVs and JSONs
    └── figures/                      # Generated plots (PNG + PDF)
```

---

## 🚀 How to Run Everything

### Step 1: Install Python Dependencies

```bash
pip install -r requirements.txt
```

Required packages: `networkx`, `matplotlib`, `numpy`, `scipy`, `tqdm`  
Optional: `streamlit`, `pyvis` (for Streamlit dashboard), `osmnx` (for real OSM maps)

### Step 2: Verify Core Algorithms Work

```bash
python -X utf8 tests/test_core.py
```

Expected output: **ALL 20 TESTS PASSED ✓**

### Step 3: Run Experiments

**Quick mode** (small graphs, ~20 seconds):
```bash
python run_all.py --quick
```

**Full mode** (large graphs, ~5-10 minutes):
```bash
python run_all.py --experiment all
```

**Individual experiments**:
```bash
python run_all.py -e scaling       # Performance: time vs graph size
python run_all.py -e stretch       # Stretch: across 4 topologies × 3 t-values
python run_all.py -e fault         # Fault tolerance: node deletions + repair
python run_all.py -e routing       # Routing: Hyderabad road network simulation
python run_all.py -e seeds         # Seed variance: 50 random seeds
```

### Step 4: Open the Interactive Visualizer

```bash
python -m http.server 8080 --directory viz/react-d3
```
Then open **http://localhost:8080** in your browser.

**Or** use the Streamlit dashboard:
```bash
streamlit run viz/streamlit/app.py
```

### Step 5: Download Real-World SNAP Datasets (Optional)

```bash
python src/python/data/download_snap.py --all
```

Downloads: ego-Facebook (4K nodes), roadNet-CA (2M nodes), com-LiveJournal (4M nodes)

### Step 6: Compile & Run C++ Version (Optional)

```bash
cd src/cpp
make all
echo "10 15" | ./spanner_cpp --algo baswana --k 2 --verify
```

---

## 🧠 How the Algorithms Work

### Baswana-Sen (2k-1)-Spanner — The Main Algorithm

**Input**: Graph G = (V, E), integer k ≥ 2  
**Output**: Subgraph H ⊆ G with stretch ≤ 2k-1

```
Phase 0: Every vertex is its own cluster
         Sampling probability p = n^(-1/k)

For each phase i = 1 to k-1:
  1. SAMPLE:  Each cluster center survives with probability p
  2. ATTACH:  Non-surviving vertices join nearest surviving cluster
              → Add attachment edge to spanner
  3. INTER:   Add lightest edge to each neighboring cluster
              → This ensures the stretch guarantee

Final: Unclustered vertices add ALL their remaining edges
```

**Why this is fast**: No BFS/Dijkstra needed! Just random sampling + local neighbor lookups = O(k·m) total.

**Key parameter**:
- k=2 → stretch ≤ 3 (3-spanner)  
- k=3 → stretch ≤ 5 (5-spanner)  
- k=4 → stretch ≤ 7 (7-spanner)

### Greedy BFS Spanner — The Baseline

```
1. Sort all edges by weight (ascending)
2. For each edge (u,v):
   - Run BFS in current spanner H
   - If d_H(u,v) > t × w(u,v), add (u,v) to H
3. Return H
```

**Why BFS, not DFS?**  
BFS finds the **shortest** path (needed for stretch verification). DFS finds *a* path but not necessarily the shortest — it could add unnecessary edges or miss violations.

---

## 📊 What Each Experiment Produces

### 1. Scaling Benchmark (`scaling_benchmark.py`)
**Question**: Does Baswana-Sen's time really scale as O(k·m)?

| Output File | Contents |
|------------|----------|
| `data/results/scaling_benchmark.csv` | Time (ms) per graph size per k |
| `data/results/union_find_benchmark.csv` | Path compression speedup |
| `data/results/data_structure_benchmark.csv` | Adj list vs matrix memory |
| `data/figures/scaling_benchmark.png` | Log-log time vs n plot |
| `data/figures/union_find_benchmark.png` | Bar chart: with vs without compression |

### 2. Stretch Experiment (`stretch_experiment.py`)
**Question**: How much stretch do we actually get? (Theory says ≤ t, practice is often much better)

| Output File | Contents |
|------------|----------|
| `data/results/stretch_experiment.csv` | Avg/max/p95 stretch per dataset × t |
| `data/figures/stretch_analysis.png` | Bar charts by topology |
| `data/figures/pareto_frontier.png` | ⭐ The key figure: sparseness vs stretch |

**Key finding**: Even a theoretical 3-spanner often has average stretch ~1.0-1.3 on real graphs.

### 3. Fault Tolerance (`fault_tolerance.py`)
**Question**: What happens when we delete high-degree nodes from the spanner?

| Output File | Contents |
|------------|----------|
| `data/results/fault_tolerance.csv` | Stretch & connectivity at 1-20% failure |
| `data/figures/fault_tolerance.png` | Stretch degradation + connectivity plots |

**Repair heuristic**: For each disconnected pair, find shortest path in remaining original graph and add those edges back.

### 4. Routing Simulation (`routing_simulation.py`)
**Question**: How practical is a spanner for real navigation?

| Output File | Contents |
|------------|----------|
| `data/results/routing_simulation.csv` | Memory saved %, route increase %, query speedup |
| `data/figures/routing_simulation.png` | Memory vs stretch tradeoff |

**Headline result**: "Google Maps on a 3-spanner uses X% less memory with only Y% longer routes"

### 5. Seed Variance (`seed_variance.py`)
**Question**: Does the random seed matter? How stable is Baswana-Sen?

| Output File | Contents |
|------------|----------|
| `data/results/seed_variance.csv` | Mean, std, CV of edge count & stretch across 50 seeds |
| `data/figures/seed_variance.png` | Box plots + histograms |

**Key finding**: Coefficient of variation ~0.001-0.003 → extremely stable across seeds.

---

## 🎨 Interactive Visualizer Features

The D3.js visualizer at `viz/react-d3/index.html` has:

| Feature | Description |
|---------|------------|
| **Graph presets** | Random (50/100/200), Grid (7×7, 10×10), Scale-Free (50/100) |
| **File upload** | Upload any edge list CSV (one `u v` per line) |
| **Stretch slider** | Drag t from 3 to 9, watch edges get pruned in real-time |
| **Algorithm toggle** | Switch between Baswana-Sen and Greedy BFS |
| **Cluster coloring** | Nodes colored by their cluster membership |
| **Edge encoding** | Spanner = bold blue, Removed = faint dashed gray |
| **Phase replay** | ▶ Play animation showing edges added phase-by-phase (600ms delay) |
| **Node tooltips** | Hover to see node ID, cluster, degree |
| **Zoom + drag** | Full pan/zoom/drag interaction |
| **Metrics bar** | Nodes, edges, sparseness ratio, construction time, validity |

---

## 🔗 Person A vs Person B Split

### Person A (You — This Codebase) = Everything That Runs
- ✅ All Python algorithm code
- ✅ All C++ code
- ✅ All experiment scripts
- ✅ All data loaders
- ✅ All visualizations
- ✅ All unit tests

### Person B (Partner) = Everything That Interprets
- History of t-spanners (Peleg 1989 → Baswana-Sen 2007)
- Theoretical proofs & stretch-size tradeoff
- Real-world use cases deep dive
- Cross-language comparison analysis (using YOUR data)
- Pareto frontier interpretation
- Full report assembly
- BFS vs DFS formal derivation

### How They Connect
| Topic | Person A's Output | Person B Uses It For |
|-------|------------------|---------------------|
| BFS vs DFS | Empirical timing in comments | Formal complexity proof in report |
| Multi-language | Python + C++ implementations | "Implementation Across Languages" chapter |
| Fault tolerance | Experiment data + repair code | Connection to f-fault-tolerant spanner literature |
| Pareto frontier | Raw (stretch, sparseness) data | Publication-quality figure + interpretation |
| Seed variance | 50-seed box plots | "Does random seed matter?" analysis |

---

## 📝 Quick Reference Card

```bash
# Run all tests
python -X utf8 tests/test_core.py

# Run quick experiments (20 seconds)
python run_all.py --quick

# Run full experiments (5-10 minutes)
python run_all.py -e all

# Download SNAP datasets
python src/python/data/download_snap.py --all

# Open visualizer
python -m http.server 8080 --directory viz/react-d3

# Open Streamlit dashboard
streamlit run viz/streamlit/app.py

# Compile C++
cd src/cpp && make all

# Run C++ spanner
echo "100 500" | ./spanner_cpp --algo baswana --k 2 --verify
```

---

## 📚 Key References

1. **Baswana & Sen** (2007) — "A simple and linear time randomized algorithm for computing sparse spanners in weighted graphs" — *Random Structures & Algorithms*
2. **Althöfer et al.** (1993) — "On sparse spanners of weighted graphs" — *Discrete & Computational Geometry*
3. **Peleg & Schäffer** (1989) — "Graph spanners" — *Journal of Graph Theory*
4. **SNAP Datasets** — https://snap.stanford.edu/data/

---

*Person A — Systems, Implementation & Engineering*  
*Algorithm Engineering, Semester 4*
