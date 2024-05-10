---
title: "Enabling Linux Kernel Tiering with Compute Express Link (CXL) Memory"
meta_title: ""
description: ""
date: 2024-05-09T00:00:00Z
image: "linux_terminal_prompt.png"
categories: ["CXL"]
author: "Steve Scargall"
tags: ["CXL", "Compute Express Link", "Linux", "Kernel"]
draft: false
---

In this blog post, we will walk through the process of enabling the Linux Kernel Transparent Page Placement (TPP) feature with CXL memory mapped as NUMA nodes using the system-ram namespace. This feature allows the kernel to automatically place pages in different types of memory based on their usage patterns.

**Prerequisites**

This guide assumes that you are using a Fedora 36 system with Kernel 5.19.13, and that your system has a Samsung CXL device installed. You can confirm the presence of the CXL device with the following command:

```bash
lspci | grep CXL
```

**Step 1: Verify Automatic Memory Onlining**

First, we need to verify if the OS automatically onlines memory. This can be done with the following command:

```bash
grep CONFIG_MEMORY_HOTPLUG_DEFAULT_ONLINE /boot/config-$(uname -r)
```

If the output is CONFIG_MEMORY_HOTPLUG_DEFAULT_ONLINE=y, then the OS is configured to automatically online memory.

**Step 2: Change the Default Memory Zone**

Next, we change the default memory zone when memory is onlined to ZONE_MOVABLE. This can be done with the following command:

```bash
sudo echo online_movable > /sys/devices/system/memory/auto_online_blocks
```

**Step 3: Convert the Namespace**

We then use daxctl to convert the namespace from devdax to system-ram for all CXL Devices. This can be done with the following command:

```bash
daxctl reconfigure-device --mode=system-ram --force all
```

**Step 4: Verify NUMA Output**

At this point, you should be able to see the single-CPU (NODE0) and Samsung CXL device (NODE1) in the NUMA output. You can check this with the following command:

```bash
numactl -H
```

**Step 5: Display Memory Blocks by NUMA Node and Zone**

You can display the memory blocks by NUMA node and Zone with the following command:

```bash
lsmem -o +NODE,ZONES
```

**Step 6: Enable Kernel Transparent Page Placement (TPP)**

Finally, we can enable Kernel Transparent Page Placement (TPP). First, check the default setting for page demotions:

```bash
cat /sys/kernel/mm/numa/demotion_enabled
```

If the output is false, enable it with the following command:

```bash
echo true > /sys/kernel/mm/numa/demotion_enabled
```

Then, enable promotions:

```bash
echo 2 > /proc/sys/kernel/numa_balancing
```

Lastly, do reclaim for each zone. This makes sure that demotion is run to maintain a minimum set of free pages in each NUMA node:

```bash
echo 1 > /proc/sys/vm/zone_reclaim_mode
```

And that’s it! You have now enabled the Linux Kernel Transparent Page Placement (TPP) feature with CXL memory mapped as NUMA nodes using the system-ram namespace.

Please note that this guide is based on a specific system configuration and may need to be adjusted based on your specific hardware and software setup. Always refer to the official documentation for the most accurate and up-to-date information.