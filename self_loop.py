import geopandas as gpd

segments = gpd.read_file("output/segments.geojson")

for node in ["J_REPLACE_WITH_C018_NODE", "J_REPLACE_WITH_C019_NODE"]:
    print(segments[
        (segments["start_node"] == node) |
        (segments["end_node"] == node)
    ][["segment_id", "road_ref", "start_node", "end_node", "length_m"]])