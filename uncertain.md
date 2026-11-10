# Component Audit

The network has 19 connected components but they aren't 19 concerning issues. 

`C001 - 1052 nodes, 1125 edges, 1324 km ... likely a main connected nw`

`C002 168 nodes, 183 edges, 167 km ... probably a secondary nw`

`C003, C004 are both NH44 and have around the same length so it's likely ki they're separate carriageways`

`C005-C009 MDR, ODR, SH nw and are clearly disconnected regional roads`

`C010 NH44 6 nodes and 6 edges may be connected to C003 AND C004`

`C011-C017 are small disconnected roads visibly`

`C018-C019 they're single nodes so this needs attention and could be a self loop ... refer to self_loop.py`

self_loop.py said

`Empty DataFrame
Columns: [segment_id, road_ref, start_node, end_node, length_m]
Index: []
Empty DataFrame
Columns: [segment_id, road_ref, start_node, end_node, length_m]
Index: []`