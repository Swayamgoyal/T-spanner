/*
 * baswana_sen.cpp — C++ Implementation of Baswana-Sen (2k-1)-Spanner
 * ====================================================================
 * Companion to the Python implementation for cross-language benchmarking.
 * 
 * Data structures:
 *   - Adjacency list: unordered_map<int, vector<pair<int, double>>>
 *   - Union-Find: with path compression + union-by-rank
 *   - Cluster membership: unordered_map<int, int>
 * 
 * Usage:
 *   ./baswana_sen < input.txt
 *   Input format: first line "n m", then m lines "u v w"
 *   Output: spanner edges, timing, statistics
 * 
 * Compile: g++ -O2 -std=c++17 -o baswana_sen baswana_sen.cpp
 * 
 * Part of t-Spanner project — Person A (Implementation & Engineering)
 */

#include <iostream>
#include <vector>
#include <unordered_map>
#include <unordered_set>
#include <set>
#include <algorithm>
#include <random>
#include <chrono>
#include <cmath>
#include <queue>
#include <numeric>
#include <fstream>
#include <sstream>
#include <climits>

using namespace std;

// ─── Union-Find with Path Compression ─────────────────────────

class UnionFind {
public:
    unordered_map<int, int> parent;
    unordered_map<int, int> rank_;
    int num_components;
    long long find_ops;
    long long path_compressions;

    UnionFind() : num_components(0), find_ops(0), path_compressions(0) {}

    void make_set(int x) {
        if (parent.count(x)) return;
        parent[x] = x;
        rank_[x] = 0;
        num_components++;
    }

    int find(int x) {
        find_ops++;
        if (!parent.count(x)) make_set(x);
        if (parent[x] != x) {
            path_compressions++;
            parent[x] = find(parent[x]); // Path compression
        }
        return parent[x];
    }

    bool unite(int x, int y) {
        int rx = find(x), ry = find(y);
        if (rx == ry) return false;
        // Union by rank
        if (rank_[rx] < rank_[ry]) swap(rx, ry);
        parent[ry] = rx;
        if (rank_[rx] == rank_[ry]) rank_[rx]++;
        num_components--;
        return true;
    }

    bool connected(int x, int y) {
        return find(x) == find(y);
    }
};

// ─── Graph Structure ──────────────────────────────────────────

struct Edge {
    int u, v;
    double w;
};

struct Graph {
    int n, m;
    unordered_map<int, vector<pair<int, double>>> adj;
    unordered_set<int> nodes;

    Graph() : n(0), m(0) {}

    void add_edge(int u, int v, double w = 1.0) {
        adj[u].push_back({v, w});
        adj[v].push_back({u, w});
        nodes.insert(u);
        nodes.insert(v);
        n = nodes.size();
        m++;
    }

    void add_node(int u) {
        nodes.insert(u);
        n = nodes.size();
    }

    // BFS distance (unweighted)
    int bfs_distance(int src, int dst) {
        if (src == dst) return 0;
        unordered_map<int, int> dist;
        dist[src] = 0;
        queue<int> q;
        q.push(src);
        while (!q.empty()) {
            int u = q.front(); q.pop();
            for (auto& [v, w] : adj[u]) {
                if (!dist.count(v)) {
                    dist[v] = dist[u] + 1;
                    if (v == dst) return dist[v];
                    q.push(v);
                }
            }
        }
        return INT_MAX; // unreachable
    }

    // Edge set (for verification)
    set<pair<int,int>> edge_set() {
        set<pair<int,int>> es;
        for (auto& [u, neighbors] : adj) {
            for (auto& [v, w] : neighbors) {
                es.insert({min(u,v), max(u,v)});
            }
        }
        return es;
    }
};

// ─── Baswana-Sen Algorithm ────────────────────────────────────

struct SpannerResult {
    Graph spanner;
    vector<Edge> spanner_edges;
    int stretch_param;
    double construction_time_ms;
    double sparseness_ratio;
    vector<string> phase_logs;
};

SpannerResult baswana_sen(Graph& g, int k, int seed = 42) {
    auto start = chrono::high_resolution_clock::now();
    
    mt19937 rng(seed);
    
    int n = g.n;
    double p = (n > 1) ? pow(n, -1.0 / k) : 1.0;
    
    // Phase 0: Every vertex is its own cluster
    unordered_map<int, int> cluster; // node -> cluster center (-1 = unclustered)
    for (int v : g.nodes) {
        cluster[v] = v;
    }
    
    // Spanner edge set
    set<pair<int,int>> spanner_edge_set;
    unordered_map<long long, double> edge_weights; // packed (u,v) -> weight
    
    auto pack = [](int u, int v) -> long long { 
        return (long long)min(u,v) * 1000000LL + max(u,v); 
    };
    
    SpannerResult result;
    
    // Phases 1 to k-1
    for (int phase = 1; phase < k; phase++) {
        int edges_processed = 0, edges_added = 0;
        int clusters_surviving = 0, vertices_unclustered = 0;
        
        // Step 1: Sample — each current cluster center survives with prob p
        unordered_set<int> sampled;
        unordered_set<int> current_centers;
        for (auto& [v, c] : cluster) {
            if (c != -1) current_centers.insert(c);
        }
        
        uniform_real_distribution<double> dist(0.0, 1.0);
        for (int c : current_centers) {
            if (dist(rng) < p) {
                sampled.insert(c);
                clusters_surviving++;
            }
        }
        
        // Step 2: Process every clustered vertex
        unordered_map<int, int> new_cluster;
        
        for (int v : g.nodes) {
            if (cluster[v] == -1) {
                new_cluster[v] = -1;
                continue;
            }
            
            int v_old_cluster = cluster[v];
            
            // Group neighbors by cluster -> lightest edge
            unordered_map<int, pair<int, double>> lightest_to_cluster;
            for (auto& [u, w] : g.adj[v]) {
                edges_processed++;
                int uc = cluster[u];
                if (uc == -1) continue;
                if (!lightest_to_cluster.count(uc) || w < lightest_to_cluster[uc].second) {
                    lightest_to_cluster[uc] = {u, w};
                }
            }
            
            if (sampled.count(v_old_cluster)) {
                // Case A: v's cluster survived
                new_cluster[v] = v_old_cluster;
                
                // Add lightest edge to each neighboring cluster that is DIFFERENT
                // and did NOT survive
                for (auto& [nc, uw] : lightest_to_cluster) {
                    if (nc != v_old_cluster && !sampled.count(nc)) {
                        int a = min(v, uw.first), b = max(v, uw.first);
                        if (!spanner_edge_set.count({a, b})) {
                            spanner_edge_set.insert({a, b});
                            edge_weights[pack(a, b)] = uw.second;
                            edges_added++;
                        }
                    }
                }
            } else {
                // Case B: v's cluster did NOT survive
                // Try to attach to nearest surviving cluster
                int best_neighbor = -1;
                double best_weight = 1e18;
                int best_cluster_id = -1;
                
                for (auto& [nc, uw] : lightest_to_cluster) {
                    if (sampled.count(nc) && uw.second < best_weight) {
                        best_weight = uw.second;
                        best_neighbor = uw.first;
                        best_cluster_id = nc;
                    }
                }
                
                if (best_neighbor != -1) {
                    new_cluster[v] = best_cluster_id;
                    int a = min(v, best_neighbor), b = max(v, best_neighbor);
                    if (!spanner_edge_set.count({a, b})) {
                        spanner_edge_set.insert({a, b});
                        edge_weights[pack(a, b)] = best_weight;
                        edges_added++;
                    }
                    
                    // Add lightest edge to each non-surviving neighboring cluster
                    for (auto& [nc, uw] : lightest_to_cluster) {
                        if (nc != best_cluster_id && !sampled.count(nc)) {
                            int a2 = min(v, uw.first), b2 = max(v, uw.first);
                            if (!spanner_edge_set.count({a2, b2})) {
                                spanner_edge_set.insert({a2, b2});
                                edge_weights[pack(a2, b2)] = uw.second;
                                edges_added++;
                            }
                        }
                    }
                } else {
                    // No surviving cluster neighbor — v becomes unclustered
                    new_cluster[v] = -1;
                    vertices_unclustered++;
                    
                    // Add lightest edge to every neighboring cluster
                    for (auto& [nc, uw] : lightest_to_cluster) {
                        int a = min(v, uw.first), b = max(v, uw.first);
                        if (!spanner_edge_set.count({a, b})) {
                            spanner_edge_set.insert({a, b});
                            edge_weights[pack(a, b)] = uw.second;
                            edges_added++;
                        }
                    }
                }
            }
        }
        
        cluster = new_cluster;
        
        ostringstream log;
        log << "Phase " << phase << ": processed=" << edges_processed 
            << " added=" << edges_added << " clusters=" << clusters_surviving
            << " unclustered=" << vertices_unclustered;
        result.phase_logs.push_back(log.str());
    }
    
    // Final phase — unclustered vertices add ALL edges
    int final_added = 0;
    for (int v : g.nodes) {
        if (cluster[v] == -1) {
            for (auto& [u, w] : g.adj[v]) {
                int a = min(v, u), b = max(v, u);
                if (!spanner_edge_set.count({a, b})) {
                    spanner_edge_set.insert({a, b});
                    edge_weights[pack(a, b)] = w;
                    final_added++;
                }
            }
        }
    }
    
    // Build spanner graph
    for (auto& [u, v] : spanner_edge_set) {
        double w = edge_weights[pack(u, v)];
        result.spanner.add_edge(u, v, w);
        result.spanner_edges.push_back({u, v, w});
    }
    for (int v : g.nodes) {
        result.spanner.add_node(v);
    }
    
    auto end = chrono::high_resolution_clock::now();
    result.construction_time_ms = chrono::duration<double, milli>(end - start).count();
    result.stretch_param = 2 * k - 1;
    result.sparseness_ratio = (g.m > 0) ? (double)result.spanner_edges.size() / g.m : 0;
    
    return result;
}

// ─── Greedy BFS Spanner ───────────────────────────────────────

SpannerResult greedy_bfs_spanner(Graph& g, int t) {
    auto start = chrono::high_resolution_clock::now();
    
    // Sort edges by weight
    vector<Edge> all_edges;
    set<pair<int,int>> seen;
    for (auto& [u, neighbors] : g.adj) {
        for (auto& [v, w] : neighbors) {
            if (u < v && !seen.count({u, v})) {
                all_edges.push_back({u, v, w});
                seen.insert({u, v});
            }
        }
    }
    sort(all_edges.begin(), all_edges.end(), [](const Edge& a, const Edge& b) {
        return a.w < b.w;
    });
    
    SpannerResult result;
    for (int v : g.nodes) result.spanner.add_node(v);
    
    int checked = 0, rejected = 0;
    
    for (auto& e : all_edges) {
        checked++;
        // BFS distance in current spanner
        int dist = result.spanner.bfs_distance(e.u, e.v);
        
        if (dist > t * e.w) {
            result.spanner.add_edge(e.u, e.v, e.w);
            result.spanner_edges.push_back(e);
        } else {
            rejected++;
        }
    }
    
    auto end = chrono::high_resolution_clock::now();
    result.construction_time_ms = chrono::duration<double, milli>(end - start).count();
    result.stretch_param = t;
    result.sparseness_ratio = (g.m > 0) ? (double)result.spanner_edges.size() / g.m : 0;
    
    return result;
}

// ─── Main ─────────────────────────────────────────────────────

void print_usage() {
    cerr << "Usage: ./spanner_cpp [options]" << endl;
    cerr << "  --algo <baswana|greedy>   Algorithm (default: baswana)" << endl;
    cerr << "  --k <int>                 k parameter for Baswana-Sen (default: 2)" << endl;
    cerr << "  --t <int>                 t parameter for greedy (default: 3)" << endl;
    cerr << "  --seed <int>              Random seed (default: 42)" << endl;
    cerr << "  --input <file>            Input file (default: stdin)" << endl;
    cerr << "  --output <file>           Output file (default: stdout)" << endl;
    cerr << "  --verify                  Verify stretch property" << endl;
    cerr << endl;
    cerr << "Input format: first line 'n m', then m lines 'u v [w]'" << endl;
}

int main(int argc, char* argv[]) {
    // Parse arguments
    string algo = "baswana";
    int k = 2, t = 3, seed = 42;
    string input_file = "", output_file = "";
    bool verify = false;
    
    for (int i = 1; i < argc; i++) {
        string arg = argv[i];
        if (arg == "--algo" && i+1 < argc) algo = argv[++i];
        else if (arg == "--k" && i+1 < argc) k = stoi(argv[++i]);
        else if (arg == "--t" && i+1 < argc) t = stoi(argv[++i]);
        else if (arg == "--seed" && i+1 < argc) seed = stoi(argv[++i]);
        else if (arg == "--input" && i+1 < argc) input_file = argv[++i];
        else if (arg == "--output" && i+1 < argc) output_file = argv[++i];
        else if (arg == "--verify") verify = true;
        else if (arg == "--help") { print_usage(); return 0; }
    }
    
    // Read input
    istream* in = &cin;
    ifstream fin;
    if (!input_file.empty()) {
        fin.open(input_file);
        if (!fin.is_open()) {
            cerr << "Error: cannot open " << input_file << endl;
            return 1;
        }
        in = &fin;
    }
    
    int n, m;
    *in >> n >> m;
    
    Graph g;
    for (int i = 0; i < m; i++) {
        int u, v;
        double w = 1.0;
        *in >> u >> v;
        if (in->peek() != '\n' && !in->eof()) {
            *in >> w;
        }
        g.add_edge(u, v, w);
    }
    
    cerr << "Loaded graph: n=" << g.n << " m=" << g.m 
         << " density=" << (2.0 * g.m / (g.n * (g.n - 1))) << endl;
    
    // Run algorithm
    SpannerResult result;
    if (algo == "baswana") {
        cerr << "Running Baswana-Sen with k=" << k << " (stretch=" << (2*k-1) << ")" << endl;
        result = baswana_sen(g, k, seed);
    } else {
        cerr << "Running Greedy BFS Spanner with t=" << t << endl;
        result = greedy_bfs_spanner(g, t);
    }
    
    // Output results
    ostream* out = &cout;
    ofstream fout;
    if (!output_file.empty()) {
        fout.open(output_file);
        out = &fout;
    }
    
    // Header
    *out << "# Spanner Results" << endl;
    *out << "# Algorithm: " << algo << endl;
    *out << "# Stretch parameter: " << result.stretch_param << endl;
    *out << "# Original edges: " << g.m << endl;
    *out << "# Spanner edges: " << result.spanner_edges.size() << endl;
    *out << "# Sparseness ratio: " << result.sparseness_ratio << endl;
    *out << "# Construction time (ms): " << result.construction_time_ms << endl;
    
    // Phase logs
    for (auto& log : result.phase_logs) {
        *out << "# " << log << endl;
    }
    
    // Spanner edges
    *out << result.spanner.n << " " << result.spanner_edges.size() << endl;
    for (auto& e : result.spanner_edges) {
        *out << e.u << " " << e.v << " " << e.w << endl;
    }
    
    // Verify if requested
    if (verify) {
        cerr << "Verifying stretch property..." << endl;
        int violations = 0, checked = 0;
        double max_stretch = 0;
        
        // Sample 500 random pairs
        vector<int> node_list(g.nodes.begin(), g.nodes.end());
        mt19937 vrng(seed);
        
        for (int i = 0; i < min(500, (int)(node_list.size() * (node_list.size()-1) / 2)); i++) {
            int u = node_list[vrng() % node_list.size()];
            int v = node_list[vrng() % node_list.size()];
            if (u == v) continue;
            
            int d_orig = g.bfs_distance(u, v);
            int d_span = result.spanner.bfs_distance(u, v);
            
            if (d_orig == 0 || d_orig == INT_MAX) continue;
            checked++;
            
            if (d_span == INT_MAX) {
                violations++;
                continue;
            }
            
            double stretch = (double)d_span / d_orig;
            max_stretch = max(max_stretch, stretch);
            if (stretch > result.stretch_param + 0.01) violations++;
        }
        
        cerr << "Verified " << checked << " pairs: max_stretch=" << max_stretch 
             << " violations=" << violations << endl;
    }
    
    cerr << "Done. Time: " << result.construction_time_ms << " ms" << endl;
    
    return 0;
}
