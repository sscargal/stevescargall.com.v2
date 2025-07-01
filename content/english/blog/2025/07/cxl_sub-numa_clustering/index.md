---
title: "CXL Memory NUMA Node Mapping with Sub-NUMA Clustering (SNC) on Linux"
meta_title: "CXL NUMA Node Mapping: SNC, Linux, and sysfs Explained"
description: "Learn how Sub-NUMA Clustering (SNC) affects CXL memory NUMA node mapping on Linux. This guide explains why sysfs, daxctl, and lsmem may disagree, and how to reliably identify CXL-backed NUMA nodes."
date: 2025-07-01T16:44:00-06:00
image: "featured_image.webp"
categories: ["Linux", "CXL"]
author: "Steve Scargall"
tags: ["CXL", "NUMA", "SNC", "Sub-NUMA Clustering", "Sub-NUMA Cluster", "Intel", Linux", "daxctl", "system-ram", "sysfs", "Memory Management"]
draft: false
aliases:
---


CXL (Compute Express Link) memory devices are revolutionizing server architectures, but they also introduce new NUMA complexity, especially when advanced memory configurations, such as Sub-NUMA Clustering (SNC), are enabled. One of the most confusing issues is the mismatch between NUMA node numbers reported by CXL sysfs attributes and those used by Linux memory management tools.

This blog post walks through a real-world scenario, complete with command outputs and diagrams, to help you understand and resolve the CXL NUMA node mapping issue with SNC enabled.

## What is Sub-NUMA Clustering?

A Sub-NUMA Cluster (SNC) is a processor mode available on recent Intel Xeon Scalable CPUs that divides each physical CPU socket into multiple NUMA (Non-Uniform Memory Access) domains. This partitioning groups cores, cache, and memory controllers within a socket into separate logical clusters, each exposed as a NUMA node to the operating system.

### How SNC Works

- **Each socket is divided into two (or more) NUMA domains.**
- **Each domain has its own set of cores, LLC (last-level cache) slices, and memory controllers.**
- **Memory accesses within a domain are faster** because of improved locality—cores access memory and cache closer to them.
- The OS and applications see more NUMA nodes than physical sockets (e.g., a 2-socket system appears as 4 NUMA nodes)[4].

### When to Use SNC

**Enable SNC if:**
- **Your workloads are NUMA-aware and optimized.** Applications such as high-performance computing (HPC), databases, and telecom workloads that can pin threads and memory allocations to specific NUMA nodes benefit most from SNC.
- **You want to minimize memory and cache latency** for local accesses and maximize bandwidth for NUMA-local workloads.
- **You have a symmetric memory configuration** (required by SNC; all memory controllers must be populated identically)[1].

**Do not enable SNC if:**
- **Your workloads are not NUMA-aware** or do not optimize for NUMA locality. Generic workloads, virtualized environments, or mixed-use servers may experience unpredictable performance or even degradation, as the OS and applications may not efficiently schedule tasks and memory allocations across the increased number of NUMA domains.
- **You have an asymmetric memory configuration** (SNC requires symmetric memory population)[1].
- **You are running legacy or poorly optimized software** that cannot take advantage of NUMA affinity.

### Performance Considerations

- **NUMA-optimized workloads:** See improved memory bandwidth and lower latency for local memory accesses in SNC mode.
- **Non-NUMA-aware workloads:** May see no benefit or even worse performance due to increased complexity in memory access patterns.
- **Benchmarks:** SNC can improve results in memory bandwidth-sensitive benchmarks (e.g., STREAM), but may not affect compute-bound benchmarks (e.g., Linpack)[1].

### Summary Table

| SNC Mode      | Advantages                                         | Disadvantages/When Not to Use           |
|---------------|----------------------------------------------------|-----------------------------------------|
| **Enabled**   | Lower local memory/cache latency, higher bandwidth | Requires NUMA-aware apps, symmetric RAM |
| **Disabled**  | Simpler topology, better for generic workloads     | Higher average memory latency           |

Use SNC for tightly controlled, NUMA-optimized workloads where memory locality is critical. Avoid SNC in general-purpose, virtualized, or mixed-use environments unless you have confirmed that your applications and OS can benefit from the additional NUMA domains.

## System Memory Topology: DRAM and CXL NUMA Nodes

When SNC is disabled (the default), each CPU socket has local DRAM. On a typical two-socket server, NUMA Node0 attached to CPU Socket 0, and NUMA Node 1 attaches to CPU socket 1, as shown in Figure 1 below.

**Figure 1: A Common System Memory Topology for a 2-Socket Server with CXL**

```text
+-----------------------+           +-----------------------+
|     CPU Socket 0      |           |     CPU Socket 1      |
|  +-----------------+  |           |  +-----------------+  |
|  |  NUMA Node 0    |  |           |  |  NUMA Node 1    |  |
|  |    DRAM + LLC   |  |           |  |    DRAM + LLC   |  |
|  +-----------------+  |           |  +-----------------+  |
+-----------------------+           +-----------------------+
         |                                  |
         |                                  |
         |                                  |
         +----------+            +----------+
                    |            |
              +-----------+ +-----------+
              | CXL Dev 0 | | CXL Dev 1 |
              | NUMA Node | | NUMA Node |
              |    2      | |    3      |
              +-----------+ +-----------+
              (PCIe Slot)   (PCIe Slot)
```

When SNC is enabled, each CPU socket is split into multiple logical NUMA nodes for improved locality. Figure 2 shows the same 2-socket server, with SNC enabled. You will notice how each physical CPU is now logically split into two SNC Domains, so the OS sees four (4) CPUs and NUMA nodes. CXL appears as Nodes 4 and 5, respectively.

**Figure 2: A Common System Memory Topology for a 2-Socket Server with CXL and SNC Enabled**

```text
+-----------------------+           +-----------------------+
|     CPU Socket 0      |           |     CPU Socket 1      |
|  +-----------------+  |           |  +-----------------+  |
|  |   SNC Domain 0  |  |           |  |   SNC Domain 2  |  |
|  | (NUMA Node 0)   |  |           |  | (NUMA Node 2)   |  |
|  |   DRAM + LLC    |  |           |  |   DRAM + LLC    |  |
|  +-----------------+  |           |  +-----------------+  |
|  +-----------------+  |           |  +-----------------+  |
|  |   SNC Domain 1  |  |           |  |   SNC Domain 3  |  |
|  | (NUMA Node 1)   |  |           |  | (NUMA Node 3)   |  |
|  |   DRAM + LLC    |  |           |  |   DRAM + LLC    |  |
|  +-----------------+  |           |  +-----------------+  |
+-----------------------+           +-----------------------+
         |      |                           |      |
         |      |                           |      |
         |      +---------------------------+      |
         |                                         |
         +-----+                           +-------+
               |                           |
         +-----------+               +-----------+
         | CXL Dev 0 |               | CXL Dev 1 |
         | NUMA Node |               | NUMA Node |
         |    4      |               |    5      |
         +-----------+               +-----------+
         (PCIe Slot)                  (PCIe Slot)
```

## The Problem

You might be thinking, "So what?". This all seems perfectly normal and reasonable. And you'd be right, except for one thing. If we rely on sysfs to determine which NUMA Node the CXL memory device is on, it returns an unexpected value. For example:

```
$ cat /sys/bus/cxl/devices/mem0/numa_node
2
```

For the non-SNC example, this is correct; however, for the SNC example, it is not. 

Let's walk through the process and delve deeper into this complex issue.

## Step-by-Step: Adding CXL Memory (with SNC Enabled)

### 1. Reconfiguring the CXL Device as System RAM

```bash
sudo daxctl reconfigure-device --mode system-ram --force dax9.0 --no-online
```

**Output:**

```json
[
  {
    "chardev":"dax9.0",
    "size":137438953472,
    "target_node":4,  <<<<<<
    "align":2097152,
    "mode":"system-ram",
    "online_memblocks":0,
    "total_memblocks":64
  }
]
reconfigured 1 device
```

> Note: `"target_node": 4` shows this device is associated with NUMA node 4.

### 2. Verifying Memory with `lsmem`

```bash
lsmem -o+ZONES,NODE
```

**Output:**

```text
RANGE                                  SIZE  STATE REMOVABLE     BLOCK  ZONES NODE
...
0x000006be80000000-0x000006de7fffffff  128G online       yes 3453-3516 Normal    4
```

The last line shows 128GB of memory on **Node 4**—this is the CXL memory!

### 3. Checking NUMA Topology with `numactl`

```bash
numactl -H
```

**Output:**

```text
available: 5 nodes (0-4)
...
node 4 cpus:
node 4 size: 0 MB
node 4 free: 0 MB
...
```

Node 4 is present, with no CPUs, and is the expected target for the CXL memory device.

### 4. The Confusing Part – `/sys/bus/cxl/devices/mem0/numa_node`

```bash
cat /sys/bus/cxl/devices/mem0/numa_node
```

**Output:**

```text
2
```

**Why does this say '2' instead of '4'?**
 When SNC is disabled, this would match expectations, but with SNC enabled, it does not.

### NUMA Node Mapping: OS vs. CXL sysfs (SNC Enabled)

**Figure 3: NUMA Node Mapping Discrepancy**

```text
+---------------------------+
| CXL Device (mem0)         |
|                           |
| sysfs: numa_node = 2      |
| daxctl: target_node = 4   |
+---------------------------+
         |            |
         |            +-------------------+
         |                                |
    +-------------+               +-----------------+
    | NUMA Node 2 |               | NUMA Node 4     |
    |   (DRAM)    |               |   (CXL)         |
    +-------------+               +-----------------+
```

## What’s Going On? (And Is This a Bug?)

### Sub-NUMA Clustering (SNC) and NUMA Node Mapping

- **SNC splits each CPU socket into multiple logical NUMA nodes.**
- The kernel’s CXL device sysfs attribute (`/sys/bus/cxl/devices/mem*/numa_node`) often reports the “physical” node number—before SNC logical splitting.
- Linux memory management tools (`daxctl`, `numactl`, `lsmem`) report the logical NUMA nodes—the ones the OS and applications actually use.

## Why the Mismatch?

- With SNC enabled, logical NUMA node numbers used by the OS may not match the physical node numbers reported by the device.
- This is a **known limitation**, not a traditional bug, and is documented by vendors and kernel maintainers.

## How Should You Identify CXL-Backed NUMA Nodes?

**Do not rely on `/sys/bus/cxl/devices/mem\*/numa_node` when SNC is enabled.**
 Instead, use:

- **`daxctl` output (look for `target_node`):**

  ```bash
  daxctl list -Mu
  ```

- **`lsmem` (shows which memory ranges are associated with which NUMA nodes):**

  ```bash
  lsmem -o+ZONES,NODE
  ```

- **`numactl -H` (shows NUMA nodes as the OS sees them).**

**Figure 4: NUMA Node Table**

```text
+-----------+-----------+-------------------+
| NUMA Node | Backed By |      Source       |
+-----------+-----------+-------------------+
|     0     |   DRAM    | lsmem, numactl    |
|     1     |   DRAM    | lsmem, numactl    |
|     2     |   DRAM    | lsmem, numactl    |
|     3     |   DRAM    | lsmem, numactl    |
|     4     |   CXL     | lsmem, daxctl     |
+-----------+-----------+-------------------+
```

## Memory Block Onlining Process

When using `--no-online` with `daxctl`, you must manually online the memory blocks for the new node. This has the advantage that you can use `online_movable` rather than the default `online` state to ensure the memory is managed by user space applications vs the Kernel.

**Figure 5: Memory Block Onlining Workflow**

```text
+--------------------------+
| Memory Blocks (Node 4)   |
+--------------------------+
| Block 3453               |
| Block 3454               |
| ...                      |
| Block 3516               |
+--------------------------+
         |         |         |
         v         v         v
   echo online > state   (for each block)
```

**Example command:**

```bash
for i in $(seq 3453 3516); do
    echo online_movable | sudo tee /sys/devices/system/memory/memory${i}/state
done
```

## CXL NUMA Node Latency Illustration

**Figure 6: Latency Pathways**

```text
[CPU]--(local)-->[DRAM Node 0]
   |
   +--(remote)-->[DRAM Node 1]
   |
   +--(CXL)----->[CXL Node 4]
         (higher latency)
```

## References

This SNC problem isn't new, and has been discussed many times. Here are some references I found on this topic:

- [Exploring Performance and Cost Optimization with ASIC-Based CXL Memory Expanders (2024)](https://openreview.net/pdf?id=cJOoD0jx6b)
  - This paper explicitly describes the use of SNC in CXL memory experiments and the resulting NUMA topology:

    > "Sub-NUMA Clustering (SNC) serves as an enhancement over the traditional NUMA architecture. It decomposes a single NUMA node into multiple smaller semi-independent sub-nodes (domains). Each sub-NUMA node possesses its own dedicated local memory, L3 caches, and CPU cores. In our experimental setup (Fig. 2(a)), we partition each CPU into four sub-NUMA nodes. Each sub-NUMA node is treated as a separate NUMA node by the OS, which can complicate memory allocation and NUMA node mapping, especially with CXL-attached memory."

  - The paper also references recent kernel patches to improve CXL NUMA awareness and interleaving, highlighting the complexity introduced by tiered memory and SNC
- [Demystifying CXL Memory with Genuine CXL-Ready Systems and Software (2023)](https://hxji.github.io/assets/pdf/cxl-micro23.pdf)
  - This paper discusses SNC and CXL memory mapping:

    > "(C3) The sub-NUMA clustering (SNC) mode provides LLC isolation among SNC nodes (§3) by directing the CPU cores within an SNC node to evict their L2 cache lines to the LLC slice within the same SNC node. ... CPU cores accessing CXL memory break LLC isolation among SNC nodes in SNC mode."

  - It also notes that CXL memory is exposed as a CPU-less NUMA node, which can differ from DRAM NUMA nodes in SNC mode
- [Linux Kernel Documentation: x86 Resource Control (resctrl)](https://docs.kernel.org/arch/x86/resctrl.html)
  - The official kernel docs describe SNC and its impact on NUMA node reporting and task scheduling:

    > "When SNC mode is enabled, Linux may load balance tasks between Sub-NUMA nodes much more readily than between regular NUMA nodes since the CPUs on Sub-NUMA nodes share the same L3 cache and the system may report the NUMA distance between Sub-NUMA nodes with a lower value than used for regular NUMA nodes."

  - The documentation also details how SNC affects resource allocation and monitoring, and that NUMA node reporting can be less intuitive when SNC is enabled
- [Intel 4th Gen Xeon Scalable Family Overview](https://www.intel.com/content/www/us/en/developer/articles/technical/fourth-generation-xeon-scalable-family-overview.html)
  - Intel’s official documentation for Sapphire Rapids CPUs discusses SNC and CXL memory, and how SNC changes the NUMA domain structure, which can affect how CXL memory is mapped and reported by the OS
- [Linux Kernel Mailing List: CXL/NVDIMM Discussions](https://lore.kernel.org)
  - The Linux kernel mailing list regularly discusses CXL and NUMA node mapping. For example, the introduction of weighted interleaving and tiered memory policies for CXL devices are discussed in the context of NUMA and SNC:
    - "Introducing Weighted Interleaving in Linux for Enhanced Memory." (See: [CXL Consortium Webinar, 2024](https://computeexpresslink.org/wp-content/uploads/2024/12/CXL-Breaking-Memory-Barriers-Webinar.pdf))


## Summary and Recommendations

- With SNC enabled, the NUMA node reported by CXL devices in sysfs may not match the logical NUMA node used by the OS.
- For all memory allocation, monitoring, and tuning, trust `daxctl`, `lsmem`, and `numactl`—not `/sys/bus/cxl/devices/mem\*/numa_node`.
- This is a known issue, not a bug, and will likely be addressed in future kernel and tool updates.

## Closing Thoughts

CXL memory is wonderful, but, like all new technologies, it has some quirks and edge cases to be aware of — especially when advanced features like SNC are enabled. By understanding the distinction between physical and logical NUMA node mappings, you can avoid confusion and ensure your system is configured correctly.

If you encounter this issue, remember: **use the NUMA node numbers reported by the Linux memory subsystem tools (daxctl), not the raw sysfs device attributes, when SNC is enabled.**

*Have you run into other CXL or NUMA quirks? Reach out on [LinkedIn](https://www.linkedin.com/in/stevescargall/)!*
