"""
FrameGenerator class responsible for generating frames based on specified parameters.

Methods:
- generate_frames: Generates frames based on input parameters.
- get_frame_data: Retrieves the generated frame data.
- clear_frames: Clears the current frame data.
"""

from typing import List
import random
import networkx as nx


class FrameGenerator:
    def __init__(self):
        self.path_up_frames = []
        self.path_down_frames = []

    def generate_frames(self, limited_G: nx.Graph, s: str, d: str, trials: int = 1000, p_edge: float = 0.5) -> None:
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
    

    def get_frame_data(self) -> List[nx.Graph]:
        return self.frames

    def clear_frames(self) -> None:
        self.frames.clear()