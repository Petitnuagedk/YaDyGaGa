import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import networkx as nx
from src.sourceGraphAugmenter import SourceGraphAugmenter
from src.frameGenerator import FrameGenerator
from src.timelineBlockGenerator import SPCTimelineBlockGenerator
from src.dynaGraph import SPCDynamicGraph
from src.propertiesChecker import PropertiesChecker

def main():
    # small demo SPC example
    G = nx.Graph()
    G.add_edges_from([("A", "C"), ("B", "C"), ("C", "E"), ("D", "B"), ("E", "F")])

    S, D = "A", "F"
    limited = SourceGraphAugmenter.augmentBaseGraph(G, [(S, D)], seed=1, verbose=False)

    fg = FrameGenerator()
    fg.generateSPCFrames(limited, S, D, trials=500, p_edge=0.5, pathPersistency=0.9)
    up = fg.path_up_frames
    down = fg.path_down_frames

    timeline_gen = SPCTimelineBlockGenerator(frames=30, path_life=0.4, stability=0.8, seed=42, mode="blocks", pathPersistency=0.9)
    tl = timeline_gen.generate_blocks()

    dyna = SPCDynamicGraph()
    dyna.buildDynaGraph(tl, up, down)
    print("Built single SPC DynamicGraph length:", len(dyna.DynamicGraph))

    # try to build a small unique set
    sset = dyna.generateUniqueSet(tl, up, down, target_count=3, seed=42, max_enumeration=2000)
    print("Unique SPC dynamics found:", len(sset))
    if sset:
        lif = PropertiesChecker.path_lifetime(graphs=sset[0].DynamicGraph, source=S, destination=D, fps=1)
        print("Example path lifetime (first DG):", lif)

if __name__ == "__main__":
    main()