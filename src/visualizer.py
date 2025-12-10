"""
Module for visualizing timelines.
"""
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import networkx as nx

class Visualizer:
    def __init__(self, timeline):
        self.timeline = timeline

    def render_text(self):
        """Render the timeline as a text representation."""
        return ' '.join(['UP' if state else 'DOWN' for state in self.timeline])

    def render_graphically(self):
        """Render the timeline graphically (placeholder for actual implementation)."""
        import matplotlib.pyplot as plt

        plt.figure(figsize=(10, 2))
        plt.plot(self.timeline, drawstyle='steps-post')
        plt.yticks([0, 1], ['DOWN', 'UP'])
        plt.title('Timeline Visualization')
        plt.xlabel('Frames')
        plt.ylabel('State')
        plt.grid(True)
        plt.show()

    def save_to_file(self, filename):
        """Save the timeline visualization to a file."""
        with open(filename, 'w') as f:
            f.write(self.render_text())

    def visualize_dynamic_graph(self, graphs, interval=1000, loop=True, node_pos=None,
                                node_size=300, node_color='skyblue', edge_color='gray',
                                absent_node_color='lightgray', with_labels=True):
        """
        Visualize a sequence (list) of networkx graphs as an animation using matplotlib.
        - graphs: list of networkx.Graph (or DiGraph) objects, one per frame.
        - interval: milliseconds between frames (default 1000 => 1 frame per second).
        - loop: whether the animation repeats after the last frame.
        - node_pos: optional dict {node: (x,y)} for consistent layout; if None, layout is computed
                    from the union of all graphs.
        - node_size, node_color, edge_color, absent_node_color, with_labels: drawing options.
        Returns the matplotlib.animation.FuncAnimation object.
        """

        if not graphs:
            raise ValueError("graphs list is empty")

        # Build union graph to have consistent node set and positions
        union = nx.Graph()
        for g in graphs:
            union.add_nodes_from(g.nodes())
            union.add_edges_from(g.edges())

        # Compute positions once unless provided
        if node_pos is None:
            # deterministic layout with seed for reproducibility
            pos = nx.circular_layout(union)
        else:
            pos = node_pos

        fig, ax = plt.subplots(figsize=(6, 6))
        ax.set_title("Dynamic Graph Visualization")
        ax.axis('off')

        def update(frame_index):
            ax.clear()
            ax.set_title(f"Frame {frame_index + 1}/{len(graphs)}")
            ax.axis('off')

            G = graphs[frame_index]

            # Node colors: highlight nodes present in this frame, fade absent ones
            node_list = list(union.nodes())
            node_colors = [
                node_color if (n in G.nodes()) else absent_node_color
                for n in node_list
            ]

            # Draw nodes from the union so positions stay stable
            nx.draw_networkx_nodes(union, pos, nodelist=node_list,
                                   node_color=node_colors, node_size=node_size, ax=ax)
            # Draw edges only for current frame (G)
            nx.draw_networkx_edges(G, pos, edge_color=edge_color, ax=ax)
            if with_labels:
                nx.draw_networkx_labels(union, pos, ax=ax)

        ani = FuncAnimation(fig, update, frames=range(len(graphs)),
                            interval=interval, repeat=loop)

        plt.show()
        return ani

