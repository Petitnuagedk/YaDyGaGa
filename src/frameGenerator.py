"""
FrameGenerator class responsible for generating frames based on specified parameters.

Methods:
- generate_frames: Generates frames based on input parameters.
- get_frame_data: Retrieves the generated frame data.
- clear_frames: Clears the current frame data.
"""

from typing import List, Dict, Tuple
import random
import networkx as nx


class FrameGenerator:
    def __init__(self):
        self.path_up_frames = []
        self.path_down_frames = []

    def generateSPCFrames(self, limited_G: nx.Graph, s: str, d: str, trials: int = 1000, p_edge: float = 0.5) -> None:
        edges = list(limited_G.edges())
        for _ in range(trials):
            H = nx.Graph()
            H.add_nodes_from(limited_G.nodes())
            for e in edges:
                if random.random() < p_edge:
                    H.add_edge(*e)
            if s in H and d in H and nx.has_path(H, s, d):
                self.path_up_frames.append(H)
            else:
                self.path_down_frames.append(H) 

    def generateMPCFrames(self,
                                  limited_G: nx.Graph,
                                  pairs: List[Tuple[str, str]],
                                  trials: int = 1000,
                                  p_edge: float = 0.5,
                                  seed: int = None) -> Dict:
        """
        Generate `trials` random frames from `limited_G` and for each frame evaluate
        reachability for each pair in `pairs`.

        Returns a dict with:
          - frames: list of generated nx.Graph objects (length == trials)
          - cases: dict mapping status_tuple -> list of frame indices where that exact pattern occurs
                   (status_tuple is tuple(bool, ...) in same order as `pairs`)
          - counts: dict mapping status_tuple -> integer count
          - per_pair: list aligned with `pairs`, each entry is {'pair': (s,d), 'up_indices': [...], 'down_indices': [...]}

        Example keys in cases:
          (False, False, False) -> all pairs down
          (True, False, False)  -> first pair up, others down
          (True, True, True)    -> all pairs up
        """
        rnd = random.Random(seed)
        edges = list(limited_G.edges())

        frames: List[nx.Graph] = []
        cases: Dict[Tuple[bool, ...], List[int]] = {}
        per_pair: List[Dict] = []
        for (s, d) in pairs:
            per_pair.append({"pair": (s, d), "up_indices": [], "down_indices": []})

        for ti in range(trials):
            # build random frame
            H = nx.Graph()
            H.add_nodes_from(limited_G.nodes())
            for e in edges:
                if rnd.random() < p_edge:
                    H.add_edge(*e)
            frames.append(H)

            # evaluate each pair
            status: List[bool] = []
            for pi, (s, d) in enumerate(pairs):
                try:
                    up = (s in H and d in H and nx.has_path(H, s, d))
                except (nx.NetworkXError, nx.NodeNotFound):
                    up = False
                status.append(bool(up))
                if up:
                    per_pair[pi]["up_indices"].append(ti)
                else:
                    per_pair[pi]["down_indices"].append(ti)

            status_t = tuple(status)
            cases.setdefault(status_t, []).append(ti)

        counts = {k: len(v) for k, v in cases.items()}

        return {
            "frames": frames,
            "cases": cases,
            "counts": counts,
            "per_pair": per_pair,
            "pairs": list(map(tuple, pairs))
        }

    def clear_frames(self) -> None:
        self.path_up_frames.clear()
        self.path_down_frames.clear()