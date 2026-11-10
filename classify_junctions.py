
import geopandas as gpd
import pandas as pd
from pathlib import Path
from collections import defaultdict

OUT = Path("output")

# 1. load 


junctions = gpd.read_file(OUT / "junctions.geojson")
segments = gpd.read_file(OUT / "segments.geojson")

print("Loaded junctions:", len(junctions))
print("Loaded segments:", len(segments))

# Preserve og classifn.
junctions["junction_class_original"] = junctions["junction_class"]

# 
# 2. build jn -> conn index


incident_segments = defaultdict(list)

for _, segment in segments.iterrows():
    start = segment["start_node"]
    end = segment["end_node"]

    incident_segments[start].append(segment)
    incident_segments[end].append(segment)


# 3. category order


CATEGORY_ORDER = ["NH", "SH", "MDR", "ODR", "OTHER"]

def classify_categories(categories):
    categories = set(categories)

    ordered = [
        category for category in CATEGORY_ORDER
        if category in categories
    ]

    return "-".join(ordered) if ordered else "UNKNOWN"


#classify each jn

results = []

for _, junction in junctions.iterrows():

    jid = junction["junction_id"]
    connected = incident_segments.get(jid, [])

    # Incident segment count includes both arms of a
    # road passing through the junction.
    incident_count = len(connected)

    # Dedupe og source roads.
    unique_roads = {}

    for segment in connected:
        source_id = segment.get("source_fid")

        if pd.isna(source_id):
            source_id = segment["segment_id"]

        unique_roads[str(source_id)] = segment

    roads = list(unique_roads.values())

    # Categories and refs
    categories = set()
    refs = set()
    fclasses = set()

    for road in roads:

        category = road.get("road_category")

        if pd.notna(category):
            categories.add(str(category).strip().upper())

        ref = road.get("road_ref")

        if pd.notna(ref) and str(ref).strip():
            refs.add(str(ref).strip())

        fclass = road.get("fclass")

        if pd.notna(fclass) and str(fclass).strip():
            fclasses.add(str(fclass).strip())

    category_combo = classify_categories(categories)

    # Number of distinct og road features
    connected_road_count = len(roads)

    # Simple structural classifn
    if incident_count <= 1:
        topology_type = "DEAD_END"
    elif incident_count == 2:
        topology_type = "TWO_ARM"
    elif incident_count == 3:
        topology_type = "THREE_ARM"
    elif incident_count == 4:
        topology_type = "FOUR_ARM"
    else:
        topology_type = "MULTI_ARM"

    results.append({
        "junction_id": jid,
        "connected_road_count": connected_road_count,
        "incident_segment_count": incident_count,
        "road_combo_class": category_combo,
        "topology_type": topology_type,
        "connected_road_refs": "; ".join(sorted(refs)),
        "connected_fclasses": "; ".join(sorted(fclasses)),
    })


#5. merged data

classification = pd.DataFrame(results)

junctions = junctions.merge(
    classification,
    on="junction_id",
    how="left"
)

#6.exports

output_file = OUT / "junctions_classified.geojson"

junctions.to_file(
    output_file,
    driver="GeoJSON"
)

junctions.drop(columns="geometry").to_csv(
    OUT / "junction_classification.csv",
    index=False
)

#net-

print("\nCLASSIFICATION SUMMARY")

print("\nRoad combination classes:")
print(junctions["road_combo_class"].value_counts())

print("\nTopology types:")
print(junctions["topology_type"].value_counts())

print("\nTotal classified junctions:", len(junctions))

print("\nOutputs:")
print(output_file)
print(OUT / "junction_classification.csv")

print("\ndone")
