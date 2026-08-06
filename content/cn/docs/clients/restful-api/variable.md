---
title: "Variable API"
linkTitle: "Variable"
weight: 11
description: "Variable（变量）REST 接口:存储和管理键值对形式的全局变量,支持图级别的配置和状态管理。"
---

### 5.1 Variables

Variables 可以用来存储有关整个图的数据，数据按照键值对的方式存取

#### 5.1.1 创建或者更新某个键值对

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

#### 5.1.2 列出全部键值对

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

#### 5.1.3 列出某个键值对

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

#### 5.1.4 删除某个键值对

##### Method & Url

```
DELETE http://localhost:8080/graphspaces/DEFAULT/graphs/hugegraph/variables/name
```

##### Response Status

```json
204
```
