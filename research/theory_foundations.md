# Chapter 3: Theoretical Foundations of t-Spanners

---

## 1. Formal Problem Statement

Given an undirected weighted graph $G = (V, E, w)$, a **$t$-spanner** is a subgraph $H = (V, E', w)$ where $E' \subseteq E$ such that:
$$\forall u, v \in V: \quad d_H(u, v) \leq t \cdot d_G(u, v)$$

The objective is to minimize $|E'|$ for a fixed stretch $t$. The parameter $t$ is called the **stretch factor** or **distortion**.

**Sparseness Ratio**: We define $\rho = |E'|/|E|$ as the fraction of original edges retained. The goal is to minimize $\rho$ while bounding the stretch.

---

## 2. The Erdős Girth Conjecture: The Optimality Limit

### 2.1 Background: Girth and Extremal Graphs
The **girth** $g(G)$ of a graph $G$ is the length of its shortest cycle. The **Erdős Girth Conjecture** (1963) states:

> **Conjecture (Erdős, 1963)**: For every integer $k \geq 1$, there exist graphs with $n$ vertices, $\Omega(n^{1+1/k})$ edges, and girth $g \geq 2k + 2$.

### 2.2 Proof Sketch: Lower Bound on Spanner Size

**Theorem**: Any $(2k-1)$-spanner of a graph $G$ with girth $g \geq 2k+2$ must contain **all** edges of $G$. Consequently, any $(2k-1)$-spanner needs $\Omega(n^{1+1/k})$ edges in the worst case.

**Proof**:
1. Let $G$ have girth $g \geq 2k+2$, and let $H$ be a $(2k-1)$-spanner of $G$.
2. Suppose for contradiction that some edge $e = (u,v)$ is not in $H$.
3. Since $e \notin H$, the shortest path from $u$ to $v$ in $H$ must use other edges of $G$.
4. In $G$, the edge $(u,v)$ has weight $w(u,v)$. The shortest path from $u$ to $v$ in $G \setminus \{e\}$ goes around a cycle containing $e$.
5. Since $g(G) \geq 2k+2$, the shortest cycle through $e$ has length $\geq 2k+2$.
6. Therefore: $d_{G \setminus e}(u,v) \geq (2k+1) \cdot w(u,v)$ (for unweighted: path has $\geq 2k+1$ edges).
7. Since $H \subseteq G \setminus \{e\}$: $d_H(u,v) \geq d_{G \setminus e}(u,v) \geq (2k+1) \cdot w(u,v)$.
8. But the stretch guarantee requires $d_H(u,v) \leq (2k-1) \cdot w(u,v)$. **Contradiction**.
9. Therefore, $e$ must be in $H$, and since $e$ was arbitrary, $H = G$.

**Implication**: If the Erdős Girth Conjecture holds, then $O(n^{1+1/k})$ is the **asymptotically optimal** size bound for $(2k-1)$-spanners. Both the greedy algorithm and Baswana-Sen achieve this bound.

### 2.3 Known Results on the Girth Conjecture
- **$k = 1$**: Trivially true (complete graphs have girth 3 and $\Theta(n^2)$ edges).
- **$k = 2, 3, 5$**: Proven using algebraic constructions (incidence graphs of projective planes).
- **General $k$**: Probabilistic constructions give graphs with $\Omega(n^{1+1/(3k-3)})$ edges and girth $2k+2$ — weaker but still sufficient for meaningful lower bounds.

---

## 3. Baswana-Sen Algorithm: Complete Analysis

### 3.1 Pseudocode with Line-by-Line Annotation

```
Algorithm: BASWANA-SEN(G, k)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Input:  Undirected weighted graph G = (V, E, w), integer k ≥ 2
Output: (2k-1)-spanner H ⊆ G with O(kn^{1+1/k}) edges (in expectation)

 1.  H ← ∅                              // Spanner edge set (initially empty)
 2.  p ← n^{-1/k}                       // Sampling probability (KEY PARAMETER)
 3.  C₀ ← {{v} : v ∈ V}                 // Phase 0: every vertex is its own cluster
 4.  cluster(v) ← v for all v ∈ V       // Cluster membership via Union-Find
 
     // ─── MAIN LOOP: k-1 phases of clustering ───
 5.  FOR i = 1 TO k-1:
 6.      Sᵢ ← sample each center from Cᵢ₋₁ independently with probability p
         // ANNOTATION: E[|Sᵢ|] = |Cᵢ₋₁| · p. After i rounds: E[|Cᵢ|] = n·p^i
     
 7.      FOR each vertex v where cluster(v) ∉ Sᵢ:
             // v's cluster was NOT sampled → v becomes "unclustered" temporarily
 8.          Find the nearest neighbor u of v such that cluster(u) ∈ Sᵢ
             // "Nearest" = minimum weight edge to a vertex in a sampled cluster
 9.          IF such u exists:
10.              Add edge (v, u) to H            // ATTACHMENT EDGE
11.              cluster(v) ← cluster(u)          // v joins u's cluster (Union-Find)
12.          ELSE:
13.              // No adjacent sampled cluster → v is "unclustered"
14.              FOR each neighbor w of v:
15.                  IF (v, w) is the min-weight edge from v to cluster(w):
16.                      Add (v, w) to H          // INTER-CLUSTER EDGE
                         // These edges preserve stretch for unclustered vertices
 
     // ─── FINAL PHASE ───
17.  FOR each unclustered vertex v after phase k-1:
18.      Add ALL edges of v to H              // Safety net: ensures stretch guarantee
 
19.  RETURN H
```

### 3.2 Probabilistic Analysis: Why $p = n^{-1/k}$ Works

**Expected cluster count after $i$ phases**:
$$E[|C_i|] = n \cdot p^i = n \cdot (n^{-1/k})^i = n^{1 - i/k}$$

After $k-1$ phases:
$$E[|C_{k-1}|] = n^{1 - (k-1)/k} = n^{1/k}$$

**Expected edge count (Phase-by-Phase)**:

- **Attachment edges per phase**: Each non-sampled vertex adds 1 edge. Number of non-sampled vertices $\approx |C_{i-1}| \cdot (1-p)$. Over all phases: $\sum_{i=1}^{k-1} n \cdot p^{i-1}(1-p) \leq kn$.
  
- **Inter-cluster edges per phase $i$**: Each unclustered vertex $v$ adds at most one edge per adjacent cluster. The expected number of adjacent clusters is bounded by the number of remaining clusters $\approx n \cdot p^i = n^{1-i/k}$. Total inter-cluster edges: $\leq n \cdot n^{1/k} = n^{1+1/k}$.

- **Final phase unclustered edges**: Unclustered vertices after phase $k-1$ each add all their edges. Expected count of unclustered vertices $= n \cdot (1-p)^{k-1} \cdot p^0 \approx n \cdot e^{-p(k-1)}$. For large $n$, this contributes $O(n^{1+1/k})$ edges.

**Total expected edges**:
$$E[|H|] = O(k \cdot n) + O(n^{1+1/k}) = O(k \cdot n^{1+1/k})$$

### 3.3 Stretch Guarantee Proof Sketch

**Claim**: For any edge $(u,v) \in E$, we have $d_H(u,v) \leq (2k-1) \cdot w(u,v)$.

**Proof by induction on phases**: 
- After phase $i$, any two vertices in the same cluster have a path of length $\leq 2i-1$ times their original distance.
- When vertex $v$ attaches to cluster $C$ via edge $(v,u)$: the attachment edge provides a path to the cluster center, and the inter-cluster edges ensure connectivity between adjacent clusters.
- After $k-1$ phases, the total multiplicative stretch is $\leq 2(k-1) + 1 = 2k - 1$.

---

## 4. BFS vs DFS: Formal Analysis for Greedy Spanners

### 4.1 The Core Requirement
The greedy spanner's correctness depends on checking: **Is $d_H(u,v) > t \cdot w(u,v)$?**

This requires computing the **exact shortest-path distance** in the current partial spanner $H$.

### 4.2 Why BFS is Mandatory

| Property | BFS | DFS |
|:---------|:----|:----|
| **Path found** | Shortest path (by edge count/weight) | Arbitrary path; often explores deep branches first |
| **Correctness for stretch check** | ✅ Exact $d_H(u,v)$ | ❌ Over-estimates $d_H(u,v)$ |
| **Resulting spanner quality** | Optimal: $O(n^{1+1/k})$ edges | Suboptimal: up to $O(m)$ edges (no pruning) |
| **Per-query complexity** | $O(V + E)$ | $O(V + E)$ |
| **Total greedy complexity** | $O(m(n + m'))$ where $m' = |H|$ | Same asymptotic, but denser $H$ → slower |

### 4.3 The DFS Failure Mode — Formal Analysis

Consider a spanner $H$ where $d_H(u,v) = 3$ via the shortest path $u \to a \to b \to v$.

**BFS**: Explores level-by-level: $\{u\} \to \{a, \ldots\} \to \{b, \ldots\} \to \{v, \ldots\}$. Discovers $v$ at distance 3. **Correctly** determines $d_H(u,v) = 3$.

**DFS**: May explore $u \to x \to y \to z \to \ldots$ (a deep branch), backtrack, then eventually find $v$ via a **longer** path. DFS reports $d_H^{DFS}(u,v) \geq 3$, possibly much larger.

**Consequence**: If $t = 3$ and $w(u,v) = 1$:
- BFS: $d_H(u,v) = 3 \leq 3 \cdot 1 = t$. Edge $(u,v)$ is **not added** (correct).
- DFS: Reports $d_H^{DFS}(u,v) = 15$. Since $15 > 3 = t$, edge $(u,v)$ is **incorrectly added**.

**Density Impact**: Using DFS can lead to a spanner with up to **3× more edges** than necessary, as many edges are added due to phantom stretch violations.

### 4.4 Weighted Graphs: Dijkstra as "Weighted BFS"
For weighted graphs, the stretch check requires Dijkstra's algorithm (not plain BFS). Dijkstra is essentially BFS weighted by edge costs, maintaining the shortest-path guarantee:

- **Dijkstra complexity**: $O((V + E) \log V)$ with a binary heap
- **Total greedy complexity**: $O(m \cdot (n + m') \log n)$ per edge

DFS provides no analog for weighted shortest paths — it simply cannot answer "what is the shortest weighted path?" correctly.

---

## 5. Algorithm Trade-offs Summary

| Algorithm | Time | Size | Stretch | Deterministic? | Weighted? |
|:----------|:-----|:-----|:--------|:--------------|:----------|
| **Greedy** (Althöfer, 1993) | $O(mn^{1+1/k})$ | $O(n^{1+1/k})$ | $2k-1$ | Yes | Yes |
| **Thorup-Zwick** (2001) | $O(kmn^{1/k})$ | $O(kn^{1+1/k})$ | $2k-1$ | No | Partial |
| **Baswana-Sen** (2007) | $O(km)$ | $O(kn^{1+1/k})$ | $2k-1$ | No | Yes |
| **Roditty-Thorup-Zwick** (2004) | $O(mn^{1/k})$ | $O(n^{1+1/k})$ | $2k-1$ | Yes | No |

**Key insight**: Baswana-Sen achieves the same stretch and near-optimal size as Greedy, but with a $\Theta(n^{1+1/k}/k)$ speedup in time. This makes it the algorithm of choice for massive graphs like social networks ($n > 10^6$).

---

## 6. The Sampling Probability: Why $n^{-1/k}$ and Not Something Else?

The sampling probability $p = n^{-1/k}$ is chosen to balance two competing objectives:

1. **Too high $p$** (e.g., $p = 0.5$): Most clusters survive each phase → few edges pruned → spanner too dense → $|H| \approx |E|$.

2. **Too low $p$** (e.g., $p = 1/n$): Very few clusters survive → many unclustered vertices → massive edge additions in final phase → spanner too dense.

3. **$p = n^{-1/k}$**: After $k-1$ phases, exactly $n^{1/k}$ clusters remain in expectation. This is the **geometric sweet spot** where:
   - Each phase reduces clusters by a factor of $n^{1/k}$
   - The total edges added across all phases is minimized
   - The final phase has few enough unclustered vertices

**For specific topologies**, this uniform probability may not be optimal:
- **Scale-free graphs**: Hubs naturally dominate clustering; a lower $p$ might suffice
- **Road networks**: Uniform degree → $p = n^{-1/k}$ works well but produces more edges
- **This motivates our Hybrid Adaptive Spanner's degree-weighted sampling**
