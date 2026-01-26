import math
import os
import json
import numpy as np
import networkx as nx

def timeline_feasible_params(frames: int, path_life: float = None, stability: float = None):
    """
    Given number of frames `frames` and either `path_life` (alpha in [0,1]) or
    `stability` (s in [0,1]), return feasible values/ranges for the other parameter.

    Definitions used:
    - l = frames
    - k = number of frames where the path exists = ceil(alpha * l)
    - transitions t is number of adjacent frame changes (0 <= t <= l-1)
    - stability s is defined as s = 1 - t/(l-1)  (fraction of unchanged adjacencies)

    Feasible transitions for a given k:
    - if k == 0 or k == l: t_min = 0, t_max = 0
    - else: t_min = 2 (one contiguous run of presences and one run of absences)
            t_max = min(l-1, 2*min(k, l-k)) (alternating as much as counts allow)

    Returns a dict with keys:
      - 'frames'
      - 'given' -> ('path_life', value) or ('stability', value)
      - 'feasible_stability' -> (s_min, s_max) if path_life provided
      - 'feasible_path_life' -> (alpha_min, alpha_max) if stability provided
      - 'possible_k' -> list of integer k values compatible with given stability (when stability provided)
    """
    l = int(frames)
    if l <= 0:
        raise ValueError("frames must be > 0")

    if (path_life is None) == (stability is None):
        raise ValueError("Provide exactly one of path_life or stability")

    # handle trivial single-frame case
    if l == 1:
        if path_life is not None:
            k = math.ceil(path_life * l)
            # stability undefined (no adjacencies) -> treat as 1.0
            return {'frames': l, 'given': ('path_life', path_life),
                    'feasible_stability': (1.0, 1.0),
                    'k': k}
        else:
            # stability given -> only path_life options are 0 or 1 depending on desired k
            return {'frames': l, 'given': ('stability', stability),
                    'feasible_path_life': (0.0, 1.0),
                    'possible_k': [0, 1]}

    if path_life is not None:
        if not (0.0 <= path_life <= 1.0):
            raise ValueError("path_life must be in [0,1]")
        k = math.ceil(path_life * l)

        # compute t_min, t_max
        if k == 0 or k == l:
            t_min = t_max = 0
        else:
            t_min = 2
            t_max = min(l - 1, 2 * min(k, l - k))

        s_min = 1 - (t_max / (l - 1))
        s_max = 1 - (t_min / (l - 1))
        # clamp to [0,1]
        s_min = max(0.0, min(1.0, s_min))
        s_max = max(0.0, min(1.0, s_max))

        return {
            'frames': l,
            'given': ('path_life', path_life),
            'k': k,
            'feasible_stability': (s_min, s_max),
            'note': f"For k={k} frames with path present, stability must be in [{s_min:.3f}, {s_max:.3f}]"
        }

    else:
        # stability provided -> find all k that can realize that stability
        if not (0.0 <= stability <= 1.0):
            raise ValueError("stability must be in [0,1]")
        feasible_ks = []
        for k in range(0, l + 1):
            if k == 0 or k == l:
                t_min = t_max = 0
            else:
                t_min = 2
                t_max = min(l - 1, 2 * min(k, l - k))
            s_min = 1 - (t_max / (l - 1))
            s_max = 1 - (t_min / (l - 1))
            # numerical tolerance
            if s_min - 1e-9 <= stability <= s_max + 1e-9:
                feasible_ks.append(k)

        if not feasible_ks:
            return {
                'frames': l,
                'given': ('stability', stability),
                'feasible_path_life': None,
                'possible_k': [],
                'note': "No feasible path_life (k) exists for the provided stability"
            }

        alpha_min = min(feasible_ks) / l
        alpha_max = max(feasible_ks) / l
        return {
            'frames': l,
            'given': ('stability', stability),
            'possible_k': feasible_ks,
            'feasible_path_life': (alpha_min, alpha_max),
            'note': f"For stability={stability}, path_life (alpha) must be in [{alpha_min:.3f}, {alpha_max:.3f}]"
        }
    
def sweep_mpc_generate(dynamic_graph_base, pairs, frames: int, path_life: float = None, stability: float = None,
                       step: float = 0.1, mode: str = "indep", trials: int = 1000, p_edge: float = 0.5, seed: int = 42):
    """
    Sweep the unspecified parameter (path_life or stability) using timeline_feasible_params,
    build one MPC dynamic graph per step, and return a list of results.

    Returns a list of dicts: {'param_name': 'path_life'|'stability', 'param_value': v, 'timeline': timeline, 'dynamic_graph': dynamic_graph}
    """
    if (path_life is None) == (stability is None):
        raise ValueError("Provide exactly one of path_life or stability")

    params_info = timeline_feasible_params(frames=frames, path_life=path_life, stability=stability)
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

def save_sweep_results_as_adj_matrices(sweep_results, out_dir, overwrite=False):
    """
    Persist sweep results to disk as adjacency matrices (CSV) per frame so non-Python
    tools (C++, etc.) can read them easily.

    Directory layout created under out_dir:
      index.csv                - summary table (entry_id,param_name,param_value,frames,dir)
      entry_{i}_{param}.json   - metadata for the entry (nodes order, param)
      entry_{i}_{param}/
         nodes.txt             - node labels, one per line (defines matrix row/col order)
         adj_frame_000.csv     - adjacency matrix for frame 0 (rows = nodes order)
         adj_frame_001.csv
         ...
    Parameters:
      - sweep_results: list of dicts as returned by sweep_mpc_generate()
        each dict must contain at least: 'param_name', 'param_value', 'dynamic_graph'
        where 'dynamic_graph' is a list of networkx.Graph frames (or similar with .nodes()/.edges()).
      - out_dir: base output directory (will be created if missing)
      - overwrite: if True, remove existing out_dir contents for same entry names
    Returns:
      - path to index CSV file
    """
    os.makedirs(out_dir, exist_ok=True)
    index_rows = []
    for i, entry in enumerate(sweep_results):
        param_name = entry.get('param_name', 'param')
        param_value = entry.get('param_value', entry.get(param_name, 'nan'))
        dyn_graph = entry.get('dynamic_graph')
        if dyn_graph is None:
            # skip malformed entry
            continue

        # Create a safe directory name
        entry_dirname = f"entry_{i}_{param_name}_{str(param_value).replace('.', '_')}"
        entry_dir = os.path.join(out_dir, entry_dirname)
        if os.path.exists(entry_dir):
            if overwrite:
                # remove files inside (do not attempt recursive delete of unrelated content)
                for fn in os.listdir(entry_dir):
                    fp = os.path.join(entry_dir, fn)
                    try:
                        if os.path.isfile(fp):
                            os.remove(fp)
                    except Exception:
                        pass
            else:
                # find a new unique name
                suffix = 1
                while os.path.exists(entry_dir):
                    entry_dir = os.path.join(out_dir, f"{entry_dirname}_{suffix}")
                    suffix += 1
        os.makedirs(entry_dir, exist_ok=True)

        # Determine node ordering: union of all nodes across frames, sorted for reproducibility
        all_nodes = set()
        for G in dyn_graph:
            all_nodes.update(list(G.nodes()))
        nodes = sorted(list(all_nodes), key=lambda x: str(x))

        # Save nodes order
        nodes_file = os.path.join(entry_dir, "nodes.txt")
        with open(nodes_file, "w", encoding="utf-8") as f:
            for n in nodes:
                f.write(f"{n}\n")

        # Save adjacency matrix per frame as CSV (0/1 integer entries)
        for t, G in enumerate(dyn_graph):
            # ensure adjacency uses same node order
            A = nx.to_numpy_array(G, nodelist=nodes, dtype=int)
            frame_file = os.path.join(entry_dir, f"adj_frame_{t:03d}.csv")
            np.savetxt(frame_file, A, fmt="%d", delimiter=",")

        # Save metadata JSON for the entry
        meta = {
            "param_name": param_name,
            "param_value": param_value,
            "frames": len(dyn_graph),
            "nodes_file": "nodes.txt",
            "adj_prefix": "adj_frame_",
            "entry_dir": os.path.basename(entry_dir)
        }
        meta_file = os.path.join(entry_dir, f"entry_{i}_meta.json")
        with open(meta_file, "w", encoding="utf-8") as mf:
            json.dump(meta, mf, indent=2)

        index_rows.append({
            "entry_id": i,
            "param_name": param_name,
            "param_value": param_value,
            "frames": len(dyn_graph),
            "entry_dir": os.path.basename(entry_dir)
        })

    # write index CSV
    index_file = os.path.join(out_dir, "index.csv")
    with open(index_file, "w", encoding="utf-8") as idxf:
        idxf.write("entry_id,param_name,param_value,frames,entry_dir\n")
        for r in index_rows:
            idxf.write(f"{r['entry_id']},{r['param_name']},{r['param_value']},{r['frames']},{r['entry_dir']}\n")

    return index_file