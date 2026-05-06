---
title: "v0.2"
linkTitle: "v0.2"
draft: true
weight: 4
---

> Note: v0.2 is an old version, not recommended to use, please use the latest version, thank you for understanding.

### 1 Test environment

#### 1.1 Software and hardware information

The load testing and target machines have the same configuration, with the following basic parameters:

CPU                                          | Memory | 网卡
-------------------------------------------- | ------ | --------
24 Intel(R) Xeon(R) CPU E5-2620 v2 @ 2.10GHz | 61G    | 1000Mbps

#### 1.2 Service Configuration

- HugeGraph Version: 0.2
- Backend Storage: Cassandra 3.10, deployed as a single node in the service.
- Backend Configuration Modification: Modified two properties in the cassandra.yaml file, while keeping the rest of the options default:

```
  batch_size_warn_threshold_in_kb: 1000
  batch_size_fail_threshold_in_kb: 1000
```

- HugeGraphServer, HugeGremlinServer, and Cassandra are all started on the same machine. Configuration files for the servers are modified only for the host and port settings.

#### 1.3 Glossary

- Samples -- The total number of threads completed in this scenario.
- Average -- The average response time.
- Median -- The statistical median of response times.
- 90% Line -- The response time below which 90% of all threads fall.
- Min -- The minimum response time.
- Max -- The maximum response time.
- Error -- The error rate.
- Troughput -- The number of requests processed per unit of time.
- KB/sec -- The throughput measured in kilobytes per second.

_Note: All time units are measured in ms._

### 2 Test Results

#### 2.1 schema

Label         | Samples | Average | Median | 90%Line | Min | Max | Error% | Throughput | KB/sec
------------- | ------- | ------- | ------ | ------- | --- | --- | ------ | ---------- | ------
property_keys | 331000  | 1       | 1      | 2       | 0   | 172 | 0.00%  | 920.7/sec  | 178.1
vertex_labels | 331000  | 1       | 2      | 2       | 1   | 126 | 0.00%  | 920.7/sec  | 193.4
edge_labels   | 331000  | 2       | 2      | 3       | 1   | 158 | 0.00%  | 920.7/sec  | 242.8

Conclusion: Under the pressure of 1000 concurrent requests lasting for 5 minutes, the average response time for the schema interface is 1-2ms, and there is no pressure.

#### 2.2 Single Insert

##### 2.2.1 Insertion Rate Test

###### Pressure Parameters

Test Method: Fixed concurrency, test server and backend processing speed.

- Concurrency: 1000
- Duration: 5 minutes

###### Performance Indicators

Label                  | Samples | Average | Median | 90%Line | Min | Max | Error% | Throughput | KB/sec
---------------------- | ------- | ------- | ------ | ------- | --- | --- | ------ | ---------- | ------
single_insert_vertices | 331000  | 0       | 1      | 1       | 0   | 21  | 0.00%  | 920.7/sec  | 234.4
single_insert_edges    | 331000  | 2       | 2      | 3       | 1   | 53  | 0.00%  | 920.7/sec  | 309.1

###### Conclusion

- For vertices: average response time of 1ms, with each request inserting one piece of data. With an average of 920 requests processed per second, the average total data processed per second is approximately 920 pieces of data.
- For edges: average response time of 1ms, with each request inserting one piece of data. With an average of 920 requests processed per second, the average total data processed per second is approximately 920 pieces of data.

##### 2.2.2 Stress Test

Test Method: Continuously increase concurrency to test the maximum stress level at which the server can still provide normal services.

###### Stress Parameters

- Duration: 5 minutes
- Service Exception Flag: Error rate greater than 0.00%

###### Performance Metrics

Concurrency  | Samples | Average | Median | 90%Line | Min | Max  | Error% | Throughput | KB/sec
------------ | ------- | ------- | ------ | ------- | --- | ---- | ------ | ---------- | ------
2000(vertex) | 661916  | 1       | 1      | 1       | 0   | 3012 | 0.00%  | 1842.9/sec | 469.1
4000(vertex) | 1316124 | 13      | 1      | 14      | 0   | 9023 | 0.00%  | 3673.1/sec | 935.0
5000(vertex) | 1468121 | 1010    | 1135   | 1227    | 0   | 9223 | 0.06%  | 4095.6/sec | 1046.0
7000(vertex) | 1378454 | 1617    | 1708   | 1886    | 0   | 9361 | 0.08%  | 3860.3/sec | 987.1
2000(edge)   | 629399  | 953     | 1043   | 1113    | 1   | 9001 | 0.00%  | 1750.3/sec | 587.6
3000(edge)   | 648364  | 2258    | 2404   | 2500    | 2   | 9001 | 0.00%  | 1810.7/sec | 607.9
4000(edge)   | 649904  | 1992    | 2112   | 2211    | 1   | 9001 | 0.06%  | 1812.5/sec | 608.5


###### Conclusion

- Vertex:
  - 4000 concurrency: normal, no error rate, average time 13ms;
  - 5000 concurrency: if 5000 data insertions are processed per second, there will be an error rate of 0.06%, indicating that it cannot be handled. The peak should be at 4000.
- Edge:
  - 1000 concurrency: response time is 2ms, which is quite different from the response time of 2000 concurrency, mainly because IO network rec and send, as well as CPU, have almost doubled);
  - 2000 concurrency: if 2000 data insertions are processed per second, the average time is 953ms, and the average number of requests processed per second is 1750;
  - 3000 concurrency: if 3000 data insertions are processed per second, the average time is 2258ms, and the average number of requests processed per second is 1810;
  - 4000 concurrency: if 4000 data insertions are processed per second, the average number of requests processed per second is 1812;

#### 2.3 Batch Insertion

##### 2.3.1 Insertion Rate Test

###### Pressure Parameters

Test Method: Fix the concurrency and test the processing speed of the server and backend.

- Concurrency: 1000
- Duration: 5 minutes

###### Performance Indicators

Label                 | Samples | Average | Median | 90%Line | Min | Max   | Error% | Throughput | KB/sec
--------------------- | ------- | ------- | ------ | ------- | --- | ----- | ------ | ---------- | ------
batch_insert_vertices | 37162   | 8959    | 9595   | 9704    | 17  | 9852  | 0.00%  | 103.4/sec  | 393.3
batch_insert_edges    | 10800   | 31849   | 34544  | 35132   | 435 | 35747 | 0.00%  | 28.8/sec   | 814.9

###### Conclusion

- Vertex: The average response time is 8959ms, which is too long. Each request inserts 199 data, and the average processing rate is 103 requests per second. Therefore, the average number of data processed per second is about 2w (20,000) data.
- Edge: The average response time is 31849ms, which is too long. Each request inserts 499 data, and the average processing rate is 28 requests per second. Therefore, the average number of data processed per second is about 13900 (13,900) data.
