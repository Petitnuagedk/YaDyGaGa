"""
Entry point for the YaDyGaGa application.

This module orchestrates the overall functionality of the project by utilizing
the classes defined in the other modules. It may include example usage of
the FrameGenerator, PropertiesChecker, TimelineBlockGenerator, TimelineAssembler,
and TimelineVisualizer classes.
"""
import networkx as nx

from frame_generator import FrameGenerator
from timeline_block_generator import TimelineBlockGenerator
from DynaGraph import DynamicGraph
from visualizer import Visualizer
from properties_checker import PropertiesChecker

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

def main():

    G = nx.Graph()
    G.add_edges_from([
        ("A", "C"), ("B", "C"), ("C", "E"), ("D", "B"),
        ("E", "F")
        ])
    S, D = "A", "F"
    limited = augment_graph_keep_baseline(G, S, D)
    # Example usage of the classes
    frame_generator = FrameGenerator()
    frame_generator.generate_frames(limited, S, D, trials=1000, p_edge=0.5)

    pathUpFrames = frame_generator.path_up_frames
    pathDownFrames = frame_generator.path_down_frames
    # properties_checker = PropertiesChecker()
    frames = 10
    path_life = 0.5
    stability = 1
    mode = "blocks"
    timeline_block_generator = TimelineBlockGenerator(frames, path_life, stability, mode)
    timeLine = timeline_block_generator.generate_blocks()

    print("Time line : ", timeLine)

    DynaGA = DynamicGraph()
    DynaGA.buildDynaGraph(timeLine, pathUpFrames, pathDownFrames)

    DynaGAset = DynaGA.generate_unique_set(timeLine, pathUpFrames, pathDownFrames, target_count=5, randomize=True, max_enumeration=1000)


    path_lifetime = PropertiesChecker.path_lifetime(graphs=DynaGA.DynamicGraph, source=S, destination=D, fps=1)
    print("Path lifetime properties: ", path_lifetime)

    path_stability = PropertiesChecker.path_stability(graphs=DynaGA.DynamicGraph, source=S, destination=D)
    print("Path stability properties: ", path_stability)

    path_length = PropertiesChecker.path_length(graphs=DynaGA.DynamicGraph, source=S, destination=D)
    print("Path length properties: ", path_length)

    print("Dynamic Graph length: ", len(DynaGA.DynamicGraph))
    timeline_visualizer = Visualizer(timeLine)
    timeline_visualizer.visualize_dynamic_graph(DynaGA.DynamicGraph)
    #timeline_visualizer.plot_random_dynamics(DynaGAset, n=3, pick_frame='random', figsize=(15, 5))
    timeline_visualizer.animate_random_dynamics(DynaGAset, n=2, pick_frame='random', interval=1000)
if __name__ == "__main__":
    main()
