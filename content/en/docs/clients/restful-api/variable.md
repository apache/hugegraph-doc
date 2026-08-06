---
title: "Variable API"
linkTitle: "Variable"
weight: 11
description: "Variable REST API: Store and manage key-value pairs as global variables for graph-level configuration and state management."
---

### 5.1 Variables

Variables can be used to store data about the entire graph. The data is accessed and stored in the form of key-value pairs.

#### 5.1.1 Creating or Updating a Key-Value Pair

##### Method & Url

```
PUT http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/variables/name
```

##### Request Body

```json
{
  "data": "tom"
}
```

##### Response Status

```json
200
```

##### Response Body

```json
{
    "name": "tom"
}
```

#### 5.1.2 Listing all key-value pairs

##### Method & Url

```
GET http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/variables
```

##### Response Status

```json
200
```

##### Response Body

```json
{
    "name": "tom"
}
```

#### 5.1.3 Listing a specific key-value pair

##### Method & Url

```
GET http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/variables/name
```

##### Response Status

```json
200
```

##### Response Body

```json
{
    "name": "tom"
}
```

#### 5.1.4 Deleting a specific key-value pair

##### Method & Url

```
DELETE http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/variables/name
```

##### Response Status

```json
204
```
