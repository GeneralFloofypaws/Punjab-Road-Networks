
import geopandas as gpd
import pandas as pd
from pathlib import Path

OUT = Path("output")

for filename in ["contact_audit.csv", "classified_intersections.csv"]:
    path = OUT / filename

    if not path.exists():
        print(f"\nMissing: {filename}")
        continue

    df = pd.read_csv(path)

    print(f"\n========== {filename} ==========")
    print("Rows:", len(df))
    print("Columns:", df.columns.tolist())
    print("\nFirst 5 records:")
    print(df.head().to_string(index=False))

    # Display useful categorical summaries.
    for col in df.columns:
        if any(word in col.lower() for word in
               ["status", "classification", "layer", "type"]):
            if df[col].nunique() <= 30:
                print(f"\n{col} distribution:")
                print(df[col].value_counts(dropna=False).to_string())

path = OUT / "uncertain_contacts.geojson"

if path.exists():
    contacts = gpd.read_file(path)

    print("\nTHESE ARE THE CONTACTS I'M NOT SURE ABT")
    print("Features:", len(contacts))
    print("Fields:", contacts.columns.tolist())
    print(contacts.drop(columns="geometry").head(10).to_string(index=False))
else:
    print("\nuncertain_contacts.geojson not found.")
