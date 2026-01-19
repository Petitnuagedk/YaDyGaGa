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

## Quick start examples

1) Typical flow to detect and animate communities from a dynamic graph (dynamic_graph is a list of networkx.Graph frames):

```python
from src.dyCoDeTa import DynaGraphCommuDetection

detector = DynaGraphCommuDetection(dynamic_graph, method="louvain", seed=444)
detector.detectStatCommunities()      # detect communities per frame
detector.unitCirclePlacement()        # place nodes deterministically for visualization
detector.HspacePropagation(threshold=0.2)  # compute H-space and propagate community ids
ani = detector.plotDynaCommunity(interval=600, annote=True)  # show/save animation
```

2) Basic usage notes
- H-space position for a community is the vector sum of its members' coordinates. Example: nodes at (0.8,0.6) and (0.6,0.8) give community H=(1.4,1.4).
- Communities across consecutive frames are considered the same when their H-space Euclidean distance is <= threshold (HspacePropagation).
- The node placement (unitCirclePlacement) is deterministic given the first frame's node ordering and the seed for reproducibility.

## Tests
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