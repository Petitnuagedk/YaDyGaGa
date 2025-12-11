from typing import List, Tuple
import random

class SPCTimelineBlockGenerator:
    """
    TimelineBlockGenerator is responsible for generating blocks of timelines
    based on specified criteria. It includes methods for creating and managing
    timeline blocks.
    """

    def __init__(self, frames: int, path_life: float, stability: float, seed : float ,mode: str = "blocks"):
        self.frames = frames
        self.path_life = path_life
        self.stability = stability
        self.mode = mode
        self.seed = seed

    def generate_blocks(self) -> List[bool]:
        """
        Generate a sequence of booleans representing timeline blocks.
        True indicates "path up" and False indicates "path down".

        Stability in [0,1] controls the number of up-blocks:
          - stability == 1 -> exactly 1 contiguous up block (if up frames > 0)
          - stability == 0 -> up frames split into as many blocks as possible (each up frame isolated)
          - intermediate -> interpolated number of up blocks between 1 and up_count

        When there is a single up block, it may be placed at an edge (one down block)
        or in the middle (two down blocks).
        """
        random.seed(self.seed)
        if self.frames <= 0:
            return []

        up_count = int(round(self.frames * self.path_life))
        up_count = max(0, min(self.frames, up_count))
        down_count = self.frames - up_count

        if self.mode == "random":
            timeline = [True] * up_count + [False] * down_count
            random.shuffle(timeline)
            return timeline

        # trivial cases
        if up_count == 0:
            return [False] * self.frames
        if down_count == 0:
            return [True] * self.frames

        # determine number of up blocks based on stability
        # min_up_blocks = 1, max_up_blocks = up_count (each up frame isolated)
        min_up_blocks = 1
        max_up_blocks = up_count
        up_blocks = int(round(min_up_blocks + (1.0 - float(self.stability)) * (max_up_blocks - min_up_blocks)))
        up_blocks = max(min_up_blocks, min(max_up_blocks, up_blocks))

        # helper to split a total into `parts` positive integers (as even as possible)
        def _split_counts(total: int, parts: int) -> List[int]:
            parts = max(1, parts)
            base = total // parts
            rem = total % parts
            sizes = [base + (1 if i < rem else 0) for i in range(parts)]
            # ensure each part at least 1 if possible
            for i in range(len(sizes)):
                if sizes[i] == 0:
                    sizes[i] = 1
            # adjust if we increased sum beyond total (rare)
            while sum(sizes) > total:
                for j in range(len(sizes)-1, -1, -1):
                    if sizes[j] > 1 and sum(sizes) > total:
                        sizes[j] -= 1
            return sizes

        # decide number of down blocks
        # minimal internal down blocks between up blocks is up_blocks - 1
        # possible down blocks are in [max(1, up_blocks - 1), up_blocks + 1]
        min_down_blocks = max(1, up_blocks - 1)
        max_down_blocks = min(up_blocks + 1, down_count)  # cannot exceed count (each block >=1)
        if max_down_blocks < min_down_blocks:
            # fallback: force min_down_blocks but will merge later
            max_down_blocks = min_down_blocks

        if up_blocks == 1:
            # single up block: either place on edge (one down block) or in middle (two down blocks)
            if down_count == 1:
                down_blocks = 1
            elif down_count >= 2:
                # random placement: half chance middle (2 down blocks), half chance edge (1 down block)
                if random.choice([True, False]):
                    down_blocks = 2
                else:
                    down_blocks = 1
            else:
                down_blocks = 1
            down_blocks = min(down_blocks, down_count)
        else:
            # multiple up blocks: prefer internal down blocks only (start and end with up)
            preferred = up_blocks - 1
            if preferred <= max_down_blocks:
                down_blocks = preferred
            else:
                down_blocks = max_down_blocks

        down_blocks = max(min_down_blocks, min(max_down_blocks, down_blocks))

        # generate sizes
        up_sizes = _split_counts(up_count, up_blocks)
        down_sizes = _split_counts(down_count, down_blocks)

        # build sequence of states (blocks) by interleaving
        blocks: List[Tuple[bool, int]] = []

        # Decide starting state to fit number of blocks: possible patterns depend on counts
        # If down_blocks == up_blocks + 1 -> must start with down and end with down
        # If down_blocks == up_blocks - 1 -> start and end with up
        # If equal -> start with either; prefer starting with up for visibility
        if down_blocks == up_blocks + 1:
            # pattern: D U D U ... D (starts with down)
            d_idx = 0
            u_idx = 0
            for i in range(down_blocks + up_blocks):
                if i % 2 == 0:
                    # down
                    blocks.append((False, down_sizes[d_idx]))
                    d_idx += 1
                else:
                    blocks.append((True, up_sizes[u_idx]))
                    u_idx += 1
        elif down_blocks == up_blocks - 1:
            # pattern: U D U D ... U (starts with up and ends with up)
            u_idx = 0
            d_idx = 0
            for i in range(down_blocks + up_blocks):
                if i % 2 == 0:
                    blocks.append((True, up_sizes[u_idx]))
                    u_idx += 1
                else:
                    blocks.append((False, down_sizes[d_idx]))
                    d_idx += 1
        else:
            # down_blocks == up_blocks or single up block cases where we may want edge/middle placement
            # prefer putting up blocks separated by downs and start with up
            u_idx = 0
            d_idx = 0
            start_with_up = True
            if up_blocks == 1 and down_blocks == 1:
                # when single up and single down, randomly choose order (edge placement)
                start_with_up = random.choice([True, False])
            for i in range(down_blocks + up_blocks):
                if start_with_up:
                    if i % 2 == 0:
                        blocks.append((True, up_sizes[u_idx]))
                        u_idx += 1
                    else:
                        blocks.append((False, down_sizes[d_idx]))
                        d_idx += 1
                else:
                    if i % 2 == 0:
                        blocks.append((False, down_sizes[d_idx]))
                        d_idx += 1
                    else:
                        blocks.append((True, up_sizes[u_idx]))
                        u_idx += 1

        # build timeline from blocks
        timeline: List[bool] = []
        for st, size in blocks:
            timeline.extend([bool(st)] * size)

        # final adjustment to ensure exact frame count
        if len(timeline) > self.frames:
            timeline = timeline[:self.frames]
        elif len(timeline) < self.frames:
            # pad with last state
            if timeline:
                timeline.extend([timeline[-1]] * (self.frames - len(timeline)))
            else:
                timeline = [False] * self.frames

        return timeline

    def _allocate_block_size(self, state: bool, remaining_up: int, remaining_down: int, remaining_blocks: int) -> int:
        """
        Allocate block size based on the current state and remaining counts.
        """
        if state:
            max_alloc = remaining_up - max(0, remaining_blocks - 1) * 0
            target = max(1, int(round(remaining_up / remaining_blocks)))
            return min(max(1, target), remaining_up) if remaining_up > 0 else 0
        else:
            max_alloc = remaining_down - max(0, remaining_blocks - 1) * 0
            target = max(1, int(round(remaining_down / remaining_blocks)))
            return min(max(1, target), remaining_down) if remaining_down > 0 else 0

    def _build_timeline_from_blocks(self, blocks: List[Tuple[bool, int]]) -> List[bool]:
        """
        Build the timeline from the generated blocks.
        """
        timeline = []
        for st, size in blocks:
            timeline.extend([bool(st)] * size)

        # Final adjustment to ensure the timeline matches the specified frame count
        if len(timeline) > self.frames:
            return timeline[:self.frames]
        elif len(timeline) < self.frames:
            if timeline:
                timeline.extend([timeline[-1]] * (self.frames - len(timeline)))
            else:
                timeline = [False] * self.frames
        return timeline
    

class MPCTimelineBlockGenerator:
    """
    Multi-Pair (MPC) timeline block generator.

    Creates a timeline of length `frames` where each frame is a tuple of booleans
    of size `n_pairs` representing the up/down state of each tracked pair.

    Parameters passed to constructor:
      - frames: total number of frames
      - n_pairs: number of (source,destination) pairs to track
      - path_life: average fraction of frames where a pair is up (0..1)
      - stability: average stability for up blocks per pair (0..1)
      - mode: 'sync' or 'indep'
          - 'sync' (default) builds a single global up/down block timeline and
            replicates it across all pairs (useful when pairs are correlated).
          - 'indep' builds independent timelines per pair (same stats but different placements).
      - seed: optional random seed for deterministic generation

    The generate() method returns a list of frame-state tuples:
      e.g. for n_pairs==3: [(False,False,False),(True,True,True), ...]
    """
    def __init__(self,
                 frames: int,
                 n_pairs: int,
                 path_life: float,
                 stability: float,
                 mode: str = "sync",
                 seed: int = None):
        self.frames = int(frames)
        self.n_pairs = int(n_pairs)
        self.path_life = float(path_life)
        self.stability = float(stability)
        self.mode = mode if mode in ("sync", "indep") else "sync"
        self.seed = seed

    def generate(self):
        """
        Generate and return the multi-pair timeline as a list of tuples (len == frames).
        """
        rnd = random.Random(self.seed)

        # Helper to create a single boolean timeline using the SPC generator logic
        def _single_tl(frames, path_life, stability, seed=None):
            g = SPCTimelineBlockGenerator(frames, path_life, stability, seed, mode="blocks")
            # SPCTimelineBlockGenerator uses random globals; if seed provided, patch random
            if seed is not None:
                print("seed was set")
                # make a private random choice by seeding the module-level random
                rnd_local = random.getstate()
                random.seed(seed)
                try:
                    tl = g.generate_blocks()
                    print(tl)
                finally:
                    random.setstate(rnd_local)
            else:
                print("seed is None")
                tl = g.generate_blocks()
            return tl

        timeline_of_tuples = []

        if self.mode == "sync":
            # single global timeline replicated across pairs
            global_seed = None if self.seed is None else (self.seed ^ 0x9e3779b9)
            global_tl = _single_tl(self.frames, self.path_life, self.stability, seed=global_seed)
            for st in global_tl:
                timeline_of_tuples.append(tuple([bool(st) for _ in range(self.n_pairs)]))
            return timeline_of_tuples

        # mode == "indep": generate independent timelines per pair and zip them
        per_pair_timelines = []
        for i in range(self.n_pairs):
            pair_seed = None if self.seed is None else (self.seed * (i+1))
            print("seed:", pair_seed)
            tl = _single_tl(self.frames, self.path_life, self.stability, seed=pair_seed)
            per_pair_timelines.append([bool(x) for x in tl])

        # transpose into frames of tuples
        for fi in range(self.frames):
            frame_tuple = tuple(per_pair_timelines[p][fi] for p in range(self.n_pairs))
            timeline_of_tuples.append(frame_tuple)

        return timeline_of_tuples

    def computeStatistics(self, timeline):
        """
        Compute simple per-pair statistics from a generated timeline (list of tuples).
        Returns dict with per_pair {'up_count','uptime_ratio','up_blocks','changes'} and
        global counts for distinct status tuples.
        """
        if not timeline:
            return {}

        frames = len(timeline)
        # collect per-pair lists
        per_pair = [ [] for _ in range(self.n_pairs) ]
        for t in timeline:
            for i, val in enumerate(t):
                per_pair[i].append(bool(val))

        stats = {"frames": frames, "pairs": []}
        for i, seq in enumerate(per_pair):
            # up blocks
            up_blocks = 0
            cur = False
            for v in seq:
                if v and not cur:
                    up_blocks += 1
                cur = v
            changes = sum(1 for j in range(1, frames) if seq[j] != seq[j-1])
            up_count = sum(1 for v in seq if v)
            stats["pairs"].append({
                "pair_index": i,
                "up_count": up_count,
                "uptime_ratio": up_count / frames,
                "up_blocks": up_blocks,
                "changes": changes,
            })

        # global status tuple counts
        if self.n_pairs == 2:
            # optimize for 2 pairs: just count the 4 possible tuples
            stats["status_tuples"] = {
                (False, False): 0,
                (False, True): 0,
                (True, False): 0,
                (True, True): 0,
            }
            for t in timeline:
                stats["status_tuples"][tuple(t)] += 1
        else:
            # general case: count all unique tuples
            stats["status_tuples"] = {}
            for t in timeline:
                if tuple(t) not in stats["status_tuples"]:
                    stats["status_tuples"][tuple(t)] = 0
                stats["status_tuples"][tuple(t)] += 1

        return stats

