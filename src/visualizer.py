"""
Module for visualizing timelines.
"""
import random
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import networkx as nx
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D
import numpy as np
from matplotlib.collections import LineCollection

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
                                absent_node_color='lightgray', with_labels=True,
                                target_pairs=None):
        """
        Animated network with a bottom contact timeline.
        If `target_pairs` is provided (list of (src,dst) tuples), highlight the
        current shortest path for each pair in a distinct color and show a legend
        on the right listing all targeted pairs.

        Improvements:
        - node labels are drawn to the right of the node (not inside)
        - when multiple target paths traverse the same link, the link is shown
          as a sequence of colored sub-segments (one segment per path) so each
          path color is visible as a fraction of the link.
        """
        if not graphs:
            raise ValueError("graphs list is empty")

        # Build union graph to have consistent node set and positions
        union = nx.Graph()
        for g in graphs:
            union.add_nodes_from(g.nodes())
            union.add_edges_from(g.edges())

        node_list = list(union.nodes())
        n_nodes = len(node_list)

        # Compute positions once unless provided (use circular layout)
        if node_pos is None:
            pos = nx.circular_layout(union) if len(union) > 0 else {}
        else:
            pos = node_pos

        # prepare pair colors
        pair_colors = {}
        if target_pairs:
            cmap = plt.cm.get_cmap('tab10')
            for i, p in enumerate(target_pairs):
                pair_colors[p] = cmap(i % cmap.N)

        # figure with two stacked subplots
        fig, (ax_top, ax_bottom) = plt.subplots(2, 1, figsize=(8, 8),
                                                gridspec_kw={'height_ratios': [2, 1]})
        ax_top.set_title("Network (animated)")
        ax_top.axis('off')

        # bottom timeline static setup
        ax_bottom.set_title("Connections over time (y = node index, x = frame)")
        ax_bottom.set_xlabel("Frame")
        ax_bottom.set_ylabel("Node")
        if n_nodes > 0:
            ax_bottom.set_ylim(-0.5, n_nodes - 0.5)
            ax_bottom.set_yticks(range(n_nodes))
            ax_bottom.set_yticklabels([str(n) for n in node_list])
        else:
            ax_bottom.set_ylim(-0.5, 0.5)
        ax_bottom.set_xlim(-0.5, max(0, len(graphs) - 0.5))
        ax_bottom.grid(True, axis='x', linestyle=':', alpha=0.4)

        node_to_index = {n: i for i, n in enumerate(node_list)}

        # draw all arcs (one per edge occurrence) and prepare scatter points for nodes that are connected
        from matplotlib.path import Path
        from matplotlib.patches import PathPatch, Rectangle

        scatter_x = []
        scatter_y = []

        for f_idx, G in enumerate(graphs):
            connected_nodes = set()
            for u, v in G.edges():
                connected_nodes.add(u)
                connected_nodes.add(v)
                if u not in node_to_index or v not in node_to_index:
                    continue
                y1 = node_to_index[u]
                y2 = node_to_index[v]
                if y1 == y2:
                    mid_y = y1
                    rad_x = 0.4
                    verts = [
                        (f_idx - rad_x, mid_y),
                        (f_idx, mid_y + 0.5),
                        (f_idx + rad_x, mid_y),
                    ]
                else:
                    mid_y = 0.5 * (y1 + y2)
                    gap = abs(y2 - y1)
                    rad_x = 0.2 + 0.12 * gap
                    verts = [
                        (f_idx, y1),
                        (f_idx + rad_x, mid_y),
                        (f_idx, y2),
                    ]
                codes = [Path.MOVETO, Path.CURVE3, Path.CURVE3]
                path = Path(verts, codes)
                patch = PathPatch(path, edgecolor=edge_color, facecolor='none',
                                  lw=1.2, alpha=0.9, zorder=1)
                ax_bottom.add_patch(patch)

            for n in connected_nodes:
                if n in node_to_index:
                    scatter_x.append(f_idx)
                    scatter_y.append(node_to_index[n])

        if scatter_x:
            ax_bottom.scatter(scatter_x, scatter_y, c=node_color, s=30, zorder=3)

        # animated soft red vertical bar (covers one-frame width)
        bar_width = 1.0
        bar = Rectangle((-0.5, -0.5), width=bar_width, height=max(0, n_nodes),
                        color='red', alpha=0.12, zorder=4)
        ax_bottom.add_patch(bar)

        # prepare legend handles for target pairs (on the right)
        legend_handles = []
        if target_pairs:
            for p, col in pair_colors.items():
                lbl = f"{p[0]} -> {p[1]}"
                legend_handles.append(Line2D([0], [0], color=col, lw=3, label=lbl))

        # place a figure-level legend so it is not removed by per-frame axis.clear()
        fig_legend = None
        if legend_handles:
            fig_legend = fig.legend(handles=legend_handles, title="Target pairs",
                                    loc='center right', bbox_to_anchor=(0.98, 0.5))
            plt.subplots_adjust(right=0.78)

        # animation: update top subplot per-frame and move the red bar
        def update(frame_index):
            ax_top.clear()
            ax_top.axis('off')
            ax_top.set_title(f"Frame {frame_index + 1}/{len(graphs)}")

            G = graphs[frame_index]

            # Node colors: highlight nodes present in this frame, fade absent ones
            top_node_colors = [
                node_color if (n in G.nodes()) else absent_node_color
                for n in node_list
            ]

            if node_list:
                nodes_coll = nx.draw_networkx_nodes(union, pos, nodelist=node_list,
                                                    node_color=top_node_colors, node_size=node_size, ax=ax_top)
                try:
                    nodes_coll.set_zorder(1)
                except Exception:
                    pass
            # draw base edges faintly (only edges present in the current frame)
            if G.number_of_edges() > 0:
                edges_coll = nx.draw_networkx_edges(G, pos, edgelist=G.edges(), edge_color=edge_color, alpha=0.6, ax=ax_top)
                try:
                    edges_coll.set_zorder(1)
                except Exception:
                    pass

            # For each target pair, compute shortest path if exists and collect path edges per-edge
            edge_to_path_colors = {}  # key: (u,v) sorted, val: list of colors in order encountered
            if target_pairs:
                for p, col in pair_colors.items():
                    s, t = p
                    if s in G and t in G:
                        try:
                            path_nodes = nx.shortest_path(G, source=s, target=t)
                            path_edges = list(zip(path_nodes[:-1], path_nodes[1:]))
                            for e in path_edges:
                                key = tuple(sorted(e))
                                edge_to_path_colors.setdefault(key, []).append(col)
                        except (nx.NetworkXNoPath, nx.NodeNotFound):
                            pass

                # Draw per-edge segmented colored representation where paths share links.
                seg_collections = []
                for (u, v), cols in edge_to_path_colors.items():
                    p0 = np.array(pos[u])
                    p1 = np.array(pos[v])
                    m = len(cols)
                    # create m consecutive sub-segments along the edge
                    segs = []
                    seg_colors = []
                    for i, c in enumerate(cols):
                        a = i / m
                        b = (i + 1) / m
                        seg_start = tuple(p0 * (1 - a) + p1 * a)
                        seg_end = tuple(p0 * (1 - b) + p1 * b)
                        segs.append((seg_start, seg_end))
                        seg_colors.append(c)
                    lc = LineCollection(segs, colors=seg_colors, linewidths=3.0, zorder=3)
                    ax_top.add_collection(lc)

            # draw full labels to the right of nodes (not inside)
            if with_labels and node_list:
                # draw labels with horizontal alignment left so they appear next to nodes
                labels = {n: str(n) for n in node_list}
                nx.draw_networkx_labels(union, pos, labels=labels, font_size=9,
                                        horizontalalignment='left', verticalalignment='center', ax=ax_top)

            # legend is drawn at figure level (fig_legend) so do not create per-frame axes legend

            # move bar on bottom timeline
            x = frame_index - 0.5  # align bar to frame column
            bar.set_x(x)

            return []

        ani = FuncAnimation(fig, update, frames=range(len(graphs)),
                            interval=interval, repeat=loop, blit=False)

        plt.tight_layout()
        plt.show()
        return ani

    def animate_random_dynamics(self,
                                dynamics,
                                n: int = 5,
                                interval: int = 1000,
                                loop: bool = True,
                                seed: int = None,
                                figsize=(15, 5),
                                node_size=100,
                                node_color='skyblue',
                                absent_node_color='lightgray',
                                edge_color='gray',
                                with_labels=True,
                                target_pairs=None):
        """
        Pick up to `n` dynamics from `dynamics` and animate them side-by-side.
        If `target_pairs` is provided, highlight shortest paths for any pair that
        appears in the union node set of that column; pair colors are consistent.
        Also display a legend (right) listing the targeted pairs.
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
            # Normalize each frame element to a single networkx.Graph.
            # Many producers (SPC with pathPersistency) may return grouped entries
            # where a frame slot can be a list of candidate graphs. For visualization
            # pick a representative graph deterministically using the provided seed.
            rnd_pick = random.Random(seed)
            normalized = []
            for fe in frames:
                if isinstance(fe, (list, tuple)):
                    # pick a representative graph from the group (deterministic choice)
                    chosen = None
                    for el in fe:
                        if isinstance(el, nx.Graph):
                            chosen = el
                            break
                    if chosen is None:
                        # fallback to random pick if group contains non-graph entries
                        try:
                            chosen = rnd_pick.choice(list(fe))
                        except Exception:
                            chosen = nx.Graph()
                    normalized.append(chosen)
                elif isinstance(fe, nx.Graph):
                    normalized.append(fe)
                else:
                    # unknown element, try to use first attribute .nodes if present
                    try:
                        if hasattr(fe, "nodes"):
                            normalized.append(fe)
                        else:
                            normalized.append(nx.Graph())
                    except Exception:
                        normalized.append(nx.Graph())

            pool.append(normalized)

        if not pool:
            raise ValueError("No valid dynamics provided")

        count = min(n, len(pool))
        chosen_indices = random.sample(range(len(pool)), count)

        # pair colors global (so same across columns)
        pair_colors = {}
        if target_pairs:
            cmap = plt.cm.get_cmap('tab10')
            for i, p in enumerate(target_pairs):
                pair_colors[p] = cmap(i % cmap.N)

        from matplotlib.path import Path
        from matplotlib.patches import PathPatch, Rectangle

        dyn_info = []
        for idx in chosen_indices:
            frames = pool[idx]
            union = nx.Graph()
            for f in frames:
                union.add_nodes_from(f.nodes())
                union.add_edges_from(f.edges())
            pos = nx.circular_layout(union) if len(union) > 0 else {}
            node_list = list(union.nodes())
            node_to_index = {n: i for i, n in enumerate(node_list)}
            patches = []
            scatter_x = []
            scatter_y = []
            for f_idx, G in enumerate(frames):
                connected_nodes = set()
                for u, v in G.edges():
                    connected_nodes.add(u)
                    connected_nodes.add(v)
                    if u not in node_to_index or v not in node_to_index:
                        continue
                    y1 = node_to_index[u]
                    y2 = node_to_index[v]
                    if y1 == y2:
                        mid_y = y1
                        rad_x = 0.4
                        verts = [
                            (f_idx - rad_x, mid_y),
                            (f_idx, mid_y + 0.5),
                            (f_idx + rad_x, mid_y),
                        ]
                    else:
                        mid_y = 0.5 * (y1 + y2)
                        gap = abs(y2 - y1)
                        rad_x = 0.2 + 0.12 * gap
                        verts = [
                            (f_idx, y1),
                            (f_idx + rad_x, mid_y),
                            (f_idx, y2),
                        ]
                    codes = [Path.MOVETO, Path.CURVE3, Path.CURVE3]
                    path = Path(verts, codes)
                    patches.append(PathPatch(path, edgecolor=edge_color, facecolor='none',
                                             lw=1.2, alpha=0.9, zorder=1))
                for n in connected_nodes:
                    if n in node_to_index:
                        scatter_x.append(f_idx)
                        scatter_y.append(node_to_index[n])

            dyn_info.append({
                "frames": frames,
                "union": union,
                "pos": pos,
                "node_list": node_list,
                "node_to_index": node_to_index,
                "length": len(frames),
                "patches": patches,
                "scatter_x": scatter_x,
                "scatter_y": scatter_y,
                "n_nodes": len(node_list),
                "bar": None,
            })

        max_frames = max(info["length"] for info in dyn_info)

        # create 2 x count axes: top row animated networks, bottom row static timelines
        fig, axes = plt.subplots(2, count, figsize=figsize,
                                 gridspec_kw={'height_ratios': [2, 1]})
        if count == 1:
            top_axes = [axes[0]]
            bottom_axes = [axes[1]]
        else:
            top_axes = axes[0]
            bottom_axes = axes[1]

        # prepare legend handles (global)
        legend_handles = []
        if target_pairs:
            for p, col in pair_colors.items():
                lbl = f"{p[0]} -> {p[1]}"
                legend_handles.append(Line2D([0], [0], color=col, lw=3, label=lbl))

        for ax_top, ax_bottom, info in zip(top_axes, bottom_axes, dyn_info):
            ax_top.axis('off')
            n_nodes = info["n_nodes"]
            node_list = info["node_list"]
            ax_bottom.set_title("Connections over time")
            ax_bottom.set_xlabel("Frame")
            ax_bottom.set_ylabel("Node")
            if n_nodes > 0:
                ax_bottom.set_ylim(-0.5, n_nodes - 0.5)
                ax_bottom.set_yticks(range(n_nodes))
                ax_bottom.set_yticklabels([str(n) for n in node_list])
            else:
                ax_bottom.set_ylim(-0.5, 0.5)
            ax_bottom.set_xlim(-0.5, max(0, info["length"] - 0.5))
            ax_bottom.grid(True, axis='x', linestyle=':', alpha=0.4)

            for p in info["patches"]:
                ax_bottom.add_patch(p)
            if info["scatter_x"]:
                ax_bottom.scatter(info["scatter_x"], info["scatter_y"], c=node_color, s=30, zorder=3)
            bar = Rectangle((-0.5, -0.5), width=1.0, height=max(0, n_nodes),
                            color='red', alpha=0.12, zorder=4)
            ax_bottom.add_patch(bar)
            info["bar"] = bar

            # add legend on top axis if target pairs provided
            if legend_handles:
                ax_top.legend(handles=legend_handles, title="Target pairs", bbox_to_anchor=(1.02, 1), loc='upper left')

        # animation: update top row per-frame and move each bottom bar
        def update(frame_index):
            for ax_top, info in zip(top_axes, dyn_info):
                ax_top.clear()
                ax_top.axis('off')
                fi = frame_index % info["length"]
                G = info["frames"][fi]
                pos = info["pos"]
                node_list = info["node_list"]

                ax_top.set_title(f"Dyn frame {fi}")

                node_colors = [node_color if (n in G.nodes()) else absent_node_color for n in node_list]

                if node_list:
                    nodes_coll = nx.draw_networkx_nodes(info["union"], pos, nodelist=node_list,
                                                        node_color=node_colors, node_size=node_size, ax=ax_top)
                    try:
                        nodes_coll.set_zorder(1)
                    except Exception:
                        pass
                # draw only edges present in the current frame
                if G.number_of_edges() > 0:
                    edges_coll = nx.draw_networkx_edges(G, pos, edgelist=G.edges(), edge_color=edge_color, ax=ax_top)
                    try:
                        edges_coll.set_zorder(1)
                    except Exception:
                        pass
                if with_labels and node_list:
                    nx.draw_networkx_labels(info["union"], pos, ax=ax_top)

                # highlight target pair paths if present in this union/graph
                if target_pairs:
                    for p, col in pair_colors.items():
                        s, t = p
                        if s in G and t in G:
                            try:
                                path_nodes = nx.shortest_path(G, source=s, target=t)
                                path_edges = list(zip(path_nodes[:-1], path_nodes[1:]))
                                path_edges_coll = nx.draw_networkx_edges(G, pos, edgelist=path_edges, edge_color=[col], width=3.0, ax=ax_top)
                                try:
                                    path_edges_coll.set_zorder(3)
                                except Exception:
                                    pass
                                path_nodes_coll = nx.draw_networkx_nodes(G, pos, nodelist=path_nodes, node_color=[col]*len(path_nodes),
                                                                         node_size=int(node_size*1.1), ax=ax_top, edgecolors='k')
                                try:
                                    path_nodes_coll.set_zorder(4)
                                except Exception:
                                    pass
                            except (nx.NetworkXNoPath, nx.NodeNotFound):
                                pass

                x = fi - 0.5
                info["bar"].set_x(x)

            return []

        ani = FuncAnimation(fig, update, frames=range(max_frames),
                            interval=interval, repeat=loop)
        plt.tight_layout()
        plt.show()
        return ani

    def plotLoadedData(self, loaded, n_display=None, interval=800, loop=True):
        """
        Plot content returned by load_from_directory().
        - single -> visualize the dynamic graph (animated)
        - batch  -> pick up to n_display dynamics and animate them side-by-side

        Returns the animation object(s) when possible.
        """
        if loaded["type"] == "single":
            dg = loaded["dynamic_graph"]
            v = Visualizer([])  # instance used to access method
            return v.visualize_dynamic_graph(dg, interval=interval, loop=loop)
        elif loaded["type"] == "batch":
            entries = loaded["entries"]
            graphs = [e["dynamic_graph"] for e in entries if e.get("dynamic_graph")]
            if not graphs:
                raise RuntimeError("No dynamic graphs found in batch to plot.")
            # limit how many to show
            if n_display is None:
                n_display = min(5, len(graphs))
            chosen = graphs[:n_display]
            v = Visualizer([])  # use animate_random_dynamics to render multiple columns
            return v.animate_random_dynamics(chosen, n=len(chosen), interval=interval, loop=loop, seed=1)
        else:
            raise ValueError("Unknown loaded data type")
