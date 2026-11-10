
import json
import geopandas as gpd
import networkx as nx
from pathlib import Path

OUT = Path("output")

# Load outputs
junctions = gpd.read_file(OUT / "junctions.geojson")
segments = gpd.read_file(OUT / "segments.geojson")

with open(OUT / "network.json", encoding="utf-8") as f:
    network = json.load(f)

nodes = network["nodes"]
edges = network["edges"]

node_ids = {n["id"] for n in nodes}
junction_ids = set(junctions["junction_id"])

print("\n========== NETWORK VALIDATION ==========")
print("Junction features:", len(junctions))
print("Segment features:", len(segments))
print("Graph nodes:", len(nodes))
print("Graph edges:", len(edges))

# Inspect actual edge structure
if edges:
    print("\nFirst edge structure:")
    print(edges[0])
    print("Available keys:", list(edges[0].keys()))

# Resolve edge endpoint names
def get_endpoints(edge):
    possible_pairs = [
        ("start_node", "end_node"),
        ("source", "target"),
        ("u", "v"),
        ("from", "to"),
    ]

    for start_key, end_key in possible_pairs:
        if start_key in edge and end_key in edge:
            return edge[start_key], edge[end_key]

    return None, None


# 1. Check graph references
missing_start = []
missing_end = []
unrecognized_edges = []

for edge in edges:
    start, end = get_endpoints(edge)

    if start is None or end is None:
        unrecognized_edges.append(edge)
        continue

    if start not in node_ids:
        missing_start.append(start)

    if end not in node_ids:
        missing_end.append(end)

print("\nMissing start-node references:", len(missing_start))
print("Missing end-node references:", len(missing_end))
print("Unrecognized edge structures:", len(unrecognized_edges))

# 2. Segment geometry
print("\nInvalid segment geometries:",
      (~segments.geometry.is_valid).sum())

print("Empty segment geometries:",
      segments.geometry.is_empty.sum())

print("Zero-length segments:",
      (segments.geometry.length == 0).sum())

# 3. Junction geometry
print("\nInvalid junction geometries:",
      (~junctions.geometry.is_valid).sum())

print("Empty junction geometries:",
      junctions.geometry.is_empty.sum())

# 4. Graph connectivity
G = nx.MultiGraph()

G.add_nodes_from(node_ids)

for edge in edges:
    start, end = get_endpoints(edge)

    if start is not None and end is not None:
        G.add_edge(start, end)

components = list(nx.connected_components(G))

print("\nConnected components:", len(components))

if components:
    print("Largest component:",
          max(len(c) for c in components))

# 5. Junction representation
print("\nJunction IDs absent from graph:",
      len(junction_ids - node_ids))

print("\nvalidated")
