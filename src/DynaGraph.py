from typing import List, Tuple
import random
import networkx as nx
import itertools
import math

class DynamicGraph:
    """
    Assembles generated timeline blocks into a cohesive timeline called a DynamicGraph.
    """

    def __init__(self):
        self.DynamicGraph = []
    
    def buildDynaGraph(self, timeline: List[bool], path_up: List[nx.Graph], path_down: List[nx.Graph]):
        """
        Given a timeline of booleans and two sets of frames (path_up and path_down),
        pick frames according to the timeline.

        :param timeline: List of booleans where True indicates "path up" and False indicates "path down".
        :param path_up: List of frames where the path exists.
        :param path_down: List of frames where the path does not exist.
        :return: List of selected frames according to the timeline.
        """
        for state in timeline:
            pool = path_up if state else path_down
            if not pool:
                # fallback to the other non-empty pool or an empty graph
                pool = path_down if path_up else (path_up if path_down else [])
            if pool:
                self.DynamicGraph.append(random.choice(pool))
            else:
                # empty graph with same nodes (no edges)
                # Try to infer node list from any available graph in pool arguments (not ideal)
                self.DynamicGraph.append(nx.Graph())

    def addGraphatindex(self, index: int, graph: nx.Graph):
        """
        Add a graph at a specific index in the DynamicGraph.

        :param index: Index at which to add the graph.
        :param graph: The graph to add.
        """
        if 0 <= index <= len(self.DynamicGraph):
            self.DynamicGraph.insert(index, graph)
        else:
            raise IndexError("Index out of bounds for DynamicGraph.")

    def clearDynaGaph(self):
        """
        Clear all added timeline blocks.
        """
        self.DynamicGraph = []

    def _frame_fingerprint(self, g: nx.Graph):
        """
        Create a stable fingerprint for a single frame (graph) suitable for equality checks.
        Fingerprint uses sorted node list and sorted edge tuples. This is cheap and frame-wise,
        not a full isomorphism test.
        """
        if g is None:
            return ("nodes", tuple(), "edges", tuple())
        nodes = tuple(sorted(map(str, g.nodes())))
        # canonicalize edges as sorted tuples of strings so direction/ordering doesn't matter
        edges = tuple(sorted(tuple(sorted((str(u), str(v)))) for u, v in g.edges()))
        return ("nodes", nodes, "edges", edges)

    def _timeline_fingerprint(self, frames: List[nx.Graph]):
        """
        Fingerprint a whole dynamic graph (sequence of frames) as tuple of frame fingerprints.
        """
        return tuple(self._frame_fingerprint(g) for g in frames)

    def generate_unique_set(self,
                            timeline: List[bool],
                            path_up: List[nx.Graph],
                            path_down: List[nx.Graph],
                            target_count: int,
                            randomize: bool = True,
                            max_enumeration: int = 1000000) -> List['DynamicGraph']:
        """
        Generate up to `target_count` distinct DynamicGraph instances following `timeline`.
        Distinctness is enforced frame-wise: two dynamics are considered equal if every
        corresponding frame has the same fingerprint (same node set and same edge set).

        End triggers:
          - stop when `target_count` unique dynamics are created
          - or when all possible combinations have been produced (no more combinations possible)
          - or when enumeration would be too large and we hit sampling limits (see max_enumeration)

        Parameters:
          - timeline: sequence of booleans (True -> use path_up pool, False -> use path_down pool)
          - path_up: list of graphs usable when timeline frame is True
          - path_down: list of graphs usable when timeline frame is False
          - target_count: desired number of unique dynamics to generate
          - randomize: if True and total combinations large, sample randomly; otherwise enumerate deterministic combos
          - max_enumeration: threshold for switching to random sampling to avoid huge enumerations

        Returns:
          list of DynamicGraph objects (length <= target_count)
        """
        if target_count <= 0:
            return []

        frames = len(timeline)
        # Build per-frame choice pools applying same fallback logic as buildDynaGraph
        pools: List[List[nx.Graph]] = []
        for state in timeline:
            primary = path_up if state else path_down
            fallback = path_down if state else path_up
            if primary:
                pools.append(primary)
            elif fallback:
                pools.append(fallback)
            else:
                # when both pools empty, use a single empty graph placeholder
                pools.append([nx.Graph()])

        # compute total combinations
        sizes = [len(p) for p in pools]
        total_combinations = 1
        for s in sizes:
            total_combinations *= s

        # if total_combinations is small, enumerate all deterministic combinations
        results: List[DynamicGraph] = []
        seen = set()

        def build_from_indices(idxs):
            frames_seq = [pools[i][idxs[i]] for i in range(frames)]
            fp = self._timeline_fingerprint(frames_seq)
            if fp in seen:
                return None
            seen.add(fp)
            dg = DynamicGraph()
            dg.DynamicGraph = frames_seq.copy()
            return dg

        # enumeration path
        if total_combinations <= max_enumeration:
            # iterate deterministic product of indices
            for indices in itertools.product(*(range(s) for s in sizes)):
                dg = build_from_indices(indices)
                if dg:
                    results.append(dg)
                    if len(results) >= target_count:
                        break
            return results

        # randomized sampling path (total_combinations huge)
        attempts = 0
        max_attempts = int(min(max_enumeration, total_combinations, target_count * 50))
        # cap attempts to avoid infinite loops; try until we get target or attempts exceeded
        while len(results) < target_count and attempts < max_attempts:
            indices = [random.randrange(s) for s in sizes]
            dg = build_from_indices(indices)
            if dg:
                results.append(dg)
            attempts += 1

        # If after sampling we still have not reached target and total_combinations is not enormous,
        # try a limited deterministic enumeration to fill gaps (best-effort).
        if len(results) < target_count and total_combinations <= max_enumeration * 5:
            for indices in itertools.product(*(range(s) for s in sizes)):
                dg = build_from_indices(indices)
                if dg:
                    results.append(dg)
                    if len(results) >= target_count:
                        break

        return results