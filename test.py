
import geopandas as gpd

j = gpd.read_file("output/junctions.geojson")
s = gpd.read_file("output/segments.geojson")

print("JUNCTION FIELDS:")
print(j.columns.tolist())

print("\nFIRST JUNCTION:")
print(j.drop(columns="geometry").iloc[0].to_dict())

print("\nSEGMENT FIELDS:")
print(s.columns.tolist())

print("\nFIRST SEGMENT:")
print(s.drop(columns="geometry").iloc[0].to_dict())
