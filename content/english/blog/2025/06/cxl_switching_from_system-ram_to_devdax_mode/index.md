---
title: "Unlock Your CXL Memory: How to Switch from NUMA (System-RAM) to Direct Access (DAX) Mode"
meta_title: "Linux CXL Memory: Convert from NUMA Node (System_RAM) to DAX Device"
description: "Learn how to convert CXL.mem devices from kernel-managed NUMA nodes to direct access (DAX) mode, enabling high-performance applications to directly mmap CXL memory on Linux."
date: 2025-06-12T16:03:01Z
image: "featured_image.webp"
categories: ["Linux", "System Administration"]
author: "Steve Scargall"
tags: ["CXL", "NUMA", "DAX", "Linux Kernel", "Memory Management", "System Administration"]
draft: false
aliases:
---

As a Linux System Administrator working with Compute Express Link (CXL) memory devices, you should be aware that as of Linux Kernel 6.3, Type 3 CXL.mem devices are now automatically brought online as memory-only NUMA nodes. While this can be beneficial for most situations, it might not be ideal if your application is designed to directly manage the CXL memory as a DAX (Direct Access) device using `mmap()`.

This blog post will explain this behavior and provide a step-by-step guide on how to convert a CXL memory device from a memory-only NUMA node back to DAX mode, allowing applications to `mmap` the underlying `/dev/daxX.Y` device. We'll also cover troubleshooting steps if the memory is actively in use by the kernel or other processes.

### Understanding CXL.mem and NUMA Node Auto-Provisioning

In recent Linux kernel versions (from 6.3 onwards), CXL.mem devices are often automatically detected and configured as dedicated NUMA nodes. This means the kernel treats the CXL memory as another pool of memory, similar to traditional DRAM, which applications can allocate from via standard memory allocation mechanisms. The `numactl -H` output clearly illustrates this:

```bash
$ numactl -H
available: 3 nodes (0-2)
node 0 cpus: ...
node 0 size: 515751 MB
node 0 free: 475572 MB
node 1 cpus: ...
node 1 size: 515992 MB
node 1 free: 470018 MB
node 2 cpus:
node 2 size: 0 MB
node 2 free: 0 MB

```

In this example, `node 2` is a memory-only NUMA node. Notice it has no CPUs associated with it (`node 2 cpus:` is empty) and its `size` and `free` are reported as 0 MB by `numactl`. This might seem counterintuitive, but it indicates that `numactl` isn't reporting the CXL memory size in the same way it does for traditional DRAM, but rather its current state as a dedicated, memory-only NUMA node.

The `lsmem` command provides a more direct view of memory ranges and their states:

```bash
$ lsmem -o+NODE,ZONES
RANGE                                  SIZE   STATE REMOVABLE     BLOCK NODE           ZONES
0x0000000000000000-0x000000007fffffff    2G  online       yes         0           None    0
0x0000000100000000-0x000000807fffffff  510G  online       yes     2-256         Normal    0
0x0000063e80000000-0x000006be7fffffff  512G  online       yes 3197-3452         Normal    1
0x000006be80000000-0x000006de7fffffff  128G offline                 3453-3516    2 Normal/Movable

Memory block size:           2G
Total online memory:         1T
Total offline memory:      128G

```

Here, we clearly see a 128GB memory range associated with `NODE 2` that is currently `offline`. If this memory were `online`, it would be plausible for applications and the Kernel to allocate memory from it.

The `cxl list` command provides more detailed information about the CXL memory device:

```bash
$ cxl list
[
  {
    "memdevs":[
      {
        "memdev":"mem0",
        "ram_size":137438953472,
        "serial":12208648699093770240,
        "numa_node":1,
        "host":"0000:b4:00.0"
      }
    ]
  },
  {
    "regions":[
      {
        "region":"region9",
        "resource":7415261036544,
        "size":137438953472,
        "type":"ram",
        "interleave_ways":1,
        "interleave_granularity":256,
        "decode_state":"commit"
      }
    ]
  }
]
```

Here, we see `memdev="mem0"` with `ram_size` of 137438953472 bytes (approximately 128 GB). This `memdev` is part of `region9` and is currently configured as `type:"ram"`, indicating it's being treated as system RAM. Crucially, the `numa_node` field for `mem0` says `1`, which might seem to contradict `numactl` showing `node 2`. This highlights that the CXL subsystem and NUMA view things slightly differently, but ultimately the CXL memory is accessible via NUMA.

The `daxctl list` command, on the other hand, shows the direct access (DAX) characteristics:

```bash
$ daxctl list
[
  {
    "chardev":"dax9.0",
    "size":137438953472,
    "target_node":2,
    "align":2097152,
    "mode":"system-ram"
  }
]

```

This output confirms that a DAX character device, `/dev/dax9.0`, exists, and it has the same size as the CXL memory. The `target_node` is `2`, which aligns with the `numactl` output for the memory-only NUMA node. The `mode` is `system-ram`, indicating that this DAX device is currently consumed by the kernel as system RAM, not directly available for `mmap` by user applications.

### Why convert to DAX mode?

While automatic NUMA provisioning of CXL memory simplifies its integration, some applications are designed to directly interact with DAX devices. This often involves:

-   **Direct Memory Access (DMA):** Applications might want to bypass the kernel's memory management to gain fine-grained control over memory allocation and access patterns.
-   **Persistent Memory Awareness:** If the CXL memory is also persistent memory, applications might leverage DAX mode to ensure data persistence across reboots.
-   **Custom Memory Allocation:** Some high-performance applications implement their own memory allocators optimized for specific memory hierarchies or access patterns, directly utilizing DAX devices.

To enable these use cases, we need to convert the CXL memory from its `system-ram` mode back to a `dax` mode, making the `/dev/daxX.Y` character device directly accessible for `open()` and `mmap()` operations.

### Step-by-Step Procedure to Convert to DAX Mode

The conversion process involves using the `ndctl` and `cxl` utilities.

**Important Note:** Modifying CXL device configurations can impact system stability if not done carefully. It is highly recommended to perform these steps on a test system first and ensure you understand the implications for your specific workload. This procedure will take the CXL memory offline temporarily. If pages are already allocated on the CXL memory (e.g., if `numastat` shows activity on node 2), the conversion process may encounter "Device or resource busy" errors. **Rebooting the host typically resolves this problem by ensuring the memory is unallocated.**

**1. Identify the CXL Memory Device and Region:**

From the `cxl list` output, identify the `memdev` and its corresponding `region`. In our example, the `memdev` is `mem0` and the `region` is `region9`.

```bash
$ cxl list
...
    "memdevs":[
      {
        "memdev":"mem0",
        "numa_node":1,
        ...
      }
    ]
  },
  {
    "regions":[
      {
        "region":"region9",
        "type":"ram",
        ...
      }
    ]
  }
...

```

From `daxctl list`, we confirm the `chardev` is `dax9.0`, which corresponds to `region9`.

```
$ daxctl list
[
  {
    "chardev":"dax9.0",
    "size":137438953472,
    "target_node":2,
    "align":2097152,
    "mode":"system-ram"
  }
]
```

**2. Handle Potentially Allocated Memory (If Necessary):**

If you encounter "Device or resource busy" errors during the `daxctl reconfigure-device` step, it means the kernel or a process is actively using memory from the CXL NUMA node.

You can check `numastat` to see if there's any activity on the CXL NUMA node (e.g., `node2` in our example):

```bash
# numastat
                           node0           node1           node2
numa_hit                 3283017         1671398              98
numa_miss                      0               0               0
numa_foreign                   0               0               0
interleave_hit               427             428               0
local_node               3235994         1584796               0
other_node                 47023           86602              98
```

If `numa_hit` or `other_node` are non-zero for your CXL node, memory is in use.

To see if a specific process is using the memory:


```bash
sudo find /proc -maxdepth 2 -type f -regex '/proc/[0-9]+/numa_maps' -print | xargs grep "N2="
```

If this command finds no PIDs, it's likely the Kernel itself is using the memory.

**The most reliable workaround is to reboot the host.** To prevent the kernel from automatically bringing the CXL memory online as `system-ram` at boot time, add `memhp_default_state=offline` to your kernel command line. This still configures the memory as `system-ram` but keeps it offline, allowing for a smooth conversion to `devdax`.

To add this to your kernel command line:

-   **For GRUB-based systems:** Edit `/etc/default/grub`, add `memhp_default_state=offline` to the `GRUB_CMDLINE_LINUX_DEFAULT` variable, then run `sudo update-grub` and reboot.

Example `cat /proc/cmdline` after applying the option:

```bash
$ cat /proc/cmdline
BOOT_IMAGE=/vmlinuz-6.8.0-51-generic root=/dev/mapper/ubuntu--vg-ubuntu--lv ro memhp_default_state=offline
```

After rebooting with `memhp_default_state=offline`, `lsmem` should show the CXL memory range as `offline` from the start:

```bash
$ lsmem -o+ZONES,NODE
RANGE                                  SIZE   STATE REMOVABLE     BLOCK          ZONES NODE
0x0000000000000000-0x000000007fffffff    2G  online       yes         0           None    0
0x0000000100000000-0x000000807fffffff  510G  online       yes     2-256         Normal    0
0x0000008080000000-0x000000a07fffffff  128G offline             257-320 Normal/Movable    2
0x0000063e80000000-0x000006be7fffffff  512G  online       yes 3197-3452         Normal    1

Memory block size:         2G
Total online memory:       1T
Total offline memory:    128G
```

With the memory offline, you are now ready for the conversion.

**3. Convert the Region to `dax` Mode using `daxctl`:**

Instead of `cxl region create-dax` which works on a CXL region, when the DAX character device already exists and is in `system-ram` mode, we use `daxctl reconfigure-device`.


```bash
sudo daxctl reconfigure-device --mode devdax --force dax9.0
```

If you've followed the `memhp_default_state=offline` workaround, you might see output like:

```bash
dax0.0: all memory sections (64) already offline
[
  {
    "chardev":"dax0.0",
    "size":137438953472,
    "target_node":2,
    "align":2097152,
    "mode":"devdax"
  }
]
reconfigured 1 device
```

The `--force` option is useful in case of minor inconsistencies.

**4. Verify the Configuration:**

Now, let's verify the changes using `daxctl list` and `numactl -H`.

```bash
$ daxctl list
[
  {
    "chardev":"dax9.0",
    "size":137438953472,
    "target_node":-1,  # Should be -1 or no target_node, indicating not bound to a NUMA node
    "align":2097152,
    "mode":"devdax"    # Should now be "devdax"
  }
]
```

The `daxctl list` output should now show `mode:"devdax"`. The `target_node` might change to `-1` or disappear, indicating it's no longer managed as a NUMA node.

And for `numactl -H`:

```bash
$ numactl -H
available: 2 nodes (0-1)
node 0 cpus: ...
node 0 size: 515751 MB
node 0 free: 475572 MB
node 1 cpus: ...
node 1 size: 515992 MB
node 1 free: 470018 MB
node distances:
node   0   1
  0:  10  21
  1:  21  10
```

Notice that `node 2` (the CXL memory NUMA node) is no longer listed under `available` nodes. This confirms that the CXL memory is no longer presented as a kernel-managed NUMA node.

Now, your application can open and `mmap` `/dev/dax9.0` directly to interact with the CXL memory in DAX mode.

### Conclusion

While recent kernel releases simplify CXL.mem integration by automatically creating memory-only NUMA nodes, understanding how to switch to DAX mode is crucial for applications requiring direct memory access. By following these steps with `cxl` and `daxctl`, and addressing potential issues with memory allocation at boot time using `memhp_default_state=offline`, you can reconfigure your CXL memory devices to expose them as `/dev/daxX.Y` character devices, enabling powerful new use cases for CXL technology. Always exercise caution and test thoroughly when making changes to memory device configurations.
