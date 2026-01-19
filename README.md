# YaDyGaGa

YaDyGaGa is a small toolkit to generate, assemble and visualize dynamic graphs (sequences of networkx Graph objects).  
It is aimed at experimentation with path uptime, stability and multi-pair scenarios where each frame is a sampled subgraph.

## Requirements
- Python 3.8+
- numpy
- networkx
- matplotlib

Install:
```
pip install -r requirements.txt
```
(ensure a GUI backend for matplotlib when using animation, or save the animation to file)


## Creating a dynamic graph

You can create a dynamic graph (a list of networkx.Graph frames) in two ways: with the repository generators (if you want block/timeline semantics) or quickly by sampling a base graph.

- Using the toolkit generators
  - Use FrameGenerator / TimelineBlockGenerator / DynaGraph modules from the repo to build timelines and assemble frames. These utilities provide higher-level control for single-pair (SPC) or multi-pair (MPC) scenarios and keep reproducibility via seeds. Example flow (adapt to actual module names in codebase):
  ```python
  from src.frame_generator import FrameGenerator
  from src.timeline_generator import TimelineBlockGenerator
  from src.dyna_graph import DynaGraph

  base_graph = ...  # networkx.Graph, your topology
  frame_gen = FrameGenerator(base_graph, seed=123)
  timeline = TimelineBlockGenerator(...)      # build SPC/MPC timeline blocks
  dyna = DynaGraph(timeline, frame_gen)
  dynamic_graph = dyna.build_frames()         # returns list of networkx.Graph frames
  ```

- Quick manual example (works without repository generators)
  - Create a sequence of sampled subgraphs from a base graph by sampling edges per frame.
  ```python
  import networkx as nx
  import random

  base = nx.erdos_renyi_graph(20, 0.15, seed=42)
  T = 10  # number of frames
  p_up = 0.8  # probability an edge is present in a frame

  dynamic_graph = []
  for t in range(T):
      Gt = nx.Graph()
      Gt.add_nodes_from(base.nodes())
      for u, v in base.edges():
          if random.random() < p_up:
              Gt.add_edge(u, v)
      dynamic_graph.append(Gt)
  # dynamic_graph is now a list of networkx.Graph frames
  ```

Once you have `dynamic_graph` (a list of networkx.Graph frames) you can feed it to the community detector:

```python
from src.dyCoDeTa import DynaGraphCommuDetection

detector = DynaGraphCommuDetection(dynamic_graph, method="louvain", seed=444)
detector.detectStatCommunities()
detector.unitCirclePlacement()
detector.HspacePropagation(threshold=0.2)
ani = detector.plotDynaCommunity(interval=600, annote=True)
```

## Examples of dynamic communities tools

Typical flow to detect and animate communities from a dynamic graph (dynamic_graph is a list of networkx.Graph frames):

```python
from src.dyCoDeTa import DynaGraphCommuDetection

detector = DynaGraphCommuDetection(dynamic_graph, method="louvain", seed=444)
detector.detectStatCommunities()      # detect communities per frame
detector.unitCirclePlacement()        # place nodes deterministically for visualization
detector.HspacePropagation(threshold=0.2)  # compute H-space and propagate community ids
ani = detector.plotDynaCommunity(interval=600, annote=True)  # show/save animation
```


## Contributing
- Follow existing module structure and add unit tests for new behavior.
- Keep augmentation deterministic with seeds where reproducibility is needed.

## License
GPL-2.0 (see LICENSE file).

## Contact
Open issues or PRs on the repository for bugs or feature requests.