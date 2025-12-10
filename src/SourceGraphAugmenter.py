import networkx as nx

class SourceGraphAugmenter:

    def __init__(self):
        pass

    def augment_graph_keep_baseline(G: nx.Graph, s: str, d: str) -> nx.Graph:
        """
        Return a new graph that contains G plus any extra edge (u,v) between
        nodes that are not neighbors in G such that adding (u,v) does NOT reduce
        the shortest-path length between s and d (compared to the baseline).
        Baseline is computed on the original G.
        """
        baseline = None
        try:
            baseline = nx.shortest_path_length(G, s, d)
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            baseline = float('inf')

        limited = G.copy()
        nodes = list(G.nodes())
        n = len(nodes)
        for i in range(n):
            for j in range(i + 1, n):
                u, v = nodes[i], nodes[j]
                if limited.has_edge(u, v):
                    continue
                # test adding (u, v) to original graph and see new distance
                H = G.copy()
                H.add_edge(u, v)
                try:
                    new_len = nx.shortest_path_length(H, s, d)
                except nx.NetworkXNoPath:
                    new_len = float('inf')
                # only allow the new edge if it does NOT reduce the s-d distance
                if new_len >= baseline:
                    limited.add_edge(u, v)
        return limited