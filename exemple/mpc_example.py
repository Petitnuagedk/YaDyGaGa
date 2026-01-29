import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import networkx as nx
from src.sourceGraphAugmenter import SourceGraphAugmenter
from src.frameGenerator import FrameGenerator
from src.timelineBlockGenerator import MPCTimelineBlockGenerator
from src.dynaGraph import MPCDynamicGraph

def main():
    G = nx.Graph()
    G.add_edges_from([("A", "C"), ("B", "C"), ("C", "E"), ("D", "B"), ("E", "F")])

    pairs = [("A", "D"), ("C", "F")]
    limited = SourceGraphAugmenter.augmentBaseGraph(G, pairs, seed=1, verbose=False)

    fg = FrameGenerator()
    mpc_frames = fg.generateMPCFrames(limited, pairs, trials=1000, p_edge=0.5, seed=1)

    timeline_gen = MPCTimelineBlockGenerator(frames=20, n_pairs=len(pairs), path_life=0.5, stability=0.8, mode="indep", seed=40, pathPersistency=0.8)
    tl = timeline_gen.generate()
    print("Sample MPC timeline (len):", len(tl))

    dyna = MPCDynamicGraph()
    # single greedy build (sanity)
    dyna.buildDynaGraph(tl, mpc_frames, seed=1, no_double=True, allow_hamming_fallback=True, force=True)
    print("Single MPC DynamicGraph length:", len(dyna.DynamicGraph))
    print("Selected indices:", getattr(dyna, "selected_frame_indices", None))

    # try to generate a small set
    dset = dyna.generateUniqueSet(tl, mpc_frames, target_count=2, seed=42, max_enumeration=5000, force=True)
    print("Unique MPC dynamics found:", len(dset))
    if dset:
        print("First DG selected indices:", getattr(dset[0], "selected_frame_indices", None))

if __name__ == "__main__":
    main()