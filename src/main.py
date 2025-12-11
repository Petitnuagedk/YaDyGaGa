"""
Entry point for the YaDyGaGa application.

This module orchestrates the overall functionality of the project by utilizing
the classes defined in the other modules. It may include example usage of
the FrameGenerator, PropertiesChecker, TimelineBlockGenerator, TimelineAssembler,
and TimelineVisualizer classes.
"""
import networkx as nx

from SourceGraphAugmenter import SourceGraphAugmenter
from frame_generator import FrameGenerator
from timeline_block_generator import TimelineBlockGenerator
from DynaGraph import DynamicGraph
from visualizer import Visualizer
from properties_checker import PropertiesChecker

def main():

    G = nx.Graph()
    G.add_edges_from([
        ("A", "C"), ("B", "C"), ("C", "E"), ("D", "B"),
        ("E", "F")
        ])
    S, D = "A", "F"
    limited = SourceGraphAugmenter.augment_graph_keep_baseline(G, S, D)
    limited_group = SourceGraphAugmenter.augment_graph_keep_group_baseline(G, [("A","F"), ("C","F")],
                                                                            seed = 1,
                                                                            verbose = True)
    print("Original Graph edges: ", G.edges())
    print("Limited Graph edges: ", limited.edges())
    print("Limited group Graph edges: ", limited_group.edges())
    return
    # Example usage of the classes
    frame_generator = FrameGenerator()
    frame_generator.generate_frames(limited, S, D, trials=1000, p_edge=0.5)

    pathUpFrames = frame_generator.path_up_frames
    pathDownFrames = frame_generator.path_down_frames
    # properties_checker = PropertiesChecker()
    frames = 50
    InversepathLength = 1 # TODO
    path_life = 0.5
    stability = 0.8
    mode = "blocks"
    timeline_block_generator = TimelineBlockGenerator(frames, path_life, stability, mode)
    timeLine = timeline_block_generator.generate_blocks()

    print("Time line : ", timeLine)

    DynaGA = DynamicGraph()
    DynaGA.buildDynaGraph(timeLine, pathUpFrames, pathDownFrames)

    #DynaGAset = DynaGA.generate_unique_set(timeLine, pathUpFrames, pathDownFrames, target_count=5, randomize=True, max_enumeration=1000)


    path_lifetime = PropertiesChecker.path_lifetime(graphs=DynaGA.DynamicGraph, source=S, destination=D, fps=1)
    print("Path lifetime properties: ", path_lifetime)

    path_stability = PropertiesChecker.path_stability(graphs=DynaGA.DynamicGraph, source=S, destination=D)
    print("Path stability properties: ", path_stability)

    path_length = PropertiesChecker.path_length(graphs=DynaGA.DynamicGraph, source=S, destination=D)
    print("Path length properties: ", path_length)

    print("Dynamic Graph length: ", len(DynaGA.DynamicGraph))
    #timeline_visualizer = Visualizer(timeLine)
    #timeline_visualizer.visualize_dynamic_graph(DynaGA.DynamicGraph)
    #timeline_visualizer.animate_random_dynamics(DynaGAset, n=2, interval=1000)



if __name__ == "__main__":
    main()
