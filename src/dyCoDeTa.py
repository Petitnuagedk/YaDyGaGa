import networkx as nx
import numpy as np
import matplotlib.pyplot as plt

class DynaGraphCommuDetection:
    def __init__(self, dynamic_graph, method="louvain", seed = 444):
        self.dynamic_graph = dynamic_graph
        self.community = [] # [C1, C2, C3, ...] where Ci is the community at time i
        self.dynaCommunity = [] # [[C1_t1, C2_t1, ...], [C1_t2, C2_t2, ...], ...] where Ci_tj is the community i at time j
        self.method = method
        self.seed = seed
        self.CommuMapper = {} # Map the nodes to their positions

    def detectStatCommunities(self):
        for frame in self.dynamic_graph:
            if self.method == "louvain":
                partition = nx.community.louvain_communities(frame, self.seed)
                self.community.append(partition)
            # TODO : add more methods here (walktrap, girvan-newman, etc.)
            else:
                raise ValueError(f"Unknown community detection method: {self.method}")
        return self.community

    def unitCirclePlacement(self):
        # Take the community detected on the first frame and place nodes in unit circle
        if not self.community:
            self.detectStatCommunities()
        fstFrameCommu = self.community[0]
        numNodes = self.dynamic_graph[0].number_of_nodes()

        for comm in fstFrameCommu:
            for node in comm:
                index = list(self.dynamic_graph[0].nodes()).index(node)
                print(index)
                angle = 2 * np.pi * index / numNodes
                x = 0.5 + 0.4 * np.math.cos(angle)
                y = 0.5 + 0.4 * np.math.sin(angle)
                self.CommuMapper[node] = (x, y)
        return self.CommuMapper

    def plotCommuMapper(self):
        comm_mapper = self.unitCirclePlacement()
        x_vals = [pos[0] for pos in comm_mapper.values()]
        y_vals = [pos[1] for pos in comm_mapper.values()]
        labels = list(comm_mapper.keys())

        plt.figure(figsize=(6, 6))
        plt.scatter(x_vals, y_vals)

        for label, x, y in zip(labels, x_vals, y_vals):
            plt.text(x, y, label, fontsize=9, ha='right')

        plt.title("Node Placement Based on Communities")
        plt.xlabel("X")
        plt.ylabel("Y")
        plt.axis('equal')
        plt.grid(True)
        plt.show()



# Convert partition dict to list of communities
#         comm_dict = {}
#         for node, comm_id in partition.items():
#             comm_dict.setdefault(comm_id, []).append(node)
#         self.dynaCommunity.append(list(comm_dict.values()))
#     else:
#         raise ValueError(f"Unknown community detection method: {self.method}")
# return self.dynaCommunity