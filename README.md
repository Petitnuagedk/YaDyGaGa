# YaDyGaGa

YaDyGaGa is a small toolkit to generate, assemble and visualize dynamic graphs (sequences of networkx graphs).  
It is aimed at experimentation with path uptime, stability and multi-pair scenarios where each frame is a sampled subgraph.

## Key components
- FrameGenerator — sample frames from a base graph (produce up/down frames for pairs).
- SourceGraphAugmenter — greedy, seeded augmentation of a base graph while keeping path baselines.
- TimelineBlockGenerator (SPC / MPC) — create block-structured timelines (single-pair or multi-pair).
- DynaGraph (SPC / MPC) — assemble timelines into concrete dynamic graph sequences selected from frame sets.
- PropertiesChecker — compute metrics: uptime, lifetime, stability, shortest-path length statistics.
- Visualizer — static/animated visualization of dynamics using matplotlib & networkx.

## Requirements
- Python 3.8+
- networkx
- matplotlib

Install:
```
pip install -r requirements.txt
```

## Quick start (example workflow)
1. Build or load a base graph G.
2. Optionally augment it with SourceGraphAugmenter to produce a limited edge set.
3. Use FrameGenerator.generate_frames_for_pairs(...) to produce a frame pool and a map of cases (per-status frame indices).
4. Create a timeline using TimelineBlockGenerator / MPCTimelineBlockGenerator.
5. Assemble a dynamic sequence with DynaGraph.buildDynaGraph(...) using the timeline and frame set.
6. Inspect metrics with PropertiesChecker and visualize with Visualizer.animate_random_dynamics or visualize_dynamic_graph.

Example (rough):
```python
from src import SourceGraphAugmenter, FrameGenerator, MPCTimelineBlockGenerator, MPCDynamicGraph, Visualizer

# 1) prepare base graph G...
limited = SourceGraphAugmenter.augmentBaseGraph(G, pairs=[("A","F"),("C","F")], seed=1)

# 2) generate frame set for pairs
fg = FrameGenerator()
frame_set = fg.generate_frames_for_pairs(limited, pairs=[("A","F"),("C","F")], trials=1000, p_edge=0.5, seed=1)

# 3) build timeline and assemble a dynamic
mpc = MPCTimelineBlockGenerator(frames=50, n_pairs=2, path_life=0.5, stability=1.0, mode="indep", seed=1)
timeline = mpc.generate()
dyn_builder = MPCDynamicGraph()
dynamic = dyn_builder.buildDynaGraph(timeline, frame_set, seed=1, no_double=True)

# 4) visualize
viz = Visualizer(timeline=None)  # timeline param optional for some methods
viz.animate_random_dynamics([dynamic], n=1, interval=500)
```

## Testing
Add unit tests under `tests/` and run with pytest:
```
pytest
```

## Contributing
- Follow existing module structure and add unit tests for new behavior.
- Keep augmentation deterministic with seeds where reproducibility is needed.

## License
GPL-2.0 (see LICENSE file).

## Contact
Open issues or PRs on the repository for bugs or feature requests.