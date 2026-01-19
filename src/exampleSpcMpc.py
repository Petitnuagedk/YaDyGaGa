"""
Entry point for the YaDyGaGa application.

This module orchestrates the overall functionality of the project by utilizing
the classes defined in the other modules. It may include example usage of
the FrameGenerator, PropertiesChecker, TimelineBlockGenerator, TimelineAssembler,
and TimelineVisualizer classes.
"""
import networkx as nx

from sourceGraphAugmenter import SourceGraphAugmenter
from frameGenerator import FrameGenerator
from timelineBlockGenerator import SPCTimelineBlockGenerator, MPCTimelineBlockGenerator
from dynaGraph import SPCDynamicGraph, MPCDynamicGraph
from dyCoDeTa import DynaGraphCommuDetection
from visualizer import Visualizer
from propertiesChecker import PropertiesChecker

def main(test: str = "SPC"):

    G = nx.Graph()
    G.add_edges_from([
        ("A", "C"), ("B", "C"), ("C", "E"), ("D", "B"),
        ("E", "F")])
    
    print("\n This is a demo case for YADYGAGA, a path constraint Dynamic graph generator\n")
    print("\n The demonstration will be made on the following graph:\n")
    print("         A         ")
    print("          \        ")
    print("       B---C       ")
    print("       |   |       ")
    print("       D   E       ")
    print("          /        ")
    print("         F         \n")
    print("Where the, in the case of SPC test, the constraint path is bewteen the pair A-F")
    print("and in the case of MPC test, pairs constraints are A-F and C-F\n")
    
    
    test = "SPC"  # Options: "SPC" (Single Path Constraint), "MPC" (Multi Path Constraint)
    viz = False

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
        frame_generator.generateSPCFrames(limitedSPC, S, D, trials=1000, p_edge=0.5)

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

        DynaGA = SPCDynamicGraph()
        DynaGA.buildDynaGraph(timeLine, pathUpFrames, pathDownFrames)
        DynaGAset = DynaGA.generate_unique_set(timeLine, pathUpFrames, pathDownFrames, target_count=5, seed = 42, max_enumeration=1000)


        path_lifetime = PropertiesChecker.path_lifetime(graphs=DynaGA.DynamicGraph, source=S, destination=D, fps=1)
        print("Path lifetime properties: ", path_lifetime)

        path_stability = PropertiesChecker.path_stability(graphs=DynaGA.DynamicGraph, source=S, destination=D)
        print("Path stability properties: ", path_stability)

        path_length = PropertiesChecker.path_length(graphs=DynaGA.DynamicGraph, source=S, destination=D)
        print("Path length properties: ", path_length)

        print("Dynamic Graph length: ", len(DynaGA.DynamicGraph))

        detector = DynaGraphCommuDetection(DynaGA.DynamicGraph, method="louvain", seed = 444)
        communities = detector.detectStatCommunities()
        print("Detected communities fro frame 1: ", communities[0])
        comm_mapper = detector.unitCirclePlacement()
        #print("Community based node placement for frame 1: ", comm_mapper)
        #detector.plotCommuMapper()

        if viz == True:
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
        print("\n","Original Graph edges: ", G.edges())
        print("Limited Graph edges: ", limitedMPC.edges(), "\n")
        frame_generator = FrameGenerator()
        MPCFrameSet = frame_generator.generateMPCFrames(limitedMPC,
                                                        pairs,
                                                        trials=1000,
                                                        p_edge=0.5,
                                                        seed = 1)
        
        frames = 50
        nPairs = len(pairs)
        pathLifeTime = 0.5
        stability = 1
        mode = "indep" # options: "sync" (default) or "indep"
        timelineGen = MPCTimelineBlockGenerator(frames, nPairs, pathLifeTime, stability, mode, seed = 40)
        # timeline_block_generator = SPCTimelineBlockGenerator(frames, path_life, stability, mode)
        timeLine = timelineGen.generate()
        # print("Time line : ", timeLine, "\n")
        # print(timelineGen.computeStatistics(timeLine), "\n")

        MPCDynaGA = MPCDynamicGraph()
        MPCDynaGA.buildDynaGraph(timeLine, MPCFrameSet)
        MPCDynaGAset = MPCDynaGA.generate_unique_set(timeLine, MPCFrameSet, target_count=5, seed = 42, max_enumeration=1000)

        if viz == True:
            timeline_visualizer = Visualizer(timeLine)
            timeline_visualizer.visualize_dynamic_graph(MPCDynaGA.DynamicGraph)
            timeline_visualizer.animate_random_dynamics(MPCDynaGAset, n=2, interval=1000)
        return



if __name__ == "__main__":
    main()
