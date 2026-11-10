from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

ASSETS_DIR = BASE_DIR / "assets"
GENERATED_DIR = BASE_DIR / "Generated"
OUTPUT_DIR = BASE_DIR / "output"

ROAD_FILE = ASSETS_DIR / "Road.shp"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


import os
import re
import json
import hashlib

import geopandas as gpd
import pandas as pd
import networkx as nx

from shapely.geometry import Point, MultiPoint
from shapely.ops import split



#config



# CONFIG

BASE_DIR = Path(__file__).resolve().parent

ASSETS_DIR = BASE_DIR / "assets"
GENERATED_DIR = BASE_DIR / "Generated"
OUTPUT_DIR = BASE_DIR / "output"

ROAD_FILE = ASSETS_DIR / "Road.shp"

ENDPOINT_TOLERANCE = 1.0
COORD_PRECISION = 1  # 0.1 metre in projected CRS

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)




# util


def stable_id(prefix, value):
    raw = str(value).encode("utf-8")
    digest = hashlib.sha1(raw).hexdigest()[:12]
    return f"{prefix}_{digest}"


def coord_key(point):
    return (
        round(point.x, COORD_PRECISION),
        round(point.y, COORD_PRECISION)
    )


def coordinate_node_id(point):
    return stable_id("N", coord_key(point))


def junction_id(point):
    return stable_id("J", coord_key(point))


def normalize_refs(value):
    if pd.isna(value):
        return []

    refs = re.split(r"[;:]", str(value).upper())

    result = []

    for ref in refs:
        ref = ref.strip()

        if not ref:
            continue

        
        if ref.isdigit():
            ref = "NH" + ref

        result.append(ref)

    return sorted(set(result))


def road_categories(refs):
    categories = set()

    for ref in refs:
        match = re.match(r"^(NH|SH|MDR|ODR)", ref)

        if match:
            categories.add(match.group(1))
        else:
            categories.add("OTHER")

    return sorted(categories)


def endpoint_position(line, point):
    start = Point(line.coords[0])
    end = Point(line.coords[-1])

    d_start = point.distance(start)
    d_end = point.distance(end)

    if min(d_start, d_end) <= ENDPOINT_TOLERANCE:
        return "start" if d_start <= d_end else "end"

    return "interior"


def extract_points(geometry):
    if geometry.is_empty:
        return []

    if geometry.geom_type == "Point":
        return [geometry]

    if geometry.geom_type == "MultiPoint":
        return list(geometry.geoms)

    if geometry.geom_type == "GeometryCollection":
        points = []

        for geom in geometry.geoms:
            points.extend(extract_points(geom))

        return points

    return []



# 1. Load road, validate road

print("\n[1/7] Loading roads...")

roads = gpd.read_file(ROAD_FILE).reset_index(drop=True)

if roads.crs is None:
    raise ValueError("Input shapefile has no CRS.")

if roads.crs.is_geographic:
    raise ValueError(
        "Use a projected CRS in metres before processing."
    )

roads["row_id"] = roads.index

roads = roads[
    roads.geometry.notna() &
    ~roads.geometry.is_empty
].copy()

roads = roads[
    roads.geometry.geom_type.isin(["LineString", "MultiLineString"])
].copy()

roads = roads.explode(index_parts=False).reset_index(drop=True)

roads["row_id"] = roads.index

print("Road features:", len(roads))
print("CRS:", roads.crs)


 
# 2. detect PoCs


print("\n[2/7] Detecting road contacts...")

left = roads[["geometry"]].copy().reset_index()
right = roads[["geometry"]].copy().reset_index()

left = left.rename(columns={"index": "left_id"})
right = right.rename(columns={"index": "right_id"})

pairs = gpd.sjoin(
    left,
    right,
    how="inner",
    predicate="intersects",
    lsuffix="left",
    rsuffix="right"
)

# Keep each road pair only once, no self-intersect
pairs = pairs[pairs["left_id"] < pairs["right_id"]]

contacts = []
split_points = {}
junction_records = {}
uncertain_records = []

for row_id, pair in pairs.iterrows():

    other_id = int(pair["index_right"])

    a = roads.iloc[row_id]
    b = roads.iloc[other_id]

    intersection = a.geometry.intersection(b.geometry)

    for point in extract_points(intersection):

        pos_a = endpoint_position(a.geometry, point)
        pos_b = endpoint_position(b.geometry, point)

        contact_type = (
            "endpoint-endpoint"
            if pos_a != "interior" and pos_b != "interior"
            else "interior-interior"
            if pos_a == "interior" and pos_b == "interior"
            else "endpoint-interior"
        )

        same_layer = a["layer"] == b["layer"]

        
        if same_layer:
            status = "connected"

        elif contact_type == "interior-interior":
            status = "grade-separated-candidate"

        else:
            status = "uncertain"

        record = {
            "fid_a": str(a["fid_1"]),
            "fid_b": str(b["fid_1"]),
            "ref_a": str(a["ref"]),
            "ref_b": str(b["ref"]),
            "layer_a": int(a["layer"]),
            "layer_b": int(b["layer"]),
            "contact_type": contact_type,
            "same_layer": bool(same_layer),
            "status": status,
            "geometry": point
        }

        contacts.append(record)

        if status == "connected":

            key = coord_key(point)

            if key not in junction_records:
                junction_records[key] = {
                    "point": point,
                    "roads": set()
                }

            junction_records[key]["roads"].update(
                [row_id, other_id]
            )

            split_points.setdefault(row_id, []).append(point)
            split_points.setdefault(other_id, []).append(point)

        else:
            uncertain_records.append(record)


print("Contact pairs:", len(contacts))
print("Connected contacts:", sum(
    c["status"] == "connected" for c in contacts
))
print("Uncertain contacts:", sum(
    c["status"] == "uncertain" for c in contacts
))



# 3.generate distinct junctures

print("\n[3/7] Generating junctions...")

junction_features = []

for key, data in junction_records.items():

    point = data["point"]
    connected_roads = data["roads"]

    refs = set()
    categories = set()
    fclasses = set()

    for road_index in connected_roads:

        road = roads.iloc[road_index]

        road_refs = normalize_refs(road["ref"])

        refs.update(road_refs)
        categories.update(road_categories(road_refs))

        if pd.notna(road["fclass"]):
            fclasses.add(str(road["fclass"]))

    junction_features.append({
        "junction_id": junction_id(point),
        "road_count": len(connected_roads),
        "road_refs": ";".join(sorted(refs)),
        "road_categories": ";".join(sorted(categories)),
        "junction_class": "-".join(sorted(categories)),
        "fclasses": ";".join(sorted(fclasses)),
        "geometry": point
    })


junctions = gpd.GeoDataFrame(
    junction_features,
    geometry="geometry",
    crs=roads.crs
)

print("Unique junctions:", len(junctions))



# 4. split roads in between junctures into segments

print("\n[4/7] Splitting roads...")

segment_features = []

for road_index, road in roads.iterrows():

    line = road.geometry

    points = split_points.get(road_index, [])

    # Dedupe splits
    unique_points = {}

    for point in points:
        unique_points[coord_key(point)] = point

    segments = [line]

    if unique_points:

        try:
            result = split(
                line,
                MultiPoint(list(unique_points.values()))
            )

            segments = list(result.geoms)

        except Exception as error:
            print(
                f"Split warning for row {road_index}: {error}"
            )

    for segment_number, segment in enumerate(segments):

        if segment.is_empty or segment.length <= 0.01:
            continue

        start_point = Point(segment.coords[0])
        end_point = Point(segment.coords[-1])

        start_key = coord_key(start_point)
        end_key = coord_key(end_point)

        start_junction = (
            junction_id(start_point)
            if start_key in junction_records
            else coordinate_node_id(start_point)
        )

        end_junction = (
            junction_id(end_point)
            if end_key in junction_records
            else coordinate_node_id(end_point)
        )

        refs = normalize_refs(road["ref"])
        categories = road_categories(refs)

        segment_id = stable_id(
            "S",
            f"{road['fid_1']}|{segment_number}|"
            f"{start_key}|{end_key}"
        )

        segment_features.append({
            "segment_id": segment_id,
            "source_fid": str(road["fid_1"]),
            "road_ref": ";".join(refs),
            "road_category": ";".join(categories),
            "fclass": str(road["fclass"]),
            "length_m": float(segment.length),
            "start_node": start_junction,
            "end_node": end_junction,
            "layer": int(road["layer"]),
            "bridge": str(road["bridge"]),
            "tunnel": str(road["tunnel"]),
            "geometry": segment
        })


segments = gpd.GeoDataFrame(
    segment_features,
    geometry="geometry",
    crs=roads.crs
)

print("Road segments:", len(segments))



# 5. graph using networkx 


print("\n[5/7] Building road graph...")

G = nx.MultiGraph()

for _, segment in segments.iterrows():

    G.add_edge(
        segment["start_node"],
        segment["end_node"],
        key=segment["segment_id"],
        segment_id=segment["segment_id"],
        road_ref=segment["road_ref"],
        road_category=segment["road_category"],
        length_m=segment["length_m"]
    )

print("Graph nodes:", G.number_of_nodes())
print("Graph edges:", G.number_of_edges())




# 6. Export into output folder

print("\n[6/7] Exporting datasets...")

segments.to_crs("EPSG:4326").to_file(
    OUTPUT_DIR / "segments.geojson",
    driver="GeoJSON"
)

junctions.to_crs("EPSG:4326").to_file(
    OUTPUT_DIR / "junctions.geojson",
    driver="GeoJSON"
)

if uncertain_records:
    uncertain_gdf = gpd.GeoDataFrame(
        uncertain_records,
        geometry="geometry",
        crs=roads.crs
    )

    uncertain_gdf.to_crs("EPSG:4326").to_file(
        OUTPUT_DIR / "uncertain_contacts.geojson",
        driver="GeoJSON"
    )

# Network JSON
network = {
    "nodes": [
        {"id": node}
        for node in G.nodes
    ],
    "edges": [
        {
            "source": u,
            "target": v,
            **data
        }
        for u, v, data in G.edges(data=True)
    ]
}

with open(
    OUTPUT_DIR / "network.json",
    "w",
    encoding="utf-8"
) as file:
    json.dump(network, file, indent=2)


# Network JSON
network = {
    "nodes": [
        {"id": node}
        for node in G.nodes
    ],
    "edges": [
        {
            "source": u,
            "target": v,
            **data
        }
        for u, v, data in G.edges(data=True)
    ]
}

with open (
    OUTPUT_DIR/"network.json",
    "w",
    encoding="utf-8"
) as file:

    json.dump(network, file, indent=2)



# 7.console.log but in python


print("\n[7/7] COMPLETE")

print("--------------------------------")
print("Original roads:", len(roads))
print("Junctions:", len(junctions))
print("Segments:", len(segments))
print("Graph nodes:", G.number_of_nodes())
print("Graph edges:", G.number_of_edges())
print("--------------------------------")

print("\nOutput files:")

for filename in os.listdir(OUTPUT_DIR):
    print(" -", filename)
