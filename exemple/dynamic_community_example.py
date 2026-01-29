import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import networkx as nx
from dynaGraph import dynamicGraph
from dyCoDeTa import DynaGraphCommuDetection

def main():
    # build a tiny dynamic graph (4 frames) for community test
    DG = dynamicGraph()
    G1 = nx.erdos_renyi_graph(8, 0.4, seed=1)
    G2 = nx.erdos_renyi_graph(8, 0.35, seed=2)
    G3 = nx.erdos_renyi_graph(8, 0.3, seed=3)
    G4 = nx.erdos_renyi_graph(8, 0.25, seed=4)
    DG.appendGraph(G1); DG.appendGraph(G2); DG.appendGraph(G3); DG.appendGraph(G4)

    detector = DynaGraphCommuDetection(DG.DynamicGraph, method="louvain", seed=42)
    comms = detector.detectStatCommunities()
    print("Detected communities for frame 0:", comms[0])
    print("Number of frames:", len(DG.DynamicGraph))

if __name__ == "__main__":
    main()