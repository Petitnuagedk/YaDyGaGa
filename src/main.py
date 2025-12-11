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
from timeline_block_generator import SPCTimelineBlockGenerator, MPCTimelineBlockGenerator
from DynaGraph import DynamicGraph
from visualizer import Visualizer
from properties_checker import PropertiesChecker

def main():

    G = nx.Graph()
    G.add_edges_from([
        ("A", "C"), ("B", "C"), ("C", "E"), ("D", "B"),
        ("E", "F")])
    
    test = "MPC"  # Options: "SPC" (Single Path Constraint), "MPC" (Multi Path Constraint)

        # Single path constraint exemple
    if test == "SPC":
        print("Single Path Constraint Test")
        S = "A" # source
        D = "F" # destination
        limitedSPC = SourceGraphAugmenter.augmentBaseGraph(G, [(S, D)],
                                                        seed = 1,
                                                        verbose = False)
        print("Original Graph edges: ", G.edges())
        print("Limited Graph edges: ", limitedSPC.edges())

        frame_generator = FrameGenerator()
        frame_generator.generate_frames(limitedSPC, S, D, trials=1000, p_edge=0.5)

        pathUpFrames = frame_generator.path_up_frames
        pathDownFrames = frame_generator.path_down_frames

        frames = 50 # need to change name to make it more clear, this is number of timeline frames
        InversepathLength = 1 # TODO : enforce geometric path length constraint in timeline generation
        path_life = 0.5
        stability = 0.8
        mode = "blocks"

        timeline_block_generator = SPCTimelineBlockGenerator(frames, path_life, stability, mode)
        timeLine = timeline_block_generator.generate_blocks()

        print("Time line : ", timeLine)

        DynaGA = DynamicGraph()
        DynaGA.buildDynaGraph(timeLine, pathUpFrames, pathDownFrames)
        DynaGAset = DynaGA.generate_unique_set(timeLine, pathUpFrames, pathDownFrames, target_count=5, seed = 42, max_enumeration=1000)


        path_lifetime = PropertiesChecker.path_lifetime(graphs=DynaGA.DynamicGraph, source=S, destination=D, fps=1)
        print("Path lifetime properties: ", path_lifetime)

        path_stability = PropertiesChecker.path_stability(graphs=DynaGA.DynamicGraph, source=S, destination=D)
        print("Path stability properties: ", path_stability)

        path_length = PropertiesChecker.path_length(graphs=DynaGA.DynamicGraph, source=S, destination=D)
        print("Path length properties: ", path_length)

        print("Dynamic Graph length: ", len(DynaGA.DynamicGraph))

        timeline_visualizer = Visualizer(timeLine)
        timeline_visualizer.visualize_dynamic_graph(DynaGA.DynamicGraph)
        timeline_visualizer.animate_random_dynamics(DynaGAset, n=2, interval=1000)

        return

    # -----------------------------
    # Multi path constraint exemple

    if test == "MPC":
        pairs = [("A","F"), ("C","F")]
        limitedMPC = SourceGraphAugmenter.augmentBaseGraph(G, pairs,
                                                        seed = 1,
                                                        verbose = False)
        print("Original Graph edges: ", G.edges())
        print("Limited Graph edges: ", limitedMPC.edges())

        frame_generator = FrameGenerator()
        dic = frame_generator.generate_frames_for_pairs(limitedMPC,
                                                        pairs,
                                                        trials=1000,
                                                        p_edge=0.5,
                                                        seed = 1)
        
        frames = 20
        nPairs = len(pairs)
        pathLifeTime = 0.5
        stability = 1
        mode = "indep"
        timelineGen = MPCTimelineBlockGenerator(frames, nPairs, pathLifeTime, stability, mode, seed = 40)
        # timeline_block_generator = SPCTimelineBlockGenerator(frames, path_life, stability, mode)
        timeLine = timelineGen.generate()
        print("Time line : ", timeLine)
        print(timelineGen.computeStatistics(timeLine))

        # print("len of dic: ", len(dic))
        # print("Generated frames: ", len(dic['frames']))
        # print("Cases found: ", len(dic['cases']))
        # print("Counts per case: ", dic['counts'])
        # print(len(dic['counts'].keys()), " unique cases found.")


        # this
        # print("case (True, True): ", dic['cases'].get((True, True), []))
        ## ---
        # print("pairs: ", len(dic['per_pair']))
        # print("frame_0", dic["frames"][0].edges())
        # print("A graph where (A,F) is up: ", dic['frames'][dic['per_pair'][0]['up_indices'][0]].edges())
        # print("pairs summary: ", dic['pairs'])
        #print("Per pair details: ", dic['per_pair'])
        #print("Frames where (A,F) is up: ", dic['per_pair'][0]['up_indices'])
        return



if __name__ == "__main__":
    main()
