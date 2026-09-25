# Other API

LLMS index: [llms.txt](/versions/1.0/llms.txt)

---

### 10.1 Other

#### 10.1.1 查看HugeGraph的版本信息

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
