from typing import List, Tuple
import random
import networkx as nx

class DynamicGraph:
    """
    Assembles generated timeline blocks into a cohesive timeline called a DynamicGraph.
    """

    def __init__(self):
        self.DynamicGraph = []
    
    def buildDynaGraph(self, timeline: List[bool], path_up: List[nx.Graph], path_down: List[nx.Graph]):
        """
        Given a timeline of booleans and two sets of frames (path_up and path_down),
        pick frames according to the timeline.

        :param timeline: List of booleans where True indicates "path up" and False indicates "path down".
        :param path_up: List of frames where the path exists.
        :param path_down: List of frames where the path does not exist.
        :return: List of selected frames according to the timeline.
        """
        for state in timeline:
            pool = path_up if state else path_down
            if not pool:
                # fallback to the other non-empty pool or an empty graph
                pool = path_down if path_up else (path_up if path_down else [])
            if pool:
                self.DynamicGraph.append(random.choice(pool))
            else:
                # empty graph with same nodes (no edges)
                # Try to infer node list from any available graph in pool arguments (not ideal)
                self.DynamicGraph.append(nx.Graph())

    def addGraphatindex(self, index: int, graph: nx.Graph):
        """
        Add a graph at a specific index in the DynamicGraph.

        :param index: Index at which to add the graph.
        :param graph: The graph to add.
        """
        if 0 <= index <= len(self.DynamicGraph):
            self.DynamicGraph.insert(index, graph)
        else:
            raise IndexError("Index out of bounds for DynamicGraph.")

    def clearDynaGaph(self):
        """
        Clear all added timeline blocks.
        """
        self.DynamicGraph = []