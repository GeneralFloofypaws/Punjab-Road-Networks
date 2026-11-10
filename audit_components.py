
import json
import geopandas as gpd
import pandas as pd
import networkx as nx
from pathlib import Path

OUT = Path("output")

with open(OUT / "network.json", encoding="utf-8") as f:
    network = json.load(f)

segments = gpd.read_file(OUT / "segments.geojson")

G = nx.MultiGraph()

for node in network["nodes"]:
    G.add_node(node["id"])

for edge in network["edges"]:
    G.add_edge(
        edge["source"],
        edge["target"],
        segment_id=edge.get("segment_id"),
        road_ref=edge.get("road_ref"),
        road_category=edge.get("road_category"),
        length_m=edge.get("length_m", 0),
    )

components = sorted(
    nx.connected_components(G),
    key=len,
    reverse=True
)

segment_by_node = {}

for _, seg in segments.iterrows():
    for node in [seg["start_node"], seg["end_node"]]:
        segment_by_node.setdefault(node, []).append(seg)

component_rows = []
node_rows = []

for index, component in enumerate(components, start=1):
    component_id = f"C{index:03d}"

    component_edges = [
        (u, v, data)
        for u, v, data in G.edges(component, data=True)
        if u in component and v in component
    ]

    categories = sorted({
        data.get("road_category", "UNKNOWN")
        for _, _, data in component_edges
    })

    refs = sorted({
        str(data.get("road_ref"))
        for _, _, data in component_edges
        if data.get("road_ref")
    })

    total_length = sum(
        float(data.get("length_m") or 0)
        for _, _, data in component_edges
    )

    component_rows.append({
        "component_id": component_id,
        "node_count": len(component),
        "edge_count": len(component_edges),
        "total_length_m": round(total_length, 2),
        "road_categories": "; ".join(categories),
        "road_refs": "; ".join(refs),
        "is_isolated": len(component) == 1,
    })

    for node in component:
        node_rows.append({
            "component_id": component_id,
            "node_id": node,
            "degree": G.degree(node),
        })

summary = pd.DataFrame(component_rows)
node_details = pd.DataFrame(node_rows)

summary.to_csv(OUT / "component_audit.csv", index=False)
node_details.to_csv(OUT / "component_nodes.csv", index=False)

print("\ncomp audit")
print("Connected components:", len(components))
print("\nComponent summary:")
print(summary.to_string(index=False))

print("\nSingleton components:",
      (summary["node_count"] == 1).sum())

print("\nLargest component:")
print(summary.iloc[0].to_dict())

print("\nExported:")
print(OUT / "component_audit.csv")
print(OUT / "component_nodes.csv")
