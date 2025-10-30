# 🧩 AWS Network Visualizer

---

## 🌟 Overview

---

In complex AWS environments, understanding network relationships across VPCs, subnets, and instances can be time-consuming and error-prone.

This tool automates the discovery of networking components and visualizes them in an intuitive graph, helping engineers identify configuration issues and understand dependencies — a key step toward automating network operations at scale.

---

## ⚙️ Simple Architecture Plan

**Core flow:**

1. Use **boto3** to pull data from:
   2. `describe_vpcs()`
   3. `describe_subnets()`
   4. `describe_internet_gateways()`
   5. `describe_instances()`

2. Use **networkx** and **matplotlib** to create a basic graph view. 
3. Export the visualization as `network_map.png`.

Example graph structure:
```
markdown

VPC → Subnets → Instances
     ↘ Internet Gateway
```


