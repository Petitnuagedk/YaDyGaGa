from typing import List, Tuple
import random
import networkx as nx
import itertools
import math

class dynamicGraph:
    """
    Base class for DynamicGraph structures.
    """
    def __init__(self):
        self.DynamicGraph = []
    
    def appendGraph(self, graph: nx.Graph):
        self.DynamicGraph.append(graph)

class SPCDynamicGraph:
    """
    Assembles generated timeline blocks into a cohesive timeline called a DynamicGraph.
    """

    def __init__(self):
        self.DynamicGraph = []
    
    def buildDynaGraph(self, timeline, path_up, path_down):
        """
        Given a timeline (legacy: List[bool] OR new: dict {'timeline':..., 'path_ids':...})
        and two sets of frames (path_up grouped as list-of-groups, path_down flat list),
        pick frames according to the timeline.

        New behavior for SPC when timeline is labeled:
         - `path_up` is expected to be a list of groups (each group is a list of frames sharing same s->d path).
         - timeline may carry `path_ids` distinguishing desired persistent path identities across up frames.
         - we map timeline path_id -> chosen group index (first occurrence chooses a group randomly,
           subsequent frames with same path_id reuse the same group).
        Legacy behavior (flat path_up list) is still supported.
        """
        rnd = random.Random()

        # accept timeline as either dict or list
        if isinstance(timeline, dict):
            tl = timeline.get('timeline', [])
            path_ids = timeline.get('path_ids', [None] * len(tl))
        else:
            tl = list(timeline)
            path_ids = [None] * len(tl)

        # detect if path_up is grouped (list of lists) or flat (list of graphs)
        grouped_up = False
        if path_up and isinstance(path_up, list) and any(isinstance(x, list) for x in path_up):
            grouped_up = True

        # prepare pools
        if grouped_up:
            groups = path_up  # list of lists
            n_groups = len(groups)
        else:
            flat_up = list(path_up) if path_up else []
            n_groups = len(flat_up)

        down_pool = list(path_down) if path_down else []

        # mapping timeline path id -> group index (for grouped_up case)
        pid_to_group = {}

        self.DynamicGraph = []
        for idx, state in enumerate(tl):
            if state:
                # up frame requested
                pid = path_ids[idx] if idx < len(path_ids) else None
                if grouped_up:
                    if n_groups == 0:
                        # no up groups available: fallback to empty graph
                        self.DynamicGraph.append(nx.Graph())
                        continue
                    if pid is None:
                        # no label: pick any group at random
                        gid = rnd.randrange(n_groups)
                    else:
                        if pid in pid_to_group:
                            gid = pid_to_group[pid]
                        else:
                            # choose a group for this path-id (allow reuse)
                            gid = rnd.randrange(n_groups)
                            pid_to_group[pid] = gid
                    # pick a frame from the chosen group
                    group_pool = groups[gid]
                    if group_pool:
                        gf = rnd.choice(group_pool)
                        self.DynamicGraph.append(gf)
                    else:
                        # empty group fallback
                        self.DynamicGraph.append(nx.Graph())
                else:
                    # flat up pool
                    if not flat_up:
                        self.DynamicGraph.append(nx.Graph())
                    else:
                        self.DynamicGraph.append(rnd.choice(flat_up))
            else:
                # down frame
                if down_pool:
                    self.DynamicGraph.append(rnd.choice(down_pool))
                else:
                    # fallback to empty graph
                    self.DynamicGraph.append(nx.Graph())
        return self.DynamicGraph

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

    def _frame_fingerprint(self, g):
        """
        Return a deterministic fingerprint for a single frame-like object.
        Accepts:
          - networkx Graph-like objects (have .nodes()/.edges())
          - lists of graphs (grouped frames) -> use first non-empty element
        """
        # handle grouped frames (list of graphs)
        if isinstance(g, (list, tuple)):
            if len(g) == 0:
                return ("EMPTY_GROUP",)
            # recurse on first element (it may itself be a group)
            return self._frame_fingerprint(g[0])

        # assume graph-like object
        try:
            nodes = tuple(sorted(map(str, g.nodes())))
            edges = tuple(sorted(tuple(sorted(map(str, e))) for e in g.edges()))
            return (nodes, edges)
        except Exception:
            # fallback: stringify object
            return (str(g),)

    def _timeline_fingerprint(self, frames):
        """
        Produce a fingerprint for a sequence of frames (used to detect duplicates).
        Frames elements may be graphs or grouped lists; _frame_fingerprint handles both.
        """
        return tuple(self._frame_fingerprint(g) for g in frames)

    def generateUniqueSet(self,
                            timeline: List[bool],
                            path_up: List[nx.Graph],
                            path_down: List[nx.Graph],
                            target_count: int,
                            seed: int = None,
                            max_enumeration: int = 1000000) -> List['SPCDynamicGraph']:
        """
        Generate up to `target_count` distinct DynamicGraph instances following `timeline`.
        Supports the new map-style timeline (dict with 'timeline' and 'path_ids') and
        grouped `path_up` (list-of-groups). When `path_up` is grouped, `path_ids`
        (if provided) bind particular up-frames to the same group index across the whole sequence;

        Behavior:
         - timeline may be a list[bool] or dict {'timeline': [...], 'path_ids': [...]}
         - when path_up is grouped (list of lists), frames with a non-None path_id must
           use the same group for that path_id across the whole sequence; frames with
           path_id == None can select from any group's frames independently.
         - fallback semantics follow buildDynaGraph: for grouped_up, if groups exist
           use them; if groups empty, treat as empty-frame placeholder. For non-grouped
           up/down the previous primary/fallback logic is preserved.
        """
        random.seed(seed)
        print("Generating unique SPCDynamicGraph set with target_count = ", target_count)

        if target_count <= 0:
            return []

        # accept timeline as either dict or list (same as buildDynaGraph)
        if isinstance(timeline, dict):
            tl = timeline.get('timeline', [])
            path_ids = timeline.get('path_ids', [None] * len(tl))
        else:
            tl = list(timeline)
            path_ids = [None] * len(tl)

        frames = len(tl)

        # detect grouped_up as in buildDynaGraph
        grouped_up = False
        if path_up and isinstance(path_up, list) and any(isinstance(x, list) for x in path_up):
            grouped_up = True

        # prepare down pool and flat_up
        down_pool = list(path_down) if path_down else []
        if not grouped_up:
            flat_up = list(path_up) if path_up else []

        results: List[SPCDynamicGraph] = []
        seen = set()

        def build_and_record(frames_seq):
            fp = self._timeline_fingerprint(frames_seq)
            if fp in seen:
                return None
            seen.add(fp)
            dg = SPCDynamicGraph()
            dg.DynamicGraph = frames_seq.copy()
            return dg
        
        # Non-grouped case: reuse previous behavior (with simple primary/fallback per-frame pools)
        if not grouped_up:
            # Build per-frame pools using primary/fallback logic (same as before)
            pools: List[List[nx.Graph]] = []
            for state in tl:
                primary = flat_up if state else down_pool
                fallback = down_pool if state else flat_up
                if primary:
                    pools.append(primary)
                elif fallback:
                    pools.append(fallback)
                else:
                    pools.append([nx.Graph()])

            sizes = [len(p) for p in pools]
            total_combinations = 1
            for s in sizes:
                total_combinations *= s

            # enumeration path
            if total_combinations <= max_enumeration:
                for indices in itertools.product(*(range(s) for s in sizes)):
                    frames_seq = [pools[i][indices[i]] for i in range(frames)]
                    dg = build_and_record(frames_seq)
                    if dg:
                        results.append(dg)
                        if len(results) >= target_count:
                            break
                return results

            # randomized sampling path
            attempts = 0
            max_attempts = int(min(max_enumeration, total_combinations, target_count * 50))
            while len(results) < target_count and attempts < max_attempts:
                indices = [random.randrange(s) for s in sizes]
                frames_seq = [pools[i][indices[i]] for i in range(frames)]
                dg = build_and_record(frames_seq)
                if dg:
                    results.append(dg)
                attempts += 1

            # best-effort deterministic fill
            if len(results) < target_count and total_combinations <= max_enumeration * 5:
                for indices in itertools.product(*(range(s) for s in sizes)):
                    frames_seq = [pools[i][indices[i]] for i in range(frames)]
                    dg = build_and_record(frames_seq)
                    if dg:
                        results.append(dg)
                        if len(results) >= target_count:
                            break

            return results
        
        # Grouped-up case
        # groups is list-of-lists (may contain empty groups)
        groups = path_up if path_up else []
        n_groups = len(groups)
        groups_sizes = [len(g) for g in groups]
        # flattened list of all up-frames across groups (for pid == None cases)
        flat_all = [g for group in groups for g in group]

        # collect ordered unique non-None path_ids to assign group indices to them
        unique_pids = []
        pid_to_slot = {}
        for pid in path_ids:
            if pid is None:
                continue
            if pid not in pid_to_slot:
                pid_to_slot[pid] = len(unique_pids)
                unique_pids.append(pid)
        m = len(unique_pids)

        # helper to create per-frame pools for a given assignment mapping (tuple of group indices per unique_pids slot)
        def pools_for_assignment(assignment):
            # assignment is tuple length m with group indices
            assign_map = {}
            for i, pid in enumerate(unique_pids):
                assign_map[pid] = assignment[i]
            pools_a: List[List[nx.Graph]] = []
            for i, state in enumerate(tl):
                if not state:
                    # down frame: use down_pool or placeholder
                    if down_pool:
                        pools_a.append(down_pool)
                    else:
                        pools_a.append([nx.Graph()])
                else:
                    # up frame: if no groups (n_groups==0) -> placeholder (matches buildDynaGraph)
                    if n_groups == 0:
                        pools_a.append([nx.Graph()])
                        continue
                    pid = path_ids[i] if i < len(path_ids) else None
                    if pid is None:
                        # can pick any group's frames
                        if flat_all:
                            pools_a.append(flat_all)
                        else:
                            pools_a.append([nx.Graph()])
                    else:
                        gid = assign_map.get(pid, None)
                        # if gid is invalid (shouldn't happen) treat as placeholder
                        if gid is None or gid < 0 or gid >= n_groups:
                            pools_a.append([nx.Graph()])
                        else:
                            group_pool = groups[gid]
                            if group_pool:
                                pools_a.append(group_pool)
                            else:
                                pools_a.append([nx.Graph()])
            return pools_a

        # compute total combinations by summing over assignments product of per-frame pool sizes
        total_combinations = 0
        if m == 0:
            # single 'assignment' where there are no pid bindings
            pools0 = pools_for_assignment(())
            sizes0 = [len(p) for p in pools0]
            prod0 = 1
            for s in sizes0:
                prod0 *= s
            total_combinations = prod0
        else:
            # avoid iterating all n_groups**m assignments when that count is huge.
            assignment_count = n_groups ** m
            # threshold for exact assignment enumeration (tunable)
            EXACT_ASSIGNMENT_LIMIT = min(100000, max(10000, int(max_enumeration)))
            if assignment_count <= EXACT_ASSIGNMENT_LIMIT:
                # exact enumeration (safe)
                for assignment in itertools.product(range(n_groups), repeat=m):
                    pools_a = pools_for_assignment(assignment)
                    prod = 1
                    for p in pools_a:
                        prod *= len(p)
                    total_combinations += prod
            else:
                # sample assignments to estimate average per-assignment product,
                # then extrapolate to approximate total_combinations.
                SAMPLE_LIMIT = 2000
                sample_n = min(SAMPLE_LIMIT, assignment_count)
                sum_prod = 0
                for _ in range(sample_n):
                    assignment = tuple(random.randrange(n_groups) for _ in range(m))
                    pools_a = pools_for_assignment(assignment)
                    prod = 1
                    for p in pools_a:
                        prod *= len(p)
                    sum_prod += prod
                avg_prod = (sum_prod / sample_n) if sample_n > 0 else 0
                # conservative estimate, but prevent zero which would break logic
                est_total = int(avg_prod * assignment_count)
                total_combinations = max(est_total, assignment_count, 1)
                print(f"estimate total_combinations={total_combinations} (assignment_count={assignment_count}, avg_prod={avg_prod:.2f})")

        # enumeration path if small enough
        if total_combinations <= max_enumeration:
            if m == 0:
                # single assignment
                pools_a = pools_for_assignment(())
                sizes = [len(p) for p in pools_a]
                for indices in itertools.product(*(range(s) for s in sizes)):
                    frames_seq = [pools_a[i][indices[i]] for i in range(frames)]
                    dg = build_and_record(frames_seq)
                    if dg:
                        results.append(dg)
                        if len(results) >= target_count:
                            break
                return results
            else:
                for assignment in itertools.product(range(n_groups), repeat=m):
                    pools_a = pools_for_assignment(assignment)
                    sizes = [len(p) for p in pools_a]
                    for indices in itertools.product(*(range(s) for s in sizes)):
                        frames_seq = [pools_a[i][indices[i]] for i in range(frames)]
                        dg = build_and_record(frames_seq)
                        if dg:
                            results.append(dg)
                            if len(results) >= target_count:
                                break
                    if len(results) >= target_count:
                        break
                return results
            
        # randomized sampling path (total_combinations huge)
        attempts = 0
        max_attempts = int(min(max_enumeration, total_combinations if total_combinations > 0 else max_enumeration, target_count * 50))
        while len(results) < target_count and attempts < max_attempts:
            # pick a random assignment for labeled pids
            if m == 0:
                assignment = ()
            else:
                assignment = tuple(random.randrange(n_groups) for _ in range(m))
            pools_a = pools_for_assignment(assignment)
            # pick random index from each pool
            indices = [random.randrange(len(p)) for p in pools_a]
            frames_seq = [pools_a[i][indices[i]] for i in range(frames)]
            dg = build_and_record(frames_seq)
            if dg:
                results.append(dg)
            attempts += 1

        # best-effort deterministic fill if still short and not too enormous
        if len(results) < target_count and total_combinations <= max_enumeration * 5:
            if m == 0:
                pools_a = pools_for_assignment(())
                sizes = [len(p) for p in pools_a]
                for indices in itertools.product(*(range(s) for s in sizes)):
                    frames_seq = [pools_a[i][indices[i]] for i in range(frames)]
                    dg = build_and_record(frames_seq)
                    if dg:
                        results.append(dg)
                        if len(results) >= target_count:
                            break
            else:
                for assignment in itertools.product(range(n_groups), repeat=m):
                    pools_a = pools_for_assignment(assignment)
                    sizes = [len(p) for p in pools_a]
                    for indices in itertools.product(*(range(s) for s in sizes)):
                        frames_seq = [pools_a[i][indices[i]] for i in range(frames)]
                        dg = build_and_record(frames_seq)
                        if dg:
                            results.append(dg)
                            if len(results) >= target_count:
                                break
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

    def generateUniqueSet(self,
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