---
title: "Linux Device Mapper WriteCache (dm-writecache) performance improvements in Linux Kernel 5.8"
date: "2020-05-31"
categories: 
  - "how-to"
  - "linux"
tags: 
  - "clflushopt"
  - "cpu"
  - "device-mapper"
  - "dm-writecache"
  - "kernel"
  - "movdir64b"
  - "optane"
  - "persistent-memory"
  - "pmem"
image: "images/disc-reader-reading-arm-hard-drive.jpg"
author: Steve Scargall
---

The Linux 'dm-writecache' target allows for writeback caching of newly written data to an SSD or NVMe using persistent memory will achieve much better performance in Linux Kernel 5.8.

Red Hat developer Mikulas Patocka has been working to enhance the dm-writecache performance using Intel Optane Persistent Memory (PMem) as the cache device.

The performance optimization now queued for Linux 5.8 is making use of CLFLUSHOPT within dm-writecache when available instead of MOVNTI. CLFLUSHOPT is one of Intel's persistent memory instructions that allows for optimized flushing of cache lines by supporting greater concurrency. The CLFLUSHOPT instruction has been supported on Intel servers since Skylake and on AMD since Zen.

The dm-writecache target will now check for CLFLUSHOPT support and use it when available, thereby helping the performance on platforms with CPUs that support CLFLUSHOPT. On CPUs that do not provide CLFLUSHOPT, the existing behavior is maintained. The dm-writecache target is single-threaded (all the copying is done while holding the writecache lock), so it benefits from the optimized flush instruction.

[The patch](https://git.kernel.org/pub/scm/linux/kernel/git/device-mapper/linux-dm.git/commit/?h=dm-5.8&id=a70589009f56daa3a1f2267f376ba4963a25f2fe) is queued as part of the Device Mapper changes for Linux 5.8. Results indicate up to 1.6X performance improvement for 4K blocks:

```
block size   512             1024            2048            4096
movnti       496 MB/s        642 MB/s        725 MB/s        744 MB/s
clflushopt   373 MB/s        688 MB/s        1.1 GB/s        1.2 GB/s
```

We see that movnti performs better for 512-byte blocks, and CLFLUSHOPT performs better for 1024-byte and larger blocks, so the patch uses CLFLUSHOPT for sizes >= 768bytes and MOVNTI for block <768bytes.

Mikulas notes that the performance benefit of using CLFLUSHOPT happens to work well with dm-writecache's single-threaded model, but this will need to be re-evaluated once memcpy\_flushcache() is enabled to use MOVDIR64B which might invalidate this performance advantage seen with cache-allocating-writes plus flushing. Detailed information about the MOVDIR64B and CLFLUSHOPT instructions can be found in the [Intel® 64 and IA-32 Architectures Software Developer’s Manuals](https://software.intel.com/content/www/us/en/develop/articles/intel-sdm.html).

Using future persistent memory product generations should also yield better performance.

For easy reference and comparison, here are the descriptions for both instructions:

### CLFLUSHOPT Description

Invalidates from every level of the cache hierarchy in the cache coherence domain the cache line that contains the linear address specified with the memory operand. If that cache line contains modified data at any level of the cache hierarchy, that data is written back to memory. The source operand is a byte memory location.

The availability of CLFLUSHOPT is indicated by the presence of the CPUID feature flag CLFLUSHOPT (CPUID.(EAX=7,ECX=0):EBX\[bit 23\]). The aligned cache line size affected is also indicated with the CPUID instruction (bits 8 through 15 of the EBX register when the initial value in the EAX register is 1).

The memory attribute of the page containing the affected line has no effect on the behavior of this instruction. It should be noted that processors are free to speculatively fetch and cache data from system memory regions assigned a memory-type allowing for speculative reads (such as, the WB, WC, and WT memory types). PREFETCHh instructions can be used to provide the processor with hints for this speculative behavior. Because this speculative fetching can occur at any time and is not tied to instruction execution, the CLFLUSH instruction is not ordered with respect to PREFETCHh instructions or any of the speculative fetching mechanisms (that is, data can be speculatively loaded into a cache line just before, during, or after the execution of a CLFLUSH instruction that references the cache line).

Executions of the CLFLUSHOPT instruction are ordered with respect to fence instructions and to locked read-modify-write instructions; they are also ordered with respect to the following accesses to the cache line being invalidated: older writes and older executions of CLFLUSH. They are not ordered with respect to writes, executions of CLFLUSH that access other cache lines, or executions of CLFLUSHOPT regardless of cache line; to enforce CLFLUSHOPT ordering with any write, CLFLUSH, or CLFLUSHOPT operation, software can insert an SFENCE instruction between CLFLUSHOPT and that operation.

The CLFLUSHOPT instruction can be used at all privilege levels and is subject to all permission checking and faults associated with a byte load (and in addition, a CLFLUSHOPT instruction is allowed to flush a linear address in an execute-only segment). Like a load, the CLFLUSHOPT instruction sets the A bit but not the D bit in the page tables.

In some implementations, the CLFLUSHOPT instruction may always cause transactional abort with Transactional Synchronization Extensions (TSX). The CLFLUSHOPT instruction is not expected to be commonly used inside typical transactional regions. However, programmers must not rely on CLFLUSHOPT instruction to force a transactional abort, since whether they cause transactional abort is implementation dependent.

CLFLUSHOPT operation is the same in non-64-bit modes and 64-bit mode.

### MOVDIR64B Description

The MOVDIR64B instruction moves 64-bytes as direct-store with 64-byte write atomicity from source memory address to destination memory address.

MOVDIR64B reads 64-bytes from the source memory address and performs a 64-byte direct-store operation to the destination address. The load operation follows normal read ordering based on source address memory-type. The direct-store is implemented by using the write combining (WC) memory type protocol for writing data. Using this protocol, the processor does not write the data into the cache hierarchy, nor does it fetch the corresponding cache line from memory into the cache hierarchy. If the destination address is cached, the line is written-back (if modified) and invalidated from the cache, before the direct-store.

Unlike stores with non-temporal hint which allow UC/WP memory-type for destination to override the non-temporal hint, direct-stores always follow WC memory type protocol irrespective of destination address memory type (including UC/WP types). Unlike WC stores and stores with non-temporal hint, direct-stores are eligible for immediate eviction from the write-combining buffer, and thus not combined with younger stores (including direct-stores) to the same address. Older WC and non-temporal stores held in the write-combing buffer may be combined with younger direct stores to the same address. Because WC protocol used by direct-stores follow weakly-ordered memory consistency model, fencing operation using SFENCE or MFENCE should follow the MOVDIR64B instruction to enforce ordering when needed.

There is no atomicity guarantee provided for the 64-byte load operation from source address, and processor implementations may use multiple load operations to read the 64-bytes. The 64-byte direct-store issued by MOVDIR64B guarantees 64-byte write-completion atomicity. This means that the data arrives at the destination in a single undivided 64-byte write transaction.
