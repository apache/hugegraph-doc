---
title: "Other API"
linkTitle: "Other"
weight: 18
description: "Other（其他接口）REST 接口:提供系统版本查询和 API 版本信息等辅助功能。"
---

### 11.1 Other

#### 11.1.1 查看HugeGraph的版本信息

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
