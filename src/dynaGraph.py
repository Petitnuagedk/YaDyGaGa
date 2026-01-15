from typing import List, Tuple
import random
import networkx as nx
import itertools
import math

class SPCDynamicGraph:
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
                            seed: int = None,
                            max_enumeration: int = 1000000) -> List['SPCDynamicGraph']:
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
          - max_enumeration: threshold for switching to random sampling to avoid huge enumerations

        Returns:
          list of DynamicGraph objects (length <= target_count)
        """
        random.seed(seed)

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
        results: List[SPCDynamicGraph] = []
        seen = set()

        def build_from_indices(idxs):
            frames_seq = [pools[i][idxs[i]] for i in range(frames)]
            fp = self._timeline_fingerprint(frames_seq)
            if fp in seen:
                return None
            seen.add(fp)
            dg = SPCDynamicGraph()
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
    
class MPCDynamicGraph:
    """
    Build a dynamic graph sequence for Multi-Pair timelines.

    Core method:
      - buildDynaGraph(mpc_timeline, mpc_frame_set, seed=None, no_double=True)

    - mpc_timeline: list of tuples of booleans, one tuple per frame (e.g. [(True,False),(True,False)])
    - mpc_frame_set: output of FrameGenerator.generate_frames_for_pairs, expected keys:
        'frames' : list[nx.Graph]
        'cases'  : dict{ status_tuple -> [frame_indices] }
    - seed: optional int for deterministic selection
    - no_double: if True avoid reusing the same frame index twice when possible
    """
    def __init__(self):
        self.DynamicGraph: List[nx.Graph] = []
        self.selected_frame_indices: List[int] = []
        self.selected_statuses: List[Tuple[bool, ...]] = []

    def _hamming(self, a: Tuple[bool, ...], b: Tuple[bool, ...]) -> int:
        return sum(1 for x, y in zip(a, b) if x != y) + abs(len(a) - len(b))

    def buildDynaGraph(self,
                       mpc_timeline: List[Tuple[bool, ...]],
                       mpc_frame_set: dict,
                       seed: int = None,
                       no_double: bool = True,
                       allow_hamming_fallback: bool = True) -> List[nx.Graph]:
        """
        Build DynamicGraph picking frames from mpc_frame_set that match each tuple
        in mpc_timeline. If an exact match does not exist for a timeline frame, we
        optionally fallback to the closest status by Hamming distance, then to any unused
        frame, then to any frame.

        Returns the list of selected nx.Graph frames and sets attributes on self.
        """
        rnd = random.Random(seed)

        frames = mpc_frame_set.get("frames", [])
        cases = mpc_frame_set.get("cases", {})

        if not mpc_timeline:
            raise ValueError("mpc_timeline is empty")
        if not frames:
            raise ValueError("mpc_frame_set has no frames")

        # normalize timeline tuples
        timeline = [tuple(bool(x) for x in t) for t in mpc_timeline]

        # copy available pools so we can remove indices when no_double is requested
        available = {k: list(v) for k, v in cases.items()}

        # build reverse map idx -> status tuple for quick lookup
        idx_to_status = {}
        for status, idxs in cases.items():
            for i in idxs:
                idx_to_status[i] = status

        chosen_indices: List[int] = []
        chosen_statuses: List[Tuple[bool, ...]] = []

        all_indices = set(range(len(frames)))

        for desired in timeline:
            # try exact pool first
            pool = available.get(desired, [])
            if pool:
                idx = rnd.choice(pool)
                chosen_indices.append(idx)
                chosen_statuses.append(desired)
                if no_double:
                    pool.remove(idx)
                continue

            # fallback by Hamming distance among existing case keys
            found = False
            if allow_hamming_fallback and cases:
                candidates = sorted(cases.keys(), key=lambda s: self._hamming(s, desired))
                for cand in candidates:
                    pool2 = available.get(cand, [])
                    if pool2:
                        idx = rnd.choice(pool2)
                        chosen_indices.append(idx)
                        chosen_statuses.append(cand)
                        if no_double:
                            pool2.remove(idx)
                        found = True
                        break
            if found:
                continue

            # fallback to any unused frame
            remaining = list(all_indices - set(chosen_indices)) if no_double else []
            if remaining:
                idx = rnd.choice(remaining)
                chosen_indices.append(idx)
                chosen_statuses.append(idx_to_status.get(idx, tuple()))
                continue

            # last resort: pick any random frame
            idx = rnd.randrange(len(frames))
            chosen_indices.append(idx)
            chosen_statuses.append(idx_to_status.get(idx, tuple()))

        # assemble DynamicGraph frames
        self.DynamicGraph = [frames[i] for i in chosen_indices]
        self.selected_frame_indices = chosen_indices
        self.selected_statuses = chosen_statuses

        return self.DynamicGraph

    def generate_unique_set(self,
                            mpc_timeline: List[Tuple[bool, ...]],
                            mpc_frame_set: dict,
                            target_count: int,
                            seed: int = None,
                            max_enumeration: int = 1000000) -> List['MPCDynamicGraph']:
        """
        Generate up to `target_count` distinct MPCDynamicGraph instances following `mpc_timeline`.
        Distinctness is enforced frame-wise (exact graph equality via simple fingerprint).

        Parameters:
          - mpc_timeline: list of status tuples
          - mpc_frame_set: output of FrameGenerator.generate_frames_for_pairs (expects 'frames' and 'cases')
          - target_count: desired number of unique dynamics
          - seed: optional int to seed random sampling
          - max_enumeration: threshold to switch from exhaustive enumeration to random sampling

        Returns list of MPCDynamicGraph objects (length <= target_count)
        """
        rnd = random.Random(seed)

        frames = mpc_frame_set.get("frames", [])
        cases = mpc_frame_set.get("cases", {})

        if target_count <= 0:
            return []
        if not mpc_timeline:
            raise ValueError("mpc_timeline is empty")
        if not frames:
            raise ValueError("mpc_frame_set has no frames")

        # For each timeline position, build a pool of candidate frame indices (fallback to all indices)
        pools_idx: List[List[int]] = []
        all_indices = list(range(len(frames)))
        for status in mpc_timeline:
            status = tuple(bool(x) for x in status)
            idxs = list(cases.get(status, []))
            if not idxs:
                # fallback: use all frames
                idxs = all_indices.copy()
            pools_idx.append(idxs)

        # compute total combinations
        sizes = [len(p) for p in pools_idx]
        total_combinations = 1
        for s in sizes:
            total_combinations *= s

        # local fingerprint helpers
        def _frame_fingerprint(g: nx.Graph):
            if g is None:
                return ("nodes", tuple(), "edges", tuple())
            nodes = tuple(sorted(map(str, g.nodes())))
            edges = tuple(sorted(tuple(sorted((str(u), str(v)))) for u, v in g.edges()))
            return ("nodes", nodes, "edges", edges)

        def _timeline_fingerprint(seq: List[nx.Graph]):
            return tuple(_frame_fingerprint(g) for g in seq)

        results: List[MPCDynamicGraph] = []
        seen = set()

        def build_from_choice_indices(choice_idxs: List[int]):
            seq = [frames[i] for i in choice_idxs]
            fp = _timeline_fingerprint(seq)
            if fp in seen:
                return None
            seen.add(fp)
            dg = MPCDynamicGraph()
            dg.DynamicGraph = seq.copy()
            dg.selected_frame_indices = choice_idxs.copy()
            dg.selected_statuses = [mpc_frame_set.get("cases_map", {}).get(i, mpc_frame_set.get("cases", {})) for i in choice_idxs]
            return dg

        # enumeration path
        if total_combinations <= max_enumeration:
            # iterate deterministic product of indices within pools
            for combo in itertools.product(*(range(len(pools_idx[i])) for i in range(len(pools_idx)))):
                # map combo positions to actual frame indices
                choice = [pools_idx[i][combo[i]] for i in range(len(combo))]
                dg = build_from_choice_indices(choice)
                if dg:
                    results.append(dg)
                    if len(results) >= target_count:
                        break
            return results

        # randomized sampling path
        attempts = 0
        max_attempts = int(min(max_enumeration, total_combinations, target_count * 50))
        while len(results) < target_count and attempts < max_attempts:
            choice = [rnd.choice(pools_idx[i]) for i in range(len(pools_idx))]
            dg = build_from_choice_indices(choice)
            if dg:
                results.append(dg)
            attempts += 1

        # best-effort deterministic fill if still short (bounded)
        if len(results) < target_count and total_combinations <= max_enumeration * 5:
            for combo in itertools.product(*(range(len(pools_idx[i])) for i in range(len(pools_idx)))):
                choice = [pools_idx[i][combo[i]] for i in range(len(combo))]
                dg = build_from_choice_indices(choice)
                if dg:
                    results.append(dg)
                    if len(results) >= target_count:
                        break

        return results