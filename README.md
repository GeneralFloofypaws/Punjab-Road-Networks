# Project Goals And Technicalities 

The objective is to build a road-network topology and visualization system using open-source tools.

We started with raw shapefiles and transform them into structured road network consisting of junctions, road segments, classifications, and connectivity information. The final network will be rendered in an interactive map.

## 1. What We Want to Achieve 

__Goal 1 Process raw data__

Take shapefiles containing different road categories 

* National Highways (NH)
* State Highways (SH)
* Major District Roads (MDR)
* Other District Roads (ODR)
* Other road categories available in the dataset

So the code should : 

* Read shapefiles and their attribute tables
* Extract road geometry and metadata
* Validate and clean geometries
* Preserve road names, references, functional classes, bridge/tunnel information and layer attributes 
* Handle inconsistent road reference formats

__Goal 2 Detect Road Intersections and Junctions__

Identify where road features meet geometrically. 

The code should (hopefully):

* Detect intersections between road geometries 
* Identify endpoint-to-endpoint contacts
* Identify endpoint-to-interior contacts
* Identify interior-to-interior crossings 
* Determine whether intersecting roads have matching vertical layers
* Use bridge, tunnel and layer attributes to identify possible grade-separated crossings

This important distinction is that __not every geometric intersection is a physically connected junction__

__Goal 3 Construct the Road Network Topology__

Convert the road geometry into a graph.

* Junctions become nodes
* Roads stretches become edges
* Connected roads share junction nodes
* Grade-separated crossings should not create false connections
* Multiple road features meeting at one location should be represented by one logical junction
* Road segments should connect consecutive junctions

__Goal 4 Split Roads Into Independently Manageable Stretches__

This is particularly important for the final application and all 

Say there's a National Highway passing through several junctions

Instead of treating the entire highway as one feature, we want: 

`Junction A -> Segment 1 -> Junction B -> Segment 2 -> Junction C`

Each segment should have: 

* A unique segment ID
* Its geometry 
* Road designation (NH5, SH20, MDR51, etc.)
* Functional classification
* Length
* Starting and ending junction IDs 
* Relevant original road attributes 

This allows individual road stretches to be selected, toggled, highlighted or analysed

__Goal 5 Classify Junctions__

Determine what kinds of roads meet at each junction.

_Example_

|Mnemonic |Represents           |
|---------|---------------------|
|NH-NH    |Two national HWs     |
|NH-SH    |National and State HW|
|NH-MDR   |National Highway, MDR|
|SH-SH    |Two state HWs        |
|SH-ODR   |State hw and ODR     |
|NH-SH-ODR|All three intersect  |

A junction may have more than two connected roads so classifications must support multiple road connections.

We should be able to preserve both the road designation and OSM functional class. They are different attributes.

__Goal 6: Export structured data__

Generate files that the frontend can consume without repeating the topology calculations.

The intended output:
* segments.geojson: individually identifiable road stretches.
* junctions.geojson: unique junction points and classifications.
* network.json or equivalent: connectivity information, if needed.

__Goal 7: Interactive visualization__

Build an interactive map where users can:
* View the entire road network.
* Toggle NH, SH, MDR, ODR and other categories independently.
* Give each road category a distinct colour.
* Display junctions as coloured points.
* View junction classifications.
* Toggle individual road stretches.
* Inspect road and junction metadata.
* Distinguish bridges, tunnels and grade-separated crossings

__Goal 8: Retrieve building footprint data__

Obtain building footprint polygons for the study area.

Potential data sources:

_OpenStreetMap building footprints through Overpass API or regional extracts._

_Microsoft Global ML Building Footprints._

Other suitable building footprint datasets, depending on local coverage and availability.

The code should:

* Retrieve building polygons for the entire study area.

* Preserve available building IDs and metadata.

* Validate and clean geometries.

* Reproject the data into an appropriate metric coordinate reference system.

* Handle missing or incomplete building coverage.

* Store the downloaded dataset locally so it does not need to be retrieved repeatedly.

We should compare available sources for coverage and completeness before choosing one.

__Goal 9: Calculate building density around junctions__

For every identified junction, analyse the surrounding built-up area.

Create buffers around each junction at multiple distances:

* 100 metres.

* 250 metres.

* 500 metres.

For each buffer, calculate:

* Number of buildings.

* Total building footprint area.

* Percentage of the buffer covered by building footprints.

* Average building footprint area.

The primary metric should be building footprint coverage:

`Building Coverage (%) = (Total Building Footprint Area / Buffer Area) × 100`

Building count and footprint coverage should both be retained because they describe different aspects of the surrounding area.

__Goal 10: Classify junctions by surrounding building density__

Use the calculated building coverage to classify junctions.

An initial classification could be:

* Very High Density: Above 40% coverage.

* High Density: 25–40% coverage.

* Medium Density: 10–25% coverage.

* Low Density: Below 10% coverage.

These are provisional thresholds. We should calibrate them against the actual study area or use quantile-based classification if the distribution makes fixed thresholds unsuitable.

Classifications should be calculated independently for each buffer radius.

This allows us to distinguish immediate junction surroundings from the wider neighbourhood.

__Important:__ Building footprint density is a proxy for built-up intensity, not population density.

__Goal 11: Generate junction density datasets__

Combine the building analysis results with the existing junction metadata.

Each junction should contain:

* Unique junction ID.

* Latitude and longitude.

* Road classification.

* Connected road IDs.

* Building count within 100m, 250m and 500m.

* Total building footprint area within each buffer.

* Building coverage percentage within each buffer.

* Density classification for each buffer radius.

* Generate the following outputs:

   * junction_density.geojson: Junctions with their building density metrics.

   * building_footprints.geojson: Building footprint polygons.

   * Updated junctions.geojson: Junction geometry, road metadata and density attributes.

__Goal 12: Visualize building density__

* Display the surrounding building density of each junction on the interactive map.

* The visualization should:

* Use graduated colours to represent density.

* Use red for very high density.

* Use orange for high density.

* Use yellow for medium density.

* Use green for low density.

* Allow building density visualization to be toggled independently of road classifications.

* Allow users to switch between 100m, 250m and 500m density measurements.

* Display building counts and coverage percentages when inspecting a junction.

* Optionally display the underlying building footprints.

This will allow users to compare junctions based on their surrounding built-up intensity.

__Goal 13: Integrate the complete processing pipeline__

The final pipeline should work as follows:

* Load raw road datasets.

* Clean and validate road geometries.

* Detect geometric intersections.

* Identify valid junctions while accounting for grade separation.

* Assign unique junction IDs.

* Construct road network topology.

* Split roads into individual segments.

* Classify junctions based on connected road categories.

* Retrieve building footprint data for the study area.

* Calculate building metrics around each junction.

* Assign building density classifications.

* Export the processed datasets.

* Visualize the complete road network and density information.

The processing should be automated and repeatable.

We should also:

* Cache downloaded building footprint data locally.

* Use spatial indexing to speed up intersection and building queries.

* Avoid repeatedly querying external APIs for individual junctions.

* Support batch processing.

* Maintain stable junction and segment IDs across processing runs.

* Keep road network processing and building density analysis as separate modules.

* The building density module should consume the generated junctions.geojson rather than being tightly coupled to the intersection detection process.