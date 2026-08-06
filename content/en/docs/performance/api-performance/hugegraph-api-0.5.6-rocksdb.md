---
title: "v0.5.6 Stand-alone(RocksDB)"
linkTitle: "v0.5.6 Stand-alone(RocksDB)"
weight: 1
---

> **Note:** 
> 
> The current performance metrics are based on an earlier version. The **latest version** has significant 
> improvements in both performance and functionality. We encourage you to refer to the most recent release featuring 
> **autonomous distributed storage** and **enhanced computational push down capabilities**. Alternatively, 
> you may wait for the community to update the data with these enhancements.

### 1 Test environment

Compressed machine information:

| CPU                                          | Memory | 网卡        | 磁盘                 |
|----------------------------------------------|--------|-----------|--------------------|
| 48 Intel(R) Xeon(R) CPU E5-2650 v4 @ 2.20GHz | 128G   | 10000Mbps | 750GB SSD,2.7T HDD |

- Information about the machine used to generate loads: configured the same as the machine that is being tested under load.
- Testing tool: Apache JMeter 2.5.1

Note: The load-generating machine and the machine under test are located in the same local network.

### 2 Test description

#### 2.1 Definition of terms (the unit of time is ms)

- Samples: The total number of threads completed in the current scenario.
- Average: The average response time.
- Median: The statistical median of the response time.
- 90% Line: The response time below which 90% of all threads fall.
- Min: The minimum response time.
- Max: The maximum response time.
- Error: The error rate.
- Throughput: The number of requests processed per unit of time.
- KB/sec: Throughput measured in terms of data transferred per second.

#### 2.2 Underlying storage

RocksDB is used for backend storage, HugeGraph and RocksDB are both started on the same machine, and the configuration files related to the server remain as default except for the modification of the host and port.

### 3 Summary of performance results

1. The speed of inserting a single vertex and edge in HugeGraph is about 1w per second
2. The batch insertion speed of vertices and edges is much faster than the single insertion speed
3. The concurrency of querying vertices and edges by id can reach more than 13000, and the average delay of requests is less than 50ms

### 4 Test results and analysis

#### 4.1 batch insertion

##### 4.1.1 Upper limit stress testing

###### Test methods

The upper limit of stress testing is to continuously increase the concurrency and test whether the server can still provide services normally.

###### Stress Parameters

Duration: 5 minutes

###### Maximum insertion speed for vertices:

<center>
  <img src="/docs/images/API-perf/v0.5.6/rocksdb/vertex_batch.png" alt="image">
</center>


###### in conclusion:

- With a concurrency of 2200, the throughput for vertices is 2026.8. This means that the system can process data at a rate of 405360 per second (2026.8 * 200).


###### Maximum insertion speed for edges


<center>
  <img src="/docs/images/API-perf/v0.5.6/rocksdb/edge_batch.png" alt="image">
</center>

###### Conclusion:

- With a concurrency of 900, the throughput for edges is 776.9. This means that the system can process data at a rate of 388450 per second (776.9 * 500).

#### 4.2 Single insertion

##### 4.2.1 Stress limit testing

###### Test Methods

Stress limit testing is a process of continuously increasing the concurrency level to test the upper limit of the server's ability to provide normal service.

###### Stress parameters

- Duration: 5 minutes.
- Service exception indicator: Error rate greater than 0.00%.

###### Single vertex insertion

<center>
  <img src="/docs/images/API-perf/v0.5.6/rocksdb/vertex_single.png" alt="image">
</center>


###### Conclusion:

- With a concurrency of 11500, the throughput is 10730. This means that the system can handle a single concurrent insertion of vertices at a concurrency level of 11500.

###### Single edge insertion

<center>
  <img src="/docs/images/API-perf/v0.5.6/rocksdb/edge_single.png" alt="image">
</center>


###### Conclusion:

- With a concurrency of 9000, the throughput is 8418. This means that the system can handle a single concurrent insertion of edges at a concurrency level of 9000.

#### 4.3 Search by ID

##### 4.3.1 Stress test upper limit

###### Testing method

Continuously increasing the concurrency level to test the upper limit of the server's ability to provide service under normal conditions.

###### stress parameters

- Duration: 5 minutes
- Service abnormality indicator: error rate greater than 0.00%

###### Querying vertices by ID

<center>
  <img src="/docs/images/API-perf/v0.5.6/rocksdb/vertex_id_query.png" alt="image">
</center>

###### Conclusion：

- Concurrency is 14,000, throughput is 12,663. The concurrency capacity for querying vertices by ID is 14,000, with an average delay of 44ms.

###### Querying edges by ID

<center>
  <img src="/docs/images/API-perf/v0.5.6/rocksdb/edge_id_query.png" alt="image">
</center>


###### Conclusion：

- Concurrency is 13,000, throughput is 12,225. The concurrency capacity for querying edges by ID is 13,000, with an average delay of 12ms.
