"""
Module for visualizing timelines.
"""
import random
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

    def animate_random_dynamics(self,
                                dynamics,
                                n: int = 5,
                                interval: int = 1000,
                                loop: bool = True,
                                pick_frame: str = 'random',
                                seed: int = None,
                                figsize=(15, 3),
                                node_size=300,
                                node_color='skyblue',
                                absent_node_color='lightgray',
                                edge_color='gray',
                                with_labels=True):
        """
        Pick up to `n` dynamics from `dynamics` (randomly, deterministically with seed)
        and animate them side-by-side. Each subplot cycles through the frames of its
        dynamic; shorter dynamics are looped (frame index modulo length).

        Parameters:
          - dynamics: list of DynamicGraph objects (attr `.DynamicGraph`) or lists of nx.Graph
          - n: number of dynamics to select and show (default 5)
          - interval: ms between frames (default 1000ms -> 1fps)
          - loop: whether animation repeats after last frame
          - pick_frame: (kept for parity with plot_random_dynamics) not used for animation
          - seed: optional int to make selection deterministic
          - figsize: figure size (width, height)
          - drawing options: node_size, node_color, absent_node_color, edge_color, with_labels

        Returns matplotlib.animation.FuncAnimation
        """
        if seed is not None:
            random.seed(seed)

        # normalize dynamics into list of list-of-graphs
        pool = []
        for d in dynamics:
            if hasattr(d, "DynamicGraph"):
                frames = getattr(d, "DynamicGraph")
            elif isinstance(d, list):
                frames = d
            else:
                continue
            if not frames:
                frames = [nx.Graph()]
            pool.append(frames)

        if not pool:
            raise ValueError("No valid dynamics provided")

        count = min(n, len(pool))
        chosen_indices = random.sample(range(len(pool)), count)

        # Precompute per-dynamic union graph, positions and node lists to keep layout stable
        dyn_info = []
        for idx in chosen_indices:
            frames = pool[idx]
            union = nx.Graph()
            for f in frames:
                union.add_nodes_from(f.nodes())
                union.add_edges_from(f.edges())
            pos = nx.circular_layout(union, seed=42) if len(union) > 0 else {}
            node_list = list(union.nodes())
            dyn_info.append({
                "frames": frames,
                "union": union,
                "pos": pos,
                "node_list": node_list,
                "length": len(frames)
            })

        max_frames = max(info["length"] for info in dyn_info)

        fig, axes = plt.subplots(1, count, figsize=figsize)
        if count == 1:
            axes = [axes]

        def update(frame_index):
            for ax, info in zip(axes, dyn_info):
                ax.clear()
                ax.axis('off')
                fi = frame_index % info["length"]  # loop per dynamic
                G = info["frames"][fi]
                pos = info["pos"]
                node_list = info["node_list"]

                ax.set_title(f"Dyn frame {fi}")

                node_colors = [node_color if (n in G.nodes()) else absent_node_color for n in node_list]

                # draw nodes and edges for this subplot
                if node_list:
                    nx.draw_networkx_nodes(info["union"], pos, nodelist=node_list,
                                           node_color=node_colors, node_size=node_size, ax=ax)
                # draw only edges present in the current frame
                nx.draw_networkx_edges(G, pos, edge_color=edge_color, ax=ax)
                if with_labels and node_list:
                    nx.draw_networkx_labels(info["union"], pos, ax=ax)

        ani = FuncAnimation(fig, update, frames=range(max_frames),
                            interval=interval, repeat=loop)
        plt.tight_layout()
        plt.show()
        return ani



    # def plot_random_dynamics(self, dynamics, n: int = 5, pick_frame='random', seed: int = None,
    #                          figsize=(15, 3), node_size=300, node_color='skyblue',
    #                          edge_color='gray', with_labels=True):
    #     """
    #     Select up to `n` random dynamic graphs from `dynamics` and plot one representative
    #     frame for each side-by-side.

    #     - dynamics: list of DynamicGraph objects (with attribute `.DynamicGraph` a list of nx.Graph)
    #                 or list of lists of nx.Graph.
    #     - n: number of dynamics to pick (default 5).
    #     - pick_frame: 'random' to pick a random frame from each dynamic, 'first' to pick index 0,
    #                   or an integer index to pick that specific frame (will be clamped).
    #     - seed: optional int to make selection deterministic.
    #     - figsize: overall figure size (width, height).
    #     - other drawing options as in visualize_dynamic_graph.

    #     This method draws a single static snapshot per selected dynamic graph.
    #     """
    #     if seed is not None:
    #         random.seed(seed)

    #     # normalize dynamics into list of list-of-graphs
    #     pool = []
    #     for d in dynamics:
    #         if hasattr(d, "DynamicGraph"):
    #             frames = getattr(d, "DynamicGraph")
    #         elif isinstance(d, list):
    #             frames = d
    #         else:
    #             # unsupported entry, skip
    #             continue
    #         if not frames:
    #             # ensure at least a placeholder empty graph
    #             frames = [nx.Graph()]
    #         pool.append(frames)

    #     if not pool:
    #         raise ValueError("No valid dynamics provided")

    #     count = min(n, len(pool))
    #     chosen_indices = random.sample(range(len(pool)), count)

    #     fig, axes = plt.subplots(1, count, figsize=figsize)
    #     if count == 1:
    #         axes = [axes]

    #     for ax, idx in zip(axes, chosen_indices):
    #         frames = pool[idx]
    #         if pick_frame == 'random':
    #             fi = random.randrange(len(frames))
    #         elif pick_frame == 'first':
    #             fi = 0
    #         else:
    #             try:
    #                 fi = int(pick_frame)
    #             except Exception:
    #                 fi = 0
    #             fi = max(0, min(fi, len(frames) - 1))

    #         G = frames[fi]

    #         # compute union positions for stability inside this dynamic
    #         union = nx.Graph()
    #         for f in frames:
    #             union.add_nodes_from(f.nodes())
    #             union.add_edges_from(f.edges())
    #         pos = nx.spring_layout(union, seed=42) if len(union) > 0 else {}

    #         ax.set_title(f"Dynamic #{idx} — frame {fi}")
    #         ax.axis('off')

    #         node_list = list(union.nodes())
    #         node_colors = [node_color if (n in G.nodes()) else 'lightgray' for n in node_list]

    #         nx.draw_networkx_nodes(union, pos, nodelist=node_list, node_color=node_colors,
    #                                node_size=node_size, ax=ax)
    #         nx.draw_networkx_edges(G, pos, edge_color=edge_color, ax=ax)
    #         if with_labels:
    #             nx.draw_networkx_labels(union, pos, ax=ax)

    #     plt.tight_layout()
    #     plt.show()