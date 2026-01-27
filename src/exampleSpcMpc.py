"""
Entry point for the YaDyGaGa application.

This module orchestrates the overall functionality of the project by utilizing
the classes defined in the other modules. It may include example usage of
the FrameGenerator, PropertiesChecker, TimelineBlockGenerator, TimelineAssembler,
and TimelineVisualizer classes.
"""
import networkx as nx
import numpy as np

import parameter
from sourceGraphAugmenter import SourceGraphAugmenter
from frameGenerator import FrameGenerator
from timelineBlockGenerator import SPCTimelineBlockGenerator, MPCTimelineBlockGenerator
from dynaGraph import dynamicGraph, SPCDynamicGraph, MPCDynamicGraph
from dyCoDeTa import DynaGraphCommuDetection, AnalyzerDynaCommu, visualizer
from visualizer import Visualizer
from propertiesChecker import PropertiesChecker

def main(test: str = "SPC", viz: bool = False):

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
    
    
    test = "Dynamic community detection"  # Options: "SPC" (Single Path Constraint), "MPC" (Multi Path Constraint), "Dynamic community detection" (self explanatory), "sweep" (parameter sweep example)
    viz = True

    parameters = parameter.timeline_feasible_params(frames=600, stability=0.8)
    print("Feasible parameters for 600 frames and stability 0.8: ", parameters["feasible_path_life"])

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
        print("Community based node placement for frame 1: ", comm_mapper)
        #detector.plotCommuMapper()
        detector.HspacePlacement(frame_index=0)
        print("Community positions in H space for frame 1: ", detector.HspaceMapper[0])
        detector.plotHspacePlacement(frame_index=0)


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

    if test == "Dynamic community detection":
        DynaGa = dynamicGraph()
        G1 = nx.Graph()
        G1.add_edges_from([("A", "D"), ("A", "E"), ("A", "B"), ("D", "B"),("D", "E"),("B", "E"), ("B", "F"),("B","C"),("C", "F"),("C","E"),("E","F"),
                           ("E","G"),("G","H"),("G","J"),("G","I"),("H","I"),("I","J"),("H","J"),
                           ("K","L"),("K","M"),("K","N"),("K","O"),("L","M"),("M","N"),("N","O"),("O","L"),("L","N"),("M","O"),("K","C"),("N","J")
                           ])
        G2 = nx.Graph()
        G2.add_edges_from([("A", "D"), ("A", "E"), ("A", "B"), ("D", "B"),("D", "E"),("B", "E"), ("B", "F"),("B","C"),("C", "F"),("C","E"),("E","F"),
                           ("E","G"),("G","H"),("G","J"),("G","I"),("H","I"),("I","J"),("H","J"),
                           ("K","L"),("K","M"),("K","N"),("K","O"),("L","M"),("M","N"),("N","O"),("O","L"),("L","N"),("M","O"),("K","C"),("N","J")
                           ])
        G3 = nx.Graph()
        G3.add_edges_from([("A", "D"), ("A", "E"), ("A", "B"), ("D", "B"),("D", "E"),("B", "E"), ("B", "F"),("B","C"),("C", "F"),("C","E"),("E","F"),
                           ("E","G"),("G","H"),("O","J"),("G","I"),("H","I"),("L","J"),("M","J"),
                           ("K","L"),("K","M"),("K","N"),("K","O"),("L","M"),("M","N"),("N","O"),("O","L"),("L","N"),("M","O"),("K","C"),("N","J")
                           ])
        G4 = nx.Graph()
        G4.add_edges_from([("A", "D"), ("A", "E"), ("A", "B"), ("D", "B"),("D", "E"),("B", "E"), ("B", "F"),("B","C"),("C", "F"),("C","E"),("E","F"),
                           ("E","G"),("G","H"),("G","J"),("G","I"),("H","I"),("I","J"),("H","J"),
                           ("K","L"),("K","M"),("K","N"),("K","O"),("L","M"),("M","N"),("N","O"),("O","L"),("L","N"),("M","O"),("K","C"),("N","J")
                           ])
        DynaGa.appendGraph(G1)
        DynaGa.appendGraph(G2)
        DynaGa.appendGraph(G3)
        DynaGa.appendGraph(G4)
        
        print("Dynamic Community Detection Test")
        # Using the SPCDynamicGraph from the previous SPC test
        detector = DynaGraphCommuDetection(DynaGa.DynamicGraph, method="louvain", seed = 444)
        communities = detector.detectStatCommunities()
        print("Detected communities for frame 1: ", communities[0])
        comm_mapper = detector.unitCirclePlacement()
        print("Community based node placement for frame 1: ", comm_mapper)
        if viz == True:
            detector.plotCommuMapper()
        detector.HspacePlacement(frame_index=0)
        print("Community positions in H space for frame 1: ", detector.HspaceMapper[0])
        if viz == True:
            detector.plotHspacePlacement(frame_index=0)
        detector.HspacePropagation(threshold=0.5)
        if viz == True:
            detector.plotDynaCommunity()

        #Exemple of usage of AnalyzerDynaCommu
        analyzer = AnalyzerDynaCommu(detector.dynaCommunity)
        dynaCommulifetime = analyzer.commuLifeTime()
        print("Dynamic community lifetime: ", dynaCommulifetime)
        flexibilityScores = analyzer.flexibility()
        print("Flexibility scores: ", flexibilityScores)
        if viz == True:
            vizu = visualizer(DynaGa.DynamicGraph, flexibilityScores)
            vizu.flexibilityVisualization()
        
        return
    
    if test == "sweep":
        pairs = [("A","F"), ("C","F")]
        sweepResults = sweep_mpc_generate(dynamic_graph_base=G,pairs=pairs, frames=100, path_life=0.5, step=0.1, mode="indep", trials=1000, p_edge=0.5, seed=42)
        print("Sweep done")
        parameter.save_sweep_results_as_adj_matrices(sweepResults, out_dir="./sweep_results/")
        return
    
    print("No test selected. Exiting.")
    return


def sweep_mpc_generate(dynamic_graph_base, pairs, frames: int, path_life: float = None, stability: float = None,
                       step: float = 0.1, mode: str = "indep", trials: int = 1000, p_edge: float = 0.5, seed: int = 42):
    """
    Sweep the unspecified parameter (path_life or stability) using timeline_feasible_params,
    build one MPC dynamic graph per step, and return a list of results.

    Returns a list of dicts: {'param_name': 'path_life'|'stability', 'param_value': v, 'timeline': timeline, 'dynamic_graph': dynamic_graph}
    """
    if (path_life is None) == (stability is None):
        raise ValueError("Provide exactly one of path_life or stability")

    params_info = parameter.timeline_feasible_params(frames=frames, path_life=path_life, stability=stability)
    results = []

    # prepare augmented base graph and frame generator once
    limitedMPC = SourceGraphAugmenter.augmentBaseGraph(dynamic_graph_base, pairs, seed=seed, verbose=False)
    frame_generator = FrameGenerator()

    nPairs = len(pairs)

    if path_life is not None:
        # produce stability values in feasible range
        s_min, s_max = params_info.get('feasible_stability', (0.0, 1.0))
        vals = np.arange(s_min, s_max + 1e-9, step)
        param_name = "stability"
        for v in np.unique(np.round(vals, 6)):
            stability_v = float(np.clip(v, 0.0, 1.0))
            # generate MPC frame set (sampling frames for each pair)
            MPCFrameSet = frame_generator.generateMPCFrames(limitedMPC, pairs, trials=trials, p_edge=p_edge, seed=seed)
            # generate timeline with current parameters
            timelineGen = MPCTimelineBlockGenerator(frames, nPairs, path_life, stability_v, mode, seed=seed)
            timeline = timelineGen.generate()
            MPCDynaGA = MPCDynamicGraph()
            MPCDynaGA.buildDynaGraph(timeline, MPCFrameSet)
            results.append({
                'param_name': param_name,
                'param_value': stability_v,
                'timeline': timeline,
                'dynamic_graph': MPCDynaGA.DynamicGraph
            })

    else:
        # stability provided -> sweep path_life values in feasible range
        feasible = params_info.get('feasible_path_life')
        if feasible is None:
            return results
        a_min, a_max = feasible
        vals = np.arange(a_min, a_max + 1e-9, step)
        param_name = "path_life"
        for v in np.unique(np.round(vals, 6)):
            path_life_v = float(np.clip(v, 0.0, 1.0))
            MPCFrameSet = frame_generator.generateMPCFrames(limitedMPC, pairs, trials=trials, p_edge=p_edge, seed=seed)
            timelineGen = MPCTimelineBlockGenerator(frames, nPairs, path_life_v, stability, mode, seed=seed)
            timeline = timelineGen.generate()
            MPCDynaGA = MPCDynamicGraph()
            MPCDynaGA.buildDynaGraph(timeline, MPCFrameSet)
            results.append({
                'param_name': param_name,
                'param_value': path_life_v,
                'timeline': timeline,
                'dynamic_graph': MPCDynaGA.DynamicGraph
            })

    return results

if __name__ == "__main__":
    main()
