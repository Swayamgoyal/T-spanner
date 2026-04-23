"""
cross_language_analysis.py — Cross-Language Data Structure Comparison
=====================================================================
Analyzes Person A's multi-language benchmark data and generates the
"Implementation Across Languages" chapter content.

Part of t-Spanner project — Person B (Research, Analysis & Writing)
"""

import os
import csv

RESULTS_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'results')


def load_csv(filename):
    filepath = os.path.join(RESULTS_DIR, filename)
    if not os.path.exists(filepath):
        print(f"[WARN] File not found: {filepath}")
        return []
    with open(filepath, 'r') as f:
        return list(csv.DictReader(f))


def analyze_language_comparison():
    """
    Compare Python vs C++ performance from language_comparison.csv.
    """
    print("\n" + "=" * 80)
    print("CROSS-LANGUAGE PERFORMANCE COMPARISON")
    print("=" * 80)

    rows = load_csv('language_comparison.csv')
    if not rows:
        print("  [INFO] No language comparison data available.")
        print("  [INFO] C++ benchmarks not yet run (cpp_time_ms is empty).")
        print("  [INFO] Generating theoretical analysis instead.\n")

    # ── Theoretical Analysis ──
    print("\n── Theoretical Data Structure Analysis ──\n")
    print("Language × Data Structure Comparison:")
    print("-" * 90)
    print(f"{'Language':<12} {'Data Structure':<25} {'Lookup':>10} {'Insert':>10} {'Memory':>12} {'Cache':>10}")
    print("-" * 90)

    ds_table = [
        ("Python", "dict (open addressing)", "O(1) avg", "O(1) avg", "~72 B/entry", "Poor"),
        ("Python", "defaultdict[list]", "O(1) avg", "O(1) amort", "~120 B/node", "Poor"),
        ("C++", "unordered_map<int,vec>", "O(1) avg", "O(1) avg", "~48 B/entry", "Moderate"),
        ("C++", "vector<vector<int>>", "O(1)", "O(1) amort", "~24 B/node", "Good"),
        ("C++", "set<int> (RB-tree)", "O(log n)", "O(log n)", "~40 B/entry", "Poor"),
        ("Java", "HashMap<Int,ArrayList>", "O(1) avg", "O(1) amort", "~80 B/entry", "Moderate"),
    ]

    for lang, ds, lookup, insert, mem, cache in ds_table:
        print(f"{lang:<12} {ds:<25} {lookup:>10} {insert:>10} {mem:>12} {cache:>10}")

    # ── Python-specific analysis ──
    print("\n── Python dict Internals ──")
    print("  Python's dict uses OPEN ADDRESSING with Robin Hood hashing.")
    print("  Load factor maintained at < 2/3 → average probe count ~1.5.")
    print("  Worst case: O(n) probes on hash collision chain.")
    print("  For Baswana-Sen's cluster membership lookup:")
    print("    - Cluster dict has n entries → ~72 * n bytes")
    print("    - Each lookup is O(1) average, O(n) worst case")
    print("    - Total: O(m) lookups × O(1) avg = O(m) expected time")

    # ── C++ analysis ──
    print("\n── C++ unordered_map Internals ──")
    print("  C++ unordered_map uses CHAINING (linked list per bucket).")
    print("  Cache-misses during pointer chasing in chains can dominate runtime.")
    print("  For Baswana-Sen:")
    print("    - Adjacency: unordered_map<int, vector<pair<int,int>>>")
    print("    - Each edge access: hash(node_id) + pointer chase + vector index")
    print("    - vector<vector<int>> is better: contiguous memory, cache-friendly")

    # ── Hash Collision Analysis ──
    print("\n── Hash Collision Analysis ──")
    print("  With n keys and m buckets (load factor α = n/m):")
    print("  Open addressing (Python): E[probes] = 1/(1-α) ≈ 3 at α=2/3")
    print("  Chaining (C++): E[probes] = 1 + α/2 ≈ 1.5 at α=1.0")
    print("  → C++ chaining has fewer probes but worse cache locality")
    print("  → Python open addressing has more probes but better locality")
    print("  → For Baswana-Sen (m >> n): hash performance is NOT the bottleneck")


def analyze_data_structures():
    """
    Analyze adjacency list vs matrix benchmark from data_structure_benchmark.csv.
    """
    print("\n" + "=" * 80)
    print("DATA STRUCTURE BENCHMARK: ADJACENCY LIST vs MATRIX")
    print("=" * 80)

    rows = load_csv('data_structure_benchmark.csv')
    if not rows:
        return

    print(f"\n{'n':>6} {'m':>6} {'List Time':>12} {'List Mem':>12} {'Matrix Time':>13} {'Matrix Mem':>12} {'Mem Ratio':>10}")
    print("-" * 80)
    for r in rows:
        print(f"{r['n']:>6} {r['m']:>6} {r['list_time_ms']:>10} ms {r['list_memory_bytes']:>10} B "
              f"{r['matrix_build_time_ms']:>11} ms {r['matrix_memory_bytes']:>10} B {r['memory_ratio']:>10}")

    # Density threshold analysis
    print("\n── Density Threshold Analysis ──")
    print("  Adjacency List: O(n + m) memory, O(degree(v)) to iterate neighbors")
    print("  Adjacency Matrix: O(n²) memory, O(n) to iterate neighbors")
    print()
    print("  Matrix becomes WASTEFUL when density < 50%:")
    print("    n=50:  m=120, density=120/1225 = 9.8%  → matrix wastes 91% of memory")
    print("    n=100: m=224, density=224/4950 = 4.5%  → matrix wastes 95.5% of memory")
    print("    n=1000: m~5000, density=5000/499500 = 1% → matrix wastes 99% of memory")
    print()
    print("  For sparse spanners (density < 10%), adjacency list is ALWAYS preferred.")
    print("  Matrix is only competitive for dense graphs (density > 50%), which spanners are not.")


def analyze_union_find():
    """
    Analyze Union-Find with/without path compression from union_find_benchmark.csv.
    """
    print("\n" + "=" * 80)
    print("UNION-FIND: PATH COMPRESSION ANALYSIS")
    print("=" * 80)

    rows = load_csv('union_find_benchmark.csv')
    if not rows:
        return

    print(f"\n{'n':>6} {'Ops':>8} {'With Comp':>12} {'Without':>12} {'Speedup':>8} {'Compressions':>14}")
    print("-" * 70)
    for r in rows:
        print(f"{r['n']:>6} {r['operations']:>8} {r['with_compression_ms']:>10} ms "
              f"{r['without_compression_ms']:>10} ms {r['speedup']:>8} {r['path_compressions']:>14}")

    print("\n── Theoretical Analysis ──")
    print("  Union-Find with path compression + union by rank:")
    print("    Amortized time per operation: O(α(n))")
    print("    where α(n) = inverse Ackermann function ≤ 4 for all practical n")
    print("    → Essentially O(1) per operation")
    print()
    print("  Without path compression:")
    print("    Worst case: O(n) per FIND (DFS-tree depth can be O(n))")
    print("    Example: union(1,2), union(2,3), ..., union(n-1,n) → linear chain")
    print("    FIND(1) traverses entire chain: n-1 steps")
    print()
    print("  Path compression flattens the tree on each FIND:")
    print("    After FIND(x), every node on the path points directly to root")
    print("    Subsequent FINDs on same path: O(1)")


def analyze_avl_alternative():
    """
    Answer: What if we used AVL tree instead of hash map for clustering?
    """
    print("\n" + "=" * 80)
    print("THOUGHT EXPERIMENT: AVL TREE vs HASH MAP FOR CLUSTERING")
    print("=" * 80)

    print()
    print("  If cluster membership used an AVL tree (balanced BST) instead of hash map:")
    print()
    print("  Hash Map (current):   O(1) avg lookup → O(m) total for Baswana-Sen")
    print("  AVL Tree (alternate): O(log n) lookup → O(m log n) total for Baswana-Sen")
    print()
    print("  Impact for n=10,000, m=50,000:")
    print("    Hash Map: ~50,000 operations × O(1) = ~50,000 steps")
    print("    AVL Tree: ~50,000 operations × O(log 10000) = ~50,000 × 13.3 = ~665,000 steps")
    print("    → AVL is ~13× slower for cluster lookups")
    print()
    print("  When would AVL be preferred?")
    print("    1. When ordered iteration over clusters is needed (AVL gives sorted order)")
    print("    2. When worst-case O(log n) is preferred over amortized O(1)")
    print("    3. When hash function quality is uncertain (adversarial inputs)")
    print()
    print("  Conclusion: For Baswana-Sen, hash map is the correct choice.")
    print("  The algorithm does not need ordered cluster iteration,")
    print("  and the O(log n) factor would be a significant overhead for large graphs.")


if __name__ == "__main__":
    print("t-Spanner Cross-Language & Data Structure Analysis (Person B)")
    print("=" * 60)

    analyze_language_comparison()
    analyze_data_structures()
    analyze_union_find()
    analyze_avl_alternative()

    print("\n[DONE] All analyses complete.")
