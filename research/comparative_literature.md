# Comparative Literature Review: Spanner Variants

| Variant | Definition | Size Bound | Construction Time | Key Reference |
| :--- | :--- | :--- | :--- | :--- |
| **Multiplicative** | $d_H(u,v) \le t \cdot d_G(u,v)$ | $O(n^{1+1/k})$ for $t=2k-1$ | $O(m)$ (Randomized) | Baswana-Sen (2007) |
| **Additive** | $d_H(u,v) \le d_G(u,v) + \beta$ | $O(n^{4/3})$ for $\beta=2$ | $O(mn)$ (Greedy) | Woodruff (2010) |
| **Mixed $(\alpha, \beta)$** | $d_H(u,v) \le \alpha d_G(u,v) + \beta$ | Varies | $O(m \log n)$ | Elkin & Peleg (2001) |
| **Fault-Tolerant** | $d_{H-F}(u,v) \le t \cdot d_{G-F}(u,v)$ | $O(f^2 k n^{1+1/k})$ | Polynomial | Chechik et al. (2009) |
| **Pairwise** | Preserve distance for $S \subseteq V \times V$ | Much smaller | Varies | Coppersmith (2006) |
| **Streaming** | Edges processed in one pass | $O(n^{1+1/k})$ | $O(1)$ per edge | Ahmed et al. (2020) |

## Situating Baswana-Sen in the Landscape
Baswana-Sen (2007) remains the gold standard for **Multiplicative Spanners** because:
1.  **Efficiency**: It is the first algorithm to hit the $O(m)$ time bound without sacrificing the $O(n^{1+1/k})$ size guarantee.
2.  **Weighted Graphs**: Unlike many earlier randomized approaches that only worked for unweighted graphs, Baswana-Sen handles weighted edges seamlessly.
3.  **Simplicity**: The clustering logic is significantly easier to implement and parallelize than the complex hierarchical decompositions used in earlier work by Thorup & Zwick.

## Trade-offs
- **Multiplicative vs Additive**: Multiplicative spanners are better for graphs with high diameter (like road networks), while additive spanners can be more efficient for very dense graphs where paths are short.
- **Static vs Fault-Tolerant**: Standard Baswana-Sen does not guarantee stretch after node failures. Our project explores a "Repair Heuristic" to bridge this gap.
