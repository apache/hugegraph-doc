# Other API

LLMS index: [llms.txt](/versions/1.7/llms.txt)

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
        "core": "1.7.0",
        "gremlin": "3.5.1",
        "api": "0.71.0.0"
    }
}
```
