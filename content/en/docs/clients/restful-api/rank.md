---
title: "Rank API"
linkTitle: "Rank"
weight: 10
description: "Rank REST API: Execute graph node ranking algorithms such as PageRank and Personalized PageRank for centrality analysis."
---

### 4.1 Rank API overview

Not only the Graph iteration （traverser) method, HugeGraph-Server also provide `Rank API` for recommendation purpose.
You can use it to recommend some vertexes much closer to a vertex.


### 4.2 Details of Rank API

#### 4.2.1 Personal Rank API

A typical scenario for `Personal Rank` algorithm is in recommendation application. According to the out edges of a vertex, 
recommend some other vertices that having the same or similar edges.

Here is a use case:
According to someone's reading habit or reading history, we can recommend some books he may be interested or some book pal.

For Example:
1. Suppose we have a vertex, Person type, and named tom.He like 5 books `a,b,c,d,e`. If we want to recommend some book pal and books for tom, an easier idea is let's check whoever also liked these books (common hobby based).
2. Now, we need someone else, like neo, he like three books `b,d,f`. And Jay, he like 4 books `c,d,e,g`, and Lee, he also like 4 books `a,d,e,f`.
3. For we don't need to recommend books tom already read, the recommend-list should only contain the books Tom's book pal already read but tom haven't read yet. Such as book "f" and "g", and with priority f > g.
4. Now, we recompute Tom's personal rank value, we will get a sorted TopN book pal or book recommend-list. (Choose OTHER_LABEL,for Only Book purpose)


##### 4.2.1.0 Data Preparation

The case above is simple. Here we also provide a public test dataset [MovieLens](https://grouplens.org/datasets/movielens/) for use case.
You should download the dataset. The load it into HugeGraph with HugeGraph-Loader. To make it simple, we ignore all properties data of user and move. only field id is enough. we also ignore the value of edge rating. 

The metadata for input file and mapping file as follows:

```groovy
////////////////////////////////////////////////////////////
// UserID::Gender::Age::Occupation::Zip-code
// MovieID::Title::Genres
// UserID::MovieID::Rating::Timestamp
////////////////////////////////////////////////////////////

// Define schema
schema.propertyKey("id").asInt().ifNotExist().create();
schema.propertyKey("rate").asInt().ifNotExist().create();

schema.vertexLabel("user")
      .properties("id")
      .primaryKeys("id")
      .ifNotExist()
      .create();
schema.vertexLabel("movie")
      .properties("id")
      .primaryKeys("id")
      .ifNotExist()
      .create();

schema.edgeLabel("rating")
      .sourceLabel("user")
      .targetLabel("movie")
      .properties("rate")
      .ifNotExist()
      .create();
```

```json
{
  "vertices": [
    {
      "label": "user",
      "input": {
        "type": "file",
        "path": "users.dat",
        "format": "TEXT",
        "delimiter": "::",
        "header": ["UserID", "Gender", "Age", "Occupation", "Zip-code"]
      },
      "ignored": ["Gender", "Age", "Occupation", "Zip-code"],
      "mapping": {
          "UserID": "id"
      }
    },
    {
      "label": "movie",
      "input": {
        "type": "file",
        "path": "movies.dat",
        "format": "TEXT",
        "delimiter": "::",
        "header": ["MovieID", "Title", "Genres"]
      },
      "ignored": ["Title", "Genres"],
      "mapping": {
          "MovieID": "id"
      }
    }
  ],
  "edges": [
    {
      "label": "rating",
      "source": ["UserID"],
      "target": ["MovieID"],
      "input": {
        "type": "file",
        "path": "ratings.dat",
        "format": "TEXT",
        "delimiter": "::",
        "header": ["UserID", "MovieID", "Rating", "Timestamp"]
      },
      "ignored": ["Timestamp"],
      "mapping": {
          "UserID": "id",
          "MovieID": "id",
          "Rating": "rate"
      }
    }
  ]
}
```

>Note: modify the `input.path` to your local path.

##### 4.2.1.1 Function Introduction

suitable for bipartite graph, will return all vertex or a list of its correlation which related to all source vertex.


> Bipartite Graph is a special model in Graph Theory, as well as a special flow in network. The strongest feature is, it split all vertex in graph into two sets. The vertex in the set is not connected. However,the vertex in two sets may connect with each other.

Suppose we have one bipartite graph based on user and things.
A random walk based PersonalRank algorithm should be likes this:


1. Choose a user u as start vertex, let's set the initial weight to be 1.0 . Go from Vu with probability alpha to a neighbor vertex, and (1-alpha) to stay.
2. If we decide to go outside, we would like to choose an edge, such as `rating`, to find a common judge.
   1. Then choose the neighbors of current vertex randomly with uniform distribution, and reset the weights with uniform distribution.
   2. Compensate the source vertex's weight with (1 - alpha)
   3. Repeat step 2;
3. Convergence after reaching a certain number of steps or precision, then we got a recommend-list.

###### Params

**Required**:
- source: the id of source vertex
- label: edge label go from the source vertex, should connect two different type of vertex

**Optional**:
- alpha: the probability of going out for one vertex in each iteration，similar to the alpha of PageRank,required, value range is (0, 1], default 0.85.
- max_degree: in query process, the max iteration number of adjacency edge for a vertex, default `10000`
- max_depth: iteration number,range [2, 50], default `5`
- with_label：result filter,default `BOTH_LABEL`,optional list as follows:
    - SAME_LABEL：Only keep vertex which has the same type as source vertex
    - OTHER_LABEL：Only keep vertex which has different type as source vertex (the another part in bipartite graph)
    - BOTH_LABEL：Keep both type vertex
- limit: max return vertex number,default `100`
- max_diff: accuracy for convergence, default `0.0001` (*will implement soon*)  
- sorted： whether sort the result by rank or not, true for descending sort, false for none, default `true`

##### 4.2.1.2 Usage

###### Method & Url

```
POST http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/traversers/personalrank
```

###### Request Body

```json
{
    "source": "1:1",
    "label": "rating",
    "alpha": 0.6,
    "max_depth": 15,
    "with_label": "OTHER_LABEL",
    "sorted": true,
    "limit": 10
}
```

###### Response Status

```json
200
```

###### Response Body

```json
{
    "2:2858": 0.0005014026017816927,
    "2:1196": 0.0004336708357653617,
    "2:1210": 0.0004128083140214213,
    "2:593": 0.00038117341069881513,
    "2:480": 0.00037005373269728036,
    "2:1198": 0.000366641614652057,
    "2:2396": 0.0003622362410538888,
    "2:2571": 0.0003593312457300953,
    "2:589": 0.00035922123055598566,
    "2:110": 0.0003466135844390885
}
```

##### 4.2.1.3 Suitable Scenario

In a bipartite graph build by two different type of vertex, recommend other most related vertex to one vertex. for example:
- Reading recommendation: find out the **books** should be recommended to someone first, It is also possible to recommend **book pal**  with the highest common preferences at the same time (just like: WeChat "your friend also read xx " function)
- Social recommendation: find out other **Poster** who interested in same topics, or other **News/Messages** you may be interested with (Such as : "Hot News" function in Weibo)
- Commodity recommendation: according to someone's shopping habit,find out a **commodity list** should recommend first, some online **salesman** may also be good (Such as : "You May Like" function in TaoBao)

#### 4.2.2 Neighbor Rank API

##### 4.2.2.0 Data Preparation

```java
public class Loader {
    public static void main(String[] args) {
        HugeClient client = new HugeClient("http://127.0.0.1:8080", "hugegraph");
        SchemaManager schema = client.schema();

        schema.propertyKey("name").asText().ifNotExist().create();

        schema.vertexLabel("person")
              .properties("name")
              .useCustomizeStringId()
              .ifNotExist()
              .create();

        schema.vertexLabel("movie")
              .properties("name")
              .useCustomizeStringId()
              .ifNotExist()
              .create();

        schema.edgeLabel("follow")
              .sourceLabel("person")
              .targetLabel("person")
              .ifNotExist()
              .create();

        schema.edgeLabel("like")
              .sourceLabel("person")
              .targetLabel("movie")
              .ifNotExist()
              .create();

        schema.edgeLabel("directedBy")
              .sourceLabel("movie")
              .targetLabel("person")
              .ifNotExist()
              .create();

        GraphManager graph = client.graph();

        Vertex O = graph.addVertex(T.label, "person", T.id, "O", "name", "O");

        Vertex A = graph.addVertex(T.label, "person", T.id, "A", "name", "A");
        Vertex B = graph.addVertex(T.label, "person", T.id, "B", "name", "B");
        Vertex C = graph.addVertex(T.label, "person", T.id, "C", "name", "C");
        Vertex D = graph.addVertex(T.label, "person", T.id, "D", "name", "D");

        Vertex E = graph.addVertex(T.label, "movie", T.id, "E", "name", "E");
        Vertex F = graph.addVertex(T.label, "movie", T.id, "F", "name", "F");
        Vertex G = graph.addVertex(T.label, "movie", T.id, "G", "name", "G");
        Vertex H = graph.addVertex(T.label, "movie", T.id, "H", "name", "H");
        Vertex I = graph.addVertex(T.label, "movie", T.id, "I", "name", "I");
        Vertex J = graph.addVertex(T.label, "movie", T.id, "J", "name", "J");

        Vertex K = graph.addVertex(T.label, "person", T.id, "K", "name", "K");
        Vertex L = graph.addVertex(T.label, "person", T.id, "L", "name", "L");
        Vertex M = graph.addVertex(T.label, "person", T.id, "M", "name", "M");

        O.addEdge("follow", A);
        O.addEdge("follow", B);
        O.addEdge("follow", C);
        D.addEdge("follow", O);

        A.addEdge("follow", B);
        A.addEdge("like", E);
        A.addEdge("like", F);

        B.addEdge("like", G);
        B.addEdge("like", H);

        C.addEdge("like", I);
        C.addEdge("like", J);

        E.addEdge("directedBy", K);
        F.addEdge("directedBy", B);
        F.addEdge("directedBy", L);

        G.addEdge("directedBy", M);
    }
}
```

##### 4.2.2.1 Function Introduction

In a general graph structure,find the first N vertices of each layer with the highest correlation with a given starting point and their relevance.

In graph words:  to go out from the starting point, get the probability of going to each vertex of each layer.

###### Params

- source: id of source vertex，required
- alpha：the probability of going out for one vertex in each iteration，similar to the alpha of PageRank,required, value range is (0, 1] 
- steps: a path rule for source vertex visited,it's a list of Step,each Step map to a layout in result,required.The structure of each Step as follows：
	- direction：the direction of edge（OUT, IN, BOTH）, BOTH for default.
	- labels：a list of edge types, will union all edge types
	- max_degree：in query process, the max iteration number of adjacency edge for a vertex, default `10000` 
        (Note: before v0.12 step only support degree as parameter name, from v0.12, use max_degree, compatible with degree)
	- top： retains only the top N results with the highest weight in each layer of the results, default 100, max 1000 
- capacity: the maximum number of vertexes visited during the traversal, optional, default 10000000

##### 4.2.2.2 Usage

###### Method & Url

```
POST http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/traversers/neighborrank
```

###### Request Body

```json
{
    "source":"O",
    "steps":[
        {
            "direction":"OUT",
            "labels":[
                "follow"
            ],
            "max_degree":-1,
            "top":100
        },
        {
            "direction":"OUT",
            "labels":[
                "follow",
                "like"
            ],
            "max_degree":-1,
            "top":100
        },
        {
            "direction":"OUT",
            "labels":[
                "directedBy"
            ],
            "max_degree":-1,
            "top":100
        }
    ],
    "alpha":0.9,
    "capacity":-1
}
```

###### Response Status

```json
200
```

###### Response Body

```json
{
    "ranks": [
        {
            "O": 1
        },
        {
            "B": 0.4305,
            "A": 0.3,
            "C": 0.3
        },
        {
            "G": 0.17550000000000002,
            "H": 0.17550000000000002,
            "I": 0.135,
            "J": 0.135,
            "E": 0.09000000000000001,
            "F": 0.09000000000000001
        },
        {
            "M": 0.15795,
            "K": 0.08100000000000002,
            "L": 0.04050000000000001
        }
    ]
}
```

##### 4.2.2.3 Suitable Scenario

Find the vertices in different layers for a given start point that should be most recommended

- For example, in the four-layered structure of the audience, friends, movies, and directors, according to the movies that a certain audience's friends like, recommend movies for that audience, or recommend directors for those movies based on who made them.