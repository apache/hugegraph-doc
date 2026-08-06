---
title: "Metrics API"
linkTitle: "Metrics"
weight: 17
description: "Metrics REST API: Retrieve runtime performance metrics, statistics, and health status data of the system."
---


HugeGraph provides a metrics interface for obtaining monitoring information, such as statistics on
each Gremlin execution time, cache size, etc. The metrics interface includes the following
categories: basic metrics, statistical metrics, system metrics, and backend storage metrics.

## 1. Basic Metrics

### 1.1 Get All Basic Metrics

##### Params

- type: If the passed value is `json`, it is returned in json format, otherwise it is returned in
  Promethaus format.

##### 1.1.1 Method & Url

```
http://localhost:8080/metrics/?type=json
```

##### Response Status

```json
200
```

##### Response Body

```json
{
  "gauges": {
    "org.apache.hugegraph.backend.cache.Cache.edge-hugegraph.capacity": {
      "value": 1000000
    },
    "org.apache.hugegraph.backend.cache.Cache.edge-hugegraph.expire": {
      "value": 600000
    },
    "org.apache.hugegraph.backend.cache.Cache.edge-hugegraph.hits": {
      "value": 0
    },
    "org.apache.hugegraph.backend.cache.Cache.edge-hugegraph.miss": {
      "value": 0
    },
    "org.apache.hugegraph.backend.cache.Cache.edge-hugegraph.size": {
      "value": 0
    },
    "org.apache.hugegraph.backend.cache.Cache.instances": {
      "value": 7
    },
    "org.apache.hugegraph.backend.cache.Cache.schema-id-hugegraph.capacity": {
      "value": 10000
    },
    "org.apache.hugegraph.backend.cache.Cache.schema-id-hugegraph.expire": {
      "value": 0
    },
    "org.apache.hugegraph.backend.cache.Cache.schema-id-hugegraph.hits": {
      "value": 0
    },
    "org.apache.hugegraph.backend.cache.Cache.schema-id-hugegraph.miss": {
      "value": 0
    },
    "org.apache.hugegraph.backend.cache.Cache.schema-id-hugegraph.size": {
      "value": 17
    },
    "org.apache.hugegraph.backend.cache.Cache.schema-name-hugegraph.capacity": {
      "value": 10000
    },
    "org.apache.hugegraph.backend.cache.Cache.schema-name-hugegraph.expire": {
      "value": 0
    },
    "org.apache.hugegraph.backend.cache.Cache.schema-name-hugegraph.hits": {
      "value": 0
    },
    "org.apache.hugegraph.backend.cache.Cache.schema-name-hugegraph.miss": {
      "value": 0
    },
    "org.apache.hugegraph.backend.cache.Cache.schema-name-hugegraph.size": {
      "value": 17
    },
    "org.apache.hugegraph.backend.cache.Cache.token-hugegraph.capacity": {
      "value": 10240
    },
    "org.apache.hugegraph.backend.cache.Cache.token-hugegraph.expire": {
      "value": 600000
    },
    "org.apache.hugegraph.backend.cache.Cache.token-hugegraph.hits": {
      "value": 0
    },
    "org.apache.hugegraph.backend.cache.Cache.token-hugegraph.miss": {
      "value": 0
    },
    "org.apache.hugegraph.backend.cache.Cache.token-hugegraph.size": {
      "value": 0
    },
    "org.apache.hugegraph.backend.cache.Cache.users-hugegraph.capacity": {
      "value": 10240
    },
    "org.apache.hugegraph.backend.cache.Cache.users-hugegraph.expire": {
      "value": 600000
    },
    "org.apache.hugegraph.backend.cache.Cache.users-hugegraph.hits": {
      "value": 0
    },
    "org.apache.hugegraph.backend.cache.Cache.users-hugegraph.miss": {
      "value": 0
    },
    "org.apache.hugegraph.backend.cache.Cache.users-hugegraph.size": {
      "value": 0
    },
    "org.apache.hugegraph.backend.cache.Cache.users_pwd-hugegraph.capacity": {
      "value": 10240
    },
    "org.apache.hugegraph.backend.cache.Cache.users_pwd-hugegraph.expire": {
      "value": 600000
    },
    "org.apache.hugegraph.backend.cache.Cache.users_pwd-hugegraph.hits": {
      "value": 0
    },
    "org.apache.hugegraph.backend.cache.Cache.users_pwd-hugegraph.miss": {
      "value": 0
    },
    "org.apache.hugegraph.backend.cache.Cache.users_pwd-hugegraph.size": {
      "value": 0
    },
    "org.apache.hugegraph.backend.cache.Cache.vertex-hugegraph.capacity": {
      "value": 10000000
    },
    "org.apache.hugegraph.backend.cache.Cache.vertex-hugegraph.expire": {
      "value": 600000
    },
    "org.apache.hugegraph.backend.cache.Cache.vertex-hugegraph.hits": {
      "value": 0
    },
    "org.apache.hugegraph.backend.cache.Cache.vertex-hugegraph.miss": {
      "value": 0
    },
    "org.apache.hugegraph.backend.cache.Cache.vertex-hugegraph.size": {
      "value": 0
    },
    "org.apache.hugegraph.server.RestServer.max-write-threads": {
      "value": 0
    },
    "org.apache.hugegraph.task.TaskManager.pending-tasks": {
      "value": 0
    },
    "org.apache.hugegraph.task.TaskManager.workers": {
      "value": 4
    },
    "org.apache.tinkerpop.gremlin.server.GremlinServer.gremlin-groovy.sessionless.class-cache.average-load-penalty": {
      "value": 922769200
    },
    "org.apache.tinkerpop.gremlin.server.GremlinServer.gremlin-groovy.sessionless.class-cache.estimated-size": {
      "value": 2
    },
    "org.apache.tinkerpop.gremlin.server.GremlinServer.gremlin-groovy.sessionless.class-cache.eviction-count": {
      "value": 0
    },
    "org.apache.tinkerpop.gremlin.server.GremlinServer.gremlin-groovy.sessionless.class-cache.eviction-weight": {
      "value": 0
    },
    "org.apache.tinkerpop.gremlin.server.GremlinServer.gremlin-groovy.sessionless.class-cache.hit-count": {
      "value": 0
    },
    "org.apache.tinkerpop.gremlin.server.GremlinServer.gremlin-groovy.sessionless.class-cache.hit-rate": {
      "value": 0
    },
    "org.apache.tinkerpop.gremlin.server.GremlinServer.gremlin-groovy.sessionless.class-cache.load-count": {
      "value": 2
    },
    "org.apache.tinkerpop.gremlin.server.GremlinServer.gremlin-groovy.sessionless.class-cache.load-failure-count": {
      "value": 0
    },
    "org.apache.tinkerpop.gremlin.server.GremlinServer.gremlin-groovy.sessionless.class-cache.load-failure-rate": {
      "value": 0
    },
    "org.apache.tinkerpop.gremlin.server.GremlinServer.gremlin-groovy.sessionless.class-cache.load-success-count": {
      "value": 2
    },
    "org.apache.tinkerpop.gremlin.server.GremlinServer.gremlin-groovy.sessionless.class-cache.long-run-compilation-count": {
      "value": 0
    },
    "org.apache.tinkerpop.gremlin.server.GremlinServer.gremlin-groovy.sessionless.class-cache.miss-count": {
      "value": 2
    },
    "org.apache.tinkerpop.gremlin.server.GremlinServer.gremlin-groovy.sessionless.class-cache.miss-rate": {
      "value": 1
    },
    "org.apache.tinkerpop.gremlin.server.GremlinServer.gremlin-groovy.sessionless.class-cache.request-count": {
      "value": 2
    },
    "org.apache.tinkerpop.gremlin.server.GremlinServer.gremlin-groovy.sessionless.class-cache.total-load-time": {
      "value": 1845538400
    },
    "org.apache.tinkerpop.gremlin.server.GremlinServer.sessions": {
      "value": 0
    }
  },
  "counters": {
    "favicon.ico/GET/FAILED_COUNTER": {
      "count": 1
    },
    "favicon.ico/GET/TOTAL_COUNTER": {
      "count": 1
    },
    "metrics/POST/FAILED_COUNTER": {
      "count": 1
    },
    "metrics/POST/TOTAL_COUNTER": {
      "count": 1
    },
    "metrics/backend/GET/SUCCESS_COUNTER": {
      "count": 2
    },
    "metrics/backend/GET/TOTAL_COUNTER": {
      "count": 2
    },
    "metrics/gauges/GET/SUCCESS_COUNTER": {
      "count": 1
    },
    "metrics/gauges/GET/TOTAL_COUNTER": {
      "count": 1
    },
    "metrics/system/GET/SUCCESS_COUNTER": {
      "count": 2
    },
    "metrics/system/GET/TOTAL_COUNTER": {
      "count": 2
    },
    "system/GET/FAILED_COUNTER": {
      "count": 1
    },
    "system/GET/TOTAL_COUNTER": {
      "count": 1
    }
  },
  "histograms": {
    "favicon.ico/GET/RESPONSE_TIME_HISTOGRAM": {
      "count": 1,
      "min": 1,
      "mean": 1,
      "max": 1,
      "stddev": 0,
      "p50": 1,
      "p75": 1,
      "p95": 1,
      "p98": 1,
      "p99": 1,
      "p999": 1
    },
    "metrics/POST/RESPONSE_TIME_HISTOGRAM": {
      "count": 1,
      "min": 21,
      "mean": 21,
      "max": 21,
      "stddev": 0,
      "p50": 21,
      "p75": 21,
      "p95": 21,
      "p98": 21,
      "p99": 21,
      "p999": 21
    },
    "metrics/backend/GET/RESPONSE_TIME_HISTOGRAM": {
      "count": 2,
      "min": 6,
      "mean": 12.6852124529148,
      "max": 20,
      "stddev": 6.992918475157571,
      "p50": 6,
      "p75": 20,
      "p95": 20,
      "p98": 20,
      "p99": 20,
      "p999": 20
    },
    "metrics/gauges/GET/RESPONSE_TIME_HISTOGRAM": {
      "count": 1,
      "min": 7,
      "mean": 7,
      "max": 7,
      "stddev": 0,
      "p50": 7,
      "p75": 7,
      "p95": 7,
      "p98": 7,
      "p99": 7,
      "p999": 7
    },
    "metrics/system/GET/RESPONSE_TIME_HISTOGRAM": {
      "count": 2,
      "min": 0,
      "mean": 8.942674506664073,
      "max": 40,
      "stddev": 16.665399873223066,
      "p50": 0,
      "p75": 0,
      "p95": 40,
      "p98": 40,
      "p99": 40,
      "p999": 40
    },
    "system/GET/RESPONSE_TIME_HISTOGRAM": {
      "count": 1,
      "min": 2,
      "mean": 2,
      "max": 2,
      "stddev": 0,
      "p50": 2,
      "p75": 2,
      "p95": 2,
      "p98": 2,
      "p99": 2,
      "p999": 2
    }
  },
  "meters": {
    "org.apache.hugegraph.api.API.commit-succeed": {
      "count": 0,
      "mean_rate": 0,
      "m15_rate": 0,
      "m5_rate": 0,
      "m1_rate": 0,
      "rate_unit": "events/second"
    },
    "org.apache.hugegraph.api.API.expected-error": {
      "count": 0,
      "mean_rate": 0,
      "m15_rate": 0,
      "m5_rate": 0,
      "m1_rate": 0,
      "rate_unit": "events/second"
    },
    "org.apache.hugegraph.api.API.illegal-arg": {
      "count": 0,
      "mean_rate": 0,
      "m15_rate": 0,
      "m5_rate": 0,
      "m1_rate": 0,
      "rate_unit": "events/second"
    },
    "org.apache.hugegraph.api.API.unknown-error": {
      "count": 0,
      "mean_rate": 0,
      "m15_rate": 0,
      "m5_rate": 0,
      "m1_rate": 0,
      "rate_unit": "events/second"
    },
    "org.apache.tinkerpop.gremlin.server.GremlinServer.errors": {
      "count": 0,
      "mean_rate": 0,
      "m15_rate": 0,
      "m5_rate": 0,
      "m1_rate": 0,
      "rate_unit": "events/second"
    }
  },
  "timers": {
    "org.apache.hugegraph.api.auth.AccessAPI.create": {
      "count": 0,
      "min": 0,
      "mean": 0,
      "max": 0,
      "stddev": 0,
      "p50": 0,
      "p75": 0,
      "p95": 0,
      "p98": 0,
      "p99": 0,
      "p999": 0,
      "duration_unit": "milliseconds",
      "mean_rate": 0,
      "m15_rate": 0,
      "m5_rate": 0,
      "m1_rate": 0,
      "rate_unit": "calls/second"
    },
    "org.apache.hugegraph.api.auth.AccessAPI.delete": {
      "count": 0,
      "min": 0,
      "mean": 0,
      "max": 0,
      "stddev": 0,
      "p50": 0,
      "p75": 0,
      "p95": 0,
      "p98": 0,
      "p99": 0,
      "p999": 0,
      "duration_unit": "milliseconds",
      "mean_rate": 0,
      "m15_rate": 0,
      "m5_rate": 0,
      "m1_rate": 0,
      "rate_unit": "calls/second"
    },
    "org.apache.hugegraph.api.auth.AccessAPI.get": {
      "count": 0,
      "min": 0,
      "mean": 0,
      "max": 0,
      "stddev": 0,
      "p50": 0,
      "p75": 0,
      "p95": 0,
      "p98": 0,
      "p99": 0,
      "p999": 0,
      "duration_unit": "milliseconds",
      "mean_rate": 0,
      "m15_rate": 0,
      "m5_rate": 0,
      "m1_rate": 0,
      "rate_unit": "calls/second"
    },
    "org.apache.hugegraph.api.auth.AccessAPI.list": {
      "count": 0,
      "min": 0,
      "mean": 0,
      "max": 0,
      "stddev": 0,
      "p50": 0,
      "p75": 0,
      "p95": 0,
      "p98": 0,
      "p99": 0,
      "p999": 0,
      "duration_unit": "milliseconds",
      "mean_rate": 0,
      "m15_rate": 0,
      "m5_rate": 0,
      "m1_rate": 0,
      "rate_unit": "calls/second"
    },
    ...
  }
}
```

##### 1.1.2 Method & Url

```
http://localhost:8080/metrics/

```

##### Response Status

```json
200
```

##### Response Body

```text
# HELP hugegraph_info
# TYPE hugegraph_info untyped
hugegraph_info{version="0.69",
} 1.0
# HELP org_apache_hugegraph_backend_cache_Cache_edge_hugegraph_capacity
# TYPE org_apache_hugegraph_backend_cache_Cache_edge_hugegraph_capacity gauge
org_apache_hugegraph_backend_cache_Cache_edge_hugegraph_capacity 1000000
# HELP org_apache_hugegraph_backend_cache_Cache_edge_hugegraph_expire
# TYPE org_apache_hugegraph_backend_cache_Cache_edge_hugegraph_expire gauge
org_apache_hugegraph_backend_cache_Cache_edge_hugegraph_expire 600000
# HELP org_apache_hugegraph_backend_cache_Cache_edge_hugegraph_hits
# TYPE org_apache_hugegraph_backend_cache_Cache_edge_hugegraph_hits gauge
org_apache_hugegraph_backend_cache_Cache_edge_hugegraph_hits 0
# HELP org_apache_hugegraph_backend_cache_Cache_edge_hugegraph_miss
# TYPE org_apache_hugegraph_backend_cache_Cache_edge_hugegraph_miss gauge
org_apache_hugegraph_backend_cache_Cache_edge_hugegraph_miss 0
# HELP org_apache_hugegraph_backend_cache_Cache_edge_hugegraph_size
# TYPE org_apache_hugegraph_backend_cache_Cache_edge_hugegraph_size gauge
org_apache_hugegraph_backend_cache_Cache_edge_hugegraph_size 0
# HELP org_apache_hugegraph_backend_cache_Cache_instances
# TYPE org_apache_hugegraph_backend_cache_Cache_instances gauge
org_apache_hugegraph_backend_cache_Cache_instances 7
# HELP org_apache_hugegraph_backend_cache_Cache_schema_id_hugegraph_capacity
# TYPE org_apache_hugegraph_backend_cache_Cache_schema_id_hugegraph_capacity gauge
org_apache_hugegraph_backend_cache_Cache_schema_id_hugegraph_capacity 10000
# HELP org_apache_hugegraph_backend_cache_Cache_schema_id_hugegraph_expire
# TYPE org_apache_hugegraph_backend_cache_Cache_schema_id_hugegraph_expire gauge
org_apache_hugegraph_backend_cache_Cache_schema_id_hugegraph_expire 0
# HELP org_apache_hugegraph_backend_cache_Cache_schema_id_hugegraph_hits
# TYPE org_apache_hugegraph_backend_cache_Cache_schema_id_hugegraph_hits gauge
org_apache_hugegraph_backend_cache_Cache_schema_id_hugegraph_hits 0
# HELP org_apache_hugegraph_backend_cache_Cache_schema_id_hugegraph_miss
# TYPE org_apache_hugegraph_backend_cache_Cache_schema_id_hugegraph_miss gauge
org_apache_hugegraph_backend_cache_Cache_schema_id_hugegraph_miss 0
# HELP org_apache_hugegraph_backend_cache_Cache_schema_id_hugegraph_size
# TYPE org_apache_hugegraph_backend_cache_Cache_schema_id_hugegraph_size gauge
org_apache_hugegraph_backend_cache_Cache_schema_id_hugegraph_size 17
# HELP org_apache_hugegraph_backend_cache_Cache_schema_name_hugegraph_capacity
# TYPE org_apache_hugegraph_backend_cache_Cache_schema_name_hugegraph_capacity gauge
org_apache_hugegraph_backend_cache_Cache_schema_name_hugegraph_capacity 10000
# HELP org_apache_hugegraph_backend_cache_Cache_schema_name_hugegraph_expire
# TYPE org_apache_hugegraph_backend_cache_Cache_schema_name_hugegraph_expire gauge
org_apache_hugegraph_backend_cache_Cache_schema_name_hugegraph_expire 0
# HELP org_apache_hugegraph_backend_cache_Cache_schema_name_hugegraph_hits
# TYPE org_apache_hugegraph_backend_cache_Cache_schema_name_hugegraph_hits gauge
org_apache_hugegraph_backend_cache_Cache_schema_name_hugegraph_hits 0
# HELP org_apache_hugegraph_backend_cache_Cache_schema_name_hugegraph_miss
# TYPE org_apache_hugegraph_backend_cache_Cache_schema_name_hugegraph_miss gauge
org_apache_hugegraph_backend_cache_Cache_schema_name_hugegraph_miss 0
# HELP org_apache_hugegraph_backend_cache_Cache_schema_name_hugegraph_size
# TYPE org_apache_hugegraph_backend_cache_Cache_schema_name_hugegraph_size gauge
org_apache_hugegraph_backend_cache_Cache_schema_name_hugegraph_size 17
...
```

### 1.2 Get Gauges Metrics

##### Method & Url

```
http://localhost:8080/metrics/gauges

```

##### Response Status

```json
200
```

##### Response Body

```json
{
  "org.apache.hugegraph.backend.cache.Cache.edge-hugegraph.capacity": {
    "value": 1000000
  },
  "org.apache.hugegraph.backend.cache.Cache.edge-hugegraph.expire": {
    "value": 600000
  },
  "org.apache.hugegraph.backend.cache.Cache.edge-hugegraph.hits": {
    "value": 0
  },
  "org.apache.hugegraph.backend.cache.Cache.edge-hugegraph.miss": {
    "value": 0
  },
  "org.apache.hugegraph.backend.cache.Cache.edge-hugegraph.size": {
    "value": 0
  },
  "org.apache.hugegraph.backend.cache.Cache.instances": {
    "value": 7
  },
  "org.apache.hugegraph.backend.cache.Cache.schema-id-hugegraph.capacity": {
    "value": 10000
  },
  "org.apache.hugegraph.backend.cache.Cache.schema-id-hugegraph.expire": {
    "value": 0
  },
  "org.apache.hugegraph.backend.cache.Cache.schema-id-hugegraph.hits": {
    "value": 0
  },
  "org.apache.hugegraph.backend.cache.Cache.schema-id-hugegraph.miss": {
    "value": 0
  },
  "org.apache.hugegraph.backend.cache.Cache.schema-id-hugegraph.size": {
    "value": 17
  },
  "org.apache.hugegraph.backend.cache.Cache.schema-name-hugegraph.capacity": {
    "value": 10000
  },
  "org.apache.hugegraph.backend.cache.Cache.schema-name-hugegraph.expire": {
    "value": 0
  },
  "org.apache.hugegraph.backend.cache.Cache.schema-name-hugegraph.hits": {
    "value": 0
  },
  "org.apache.hugegraph.backend.cache.Cache.schema-name-hugegraph.miss": {
    "value": 0
  },
  "org.apache.hugegraph.backend.cache.Cache.schema-name-hugegraph.size": {
    "value": 17
  },
  "org.apache.hugegraph.backend.cache.Cache.token-hugegraph.capacity": {
    "value": 10240
  },
  "org.apache.hugegraph.backend.cache.Cache.token-hugegraph.expire": {
    "value": 600000
  },
  "org.apache.hugegraph.backend.cache.Cache.token-hugegraph.hits": {
    "value": 0
  },
  "org.apache.hugegraph.backend.cache.Cache.token-hugegraph.miss": {
    "value": 0
  },
  "org.apache.hugegraph.backend.cache.Cache.token-hugegraph.size": {
    "value": 0
  },
  "org.apache.hugegraph.backend.cache.Cache.users-hugegraph.capacity": {
    "value": 10240
  },
  "org.apache.hugegraph.backend.cache.Cache.users-hugegraph.expire": {
    "value": 600000
  },
  "org.apache.hugegraph.backend.cache.Cache.users-hugegraph.hits": {
    "value": 0
  },
  "org.apache.hugegraph.backend.cache.Cache.users-hugegraph.miss": {
    "value": 0
  },
  "org.apache.hugegraph.backend.cache.Cache.users-hugegraph.size": {
    "value": 0
  },
  "org.apache.hugegraph.backend.cache.Cache.users_pwd-hugegraph.capacity": {
    "value": 10240
  },
  "org.apache.hugegraph.backend.cache.Cache.users_pwd-hugegraph.expire": {
    "value": 600000
  },
  "org.apache.hugegraph.backend.cache.Cache.users_pwd-hugegraph.hits": {
    "value": 0
  },
  "org.apache.hugegraph.backend.cache.Cache.users_pwd-hugegraph.miss": {
    "value": 0
  },
  "org.apache.hugegraph.backend.cache.Cache.users_pwd-hugegraph.size": {
    "value": 0
  },
  "org.apache.hugegraph.backend.cache.Cache.vertex-hugegraph.capacity": {
    "value": 10000000
  },
  "org.apache.hugegraph.backend.cache.Cache.vertex-hugegraph.expire": {
    "value": 600000
  },
  "org.apache.hugegraph.backend.cache.Cache.vertex-hugegraph.hits": {
    "value": 0
  },
  "org.apache.hugegraph.backend.cache.Cache.vertex-hugegraph.miss": {
    "value": 0
  },
  "org.apache.hugegraph.backend.cache.Cache.vertex-hugegraph.size": {
    "value": 0
  },
  "org.apache.hugegraph.server.RestServer.max-write-threads": {
    "value": 0
  },
  "org.apache.hugegraph.task.TaskManager.pending-tasks": {
    "value": 0
  },
  "org.apache.hugegraph.task.TaskManager.workers": {
    "value": 4
  },
  "org.apache.tinkerpop.gremlin.server.GremlinServer.gremlin-groovy.sessionless.class-cache.average-load-penalty": {
    "value": 9.227692E8
  },
  "org.apache.tinkerpop.gremlin.server.GremlinServer.gremlin-groovy.sessionless.class-cache.estimated-size": {
    "value": 2
  },
  "org.apache.tinkerpop.gremlin.server.GremlinServer.gremlin-groovy.sessionless.class-cache.eviction-count": {
    "value": 0
  },
  "org.apache.tinkerpop.gremlin.server.GremlinServer.gremlin-groovy.sessionless.class-cache.eviction-weight": {
    "value": 0
  },
  "org.apache.tinkerpop.gremlin.server.GremlinServer.gremlin-groovy.sessionless.class-cache.hit-count": {
    "value": 0
  },
  "org.apache.tinkerpop.gremlin.server.GremlinServer.gremlin-groovy.sessionless.class-cache.hit-rate": {
    "value": 0.0
  },
  "org.apache.tinkerpop.gremlin.server.GremlinServer.gremlin-groovy.sessionless.class-cache.load-count": {
    "value": 2
  },
  "org.apache.tinkerpop.gremlin.server.GremlinServer.gremlin-groovy.sessionless.class-cache.load-failure-count": {
    "value": 0
  },
  "org.apache.tinkerpop.gremlin.server.GremlinServer.gremlin-groovy.sessionless.class-cache.load-failure-rate": {
    "value": 0.0
  },
  "org.apache.tinkerpop.gremlin.server.GremlinServer.gremlin-groovy.sessionless.class-cache.load-success-count": {
    "value": 2
  },
  "org.apache.tinkerpop.gremlin.server.GremlinServer.gremlin-groovy.sessionless.class-cache.long-run-compilation-count": {
    "value": 0
  },
  "org.apache.tinkerpop.gremlin.server.GremlinServer.gremlin-groovy.sessionless.class-cache.miss-count": {
    "value": 2
  },
  "org.apache.tinkerpop.gremlin.server.GremlinServer.gremlin-groovy.sessionless.class-cache.miss-rate": {
    "value": 1.0
  },
  "org.apache.tinkerpop.gremlin.server.GremlinServer.gremlin-groovy.sessionless.class-cache.request-count": {
    "value": 2
  },
  "org.apache.tinkerpop.gremlin.server.GremlinServer.gremlin-groovy.sessionless.class-cache.total-load-time": {
    "value": 1845538400
  },
  "org.apache.tinkerpop.gremlin.server.GremlinServer.sessions": {
    "value": 0
  }
}
```

### 1.3 Get Counters Metrics

##### Method & Url

```
GET http://localhost:8080/metrics/counters

```

##### Response Status

```json
200
```

##### Response Body

```json
{
  "favicon.ico/GET/FAILED_COUNTER": {
    "count": 1
  },
  "favicon.ico/GET/TOTAL_COUNTER": {
    "count": 1
  },
  "metrics//GET/SUCCESS_COUNTER": {
    "count": 2
  },
  "metrics//GET/TOTAL_COUNTER": {
    "count": 2
  },
  "metrics/POST/FAILED_COUNTER": {
    "count": 1
  },
  "metrics/POST/TOTAL_COUNTER": {
    "count": 1
  },
  "metrics/backend/GET/SUCCESS_COUNTER": {
    "count": 2
  },
  "metrics/backend/GET/TOTAL_COUNTER": {
    "count": 2
  },
  "metrics/gauges/GET/SUCCESS_COUNTER": {
    "count": 1
  },
  "metrics/gauges/GET/TOTAL_COUNTER": {
    "count": 1
  },
  "metrics/statistics/GET/SUCCESS_COUNTER": {
    "count": 2
  },
  "metrics/statistics/GET/TOTAL_COUNTER": {
    "count": 2
  },
  "metrics/system/GET/SUCCESS_COUNTER": {
    "count": 2
  },
  "metrics/system/GET/TOTAL_COUNTER": {
    "count": 2
  },
  "metrics/timers/GET/SUCCESS_COUNTER": {
    "count": 1
  },
  "metrics/timers/GET/TOTAL_COUNTER": {
    "count": 1
  },
  "system/GET/FAILED_COUNTER": {
    "count": 1
  },
  "system/GET/TOTAL_COUNTER": {
    "count": 1
  }
}
```

### 1.4 Get Histograms Metrics

##### Method & Url

```
GET http://localhost:8080/metrics/gauges

```

##### Response Status

```json
200
```

##### Response Body

```json
{
  "favicon.ico/GET/RESPONSE_TIME_HISTOGRAM": {
    "count": 1,
    "min": 1,
    "mean": 1.0,
    "max": 1,
    "stddev": 0.0,
    "p50": 1.0,
    "p75": 1.0,
    "p95": 1.0,
    "p98": 1.0,
    "p99": 1.0,
    "p999": 1.0
  },
  "metrics//GET/RESPONSE_TIME_HISTOGRAM": {
    "count": 2,
    "min": 10,
    "mean": 10.0,
    "max": 10,
    "stddev": 0.0,
    "p50": 10.0,
    "p75": 10.0,
    "p95": 10.0,
    "p98": 10.0,
    "p99": 10.0,
    "p999": 10.0
  },
  "metrics/POST/RESPONSE_TIME_HISTOGRAM": {
    "count": 1,
    "min": 21,
    "mean": 21.0,
    "max": 21,
    "stddev": 0.0,
    "p50": 21.0,
    "p75": 21.0,
    "p95": 21.0,
    "p98": 21.0,
    "p99": 21.0,
    "p999": 21.0
  },
  "metrics/backend/GET/RESPONSE_TIME_HISTOGRAM": {
    "count": 2,
    "min": 6,
    "mean": 12.6852124529148,
    "max": 20,
    "stddev": 6.992918475157571,
    "p50": 6.0,
    "p75": 20.0,
    "p95": 20.0,
    "p98": 20.0,
    "p99": 20.0,
    "p999": 20.0
  },
  "metrics/gauges/GET/RESPONSE_TIME_HISTOGRAM": {
    "count": 1,
    "min": 7,
    "mean": 7.0,
    "max": 7,
    "stddev": 0.0,
    "p50": 7.0,
    "p75": 7.0,
    "p95": 7.0,
    "p98": 7.0,
    "p99": 7.0,
    "p999": 7.0
  },
  "metrics/statistics/GET/RESPONSE_TIME_HISTOGRAM": {
    "count": 2,
    "min": 1,
    "mean": 1.4551211076264199,
    "max": 2,
    "stddev": 0.49798181193626,
    "p50": 1.0,
    "p75": 2.0,
    "p95": 2.0,
    "p98": 2.0,
    "p99": 2.0,
    "p999": 2.0
  },
  "metrics/system/GET/RESPONSE_TIME_HISTOGRAM": {
    "count": 2,
    "min": 0,
    "mean": 8.942674506664073,
    "max": 40,
    "stddev": 16.665399873223066,
    "p50": 0.0,
    "p75": 0.0,
    "p95": 40.0,
    "p98": 40.0,
    "p99": 40.0,
    "p999": 40.0
  },
  "metrics/timers/GET/RESPONSE_TIME_HISTOGRAM": {
    "count": 1,
    "min": 3,
    "mean": 3.0,
    "max": 3,
    "stddev": 0.0,
    "p50": 3.0,
    "p75": 3.0,
    "p95": 3.0,
    "p98": 3.0,
    "p99": 3.0,
    "p999": 3.0
  },
  "system/GET/RESPONSE_TIME_HISTOGRAM": {
    "count": 1,
    "min": 2,
    "mean": 2.0,
    "max": 2,
    "stddev": 0.0,
    "p50": 2.0,
    "p75": 2.0,
    "p95": 2.0,
    "p98": 2.0,
    "p99": 2.0,
    "p999": 2.0
  }
}
```

### 1.5 Get Meters Metrics

##### Method & Url

```
GET http://localhost:8080/metrics/meters

```

##### Response Status

```json
200
```

##### Response Body

```json
{
  "org.apache.hugegraph.api.API.commit-succeed": {
    "count": 0,
    "mean_rate": 0.0,
    "m15_rate": 0.0,
    "m5_rate": 0.0,
    "m1_rate": 0.0,
    "rate_unit": "events/second"
  },
  "org.apache.hugegraph.api.API.expected-error": {
    "count": 0,
    "mean_rate": 0.0,
    "m15_rate": 0.0,
    "m5_rate": 0.0,
    "m1_rate": 0.0,
    "rate_unit": "events/second"
  },
  "org.apache.hugegraph.api.API.illegal-arg": {
    "count": 0,
    "mean_rate": 0.0,
    "m15_rate": 0.0,
    "m5_rate": 0.0,
    "m1_rate": 0.0,
    "rate_unit": "events/second"
  },
  "org.apache.hugegraph.api.API.unknown-error": {
    "count": 0,
    "mean_rate": 0.0,
    "m15_rate": 0.0,
    "m5_rate": 0.0,
    "m1_rate": 0.0,
    "rate_unit": "events/second"
  },
  "org.apache.tinkerpop.gremlin.server.GremlinServer.errors": {
    "count": 0,
    "mean_rate": 0.0,
    "m15_rate": 0.0,
    "m5_rate": 0.0,
    "m1_rate": 0.0,
    "rate_unit": "events/second"
  }
}
```

### 1.6 Get Timers Metrics

##### Method & Url

```
GET http://localhost:8080/metrics/timers

```

##### Response Status

```json
200
```

##### Response Body

```json
{
  "org.apache.hugegraph.api.auth.AccessAPI.create": {
    "count": 0,
    "min": 0.0,
    "mean": 0.0,
    "max": 0.0,
    "stddev": 0.0,
    "p50": 0.0,
    "p75": 0.0,
    "p95": 0.0,
    "p98": 0.0,
    "p99": 0.0,
    "p999": 0.0,
    "duration_unit": "milliseconds",
    "mean_rate": 0.0,
    "m15_rate": 0.0,
    "m5_rate": 0.0,
    "m1_rate": 0.0,
    "rate_unit": "calls/second"
  },
  "org.apache.hugegraph.api.auth.AccessAPI.delete": {
    "count": 0,
    "min": 0.0,
    "mean": 0.0,
    "max": 0.0,
    "stddev": 0.0,
    "p50": 0.0,
    "p75": 0.0,
    "p95": 0.0,
    "p98": 0.0,
    "p99": 0.0,
    "p999": 0.0,
    "duration_unit": "milliseconds",
    "mean_rate": 0.0,
    "m15_rate": 0.0,
    "m5_rate": 0.0,
    "m1_rate": 0.0,
    "rate_unit": "calls/second"
  },
  ...
}
```

## 2.Statistical Metrics

##### Params

- type: If the passed value is JSON, it is returned in JSON format, otherwise it is returned in
  Promethaus format.

##### 2.1 Method & Url

```
GET http://localhost:8080/metrics/statistics
```

##### Response Status

```text
# HELP hugegraph_info
# TYPE hugegraph_info untyped
hugegraph_info{version="0.69",
} 1.0
# HELP metrics_POST
# TYPE metrics_POST gauge
metrics_POST{name=FAILED_REQUEST,} 1
metrics_POST{name=MEAN_RESPONSE_TIME,} 21.0
metrics_POST{
name=MAX_RESPONSE_TIME,
} 21
metrics_POST{name=SUCCESS_REQUEST,
} 0
metrics_POST{
name=TOTAL_REQUEST,
} 1
# HELP metrics_backend_GET
# TYPE metrics_backend_GET gauge
metrics_backend_GET{name=FAILED_REQUEST,
} 0
metrics_backend_GET{
name=MEAN_RESPONSE_TIME,
} 12.6852124529148
metrics_backend_GET{
name=MAX_RESPONSE_TIME,
} 20
metrics_backend_GET{
name=SUCCESS_REQUEST,
} 2
metrics_backend_GET{name=TOTAL_REQUEST,} 2
# HELP system_GET
# TYPE system_GET gauge
system_GET{name=FAILED_REQUEST,} 1
system_GET{name=MEAN_RESPONSE_TIME,} 2.0
system_GET{name=MAX_RESPONSE_TIME,} 2
system_GET{
name=SUCCESS_REQUEST,
} 0
system_GET{name=TOTAL_REQUEST,
} 1
# HELP metrics_gauges_GET
# TYPE metrics_gauges_GET gauge
metrics_gauges_GET{name=FAILED_REQUEST,} 0
metrics_gauges_GET{name=MEAN_RESPONSE_TIME,
} 7.0
metrics_gauges_GET{
name=MAX_RESPONSE_TIME,
} 7
metrics_gauges_GET{
name=SUCCESS_REQUEST,
} 1
metrics_gauges_GET{
name=TOTAL_REQUEST,
} 1
# HELP favicon.ico_GET
# TYPE favicon.ico_GET gauge
favicon.ico_GET{name=FAILED_REQUEST,
} 1
favicon.ico_GET{
name=MEAN_RESPONSE_TIME,
} 1.0
favicon.ico_GET{name=MAX_RESPONSE_TIME,} 1
favicon.ico_GET{name=SUCCESS_REQUEST,} 0
favicon.ico_GET{
name=TOTAL_REQUEST,
} 1
# HELP metrics__GET
# TYPE metrics__GET gauge
metrics__GET{name=FAILED_REQUEST,} 0
metrics__GET{name=MEAN_RESPONSE_TIME,} 10.0
metrics__GET{name=MAX_RESPONSE_TIME,
} 10
metrics__GET{
name=SUCCESS_REQUEST,
} 2
metrics__GET{
name=TOTAL_REQUEST,
} 2
# HELP metrics_system_GET
# TYPE metrics_system_GET gauge
metrics_system_GET{name=FAILED_REQUEST,} 0
metrics_system_GET{name=MEAN_RESPONSE_TIME,
} 8.942674506664073
metrics_system_GET{
name=MAX_RESPONSE_TIME,
} 40
metrics_system_GET{name=SUCCESS_REQUEST,} 2
metrics_system_GET{name=TOTAL_REQUEST,
} 2

```

##### Response Body

```json
200
```

##### 2.2 Method & Url

```
GET http://localhost:8080/metrics/statistics?type=json
```

##### Response Status

```json
200
```

##### Response Body

```json
{
  "metrics/POST": {
    "FAILED_REQUEST": 1,
    "MEAN_RESPONSE_TIME": 21,
    "MAX_RESPONSE_TIME": 21,
    "SUCCESS_REQUEST": 0,
    "TOTAL_REQUEST": 1
  },
  "metrics/backend/GET": {
    "FAILED_REQUEST": 0,
    "MEAN_RESPONSE_TIME": 12.6852124529148,
    "MAX_RESPONSE_TIME": 20,
    "SUCCESS_REQUEST": 2,
    "TOTAL_REQUEST": 2
  },
  "system/GET": {
    "FAILED_REQUEST": 1,
    "MEAN_RESPONSE_TIME": 2,
    "MAX_RESPONSE_TIME": 2,
    "SUCCESS_REQUEST": 0,
    "TOTAL_REQUEST": 1
  },
  "metrics/gauges/GET": {
    "FAILED_REQUEST": 0,
    "MEAN_RESPONSE_TIME": 7,
    "MAX_RESPONSE_TIME": 7,
    "SUCCESS_REQUEST": 1,
    "TOTAL_REQUEST": 1
  },
  "favicon.ico/GET": {
    "FAILED_REQUEST": 1,
    "MEAN_RESPONSE_TIME": 1,
    "MAX_RESPONSE_TIME": 1,
    "SUCCESS_REQUEST": 0,
    "TOTAL_REQUEST": 1
  },
  "metrics//GET": {
    "FAILED_REQUEST": 0,
    "MEAN_RESPONSE_TIME": 10,
    "MAX_RESPONSE_TIME": 10,
    "SUCCESS_REQUEST": 2,
    "TOTAL_REQUEST": 2
  },
  "metrics/system/GET": {
    "FAILED_REQUEST": 0,
    "MEAN_RESPONSE_TIME": 8.942674506664073,
    "MAX_RESPONSE_TIME": 40,
    "SUCCESS_REQUEST": 2,
    "TOTAL_REQUEST": 2
  }
}
```

## 3.System Metrics

System metrics mainly return the machine metrics, such as memory, threads, and other information.

##### Method & Url

```
GET http://localhost:8080/metrics/system
```

##### Response Status

```json
200
```

##### Response Body

```json
{
  "basic": {
    "mem": 1010,
    "mem_total": 911,
    "mem_used": 239,
    "mem_free": 671,
    "mem_unit": "MB",
    "processors": 20,
    "uptime": 137503,
    "systemload_average": -1.0
  },
  "heap": {
    "committed": 911,
    "init": 254,
    "used": 239,
    "max": 3596
  },
  "nonheap": {
    "committed": 98,
    "init": 2,
    "used": 95,
    "max": 0
  },
  "thread": {
    "peak": 82,
    "daemon": 34,
    "total_started": 108,
    "count": 82
  },
  "class_loading": {
    "count": 11495,
    "loaded": 11495,
    "unloaded": 0
  },
  "garbage_collector": {
    "ps_scavenge_count": 16,
    "ps_scavenge_time": 155,
    "ps_marksweep_count": 3,
    "ps_marksweep_time": 494,
    "time_unit": "ms"
  }
}
```

## 4.Backend Metrics

HugeGraph supports multiple backend storage, with backend metrics including memory, disk, and other
information.

##### Method & Url

```
GET http://localhost:8080/metrics/backend
```

##### Response Status

```json
200
```

##### Response Body

```json
{
  "hugegraph": {
    "backend": "rocksdb",
    "nodes": 1,
    "cluster_id": "local",
    "servers": {
      "local": {
        "mem_unit": "MB",
        "disk_unit": "GB",
        "mem_used": 0.1,
        "mem_used_readable": "103.53 KB",
        "disk_usage": 0.03,
        "disk_usage_readable": "29.03 KB",
        "block_cache_usage": 0.00359344482421875,
        "block_cache_pinned_usage": 0.00359344482421875,
        "block_cache_capacity": 304.0,
        "estimate_table_readers_mem": 0.019697189331054688,
        "size_all_mem_tables": 0.07421875,
        "cur_size_all_mem_tables": 0.07421875,
        "estimate_live_data_size": 5.536526441574097E-5,
        "total_sst_files_size": 5.536526441574097E-5,
        "live_sst_files_size": 5.536526441574097E-5,
        "estimate_pending_compaction_bytes": 0.0,
        "estimate_num_keys": 0,
        "num_entries_active_mem_table": 0,
        "num_entries_imm_mem_tables": 0,
        "num_deletes_active_mem_table": 0,
        "num_deletes_imm_mem_tables": 0,
        "num_running_flushes": 0,
        "mem_table_flush_pending": 0,
        "num_running_compactions": 0,
        "compaction_pending": 0,
        "num_immutable_mem_table": 0,
        "num_snapshots": 0,
        "oldest_snapshot_time": 0,
        "num_live_versions": 38,
        "current_super_version_number": 38
      }
    }
  }
}
```

