---
title: "Traverser API"
linkTitle: "Traverser"
weight: 9
description: "Traverser REST API: Execute complex graph algorithms and path queries including shortest path, k-neighbors, similarity computation, and advanced analytics."
---

### 3.1 Overview of Traverser API

HugeGraphServer provides a RESTful API interface for the HugeGraph graph database. In addition to the basic CRUD operations for vertices and edges, it also offers several traversal methods, which we refer to as the `traverser API`. These traversal methods implement various complex graph algorithms, making it convenient for users to analyze and explore the graph.

The Traverser API supported by HugeGraph includes:

- K-out API: It finds neighbors that are exactly N steps away from a given starting vertex. There are two versions:
    - The basic version uses the GET method to find neighbors that are exactly N steps away from a given starting vertex.
    - The advanced version uses the POST method to find neighbors that are exactly N steps away from a given starting vertex. The advanced version differs from the basic version in the following ways:
        - Supports counting the number of neighbors only
        - Supports filtering by edge and vertex properties
        - Supports returning the shortest path to reach the neighbor
- K-neighbor API: It finds all neighbors that are within N steps of a given starting vertex. There are two versions:
    - The basic version uses the GET method to find all neighbors that are within N steps of a given starting vertex.
    - The advanced version uses the POST method to find all neighbors that are within N steps of a given starting vertex. The advanced version differs from the basic version in the following ways:
        - Supports counting the number of neighbors only
        - Supports filtering by edge and vertex properties
        - Supports returning the shortest path to reach the neighbor
- Same Neighbors: It queries the common neighbors of two vertices.
- Jaccard Similarity API: It calculates the Jaccard similarity, which includes two types:
    - One type uses the GET method to calculate the similarity (intersection over union) of neighbors between two vertices.
    - The other type uses the POST method to find the top N vertices with the highest Jaccard similarity to a given starting vertex in the entire graph.
- Shortest Path API: It finds the shortest path between two vertices.
- All Shortest Paths: It finds all shortest paths between two vertices.
- Weighted Shortest Path: It finds the shortest weighted path from a starting vertex to a target vertex.
- Single Source Shortest Path: It finds the weighted shortest path from a single source vertex to all other vertices.
- Multi Node Shortest Path: It finds the shortest path between every pair of specified vertices.
- Paths API: It finds all paths between two vertices. There are two versions:
    - The basic version uses the GET method to find all paths between a given starting vertex and an ending vertex.
    - The advanced version uses the POST method to find all paths that meet certain conditions between a set of starting vertices and a set of ending vertices.
### 3.2 Detailed Explanation of Traverser API

In the following, we provide a detailed explanation of the Traverser API:

- Customized Paths API: It traverses all paths that pass through a batch of vertices according to a specific pattern.
- Template Path API: It specifies a starting point, an ending point, and the path information between them to find matching paths.
- Crosspoints API: It finds the intersection (common ancestors or common descendants) between two vertices.
- Customized Crosspoints API: It traverses multiple patterns starting from a batch of vertices and finds the intersections with the vertices reached in the final step.
- Rings API: It finds the cyclic paths that can be reached from a starting vertex.
- Rays API: It finds the paths from a starting vertex that reach the boundaries (i.e., paths without cycles).
- Fusiform Similarity API: It finds the fusiform similar vertices to a given vertex.
- Vertices API:
	- Batch querying vertices by ID.
	- Getting the partitions of vertices.
	- Querying vertices by partition.
- Edges API:
	- Batch querying edges by ID.
	- Getting the partitions of edges.
	- Querying edges by partition.

### 3.2 Detailed Explanation of Traverser API

The usage examples provided in this section are based on the graph presented on the TinkerPop official website:

![tinkerpop example graph](http://tinkerpop.apache.org/docs/3.4.0/images/tinkerpop-modern.png)

The data import program is as follows:

```java
public class Loader {
    public static void main(String[] args) {
        HugeClient client = new HugeClient("http://127.0.0.1:8080", "hugegraph");
        SchemaManager schema = client.schema();
        schema.propertyKey("name").asText().ifNotExist().create();
        schema.propertyKey("age").asInt().ifNotExist().create();
        schema.propertyKey("city").asText().ifNotExist().create();
        schema.propertyKey("weight").asDouble().ifNotExist().create();
        schema.propertyKey("lang").asText().ifNotExist().create();
        schema.propertyKey("date").asText().ifNotExist().create();
        schema.propertyKey("price").asInt().ifNotExist().create();

        schema.vertexLabel("person")
              .properties("name", "age", "city")
              .primaryKeys("name")
              .nullableKeys("age")
              .ifNotExist()
              .create();

        schema.vertexLabel("software")
              .properties("name", "lang", "price")
              .primaryKeys("name")
              .nullableKeys("price")
              .ifNotExist()
              .create();

        schema.indexLabel("personByCity")
              .onV("person")
              .by("city")
              .secondary()
              .ifNotExist()
              .create();

        schema.indexLabel("personByAgeAndCity")
              .onV("person")
              .by("age", "city")
              .secondary()
              .ifNotExist()
              .create();

        schema.indexLabel("softwareByPrice")
              .onV("software")
              .by("price")
              .range()
              .ifNotExist()
              .create();

        schema.edgeLabel("knows")
              .multiTimes()
              .sourceLabel("person")
              .targetLabel("person")
              .properties("date", "weight")
              .sortKeys("date")
              .nullableKeys("weight")
              .ifNotExist()
              .create();

        schema.edgeLabel("created")
              .sourceLabel("person").targetLabel("software")
              .properties("date", "weight")
              .nullableKeys("weight")
              .ifNotExist()
              .create();

        schema.indexLabel("createdByDate")
              .onE("created")
              .by("date")
              .secondary()
              .ifNotExist()
              .create();

        schema.indexLabel("createdByWeight")
              .onE("created")
              .by("weight")
              .range()
              .ifNotExist()
              .create();

        schema.indexLabel("knowsByWeight")
              .onE("knows")
              .by("weight")
              .range()
              .ifNotExist()
              .create();

        GraphManager graph = client.graph();
        Vertex marko = graph.addVertex(T.label, "person", "name", "marko",
                                       "age", 29, "city", "Beijing");
        Vertex vadas = graph.addVertex(T.label, "person", "name", "vadas",
                                       "age", 27, "city", "Hongkong");
        Vertex lop = graph.addVertex(T.label, "software", "name", "lop",
                                     "lang", "java", "price", 328);
        Vertex josh = graph.addVertex(T.label, "person", "name", "josh",
                                      "age", 32, "city", "Beijing");
        Vertex ripple = graph.addVertex(T.label, "software", "name", "ripple",
                                        "lang", "java", "price", 199);
        Vertex peter = graph.addVertex(T.label, "person", "name", "peter",
                                       "age", 35, "city", "Shanghai");

        marko.addEdge("knows", vadas, "date", "20160110", "weight", 0.5);
        marko.addEdge("knows", josh, "date", "20130220", "weight", 1.0);
        marko.addEdge("created", lop, "date", "20171210", "weight", 0.4);
        josh.addEdge("created", lop, "date", "20091111", "weight", 0.4);
        josh.addEdge("created", ripple, "date", "20171210", "weight", 1.0);
        peter.addEdge("created", lop, "date", "20170324", "weight", 0.2);
    }
}
```

The vertex IDs are:

```
"2:ripple",
"1:vadas",
"1:peter",
"1:josh",
"1:marko",
"2:lop"
```

The edge IDs are:

```
"S1:peter>2>>S2:lop",
"S1:josh>2>>S2:lop",
"S1:josh>2>>S2:ripple",
"S1:marko>1>20130220>S1:josh",
"S1:marko>1>20160110>S1:vadas",
"S1:marko>2>>S2:lop"
```

#### 3.2.1 K-out API (GET, Basic Version)

##### 3.2.1.1 Functionality Overview

The K-out API allows you to find vertices that are exactly "depth" steps away from a given starting vertex, considering the specified direction, edge type (optional), and depth.

###### Params

- source: ID of the starting vertex (required)
- direction: Direction of traversal from the starting vertex (OUT, IN, BOTH). Optional, default is BOTH.
- max_depth: Number of steps (required)
- label: Edge type (optional), represents all edge labels by default
- nearest: When nearest is set to true, it means the shortest path length from the starting vertex to the result vertices is equal to the depth, and there is no shorter path. When nearest is set to false, it means there is at least one path of length depth from the starting vertex to the result vertices (not necessarily the shortest and may contain cycles). Optional, default is true.
- max_degree: Maximum number of adjacent edges to traverse per vertex during the query. Optional, default is 10000.
- capacity: Maximum number of vertices to be visited during the traversal. Optional, default is 10000000.
- limit: Maximum number of vertices to be returned. Optional, default is 10000000.

##### 3.2.1.2 Usage Example

###### Method & Url

```
GET http://localhost:8080/graphs/{graph}/traversers/kout?source="1:marko"&max_depth=2
```

###### Response Status

```json
200
```

###### Response Body

```json
{
    "vertices":[
        "2:ripple",
        "1:peter"
    ]
}
```

##### 3.2.1.3 Use Cases

Finding vertices that are exactly N steps away in a relationship. Two examples:

- In a family relationship, finding all grandchildren of a person. The set of vertices that can be reached by person A through two consecutive "son" edges.
- Discovering potential friends in a social network. For example, finding users who are two degrees of friendship away from the target user, reachable through two consecutive "friend" edges.

#### 3.2.2 K-out API (POST, Advanced Version)

##### 3.2.2.1 Functionality Overview

The K-out API allows you to find vertices that are exactly "depth" steps away from a given starting vertex, considering the specified steps (including direction, edge type, and attribute filtering).

> The advanced version differs from the basic version of K-out API in the following aspects:
> - Supports counting the number of neighbors only
> - Supports edge attribute filtering
> - Supports returning the shortest path to the neighbor

###### Params

- source: The ID of the starting vertex, required.
- steps: Steps from the starting point, required, with the following structure:
    - direction: Represents the direction of the edges (OUT, IN, BOTH), default is BOTH.
    - edge_steps: The step set of edges, supporting label and properties filtering for the edge. If edge_steps is empty, the edge is not filtered.
        - label: Edge types.
        - properties: Filter edges based on property values.
    - vertex_steps: The step set of vertices, supporting label and properties filtering for the vertex. If vertex_steps is empty, the vertex is not filtered.
        - label: Vertex types.
        - properties: Filter vertices based on property values.
    - max_degree: Maximum number of adjacent edges to traverse for a single vertex, default is 10000 (Note: Prior to version 0.12, the parameter name was "degree" instead of "max_degree". Starting from version 0.12, "max_degree" is used uniformly, while still supporting the "degree" syntax for backward compatibility).
    - skip_degree: Sets the minimum number of edges to skip super vertices during the query process. If the number of adjacent edges for a vertex is greater than skip_degree, the vertex is completely skipped. Optional. If enabled, it should satisfy the constraint `skip_degree >= max_degree`. Default is 0 (not enabled), indicating no skipping of any vertices (Note: Enabling this configuration means that during traversal, an attempt will be made to access skip_degree edges of a vertex, not just max_degree edges. This incurs additional traversal overhead and may have a significant impact on query performance. Please enable it only after understanding the implications).
- max_depth: Number of steps, required.
- nearest: When nearest is true, it means the shortest path length from the starting vertex to the result vertex is equal to depth, and there is no shorter path. When nearest is false, it means there is a path of length depth from the starting vertex to the result vertex (not necessarily the shortest and can contain cycles). Optional, default is true.
- count_only: Boolean value, true indicates only counting the number of results without returning specific results, false indicates returning specific results. Default is false.
- with_path: When true, it returns the shortest path from the starting vertex to each neighbor. When false, it does not return the shortest path. Optional, default is false.
- with_edge: Optional parameter, default is false:
    - When true, the result will include complete edge information (all edges in the path):
        - When with_path is true, it returns complete information of all edges in all paths.
        - When with_path is false, no information is returned.
    - When false, it only returns edge IDs.
- with_vertex: Optional parameter, default is false:
    - When true, the result will include complete vertex information (all vertices in the path):
        - When with_path is true, it returns complete information of all vertices in all paths.
        - When with_path is false, it returns complete information of all neighbors.
    - When false, it only returns vertex IDs.
- capacity: Maximum number of vertices to visit during traversal. Optional, default is 10000000.
- limit: Maximum number of vertices to return. Optional, default is 10000000.
- traverse_mode: Traversal mode. There are two options: "breadth_first_search" and "depth_first_search", default is "breadth_first_search".

##### 3.2.2.2 Usage

###### Method & Url

```
POST http://localhost:8080/graphs/{graph}/traversers/kout
```

###### Request Body

```json
{
    "source": "1:marko",
    "steps": {
        "direction": "BOTH",
        "edge_steps": [
            {
                "label": "knows",
                "properties": {
                    "weight": "P.gt(0.1)"
                }
            },
            {
                "label": "created",
                "properties": {
                    "weight": "P.gt(0.1)"
                }
            }
        ],
        "vertex_steps": [
            {
                "label": "person",
                "properties": {
                    "age": "P.lt(32)"
                }
            },
            {
                "label": "software",
                "properties": {}
            }
        ],
        "max_degree": 10000,
        "skip_degree": 100000
    },
    "max_depth": 1,
    "nearest": true,
    "limit": 10000,
    "with_vertex": true,
    "with_path": true,
    "with_edge": true
}
```

###### Response Status

```json
200
```

###### Response Body

```json
{
    "size": 2,
    "kout": [
        "1:vadas",
        "2:lop"
    ],
    "paths": [
        {
            "objects": [
                "1:marko",
                "2:lop"
            ]
        },
        {
            "objects": [
                "1:marko",
                "1:vadas"
            ]
        }
    ],
    "vertices": [
        {
            "id": "1:marko",
            "label": "person",
            "type": "vertex",
            "properties": {
                "name": "marko",
                "age": 29,
                "city": "Beijing"
            }
        },
        {
            "id": "1:vadas",
            "label": "person",
            "type": "vertex",
            "properties": {
                "name": "vadas",
                "age": 27,
                "city": "Hongkong"
            }
        },
        {
            "id": "2:lop",
            "label": "software",
            "type": "vertex",
            "properties": {
                "name": "lop",
                "lang": "java",
                "price": 328
            }
        }
    ],
    "edges": [
        {
            "id": "S1:marko>1>20160110>S1:vadas",
            "label": "knows",
            "type": "edge",
            "outV": "1:marko",
            "outVLabel": "person",
            "inV": "1:vadas",
            "inVLabel": "person",
            "properties": {
                "weight": 0.5,
                "date": "20160110"
            }
        },
        {
            "id": "S1:marko>2>>S2:lop",
            "label": "created",
            "type": "edge",
            "outV": "1:marko",
            "outVLabel": "person",
            "inV": "2:lop",
            "inVLabel": "software",
            "properties": {
                "weight": 0.4,
                "date": "20171210"
            }
        }
    ]
}

```

##### 3.2.2.3 Use Cases

Refer to 3.2.1.3.

#### 3.2.3 K-neighbor (GET, Basic Version)

##### 3.2.3.1 Function Introduction

Find all vertices that are reachable within depth steps, including the starting vertex, based on the starting vertex, direction, edge type (optional), and depth.

> Equivalent to the union of: starting vertex, K-out(1), K-out(2), ..., K-out(max_depth).

###### Params

- source: ID of the starting vertex, required.
- direction: Direction in which the starting vertex's edges extend (OUT, IN, BOTH). Optional, default is BOTH.
- max_depth: Number of steps, required.
- label: Edge type, optional, default represents all edge labels.
- max_degree: Maximum number of adjacent edges to traverse for a single vertex during the query process. Optional, default is 10000.
- limit: Maximum number of vertices to return, also represents the maximum number of vertices to visit during traversal. Optional, default is 10000000.

##### 3.2.3.2 Usage

###### Method & Url

```
GET http://localhost:8080/graphs/{graph}/traversers/kneighbor?source=“1:marko”&max_depth=2
```

###### Response Status

```json
200
```

###### Response Body

```json
{
    "vertices":[
        "2:ripple",
        "1:marko",
        "1:josh",
        "1:vadas",
        "1:peter",
        "2:lop"
    ]
}
```

##### 3.2.3.3 Use Cases

Find all vertices reachable within N steps, for example:

- In a family relationship, find all descendants within five generations of a person. This can be achieved by traversing five consecutive "parent-child" edges from person A.
- In a social network, discover friend circles. For example, users who can be reached by 1, 2, or 3 "friend" edges from the target user can form the target user's friend circle.

#### 3.2.4 K-neighbor API (POST, Advanced Version)

##### 3.2.4.1 Function Introduction

Find all vertices that are reachable within depth steps from the starting vertex, based on the starting vertex, steps (including direction, edge type, and filter properties), and depth.

> The difference from the Basic Version of K-neighbor API is that:
> - It supports counting the number of neighbors only.
> - It supports filtering edges based on their properties.
> - It supports returning the shortest path to reach the neighbors.

###### Params

- source: Starting vertex ID, required.
- steps: Steps from the starting point, required, with the following structure:
    - direction: Represents the direction of the edges (OUT, IN, BOTH), default is BOTH.
    - edge_steps: The step set of edges, supporting label and properties filtering for the edge. If edge_steps is empty, the edge is not filtered.
        - label: Edge types.
        - properties: Filter edges based on property values.
    - vertex_steps: The step set of vertices, supporting label and properties filtering for the vertex. If vertex_steps is empty, the vertex is not filtered.
        - label: Vertex types.
        - properties: Filter vertices based on property values.
    - max_degree: Maximum number of adjacent edges to traverse for each vertex during the query process. Default is 10000. (Note: Before version 0.12, the parameter name within the step only supported "degree." Starting from version 0.12, it is unified as "max_degree" and is backward compatible with the "degree" notation.)
    - skip_degree: Used to set the minimum number of edges to discard super vertices during the query process. When the number of adjacent edges for a vertex exceeds skip_degree, the vertex is completely discarded. This is an optional parameter. If enabled, it should satisfy the constraint `skip_degree >= max_degree`. Default is 0 (not enabled), which means no vertices are skipped. (Note: When this configuration is enabled, the traversal will attempt to access skip_degree edges for each vertex, not just max_degree edges. This incurs additional traversal overhead and may significantly impact query performance. Please make sure to understand this before enabling.)
- max_depth: Number of steps, required.
- count_only: Boolean value. If true, only the count of results is returned without the actual results. If false, the specific results are returned. Default is false.
- with_path: If true, the shortest path from the starting point to each neighbor is returned. If false, the shortest path from the starting point to each neighbor is not returned. This is an optional parameter. Default is false.
- with_edge: Optional parameter, default is false:
    - When true, the result will include complete edge information (all edges in the path):
        - When with_path is true, it returns complete information of all edges in all paths.
        - When with_path is false, no information is returned.
    - When false, it only returns edge IDs.
- with_vertex: Optional parameter, default is false:
    - When true, the result will include complete vertex information (all vertices in the path):
        - When with_path is true, it returns complete information of all vertices in all paths.
        - When with_path is false, it returns complete information of all neighbors.
    - When false, it only returns vertex IDs.
- limit: Maximum number of vertices to be returned. Also, the maximum number of vertices visited during the traversal process. This is an optional parameter. Default is 10000000.

##### 3.2.4.2 Usage Method

###### Method & Url

```
POST http://localhost:8080/graphs/{graph}/traversers/kneighbor
```

###### Request Body

```json
{
    "source": "1:marko",
    "steps": {
        "direction": "BOTH",
        "edge_steps": [
            {
                "label": "knows",
                "properties": {
                    "weight": "P.gt(0.1)"
                }
            },
            {
                "label": "created",
                "properties": {
                    "weight": "P.gt(0.1)"
                }
            }
        ],
        "vertex_steps": [
            {
                "label": "person",
                "properties": {
                    "age": "P.lt(32)"
                }
            },
            {
                "label": "software",
                "properties": {}
            }
        ],
        "max_degree": 10000,
        "skip_degree": 100000
    },
    "max_depth": 1,
    "nearest": true,
    "limit": 10000,
    "with_vertex": true,
    "with_path": true,
    "with_edge": true
}
```

###### Response Status

```json
200
```

###### Response Body

```json
{
    "size": 4,
    "kneighbor": [
        "1:josh",
        "2:lop",
        "1:peter",
        "2:ripple"
    ],
    "paths": [
        {
            "objects": [
                "1:marko",
                "2:lop"
            ]
        },
        {
            "objects": [
                "1:marko",
                "2:lop",
                "1:peter"
            ]
        },
        {
            "objects": [
                "1:marko",
                "1:josh"
            ]
        },
        {
            "objects": [
                "1:marko",
                "1:josh",
                "2:ripple"
            ]
        }
    ],
    "vertices": [
        {
            "id": "2:ripple",
            "label": "software",
            "type": "vertex",
            "properties": {
                "name": "ripple",
                "lang": "java",
                "price": 199
            }
        },
        {
            "id": "1:marko",
            "label": "person",
            "type": "vertex",
            "properties": {
                "name": "marko",
                "age": 29,
                "city": "Beijing"
            }
        },
        {
            "id": "1:josh",
            "label": "person",
            "type": "vertex",
            "properties": {
                "name": "josh",
                "age": 32,
                "city": "Beijing"
            }
        },
        {
            "id": "1:peter",
            "label": "person",
            "type": "vertex",
            "properties": {
                "name": "peter",
                "age": 35,
                "city": "Shanghai"
            }
        },
        {
            "id": "2:lop",
            "label": "software",
            "type": "vertex",
            "properties": {
                "name": "lop",
                "lang": "java",
                "price": 328
            }
        }
    ],
    "edges": [
        {
            "id": "S1:josh>2>>S2:ripple",
            "label": "created",
            "type": "edge",
            "outV": "1:josh",
            "outVLabel": "person",
            "inV": "2:ripple",
            "inVLabel": "software",
            "properties": {
                "weight": 1.0,
                "date": "20171210"
            }
        },
        {
            "id": "S1:marko>2>>S2:lop",
            "label": "created",
            "type": "edge",
            "outV": "1:marko",
            "outVLabel": "person",
            "inV": "2:lop",
            "inVLabel": "software",
            "properties": {
                "weight": 0.4,
                "date": "20171210"
            }
        },
        {
            "id": "S1:marko>1>20130220>S1:josh",
            "label": "knows",
            "type": "edge",
            "outV": "1:marko",
            "outVLabel": "person",
            "inV": "1:josh",
            "inVLabel": "person",
            "properties": {
                "weight": 1.0,
                "date": "20130220"
            }
        },
        {
            "id": "S1:peter>2>>S2:lop",
            "label": "created",
            "type": "edge",
            "outV": "1:peter",
            "outVLabel": "person",
            "inV": "2:lop",
            "inVLabel": "software",
            "properties": {
                "weight": 0.2,
                "date": "20170324"
            }
        }
    ]
}
```

##### 3.2.4.3 Use Cases

See 3.2.3.3

#### 3.2.5 Same Neighbors

##### 3.2.5.1 Function Introduction

Retrieve the common neighbors of two vertices.

###### Params

- vertex: ID of one vertex, required.
- other: ID of another vertex, required.
- direction: Direction in which the vertex expands outward (OUT, IN, BOTH). Optional, default is BOTH.
- label: Edge type. Optional, default represents all edge labels.
- max_degree: Maximum number of adjacent edges to traverse for each vertex during the query process. Optional, default is 10000.
- limit: Maximum number of common neighbors to be returned. Optional, default is 10000000.

##### 3.2.5.2 Usage Method

###### Method & Url

```
GET http://localhost:8080/graphs/{graph}/traversers/sameneighbors?vertex=“1:marko”&other="1:josh"
```

###### Response Status

```json
200
```

###### Response Body

```json
{
    "same_neighbors":[
        "2:lop"
    ]
}
```

##### 3.2.5.3 Use Cases

Find the common neighbors of two vertices:

- In a social network, find the common followers or users both users are following.

#### 3.2.6 Jaccard Similarity (GET)

##### 3.2.6.1 Function Introduction

Compute the Jaccard similarity between two vertices (the intersection of the neighbors of the two vertices divided by the union of the neighbors of the two vertices).

###### Params

- vertex: ID of one vertex, required.
- other: ID of another vertex, required.
- direction: Direction in which the vertex expands outward (OUT, IN, BOTH). Optional, default is BOTH.
- label: Edge type. Optional, default represents all edge labels.
- max_degree: Maximum number of adjacent edges to traverse for each vertex during the query process. Optional, default is 10000.

##### 3.2.6.2 Usage Method

###### Method & Url

```
GET http://localhost:8080/graphs/{graph}/traversers/jaccardsimilarity?vertex="1:marko"&other="1:josh"
```

###### Response Status

```json
200
```

###### Response Body

```json
{
    "jaccard_similarity": 0.2
}
```

##### 3.2.6.3 Use Cases

Used to evaluate the similarity or closeness between two vertices.

#### 3.2.7 Jaccard Similarity (POST)

##### 3.2.7.1 Function Introduction

Compute the N vertices with the highest Jaccard similarity to a specified vertex.

> The Jaccard similarity is calculated as the intersection of the neighbors of the two vertices divided by the union of the neighbors of the two vertices.

###### Params

- vertex: ID of a vertex, required.
- Steps from the starting point, required. The structure is as follows:
	- direction: Direction of the edges (OUT, IN, BOTH). Optional, default is BOTH.
	- labels: List of edge types.
	- properties: Filter edges based on property values.
	- max_degree: Maximum number of adjacent edges to traverse for each vertex during the query process. Default is 10000. (Note: Prior to version 0.12, the parameter name inside "step" was "degree". Starting from version 0.12, it is unified as "max_degree" and still compatible with "degree" notation.)
	- skip_degree: Used to set the minimum number of edges to skip super vertices during the query process. If the number of adjacent edges for a vertex is greater than skip_degree, the vertex is completely skipped. Optional, default is 0 (not enabled), which means no skipping. (Note: When this configuration is enabled, the traversal will attempt to access skip_degree edges of a vertex, not just max_degree edges. This incurs additional traversal overhead and may have a significant impact on query performance. Please enable it after understanding and confirming.)
- top: Return the top N vertices with the highest Jaccard similarity for a starting vertex. Optional, default is 100.
- capacity: Maximum number of vertices to be visited during the traversal process. Optional, default is 10000000.

##### 3.2.7.2 Usage Method

###### Method & Url

```
POST http://localhost:8080/graphs/{graph}/traversers/jaccardsimilarity
```

###### Request Body

```json
{
  "vertex": "1:marko",
  "step": {
    "direction": "BOTH",
    "labels": [],
    "max_degree": 10000,
    "skip_degree": 100000
  },
  "top": 3
}
```

###### Response Status

```json
200
```

###### Response Body

```json
{
    "2:ripple": 0.3333333333333333,
    "1:peter": 0.3333333333333333,
    "1:josh": 0.2
}
```

##### 3.2.7.3 Use Cases

Used to find the vertices in the graph that have the highest similarity to a specified vertex.

#### 3.2.8 Shortest Path

##### 3.2.8.1 Function Introduction

Find the shortest path between a starting vertex and a target vertex based on the direction, edge type (optional), and maximum depth.

###### Params

- source: ID of the starting vertex, required.
- target: ID of the target vertex, required.
- direction: Direction in which the starting vertex expands (OUT, IN, BOTH). Optional, default is BOTH.
- max_depth: Maximum number of steps, required.
- label: Edge type, optional. Default represents all edge labels.
- max_degree: Maximum number of adjacent edges to traverse for each vertex during the query process. Optional, default is 10000.
- skip_degree: Used to set the minimum number of edges to skip super vertices during the query process. If the number of adjacent edges for a vertex is greater than skip_degree, the vertex is completely skipped. Optional, default is 0 (not enabled), which means no skipping. (Note: When this configuration is enabled, the traversal will attempt to access skip_degree edges of a vertex, not just max_degree edges. This incurs additional traversal overhead and may have a significant impact on query performance. Please enable it after understanding and confirming.)
- capacity: Maximum number of vertices to be visited during the traversal process. Optional, default is 10000000.

##### 3.2.8.2 Usage Method

###### Method & Url

```
GET http://localhost:8080/graphs/{graph}/traversers/shortestpath?source="1:marko"&target="2:ripple"&max_depth=3
```

###### Response Status

```json
200
```

###### Response Body

```json
{
    "path":[
        "1:marko",
        "1:josh",
        "2:ripple"
    ]
}
```

##### 3.2.8.3 Use Cases

Used to find the shortest path between two vertices, for example:

- In a social network, finding the shortest path between two users, representing the closest friend relationship chain.
- In a device association network, finding the shortest association relationship between two devices.

#### 3.2.9 All Shortest Paths

##### 3.2.9.1 Function Introduction

Find all shortest paths between a starting vertex and a target vertex based on the direction, edge type (optional), and maximum depth.

###### Params

- source: ID of the starting vertex, required.
- target: ID of the target vertex, required.
- direction: Direction in which the starting vertex expands (OUT, IN, BOTH). Optional, default is BOTH.
- max_depth: Maximum number of steps, required.
- label: Edge type, optional. Default represents all edge labels.
- max_degree: Maximum number of adjacent edges to traverse for each vertex during the query process. Optional, default is 10000.
- skip_degree: Used to set the minimum number of edges to skip super vertices during the query process. If the number of adjacent edges for a vertex is greater than skip_degree, the vertex is completely skipped. Optional, default is 0 (not enabled), which means no skipping. (Note: When this configuration is enabled, the traversal will attempt to access skip_degree edges of a vertex, not just max_degree edges. This incurs additional traversal overhead and may have a significant impact on query performance. Please enable it after understanding and confirming.)
- capacity: Maximum number of vertices to be visited during the traversal process. Optional, default is 10000000.

##### 3.2.9.2 Usage Method

###### Method & Url

```
GET http://localhost:8080/graphs/{graph}/traversers/allshortestpaths?source="A"&target="Z"&max_depth=10
```

###### Response Status

```json
200
```

###### Response Body

```json
{
    "paths":[
        {
            "objects": [
                "A",
                "B",
                "C",
                "Z"
            ]
        },
        {
            "objects": [
                "A",
                "M",
                "N",
                "Z"
            ]
        }
    ]
}
```

##### 3.2.9.3 Use Cases

Used to find all shortest paths between two vertices, for example:

- In a social network, finding all shortest paths between two users, representing all the closest friend relationship chains.
- In a device association network, finding all shortest association relationships between two devices.

#### 3.2.10 Weighted Shortest Path

##### 3.2.10.1 Function Introduction

Find a weighted shortest path between a starting vertex and a target vertex based on the direction, edge type (optional), maximum depth, and edge weight property.

###### Params

- source: ID of the starting vertex, required.
- target: ID of the target vertex, required.
- direction: Direction in which the starting vertex expands (OUT, IN, BOTH). Optional, default is BOTH.
- label: Edge type, optional. Default represents all edge labels.
- weight: Edge weight property, required. It must be a numeric property.
- max_degree: Maximum number of adjacent edges to traverse for each vertex during the query process. Optional, default is 10000.
- skip_degree: Used to set the minimum number of edges to skip super vertices during the query process. If the number of adjacent edges for a vertex is greater than skip_degree, the vertex is completely skipped. Optional, default is 0 (not enabled), which means no skipping. (Note: When this configuration is enabled, the traversal will attempt to access skip_degree edges of a vertex, not just max_degree edges. This incurs additional traversal overhead and may have a significant impact on query performance. Please enable it after understanding and confirming.)
- capacity: Maximum number of vertices to be visited during the traversal process. Optional, default is 10000000.
- with_vertex: true to include complete vertex information (all vertices in the path) in the result, false to only return vertex IDs. Optional, default is false.

##### 3.2.10.2 Usage Method

###### Method & Url

```
GET http://localhost:8080/graphs/{graph}/traversers/weightedshortestpath?source="1:marko"&target="2:ripple"&weight="weight"&with_vertex=true
```

###### Response Status

```json
200
```

###### Response Body

```json
{
    "path": {
        "weight": 2.0,
        "vertices": [
            "1:marko",
            "1:josh",
            "2:ripple"
        ]
    },
    "vertices": [
        {
            "id": "1:marko",
            "label": "person",
            "type": "vertex",
            "properties": {
                "name": "marko",
                "age": 29,
                "city": "Beijing"
            }
        },
        {
            "id": "1:josh",
            "label": "person",
            "type": "vertex",
            "properties": {
                "name": "josh",
                "age": 32,
                "city": "Beijing"
            }
        },
        {
            "id": "2:ripple",
            "label": "software",
            "type": "vertex",
            "properties": {
                "name": "ripple",
                "lang": "java",
                "price": 199
            }
        }
    ]
}
```

##### 3.2.10.3 Use Cases

Used to find the weighted shortest path between two vertices, for example:

- In a transportation network, finding the transportation method that requires the least cost from city A to city B.

#### 3.2.11 Single Source Shortest Path

##### 3.2.11.1 Function Introduction

Starting from a vertex, find the shortest paths from that vertex to other vertices in the graph (optional with weight).

###### Params

- source: ID of the starting vertex, required.
- direction: Direction in which the starting vertex expands (OUT, IN, BOTH). Optional, default is BOTH.
- label: Edge type, optional. Default represents all edge labels.
- weight: Edge weight property, optional. It must be a numeric property. If not provided or the edges don't have this property, the weight is considered as 1.0.
- max_degree: Maximum number of adjacent edges to traverse for each vertex during the query process. Optional, default is 10000.
- skip_degree: Used to set the minimum number of edges to skip super vertices during the query process. If the number of adjacent edges for a vertex is greater than skip_degree, the vertex is completely skipped. Optional, default is 0 (not enabled), which means no skipping. (Note: When this configuration is enabled, the traversal will attempt to access skip_degree edges of a vertex, not just max_degree edges. This incurs additional traversal overhead and may have a significant impact on query performance. Please enable it after understanding and confirming.)
- capacity: Maximum number of vertices to be visited during the traversal process. Optional, default is 10000000.
- limit: Number of target vertices to be queried and the number of shortest paths to be returned. Optional, default is 10.
- with_vertex: true to include complete vertex information (all vertices in the path) in the result, false to only return vertex IDs. Optional, default is false.

##### 3.2.11.2 Usage Method

###### Method & Url

```
GET http://localhost:8080/graphs/{graph}/traversers/singlesourceshortestpath?source="1:marko"&with_vertex=true
```

###### Response Status

```json
200
```

###### Response Body

```json
{
    "paths": {
        "2:ripple": {
            "weight": 2.0,
            "vertices": [
                "1:marko",
                "1:josh",
                "2:ripple"
            ]
        },
        "1:josh": {
            "weight": 1.0,
            "vertices": [
                "1:marko",
                "1:josh"
            ]
        },
        "1:vadas": {
            "weight": 1.0,
            "vertices": [
                "1:marko",
                "1:vadas"
            ]
        },
        "1:peter": {
            "weight": 2.0,
            "vertices": [
                "1:marko",
                "2:lop",
                "1:peter"
            ]
        },
        "2:lop": {
            "weight": 1.0,
            "vertices": [
                "1:marko",
                "2:lop"
            ]
        }
    },
    "vertices": [
        {
            "id": "2:ripple",
            "label": "software",
            "type": "vertex",
            "properties": {
                "name": "ripple",
                "lang": "java",
                "price": 199
            }
        },
        {
            "id": "1:marko",
            "label": "person",
            "type": "vertex",
            "properties": {
                "name": "marko",
                "age": 29,
                "city": "Beijing"
            }
        },
        {
            "id": "1:josh",
            "label": "person",
            "type": "vertex",
            "properties": {
                "name": "josh",
                "age": 32,
                "city": "Beijing"
            }
        },
        {
            "id": "1:vadas",
            "label": "person",
            "type": "vertex",
            "properties": {
                "name": "vadas",
                "age": 27,
                "city": "Hongkong"
            }
        },
        {
            "id": "1:peter",
            "label": "person",
            "type": "vertex",
            "properties": {
                "name": "peter",
                "age": 35,
                "city": "Shanghai"
            }
        },
        {
            "id": "2:lop",
            "label": "software",
            "type": "vertex",
            "properties": {
                "name": "lop",
                "lang": "java",
                "price": 328
            }
        }
    ]
}
```

##### 3.2.11.3 Use Cases

Used to find the weighted shortest path from one vertex to other vertices, for example:

- Finding the shortest travel time by bus from Beijing to all other cities in the country.

#### 3.2.12 Multi Node Shortest Path

##### 3.2.12.1 Function Introduction

Finds the shortest paths between pairs of specified vertices.

###### Params

- vertices: Defines the starting vertices, required. It can be specified in the following ways:
	- ids: Provide a list of vertex IDs as starting vertices.
	- label and properties: If no IDs are specified, use the combined conditions of label and properties to query the starting vertices.
		- label: Vertex type.
		- properties: Query the starting vertices based on property values.
		> Note: Property values in properties can be a list, indicating that the value of the key can be any value in the list.
- step: Represents the path from the starting vertices to the destination vertices, required. The structure of the step is as follows:
	- direction: Represents the direction of the edges (OUT, IN, BOTH). Default is BOTH.
	- labels: List of edge types.
	- properties: Filters the edges based on property values.
	- max_degree: Maximum number of adjacent edges to traverse for each vertex during the query process. Default is 10000. (Note: Before version 0.12, the step only supported "degree" as the parameter name. Starting from version 0.12, "max_degree" is used uniformly, and "degree" is still supported for backward compatibility.)
	- skip_degree: Used to set the minimum number of edges to skip super vertices during the query process. If the number of adjacent edges for a vertex is greater than skip_degree, the vertex is completely skipped. Optional, default is 0 (not enabled), which means no skipping. (Note: When this configuration is enabled, the traversal will attempt to access skip_degree edges of a vertex, not just max_degree edges. This incurs additional traversal overhead and may have a significant impact on query performance. Please enable it after understanding and confirming.)
- max_depth: Number of steps, required.
- capacity: Maximum number of vertices to be visited during the traversal process. Optional, default is 10000000.
- with_vertex: true to include complete vertex information (all vertices in the path) in the result, false to only return vertex IDs. Optional, default is false.

##### 3.2.12.2 Usage Method

###### Method & Url

```
POST http://localhost:8080/graphs/{graph}/traversers/multinodeshortestpath
```

###### Request Body

```json
{
    "vertices": {
        "ids": ["382:marko", "382:josh", "382:vadas", "382:peter", "383:lop", "383:ripple"]
    },
    "step": {
        "direction": "BOTH",
        "properties": {
        }
    },
    "max_depth": 10,
    "capacity": 100000000,
    "with_vertex": true
}
```

###### Response Status

```json
200
```

###### Response Body

```json
{
    "paths": [
        {
            "objects": [
                "382:peter",
                "383:lop"
            ]
        },
        {
            "objects": [
                "382:peter",
                "383:lop",
                "382:marko"
            ]
        },
        {
            "objects": [
                "382:peter",
                "383:lop",
                "382:josh"
            ]
        },
        {
            "objects": [
                "382:peter",
                "383:lop",
                "382:marko",
                "382:vadas"
            ]
        },
        {
            "objects": [
                "383:lop",
                "382:marko"
            ]
        },
        {
            "objects": [
                "383:lop",
                "382:josh"
            ]
        },
        {
            "objects": [
                "383:lop",
                "382:marko",
                "382:vadas"
            ]
        },
        {
            "objects": [
                "382:peter",
                "383:lop",
                "382:josh",
                "383:ripple"
            ]
        },
        {
            "objects": [
                "382:marko",
                "382:josh"
            ]
        },
        {
            "objects": [
                "383:lop",
                "382:josh",
                "383:ripple"
            ]
        },
        {
            "objects": [
                "382:marko",
                "382:vadas"
            ]
        },
        {
            "objects": [
                "382:marko",
                "382:josh",
                "383:ripple"
            ]
        },
        {
            "objects": [
                "382:josh",
                "383:ripple"
            ]
        },
        {
            "objects": [
                "382:josh",
                "382:marko",
                "382:vadas"
            ]
        },
        {
            "objects": [
                "382:vadas",
                "382:marko",
                "382:josh",
                "383:ripple"
            ]
        }
    ],
    "vertices": [
        {
            "id": "382:peter",
            "label": "person",
            "type": "vertex",
            "properties": {
                "name": "peter",
                "age": 29,
                "city": "Shanghai"
            }
        },
        {
            "id": "383:lop",
            "label": "software",
            "type": "vertex",
            "properties": {
                "name": "lop",
                "lang": "java",
                "price": 328
            }
        },
        {
            "id": "382:marko",
            "label": "person",
            "type": "vertex",
            "properties": {
                "name": "marko",
                "age": 29,
                "city": "Beijing"
            }
        },
        {
            "id": "382:josh",
            "label": "person",
            "type": "vertex",
            "properties": {
                "name": "josh",
                "age": 32,
                "city": "Beijing"
            }
        },
        {
            "id": "382:vadas",
            "label": "person",
            "type": "vertex",
            "properties": {
                "name": "vadas",
                "age": 27,
                "city": "Hongkong"
            }
        },
        {
            "id": "383:ripple",
            "label": "software",
            "type": "vertex",
            "properties": {
                "name": "ripple",
                "lang": "java",
                "price": 199
            }
        }
    ]
}
```

##### 3.2.12.3 Use Cases

Used to find the shortest paths between multiple vertices, for example:

- Finding the shortest paths between multiple companies and their legal representatives.

#### 3.2.13 Paths (GET, Basic Version)

##### 3.2.13.1 Function Introduction

Finds all paths based on conditions such as the starting vertex, destination vertex, direction, edge types (optional), and maximum depth.

###### Params

- source: ID of the starting vertex, required.
- target: ID of the destination vertex, required.
- direction: Direction in which the starting vertex expands (OUT, IN, BOTH). Optional, default is BOTH.
- label: Edge type. Optional, default represents all edge labels.
- max_depth: Number of steps, required.
- max_degree: Maximum number of adjacent edges to traverse for each vertex during the query process. Optional, default is 10000.
- capacity: Maximum number of vertices to be visited during the traversal process. Optional, default is 10000000.
- limit: Maximum number of paths to be returned. Optional, default is 10.

##### 3.2.13.2 Usage Method

###### Method & Url

```
GET http://localhost:8080/graphs/{graph}/traversers/paths?source="1:marko"&target="1:josh"&max_depth=5
```

###### Response Status

```json
200
```

###### Response Body

```json
{
    "paths":[
        {
            "objects":[
                "1:marko",
                "1:josh"
            ]
        },
        {
            "objects":[
                "1:marko",
                "2:lop",
                "1:josh"
            ]
        }
    ]
}
```

##### 3.2.13.3 Use Cases

Used to find all paths between two vertices, for example:

- In a social network, finding all possible relationship paths between two users.
- In a device association network, finding all associated paths between two devices.

#### 3.2.14 Paths (POST, Advanced Version)

##### 3.2.14.1 Function Introduction

Finds all paths based on conditions such as the starting vertex, destination vertex, steps (step), and maximum depth.

###### Params

- sources: Defines the starting vertices, required. The specification methods include:
	- ids: Provide the starting vertices through a list of vertex IDs.
	- label and properties: If no IDs are specified, use the label and properties as combined conditions to query the starting vertices.
		- label: Vertex type.
		- properties: Query the starting vertices based on the values of their properties.
		> Note: The property values in properties can be a list, indicating that any value corresponding to the key is acceptable.
- targets: Defines the destination vertices, required. The specification methods include:
	- ids: Provide the destination vertices through a list of vertex IDs.
	- label and properties: If no IDs are specified, use the label and properties as combined conditions to query the destination vertices.
		- label: Vertex type.
		- properties: Query the destination vertices based on the values of their properties.
		> Note: The property values in properties can be a list, indicating that any value corresponding to the key is acceptable.
- step: Represents the path from the starting vertex to the destination vertex, required. The structure of Step is as follows:
	- direction: Represents the direction of edges (OUT, IN, BOTH). The default is BOTH.
	- labels: List of edge types.
	- properties: Filters edges based on property values.
	- max_degree: Maximum number of adjacent edges to traverse for each vertex during the query process. Default is 10000. (Note: Prior to version 0.12, step only supported degree as a parameter name. Starting from version 0.12, max_degree is used uniformly and degree writing is backward compatible.)
	- skip_degree: Used to set the minimum number of edges to be discarded for super vertices during the query process. When the number of adjacent edges for a vertex is greater than skip_degree, the vertex is completely discarded. Optional, if enabled, it must satisfy the constraint `skip_degree >= max_degree`. Default is 0 (not enabled), which means no points are skipped. (Note: When this configuration is enabled, the traversal will attempt to visit skip_degree edges of a vertex, not just max_degree edges. This incurs additional traversal overhead and may have a significant impact on query performance. Please make sure to understand before enabling it.)
- max_depth: Number of steps, required.
- nearest: When nearest is true, it means the shortest path length from the starting vertex to the result vertex is depth, and there is no shorter path. When nearest is false, it means there is a path of length depth from the starting vertex to the result vertex (not necessarily the shortest path and can have cycles). Optional, default is true.
- capacity: Maximum number of vertices to be visited during the traversal process. Optional, default is 10000000.
- limit: Maximum number of paths to be returned. Optional, default is 10.
- with_vertex: When true, the results include complete vertex information (all vertices in the path). When false, only the vertex IDs are returned. Optional, default is false.

##### 3.2.14.2 Usage Method

###### Method & Url

```
POST http://localhost:8080/graphs/{graph}/traversers/paths
```

###### Request Body

```json
{
"sources": {
  "ids": ["1:marko"]
},
"targets": {
  "ids": ["1:peter"]
},
"step": {
"direction": "BOTH",
  "properties": {
    "weight": "P.gt(0.01)"
  }
},
"max_depth": 10,
"capacity": 100000000,
"limit": 10000000,
"with_vertex": false
}
```

###### Response Status

```json
200
```

###### Response Body

```json
{
    "paths": [
        {
            "objects": [
                "1:marko",
                "1:josh",
                "2:lop",
                "1:peter"
            ]
        },
        {
            "objects": [
                "1:marko",
                "2:lop",
                "1:peter"
            ]
        }
    ]
}

```

##### 3.2.14.3 Use Cases

Used to find all paths between two vertices, for example:

- In a social network, finding all possible relationship paths between two users.
- In a device association network, finding all associated paths between two devices.

#### 3.2.15 Customized Paths

##### 3.2.15.1 Function Introduction

Finds all paths that meet the specified conditions based on a batch of starting vertices, edge rules (including direction, edge types, and property filters), and maximum depth.

###### Params

- sources: Defines the starting vertices, required. The specification methods include:
	- ids: Provide the starting vertices through a list of vertex IDs.
	- label and properties: If no IDs are specified, use the label and properties as combined conditions to query the starting vertices.
		- label: Vertex type.
		- properties: Query the starting vertices based on the values of their properties.
		> Note: The property values in properties can be a list, indicating that any value corresponding to the key is acceptable.
- steps: Represents the path rules traversed from the starting vertices and is a list of Steps. Required. The structure of each Step is as follows:
	- direction: Represents the direction of edges (OUT, IN, BOTH). The default is BOTH.
	- labels: List of edge types.
	- properties: Filters edges based on property values.
	- weight_by: Calculates the weight of edges based on the specified property. It is effective when sort_by is not NONE and is mutually exclusive with default_weight.
	- default_weight: The default weight to be used when there is no property to calculate the weight of edges. It is effective when sort_by is not NONE and is mutually exclusive with weight_by.
	- max_degree: Maximum number of adjacent edges to traverse for each vertex during the query process. Default is 10000. (Note: Prior to version 0.12, step only supported degree as a parameter name. Starting from version 0.12, max_degree is used uniformly and degree writing is backward compatible.)
	- sample: Used when sampling is needed for the edges that meet the conditions of a specific step. -1 means no sampling, and the default is to sample 100 edges.
- sort_by: Sorts the paths based on their weights. Optional, default is NONE:
	- NONE: No sorting, default value.
	- INCR: Sorts in ascending order based on path weights.
	- DECR: Sorts in descending order based on path weights.
- capacity: Maximum number of vertices to be visited during the traversal process. Optional, default is 10000000.
- limit: Maximum number of paths to be returned. Optional, default is 10.
- with_vertex: When true, the results include complete vertex information (all vertices in the path). When false, only the vertex IDs are returned. Optional, default is false.

##### 3.2.15.2 Usage Method

###### Method & Url

```
POST http://localhost:8080/graphs/{graph}/traversers/customizedpaths
```

###### Request Body

```json
{
    "sources":{
        "ids":[

        ],
        "label":"person",
        "properties":{
            "name":"marko"
        }
    },
    "steps":[
        {
            "direction":"OUT",
            "labels":[
                "knows"
            ],
            "weight_by":"weight",
            "max_degree":-1
        },
        {
            "direction":"OUT",
            "labels":[
                "created"
            ],
            "default_weight":8,
            "max_degree":-1,
            "sample":1
        }
    ],
    "sort_by":"INCR",
    "with_vertex":true,
    "capacity":-1,
    "limit":-1
}
```

###### Response Status

```json
200
```

###### Response Body

```json
{
    "paths":[
        {
            "objects":[
                "1:marko",
                "1:josh",
                "2:lop"
            ],
            "weights":[
                1,
                8
            ]
        }
    ],
    "vertices":[
        {
            "id":"1:marko",
            "label":"person",
            "type":"vertex",
            "properties":{
                "city":[
                    {
                        "id":"1:marko>city",
                        "value":"Beijing"
                    }
                ],
                "name":[
                    {
                        "id":"1:marko>name",
                        "value":"marko"
                    }
                ],
                "age":[
                    {
                        "id":"1:marko>age",
                        "value":29
                    }
                ]
            }
        },
        {
            "id":"1:josh",
            "label":"person",
            "type":"vertex",
            "properties":{
                "city":[
                    {
                        "id":"1:josh>city",
                        "value":"Beijing"
                    }
                ],
                "name":[
                    {
                        "id":"1:josh>name",
                        "value":"josh"
                    }
                ],
                "age":[
                    {
                        "id":"1:josh>age",
                        "value":32
                    }
                ]
            }
        },
        {
            "id":"2:lop",
            "label":"software",
            "type":"vertex",
            "properties":{
                "price":[
                    {
                        "id":"2:lop>price",
                        "value":328
                    }
                ],
                "name":[
                    {
                        "id":"2:lop>name",
                        "value":"lop"
                    }
                ],
                "lang":[
                    {
                        "id":"2:lop>lang",
                        "value":"java"
                    }
                ]
            }
        }
    ]
}
```

##### 3.2.15.3 Use Cases

Suitable for finding various complex sets of paths, for example:

- In a social network, finding the paths from users who have watched movies directed by Zhang Yimou to the influencers they follow (Zhang Yimou ---> Movie ---> User ---> Influencer).
- In a risk control network, finding the paths from multiple high-risk users to the friends of their direct relatives (High-risk user ---> Direct relative ---> Friend).

#### 3.2.16 Template Paths

##### 3.2.16.1 Function Introduction

Finds all paths that meet the specified conditions based on a batch of starting vertices, edge rules (including direction, edge types, and property filters), and maximum depth.

###### Params

- sources: Defines the starting vertices, required. The specification methods include:
	- ids: Provide the starting vertices through a list of vertex IDs.
	- label and properties: If no IDs are specified, use the label and properties as combined conditions to query the starting vertices.
		- label: Vertex type.
		- properties: Query the starting vertices based on the values of their properties.
		> Note: The property values in properties can be a list, indicating that any value corresponding to the key is acceptable.
- targets: Defines the ending vertices, required. The specification methods include:
	- ids: Provide the ending vertices through a list of vertex IDs.
	- label and properties: If no IDs are specified, use the label and properties as combined conditions to query the ending vertices.
		- label: Vertex type.
		- properties: Query the ending vertices based on the values of their properties.
		> Note: The property values in properties can be a list, indicating that any value corresponding to the key is acceptable.
- steps: Represents the path rules traversed from the starting vertices and is a list of Steps. Required. The structure of each Step is as follows:
	- direction: Represents the direction of edges (OUT, IN, BOTH). The default is BOTH.
	- labels: List of edge types.
	- properties: Filters edges based on property values.
	- max_times: The number of times the current step can be repeated. When set to N, it means the starting vertices can pass through the current step 1-N times.
	- max_degree: Maximum number of adjacent edges to traverse for each vertex during the query process. Default is 10000. (Note: Prior to version 0.12, step only supported degree as a parameter name. Starting from version 0.12, max_degree is used uniformly and degree writing is backward compatible.)
	- skip_degree: Used to set the minimum number of edges to discard super vertices during the query process. When the number of adjacent edges of a vertex is greater than skip_degree, the vertex is completely discarded. Optional. If enabled, it must satisfy the `skip_degree >= max_degree` constraint. Default is 0 (not enabled), which means no points are skipped. (Note: After enabling this configuration, traversing will attempt to access a vertex's skip_degree edges, not just max_degree edges. This incurs additional traversal overhead and may have a significant impact on query performance. Please ensure understanding before enabling.)
- with_ring: Boolean value, true to include cycles; false to exclude cycles. Default is false.
- capacity: Maximum number of vertices to be visited during the traversal process. Optional, default is 10000000.
- limit: Maximum number of paths to be returned. Optional, default is 10.
- with_vertex: When true, the results include complete vertex information (all vertices in the path). When false, only the vertex IDs are returned. Optional, default is

 false.

##### 3.2.16.2 Usage Method

###### Method & Url

```
POST http://localhost:8080/graphs/{graph}/traversers/templatepaths
```

###### Request Body

```json
{
  "sources": {
    "ids": [],
    "label": "person",
    "properties": {
      "name": "vadas"
    }
  },
  "targets": {
    "ids": [],
    "label": "software",
    "properties": {
      "name": "ripple"
    }
  },
  "steps": [
    {
      "direction": "IN",
      "labels": ["knows"],
      "properties": {
      },
      "max_degree": 10000,
      "skip_degree": 100000
    },
    {
      "direction": "OUT",
      "labels": ["created"],
      "properties": {
      },
      "max_degree": 10000,
      "skip_degree": 100000
    },
    {
      "direction": "IN",
      "labels": ["created"],
      "properties": {
      },
      "max_degree": 10000,
      "skip_degree": 100000
    },
    {
      "direction": "OUT",
      "labels": ["created"],
      "properties": {
      },
      "max_degree": 10000,
      "skip_degree": 100000
    }
  ],
  "capacity": 10000,
  "limit": 10,
  "with_vertex": true
}
```

###### Response Status

```json
200
```

###### Response Body

```json
{
    "paths": [
        {
            "objects": [
                "1:vadas",
                "1:marko",
                "2:lop",
                "1:josh",
                "2:ripple"
            ]
        }
    ],
    "vertices": [
        {
            "id": "2:ripple",
            "label": "software",
            "type": "vertex",
            "properties": {
                "name": "ripple",
                "lang": "java",
                "price": 199
            }
        },
        {
            "id": "1:marko",
            "label": "person",
            "type": "vertex",
            "properties": {
                "name": "marko",
                "age": 29,
                "city": "Beijing"
            }
        },
        {
            "id": "1:josh",
            "label": "person",
            "type": "vertex",
            "properties": {
                "name": "josh",
                "age": 32,
                "city": "Beijing"
            }
        },
        {
            "id": "1:vadas",
            "label": "person",
            "type": "vertex",
            "properties": {
                "name": "vadas",
                "age": 27,
                "city": "Hongkong"
            }
        },
        {
            "id": "2:lop",
            "label": "software",
            "type": "vertex",
            "properties": {
                "name": "lop",
                "lang": "java",
                "price": 328
            }
        }
    ]
}

```

##### 3.2.16.3 Use Cases

Suitable for finding various complex template paths, such as personA -(Friend)-> personB -(Classmate)-> personC, where the "Friend" and "Classmate" edges can have a maximum depth of 3 and 4 layers, respectively.

#### 3.2.17 Crosspoints

##### 3.2.17.1 Function Introduction

Finds the intersection points based on the specified conditions, including starting vertices, destination vertices, direction, edge types (optional), and maximum depth.

###### Params

- source: ID of the starting vertex, required.
- target: ID of the destination vertex, required.
- direction: The direction from the starting vertex to the destination vertex. The reverse direction is used from the destination vertex to the starting vertex. When set to BOTH, the direction is not considered (OUT, IN, BOTH). Optional, default is BOTH.
- label: Edge type, optional. Default represents all edge labels.
- max_depth: Number of steps, required.
- max_degree: Maximum number of adjacent edges to traverse for each vertex during the query process. Optional, default is 10000.
- capacity: Maximum number of vertices to be visited during the traversal process. Optional, default is 10000000.
- limit: Maximum number of intersection points to be returned. Optional, default is 10.

##### 3.2.17.2 Usage Method

###### Method & Url

```
GET http://localhost:8080/graphs/{graph}/traversers/crosspoints?source="2:lop"&target="2:ripple"&max_depth=5&direction=IN
```

###### Response Status

```json
200
```

###### Response Body

```json
{
    "crosspoints":[
        {
            "crosspoint":"1:josh",
            "objects":[
                "2:lop",
                "1:josh",
                "2:ripple"
            ]
        }
    ]
}
```

##### 3.2.17.3 Use Cases

Used to find the intersection points and their paths between two vertices, such as:

- In a social network, finding the topics or influencers that two users have in common.
- In a family relationship, finding common ancestors.

#### 3.2.18 Customized Crosspoints

##### 3.2.18.1 Function Introduction

Finds the intersection of destination vertices that satisfy the specified conditions, including starting vertices, multiple edge rules (including direction, edge type, and property filters), and maximum depth.

###### Params

- sources: Defines the starting vertices, required. The specified options include:
	- ids: Provides a list of vertex IDs as starting vertices.
	- label and properties: If no IDs are specified, uses the combined conditions of label and properties to query the starting vertices.
		- label: Type of the vertex.
		- properties: Queries the starting vertices based on property values.
		> Note: Property values in properties can be a list, indicating that the value of the key can be any item in the list.

- path_patterns: Represents the path rules to be followed from the starting vertices. It is a list of rules. Required. Each rule is a PathPattern.
	- Each PathPattern consists of a list of steps, where each step has the following structure:
		- direction: Indicates the direction of the edge (OUT, IN, BOTH). Default is BOTH.
		- labels: List of edge types.
		- properties: Filters the edges based on property values.
		- max_degree: Maximum number of adjacent edges to traverse for each vertex during the query process. Default is 10000.
		- skip_degree: Sets the minimum number of edges to discard super vertices during the query process. If the number of adjacent edges for a vertex is greater than skip_degree, the vertex is completely discarded. Optional. If enabled, it must satisfy the constraint `skip_degree >= max_degree`. Default is 0 (not enabled), which means no vertices are skipped. Note: When this configuration is enabled, the traversal process will attempt to visit skip_degree edges of a vertex, not just max_degree edges. This incurs additional traversal overhead and may significantly impact query performance. Please make sure you understand it before enabling.

- capacity: Maximum number of vertices to be visited during the traversal process. Optional. Default is 10000000.
- limit: Maximum number of paths to be returned. Optional. Default is 10.
- with_path: When set to true, returns the paths where the intersection points are located. When set to false, does not return the paths. Optional. Default is false.
- with_vertex: Optional. Default is false.
	- When set to true, the result includes complete vertex information (all vertices in the paths):
		- When with_path is true, it returns complete information of all vertices in the paths.
		- When with_path is false, it returns complete information of all intersection points.
	- When set to false, only the vertex IDs are returned.

##### 3.2.18.2 Usage Method

###### Method & Url

```
POST http://localhost:8080/graphs/{graph}/traversers/customizedcrosspoints
```

###### Request Body

```json
{
    "sources":{
        "ids":[
            "2:lop",
            "2:ripple"
        ]
    },
    "path_patterns":[
        {
            "steps":[
                {
                    "direction":"IN",
                    "labels":[
                        "created"
                    ],
                    "max_degree":-1
                }
            ]
        }
    ],
    "with_path":true,
    "with_vertex":true,
    "capacity":-1,
    "limit":-1
}
```

###### Response Status

```json
200
```

###### Response Body

```json
{
    "crosspoints":[
        "1:josh"
    ],
    "paths":[
        {
            "objects":[
                "2:ripple",
                "1:josh"
            ]
        },
        {
            "objects":[
                "2:lop",
                "1:josh"
            ]
        }
    ],
    "vertices":[
        {
            "id":"2:ripple",
            "label":"software",
            "type":"vertex",
            "properties":{
                "price":[
                    {
                        "id":"2:ripple>price",
                        "value":199
                    }
                ],
                "name":[
                    {
                        "id":"2:ripple>name",
                        "value":"ripple"
                    }
                ],
                "lang":[
                    {
                        "id":"2:ripple>lang",
                        "value":"java"
                    }
                ]
            }
        },
        {
            "id":"1:josh",
            "label":"person",
            "type":"vertex",
            "properties":{
                "city":[
                    {
                        "id":"1:josh>city",
                        "value":"Beijing"
                    }
                ],
                "name":[
                    {
                        "id":"1:josh>name",
                        "value":"josh"
                    }
                ],
                "age":[
                    {
                        "id":"1:josh>age",
                        "value":32
                    }
                ]
            }
        },
        {
            "id":"2:lop",
            "label":"software",
            "type":"vertex",
            "properties":{
                "price":[
                    {
                        "id":"2:lop>price",
                        "value":328
                    }
                ],
                "name":[
                    {
                        "id":"2:lop>name",
                        "value":"lop"
                    }
                ],
                "lang":[
                    {
                        "id":"2:lop>lang",
                        "value":"java"
                    }
                ]
            }
        }
    ]
}
```

##### 3.2.18.3 Use Cases

Used to query a group of vertices that have intersections at the destination through multiple paths. For example:

- In a product knowledge graph, multiple models of smartphones, learning devices, and gaming devices belong to the top-level category of electronic devices through different lower-level category paths.

#### 3.2.19 Rings

##### 3.2.19.1 Function Introduction

Finds reachable cycles based on the specified conditions, including starting vertices, direction, edge types (optional), and maximum depth.

For example: 1 -> 25 -> 775 -> 14690 -> 25, where the cycle is 25 -> 775 -> 14690 -> 25.

###### Params

- source: Starting vertex ID, required.
- direction: Direction of edges emitted from the starting vertex (OUT, IN, BOTH). Optional. Default is BOTH.
- label: Edge type. Optional. Default represents all edge labels.
- max_depth: Number of steps. Required.
- source_in_ring: Whether the starting point is included in the cycle. Optional. Default is true.
- max_degree: Maximum number of adjacent edges to traverse for each vertex during the query process. Optional. Default is 10000.
- capacity: Maximum number of vertices to be visited during the traversal process. Optional. Default is 10000000.
- limit: Maximum number of reachable cycles to be returned. Optional. Default is 10.

##### 3.2.19.2 Usage Method

###### Method & Url

```
GET http://localhost:8080/graphs/{graph}/traversers/rings?source="1:marko"&max_depth=2
```

###### Response Status

```json
200
```

###### Response Body

```json
{
    "rings":[
        {
            "objects":[
                "1:marko",
                "1:josh",
                "1:marko"
            ]
        },
        {
            "objects":[
                "1:marko",
                "1:vadas",
                "1:marko"
            ]
        },
        {
            "objects":[
                "1:marko",
                "2:lop",
                "1:marko"
            ]
        }
    ]
}
```

##### 3.2.19.3 Use Cases

Used to query cycles reachable from the starting vertex, for example:

- In a risk control project, querying individuals or devices involved in a circular guarantee that a user is connected to.
- In a device network, discovering devices that have circular references around a specific device.

#### 3.2.20 Rays

##### 3.2.20.1 Function Introduction

Finds paths that diverge from the starting vertex and reach boundary vertices based on the specified conditions, including starting vertices, direction, edge types (optional), and maximum depth.

For example: 1 -> 25 -> 775 -> 14690 -> 2289 -> 18379, where 18379 is the boundary vertex, meaning there are no edges emitted from 18379.

###### Params

- source: Starting vertex ID, required.
- direction: Direction of edges emitted from the starting vertex (OUT, IN, BOTH). Optional. Default is BOTH.
- label: Edge type. Optional. Default represents all edge labels.
- max_depth: Number of steps. Required.
- max_degree: Maximum number of adjacent edges to traverse for each vertex during the query process. Optional. Default is 10000.
- capacity: Maximum number of vertices to be visited during the traversal process. Optional. Default is 10000000.
- limit: Maximum number of non-cycle paths to be returned. Optional. Default is 10.

##### 3.2.20.2 Usage Method

###### Method & Url

```
GET http://localhost:8080/graphs/{graph}/traversers/rays?source="1:marko"&max_depth=2&direction=OUT
```

###### Response Status

```json
200
```

###### Response Body

```json
{
    "rays":[
        {
            "objects":[
                "1:marko",
                "1:vadas"
            ]
        },
        {
            "objects":[
                "1:marko",
                "2:lop"
            ]
        },
        {
            "objects":[
                "1:marko",
                "1:josh",
                "2:ripple"
            ]
        },
        {
            "objects":[
                "1:marko",
                "1:josh",
                "2:lop"
            ]
        }
    ]
}
```

##### 3.2.20.3 Use Cases

Used to find paths from the starting vertex to boundary vertices based on a specific relationship, for example:

- In a family relationship, finding paths from a person to all descendants who do not have children.
- In a device network, discovering paths from a specific device to terminal devices.

#### 3.2.21 Fusiform Similarity

##### 3.2.21.1 Function Introduction

Queries a batch of "fusiform similar vertices" based on specified conditions. When two vertices share a certain relationship with many common vertices, they are considered "fusiform similar vertices." For example, if "Reader A" has read 100 books, readers who have read 80 or more of these 100 books can be defined as "fusiform similar vertices" of "Reader A."

###### Params

- sources: Starting vertices, required. Specify using:
	- ids: Provide a list of vertex IDs as starting vertices.
	- label and properties: If ids are not specified, use the combined conditions of label and properties to query the starting vertices.
		- label: Vertex type.
		- properties: Query the starting vertices based on the values of their properties.
		> Note: Property values in properties can be a list, indicating that the value of the key can be any value in the list.

- label: Edge type. Optional. Default represents all edge labels.
- direction: Direction in which the starting vertex diverges (OUT, IN, BOTH). Optional. Default is BOTH.
- min_neighbors: Minimum number of neighbors. If the number of neighbors is less than this threshold, the starting vertex is not considered a "fusiform similar vertex." For example, if you want to find "fusiform similar vertices" of books read by "Reader A," and min_neighbors is set to 100, it means that "Reader A" must have read at least 100 books to have "fusiform similar vertices." Required.
- alpha: Similarity, representing the proportion of common neighbors between the starting vertex and "fusiform similar vertices" to all neighbors of the starting vertex. Required.
- min_similars: Minimum number of "fusiform similar vertices." Only when the number of "fusiform similar vertices" of the starting vertex is greater than or equal to this value, the starting vertex and its "fusiform similar vertices" will be returned. Optional. Default is 1.
- top: Returns the top highest similarity "fusiform similar vertices" of a starting vertex. Required. 0 means all.
- group_property: Used together with min_groups. Returns the starting vertex and its "fusiform similar vertices" only if there are at least min_groups different values for a certain attribute of the starting vertex and its "fusiform similar vertices." For example, when recommending "out-of-town" book buddies for "Reader A," set group_property to the "city" attribute of readers and min_group to at least 2. Optional. If not specified, no filtering based on attributes is needed.
- min_groups: Used together with group_property. Only meaningful when group_property is set.
- max_degree: Maximum number of adjacent edges to traverse for each vertex during the query process. Optional. Default is 10000.
- capacity: Maximum number of vertices to be visited during the traversal process. Optional. Default is 10000000.
- limit: Maximum number of results to be returned (one starting vertex and its "fusiform similar vertices" count as one result). Optional. Default is 10.
- with_intermediary: Whether to return the starting vertex and the intermediate vertices that are commonly related to the "fusiform

 similar vertices." Default is false.
- with_vertex: Optional. Default is false.
	- true: Returns complete vertex information in the results.
	- false: Only returns vertex IDs.

##### 3.2.21.2 Usage Method

###### Method & Url

```
POST http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/traversers/fusiformsimilarity
```

###### Request Body

```json
{
    "sources":{
        "ids":[],
        "label": "person",
        "properties": {
            "name":"p1"
        }
    },
    "label":"read",
    "direction":"OUT",
    "min_neighbors":8,
    "alpha":0.75,
    "min_similars":1,
    "top":0,
    "group_property":"city",
    "min_group":2,
    "max_degree": 10000,
    "capacity": -1,
    "limit": -1,
    "with_intermediary": false,
    "with_vertex":true
}

```

###### Response Status

```json
200
```

###### Response Body

```json
{
    "similars": {
        "3:p1": [
            {
                "id": "3:p2",
                "score": 0.8888888888888888,
                "intermediaries": [
                ]
            },
            {
                "id": "3:p3",
                "score": 0.7777777777777778,
                "intermediaries": [
                ]
            }
        ]
    },
    "vertices": [
        {
            "id": "3:p1",
            "label": "person",
            "type": "vertex",
            "properties": {
                "name": "p1",
                "city": "Beijing"
            }
        },
        {
            "id": "3:p2",
            "label": "person",
            "type": "vertex",
            "properties": {
                "name": "p2",
                "city": "Shanghai"
            }
        },
        {
            "id": "3:p3",
            "label": "person",
            "type": "vertex",
            "properties": {
                "name": "p3",
                "city": "Beijing"
            }
        }
    ]
}
```

##### 3.2.21.3 Use Cases

Used to query vertices that have high similarity with a group of vertices. For example:

- Readers with similar book lists to a specific reader.
- Players who play similar games to a specific player.

#### 3.2.22 Vertices

##### 3.2.22.1 Batch Query Vertices by Vertex IDs

###### Params

- ids: List of vertex IDs to be queried.

###### Method & Url

```
GET http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/traversers/vertices?ids="1:marko"&ids="2:lop"
```

###### Response Status

```json
200
```

###### Response Body

```json
{
    "vertices":[
        {
            "id":"1:marko",
            "label":"person",
            "type":"vertex",
            "properties":{
                "city":[
                    {
                        "id":"1:marko>city",
                        "value":"Beijing"
                    }
                ],
                "name":[
                    {
                        "id":"1:marko>name",
                        "value":"marko"
                    }
                ],
                "age":[
                    {
                        "id":"1:marko>age",
                        "value":29
                    }
                ]
            }
        },
        {
            "id":"2:lop",
            "label":"software",
            "type":"vertex",
            "properties":{
                "price":[
                    {
                        "id":"2:lop>price",
                        "value":328
                    }
                ],
                "name":[
                    {
                        "id":"2:lop>name",
                        "value":"lop"
                    }
                ],
                "lang":[
                    {
                        "id":"2:lop>lang",
                        "value":"java"
                    }
                ]
            }
        }
    ]
}
```

##### 3.2.22.2 Get Vertex Shard Information

Obtain vertex shard information by specifying the shard size `split_size` (can be used in conjunction with Scan in 3.2.21.3 to retrieve vertices).

###### Params

- split_size: Shard size, required.

###### Method & Url

```
GET http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/traversers/vertices/shards?split_size=67108864
```

###### Response Status

```json
200
```

###### Response Body

```json
{
    "shards":[
        {
            "start": "0",
            "end": "2165893",
            "length": 0
        },
        {
            "start": "2165893",
            "end": "4331786",
            "length": 0
        },
        {
            "start": "4331786",
            "end": "6497679",
            "length": 0
        },
        {
            "start": "6497679",
            "end": "8663572",
            "length": 0
        },
        ......
    ]
}
```

##### 3.2.22.3 Batch Retrieve Vertices Based on Shard Information

Retrieve vertices in batches based on the specified shard information (refer to 3.2.21.2 Shard for obtaining shard information).

###### Params

- start: Shard start position, required.
- end: Shard end position, required.
- page: Page position for pagination, optional. Default is null, no pagination. When page is "", it represents the first page of pagination starting from the position indicated by start.
- page_limit: The upper limit of the number of vertices per page when retrieving vertices with pagination, optional. Default is 100000.

###### Method & Url

```
GET http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/traversers/vertices/scan?start=0&end=4294967295
```

###### Response Status

```json
200
```

###### Response Body

```json
{
    "vertices":[
        {
            "id":"2:ripple",
            "label":"software",
            "type":"vertex",
            "properties":{
                "price":[
                    {
                        "id":"2:ripple>price",
                        "value":199
                    }
                ],
                "name":[
                    {
                        "id":"2:ripple>name",
                        "value":"ripple"
                    }
                ],
                "lang":[
                    {
                        "id":"2:ripple>lang",
                        "value":"java"
                    }
                ]
            }
        },
        {
            "id":"1:vadas",
            "label":"person",
            "type":"vertex",
            "properties":{
                "city":[
                    {
                        "id":"1:vadas>city",
                        "value":"Hongkong"
                    }
                ],
                "name":[
                    {
                        "id":"1:vadas>name",
                        "value":"vadas"
                    }
                ],
                "age":[
                    {
                        "id":"1:vadas>age",
                        "value":27
                    }
                ]
            }
        },
        {
            "id":"1:peter",
            "label":"person",
            "type":"vertex",
            "properties":{
                "city":[
                    {
                        "id":"1:peter>city",
                        "value":"Shanghai"
                    }
                ],
                "name":[
                    {
                        "id":"1:peter>name",
                        "value":"peter"
                    }
                ],
                "age":[
                    {
                        "id":"1:peter>age",
                        "value":35
                    }
                ]
            }
        },
        {
            "id":"1:josh",
            "label":"person",
            "type":"vertex",
            "properties":{
                "city":[
                    {
                        "id":"1:josh>city",
                        "value":"Beijing"
                    }
                ],
                "name":[
                    {
                        "id":"1:josh>name",
                        "value":"josh"
                    }
                ],
                "age":[
                    {
                        "id":"1:josh>age",
                        "value":32
                    }
                ]
            }
        },
        {
            "id":"1:marko",
            "label":"person",
            "type":"vertex",
            "properties":{
                "city":[
                    {
                        "id":"1:marko>city",
                        "value":"Beijing"
                    }
                ],
                "name":[
                    {
                        "id":"1:marko>name",
                        "value":"marko"
                    }
                ],
                "age":[
                    {
                        "id":"1:marko>age",
                        "value":29
                    }
                ]
            }
        },
        {
            "id":"2:lop",
            "label":"software",
            "type":"vertex",
            "properties":{
                "price":[
                    {
                        "id":"2:lop>price",
                        "value":328
                    }
                ],
                "name":[
                    {
                        "id":"2:lop>name",
                        "value":"lop"
                    }
                ],
                "lang":[
                    {
                        "id":"2:lop>lang",
                        "value":"java"
                    }
                ]
            }
        }
    ]
}
```

##### 3.2.22.4 Use Cases

- Querying vertices by ID list, which can be used for batch vertex queries. For example, after querying multiple paths in a path search, you can further query all vertex properties of a specific path.
- Retrieving shards and querying vertices by shard, which can be used to traverse all vertices.

#### 3.2.23 Edges

##### 3.2.23.1 Batch Retrieve Edges Based on Edge IDs

###### Params

- ids: List of edge IDs to be queried.

###### Method & Url

```
GET http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/traversers/edges?ids="S1:josh>1>>S2:lop"&ids="S1:josh>1>>S2:ripple"
```

###### Response Status

```json
200
```

###### Response Body

```json
{
    "edges": [
        {
            "id": "S1:josh>1>>S2:lop",
            "label": "created",
            "type": "edge",
            "inVLabel": "software",
            "outVLabel": "person",
            "inV": "2:lop",
            "outV": "1:josh",
            "properties": {
                "date": "20091111",
                "weight": 0.4
            }
        },
        {
            "id": "S1:josh>1>>S2:ripple",
            "label": "created",
            "type": "edge",
            "inVLabel": "software",
            "outVLabel": "person",
            "inV": "2:ripple",
            "outV": "1:josh",
            "properties": {
                "date": "20171210",
                "weight": 1
            }
        }
    ]
}
```

##### 3.2.23.2 Retrieve Edge Shard Information

Retrieve shard information for edges by specifying the shard size (`split_size`). This can be used in conjunction with the Scan operation described in section 3.2.22.3 to retrieve edges.

###### Params

- split_size: Shard size, required field.

###### Method & Url

```
GET http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/traversers/edges/shards?split_size=4294967295
```

###### Response Status

```json
200
```

###### Response Body

```json
{
    "shards":[
        {
            "start": "0",
            "end": "1073741823",
            "length": 0
        },
        {
            "start": "1073741823",
            "end": "2147483646",
            "length": 0
        },
        {
            "start": "2147483646",
            "end": "3221225469",
            "length": 0
        },
        {
            "start": "3221225469",
            "end": "4294967292",
            "length": 0
        },
        {
            "start": "4294967292",
            "end": "4294967295",
            "length": 0
        }
    ]
}
```

##### 3.2.23.3 Batch Retrieve Edges Based on Shard Information

Batch retrieve edges by specifying shard information (refer to section 3.2.22.2 for shard retrieval).

###### Params

- start: Shard starting position, required field.
- end: Shard ending position, required field.
- page: Page position for pagination, optional field. Default is null, which means no pagination. When `page` is empty, it indicates the first page of pagination starting from the position indicated by `start`.
- page_limit: Upper limit of the number of edges per page for paginated retrieval, optional field. Default is 100000.

###### Method & Url

```
GET http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/traversers/edges/scan?start=0&end=3221225469
```

###### Response Status

```json
200
```

###### Response Body

```json
{
    "edges":[
        {
            "id":"S1:peter>2>>S2:lop",
            "label":"created",
            "type":"edge",
            "inVLabel":"software",
            "outVLabel":"person",
            "inV":"2:lop",
            "outV":"1:peter",
            "properties":{
                "weight":0.2,
                "date":"20170324"
            }
        },
        {
            "id":"S1:josh>2>>S2:lop",
            "label":"created",
            "type":"edge",
            "inVLabel":"software",
            "outVLabel":"person",
            "inV":"2:lop",
            "outV":"1:josh",
            "properties":{
                "weight":0.4,
                "date":"20091111"
            }
        },
        {
            "id":"S1:josh>2>>S2:ripple",
            "label":"created",
            "type":"edge",
            "inVLabel":"software",
            "outVLabel":"person",
            "inV":"2:ripple",
            "outV":"1:josh",
            "properties":{
                "weight":1,
                "date":"20171210"
            }
        },
        {
            "id":"S1:marko>1>20130220>S1:josh",
            "label":"knows",
            "type":"edge",
            "inVLabel":"person",
            "outVLabel":"person",
            "inV":"1:josh",
            "outV":"1:marko",
            "properties":{
                "weight":1,
                "date":"20130220"
            }
        },
        {
            "id":"S1:marko>1>20160110>S1:vadas",
            "label":"knows",
            "type":"edge",
            "inVLabel":"person",
            "outVLabel":"person",
            "inV":"1:vadas",
            "outV":"1:marko",
            "properties":{
                "weight":0.5,
                "date":"20160110"
            }
        },
        {
            "id":"S1:marko>2>>S2:lop",
            "label":"created",
            "type":"edge",
            "inVLabel":"software",
            "outVLabel":"person",
            "inV":"2:lop",
            "outV":"1:marko",
            "properties":{
                "weight":0.4,
                "date":"20171210"
            }
        }
    ]
}
```

##### 3.2.23.4 Use Cases

- Querying edges based on ID list, suitable for batch retrieval of edges.
- Retrieving shard information and querying edges based on shards, useful for traversing all edges.
