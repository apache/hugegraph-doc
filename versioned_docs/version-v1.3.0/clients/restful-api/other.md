---
title: "Other API"
linkTitle: "Other"
weight: 18
description: "Other REST API: Provide auxiliary functions such as system version query and API version information."
---

### 11.1 Other

#### 11.1.1 View Version Information of HugeGraph

##### Method & Url

```
GET http://localhost:8080/versions
```

##### Response Status

```json
200
```

##### Response Body

```json
{
    "versions": {
        "version": "v1",
        "core": "0.4.5.1",
        "gremlin": "3.2.5",
        "api": "0.13.2.0"
    }
}
```
