---
title: "Understanding STREAM: Benchmarking Memory Bandwidth for DRAM and CXL"
meta_title: "A detailed deep-dive into how STREAM works"
description: "This article takes a deep dive into the STREAM benchmark, how it works, and why it's helpful in benchmarking heterogeneous memory systems such as DRAM and CXL."
date: 2025-01-20T00:00:00Z
image: "featured_image.webp"
categories: ["Linux", "CXL"]
author: "Steve Scargall"
tags: ["STREAM Benchmark", "Benchmark", "CXL", "DRAM"]
draft: false
aliases:
---

In today’s Artificial Intelligence (AI), Machine Learning (ML), and high-performance computing (HPC) landscape, memory bandwidth is a critical factor in determining overall system performance. As workloads grow increasingly data-intensive, traditional DRAM-only setups are often insufficient, prompting the rise of new memory expansion technologies like **Compute Express Link (CXL)**. To evaluate memory bandwidth across DRAM and CXL devices, we use a modified industry-standard tool called **STREAM**.

In this blog, we’ll explore what STREAM is, how it works, why it’s commonly used for benchmarking memory bandwidth, and how a modified version of STREAM can be used to measure performance in heterogeneous memory environments, including DRAM and CXL.

## What is STREAM?

**STREAM** is a simple yet powerful benchmark designed to measure **sustainable memory bandwidth**. It performs a series of operations on large arrays and reports the memory throughput for each operation. Unlike CPU benchmarks that measure processing power, STREAM focuses purely on how fast data can be moved in and out of memory, making it an essential tool for assessing memory subsystem performance.

STREAM tests memory bandwidth using four basic vector operations:

1.  **Copy**: Copies data from one array to another.
2.  **Scale**: Reads an array, scales its elements by a constant, and writes the result to another array.
3.  **Add**: Reads two arrays, adds them element-wise, and writes the result to a third array.
4.  **Triad**: Combines reading, scaling, and adding operations by reading two arrays, scaling one of them, adding the result to the other, and writing to a third array.

Each of these operations stresses different aspects of the memory subsystem, making STREAM an ideal benchmark for evaluating memory bandwidth under various workloads.

## How STREAM Works

The core idea behind STREAM is to operate on arrays large enough to exceed the system’s cache size, ensuring that data must be fetched directly from main memory. This approach provides an accurate measure of sustainable memory bandwidth, as it eliminates the effects of caching optimizations that could artificially inflate performance.

Here’s how each operation works:

###  Add Operation
The Add operation reads two arrays from memory and writes the sum into a third array. Mathematically, it can be represented as:

```c
C[i] = A[i] + B[i]
```

-   Two arrays (`A` and `B`) are read from memory.
-   An element-wise addition is performed.
-   The result is stored in a third array (`C`), which requires a write operation.

The Add operation is useful for measuring **read and write bandwidth** simultaneously. Since two arrays are read and one is written, it represents scenarios where multiple data streams are combined, such as in matrix or vector addition. This operation is critical for evaluating how well the memory subsystem handles multiple concurrent data streams and its ability to sustain high throughput during combined read/write workloads.

### 2. Copy Operation
The Copy operation reads an array from memory and writes it into another array. Mathematically, it can be expressed as:

```c
B[i] = A[i]
```

-   An array (`A`) is read from memory.
-   The elements are directly written into a second array (`B`), with no computation performed.

The Copy operation is a fundamental test for **pure memory bandwidth** during sequential access. Since it involves only one read and one write operation without computation, it directly measures how quickly data can be moved between different locations in memory. This is particularly relevant for applications that require frequent data duplication, such as buffering and caching.

### 3. Scale Operation

The Scale operation reads an array, scales its elements by a constant factor, and writes the result into another array. It is represented as:

```c
B[i] = scalar * A[i]
```

-   An array (`A`) is read from memory.
-   Each element is multiplied by a constant (`scalar`).
-   The result is written into a second array (`B`).

The Scale operation combines **memory bandwidth and simple arithmetic computation**. It is useful for evaluating how well the memory subsystem performs when computations are applied to data before writing it back. This scenario is common in scientific computing, where datasets are often scaled or transformed before further processing.

### 4. Triad Operation

The Triad operation reads two arrays, scales one of them by a constant, adds the result to the other array, and writes the final result into a third array. It is represented as:

```c
C[i] = A[i] + scalar * B[i]
```

-   Two arrays (`A` and `B`) are read from memory.
-   The elements of `B` are scaled by a constant (`scalar`).
-   The scaled elements are added to the corresponding elements of `A`.
-   The result is written into a third array (`C`).

The Triad operation combines **multiple memory accesses with arithmetic computation**, making it a comprehensive test of the memory subsystem’s capabilities. This operation closely resembles real-world applications, such as vector updates in numerical simulations and iterative solvers. It is critical for understanding how the system performs under workloads that involve both high data throughput and computation.

## The Importance of STREAM Operations in Measuring Memory Throughput

Each operation in the STREAM benchmark stresses the memory subsystem in a unique way:

-   **Copy** focuses purely on data movement, which helps measure baseline memory bandwidth.
-   **Add** and **Scale** introduce basic arithmetic operations, providing insight into how well the system handles mixed workloads involving both computation and data transfer.
-   **Triad** represents a realistic workload where multiple memory streams are processed and combined, making it the most comprehensive test for effective memory bandwidth.

Together, these operations provide a holistic view of the memory subsystem’s performance. By measuring the throughput of each operation, STREAM allows users to identify potential bottlenecks in the memory hierarchy, including cache bandwidth, memory controller efficiency, and the performance of memory interleaving across multiple devices (such as CXL and DRAM).

## Why Use STREAM for Benchmarking DRAM and CXL?

STREAM is widely used for memory benchmarking because it directly measures the effective throughput of the memory subsystem, providing key insights into how well a system handles large, sequential data streams. This makes it ideal for evaluating:

-   **DRAM Performance**: Traditional STREAM benchmarks can be used to measure bandwidth for DRAM-only setups, helping identify bottlenecks in memory-bound workloads.
-   **CXL Memory Performance**: As CXL emerges as a critical technology for expanding memory beyond DRAM limitations, STREAM provides a reliable way to measure how well CXL memory devices integrate into the system’s memory hierarchy.

CXL memory devices act as an extension of main memory, offering higher capacities but potentially higher latency compared to DRAM. By using STREAM, we can evaluate how well CXL memory scales bandwidth as more devices are added, and how it compares to DRAM in terms of effective throughput.

## **Using a Modified STREAM for NUMA-Aware Benchmarking**

While the original STREAM benchmark is effective for homogeneous memory systems, it lacks the ability to distinguish between different types of memory, such as DRAM and CXL, in a **Non-Uniform Memory Access (NUMA)** environment. NUMA systems have multiple memory nodes, and accessing memory on a remote node can have significantly higher latency than accessing local memory.

To address this limitation, a modified version of STREAM is available from the [CXLBench GitHub repository](https://github.com/cxlbench/cxlbench). This version adds support for NUMA-aware memory allocation, allowing users to benchmark DRAM and CXL memory separately or in combination.

**Key Features of the Modified STREAM**:

-   **NUMA Node Awareness**: The modified STREAM allows users to bind memory allocations to specific NUMA nodes, ensuring that benchmarks accurately reflect the performance of DRAM, CXL, or mixed memory configurations.
-   **Customizable Setup**: Users can configure the number of threads, memory node bindings, and array sizes to match their specific hardware setup.
-   **Scalable Benchmarking**: The modified STREAM supports scaling tests, enabling users to evaluate how bandwidth changes as more CXL devices are added to the system.

## Explanation of Differences in Sub-Benchmark Results

Let's say you are testing multiple CXL devices and you get the following results (example only)

```markdown
| Sub-Benchmark | 1 x CXL Module (GiB/sec) | 2 x CXL Modules (GiB/sec) | 4 x CXL Modules (GiB/sec) |
|---------------|--------------------------|---------------------------|---------------------------|
| Add           | 20                       | 40                        | 80                        |
| Copy          | 20                       | 36                        | 76                        |
| Scale         | 20                       | 36                        | 76                        |
| Triad         | 24                       | 41                        | 84                        |
```

Although all four sub-benchmarks demonstrate similar scaling behavior as the number of CXL devices increases, there are notable differences in peak bandwidth among them:

1.  **Nature of Operations and Arithmetic Complexity**:
    - The **Add** operation involves reading two arrays from memory and writing the result to a third array. This results in three memory operations: two reads and one write. The combined memory access pattern leads to high utilization of memory bandwidth.
    - The **Copy** operation involves reading a single array and writing it to another array, resulting in only two memory operations: one read and one write. Since it involves fewer operations, it places less demand on the memory subsystem compared to the Add operation.
    - The **Add** and **Triad** sub-benchmarks involve arithmetic operations in addition to reading and writing memory. In particular, the **Triad** operation involves two reads, a scaling multiplication, and an addition before writing the result, resulting in higher memory bandwidth utilization. Consequently, **Triad** achieves the highest peak bandwidth among all sub-benchmarks.
    - The **Copy** and **Scale** sub-benchmarks involve simpler operations: Copy only performs a read and write, while Scale performs a read, a multiplication by a scalar, and a write. These simpler operations result in slightly lower peak bandwidth compared to Add and Triad.

2.  **Memory Access Patterns**:
    
    - In the **Add** sub-benchmark, since two arrays are read simultaneously, the CPU can better utilize prefetching mechanisms to load data into caches, resulting in more efficient memory access.
    - In the **Copy** sub-benchmark, the sequential reading and writing of data result in slightly lower bandwidth utilization because the memory controller cannot interleave multiple data streams as effectively as it can during the Add operation.
    - **Triad** benefits from interleaving two separate memory reads with a write operation, which allows for better utilization of memory bandwidth. This is why it achieves a slightly higher bandwidth than **Add**, despite involving similar arithmetic operations.
    - **Copy** and **Scale** involve single-stream memory access patterns. Since they do not interleave multiple reads, they place less demand on the memory channels, leading to slightly lower bandwidth.

3. **Cache and Prefetching Effects**:

    - The **Add** sub-benchmark benefits from the CPU's ability to prefetch two separate data streams in parallel and interleave them with the write operation, maximizing the utilization of available bandwidth.
    - In contrast, the **Copy** sub-benchmark, which involves only a single read and a write, may experience fewer opportunities for such prefetching optimizations, leading to slightly lower throughput.

4. **Saturation Points**:

    - For all sub-benchmarks, bandwidth scales with the number of CXL devices. The system reaches maximum bandwidth using more CXL modules. The variations in peak performance reflect differences in how well each operation saturates the memory subsystem.

Operations involving multiple concurrent memory accesses (Add and Triad) tend to achieve higher peak bandwidth compared to simpler operations (Copy and Scale). This is because they place greater demand on memory bandwidth and more effectively utilize the available memory channels by interleaving multiple streams.

## Conclusion

STREAM is a powerful and flexible tool for benchmarking memory bandwidth, providing valuable insights into the performance of both traditional DRAM and emerging CXL memory technologies. By using a modified, NUMA-aware version of STREAM, users can accurately measure and compare bandwidth across different memory nodes, helping them make informed decisions about system configurations for memory-intensive workloads.

As memory technologies evolve, tools like STREAM will remain essential for understanding system performance and guiding hardware optimization efforts. Whether you’re evaluating DRAM-only systems or exploring the potential of CXL memory, STREAM provides a reliable and straightforward method for benchmarking sustainable memory bandwidth.
