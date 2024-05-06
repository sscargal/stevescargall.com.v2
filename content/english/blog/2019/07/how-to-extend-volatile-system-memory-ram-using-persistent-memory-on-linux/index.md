---
title: "How To Extend Volatile System Memory (RAM) using Persistent Memory on Linux"
date: "2019-07-09"
categories: 
  - "how-to"
  - "linux"
tags: 
  - "daxctl"
  - "dram"
  - "kernel"
  - "ndctl"
  - "persistent-memory"
  - "pmem"
image: "images/pexels-photo-2588757.jpeg"
---

[Intel(R) Optane(TM) Persistent Memory](https://www.intel.com/content/www/us/en/architecture-and-technology/optane-dc-persistent-memory.html) delivers a unique combination of affordable large capacity and support for data persistence. Electrically compatible with DDR4, large capacity modules up to 512GB each can be installed in compatible servers alongside DDR on the memory bus.

Intel's persistent memory product can be provisioned in a volatile "Memory Mode" which replaces DRAM volatile capacity with the persistent memory capacity, and persistent "AppDirect" mode which presents both DRAM and persistent memory to the operating system and applications. Both modes are explained in more detail [here](https://itpeernetwork.intel.com/intel-optane-dc-persistent-memory-operating-modes/). It is possible to configure a system to utilize a percentage of persistent memory as volatile and persistent, but this mixed-mode still provisions all the DRAM capacity as a Last-Level Cache.

So what happens if you don't need all the persistent memory capacity to be persistent? What if you could save money on purchasing DRAM and instead replace some of the volatile DDR memory capacity with the cheaper persistent memory. Granted, the performance of persistent memory isn't quite that of DRAM, but in most cases, this may not matter. In Linux Kernel v5.1 and later you can have your cake and eat it thanks to this [patchset](https://lkml.org/lkml/2019/3/10/189). Background information can be found [here](https://patchwork.kernel.org/cover/10829019/) and [here](https://patchwork.kernel.org/patch/10829041/). Basically, we can now create a Direct Access (DAX) namespace and dynamically assign it as a volatile memory address space that the Kernel can use to extend the current DRAM capacity.

This idea isn't new. Several server vendors, such as Sun Microsystems (RIP), had the ability to dynamically assign and unassign CPUs and DRAM on demand. "Dynamic System RAM" is still very cool and extremely useful.

## Adding Persistent Memory as System-RAM/DRAM

Instructions in this [patchset](https://patchwork.kernel.org/patch/10829041/) indicate how you can manually bind and unbind memory from the kernel, but it doesn't describe how to create the DAX device or how to convert it to a "system-ram" device type. See below.

If you do not have access to a server with persistent memory, you can emulate persistent memory within KVM/QEMU using the instructions on [docs.pmem.io](https://docs.pmem.io/getting-started-guide/creating-development-environments/virtualization/qemu) to create a VM, then you can use the instructions in this [patchset](https://patchwork.kernel.org/cover/10829019/) to create the dax device and bind it to extend the DRAM capacity.

If you do have access to a system with persistent memory, you can use the following instructions which is much easier than manually fiddling around with Kernel variables.

Requirements:

- A Linux Distribution with Kernel v5.1 or later. We use Fedora 30 for the following walk through.

- ndctl and daxctl v65.0 or later with the 'kmem' feature.

1\. If ndctl/daxctl v65.0 or later is available in the Linux package repository for your distribution, install or update to the latest version using the package manager command (apt, dnf, rpm, yum, etc). Once installed, you can skip to Step 5. Otherwise, clone `ndctl` from GitHub and build it from source code using Steps 1-4:

```
$ mkdir /downloads
$ git clone https://github.com/pmem/ndctl
```

2\. Make sure you're using the 'master' branch.

```
$ git branch    <-- Use git branch -a to show all branches
* master
```

3\. Install the ndctl prerequisites. See the instructions [here](https://docs.pmem.io/getting-started-guide/installing-ndctl#installing-ndctl-from-source-on-linux) for more Linux distributions.

```
$ sudo dnf install git gcc gcc-c++ autoconf automake asciidoc asciidoctor xmlto libtool pkg-config glib2 glib2-devel libfabric libfabric-devel doxygen graphviz pandoc ncurses kmod kmod-devel libudev-devel libuuid-devel json-c-devel keyutils-libs-devel
```

4\. Configure and Build `ndctl` and `daxctl` within the current directory. If you want to install these binaries, I recommend a non-default location such as /opt rather than /usr/local to avoid conflicting or overwriting libraries and binaries that are delivered with your Linux package repository.

```
$ cd /downloads/ndctl 
$ ./autogen.sh
$ ./configure CFLAGS='-g -O2' --prefix=/opt/ndctl --sysconfdir=/etc --libdir=/opt/ndctl/lib64
$ make
$ sudo make install <--- optional
```

5\. For this example, we will create a 12GiB DAX namespace from the available capacity in Region0. To learn more about provisioning persistent memory [watch this webinar recording](https://software.intel.com/en-us/videos/provisioning-intel-optane-dc-persistent-memory-modules-in-linux).

```
$ sudo ndctl create-namespace --mode=dax --region=0 --size=12g
{
  "dev":"namespace0.1",
  "mode":"devdax",
  "map":"dev",
  "size":"11.81 GiB (12.68 GB)",
  "uuid":"328c2736-c538-4772-ae73-ba0338d49efb",
  "daxregion":{
    "id":0,
    "size":"11.81 GiB (12.68 GB)",
    "align":2097152,
    "devices":[
      {
        "chardev":"dax0.1",
        "size":"11.81 GiB (12.68 GB)"
      }
    ]
  },
  "align":2097152
}
```

Make a note of the 'chardev' as it will be required when we convert it to a 'system-ram' type. In this example, we just created a /dev/dax0.1 device.

6\. Check the current memory configuration and resources using your favorite tool(s) to get a before snapshot. Here, we use the `lsmem` command to show the current memory layout.

```
$ lsmem
RANGE                                  SIZE  STATE REMOVABLE   BLOCK
0x0000000000000000-0x000000007fffffff    2G online        no       0
0x0000000100000000-0x000000277fffffff  154G online       yes    2-78
0x0000002780000000-0x000000297fffffff    8G online        no   79-82
0x0000002980000000-0x0000002effffffff   22G online       yes   83-93
0x0000002f00000000-0x0000002fffffffff    4G online        no   94-95
0x000001aa80000000-0x000001d0ffffffff  154G online       yes 853-929
0x000001d100000000-0x000001d37fffffff   10G online        no 930-934
0x000001d380000000-0x000001d8ffffffff   22G online       yes 935-945
0x000001d900000000-0x000001d9ffffffff    4G online        no 946-947

Memory block size:         2G
Total online memory:     380G
Total offline memory:      0B
```

7\. Reconfigure the operational mode of a dax device

The `daxctl reconfigure-device` command can be used to convert a regular `devdax` mode device to a `system-ram` mode which allows for the dax range to be hot-plugged into the system as regular memory.

**NOTE 1:** This is a destructive operation. Any data on the dax device _will_ be lost.

**NOTE 2:** Device reconfiguration depends on the dax-bus device model. If dax-class is in use (via the dax\_pmem\_compat driver), the reconfiguration will fail. See `man daxctl-migrate-device-model` for more information.

We will use the previously created dax0.1 device and initially configure it in an 'offline' state such that the capacity is not automatically assigned to the DRAM capacity. You can provision it in one step, but I prefer this approach in case the conversion fails for some reason which makes it easier to undo the operation.

```
$ sudo daxctl reconfigure-device --mode=system-ram --no-online dax0.1
[
  {
    "chardev":"dax0.1",
    "size":12681478144,
    "target_node":2,
    "mode":"system-ram"
  }
]
reconfigured 1 device
```

Your Kernel doesn't support this feature if you see the following error.

```
# daxctl reconfigure-device --mode=system-ram --no-online dax0.0
libkmod: kmod_module_insert_module: could not find module by name='kmem'
libdaxctl: daxctl_insert_kmod_for_mode: dax0.0: insert failure: -2
error reconfiguring devices: No such file or directory
reconfigured 0 devices
```

Some Linux distributions, such as CentOS, may not enable the required 'device migration model' feature by default. This results in the following error:

```
# daxctl reconfigure-device --mode=system-ram --no-online dax0.0
libdaxctl: daxctl_dev_disable: dax0.0: error: device model is dax-class
libdaxctl: daxctl_dev_disable: dax0.0: see man daxctl-migrate-device-model
dax0.0: disable failed: Operation not supported
error reconfiguring devices: Operation not supported
reconfigured 0 devices
```

Do the following to resolve the issue:

```
// Enable the migrate device model daxctl support.
// Note: This does not take effect immediately!

# daxctl migrate-device-model
success: installed /etc/modprobe.d/daxctl.conf

// From the daxctl-migrate-device-model(1) man page:

       The modprobe policy established by this utility becomes effective after the next  reboot,  or  after  all  
       DAX  related modules have been removed and re-loaded with "udevadm trigger"

// Reload the udev rules and driver modules:

# lsmod | grep -i dax
dax_pmem_compat        16384  0
device_dax             20480  1 dax_pmem_compat
dax_pmem_core          16384  1 dax_pmem_compat

# udevadm trigger

# lsmod | grep -i dax
dax_pmem               16384  0
dax_pmem_compat        16384  0
device_dax             20480  1 dax_pmem_compat
dax_pmem_core          16384  2 dax_pmem,dax_pmem_compat

// Configure the device

# daxctl reconfigure-device --mode=system-ram --no-online dax0.0
[
  {
    "chardev":"dax0.0",
    "size":1598128390144,
    "target_node":2,
    "mode":"system-ram",
    "movable":false
  }
]
reconfigured 1 device

// If you still encounter the device model error, reboot and try this step again.
```

8\. Bring the new memory capacity online

We will use the `daxctl online-memory` command which is complementary to the `daxctl-reconfigure-device` command, when used with the `--no-online` option to skip onlining memory sections immediately after the  
reconfigure. In these scenarios, the memory can be onlined at a later time using the `daxctl-online-memory` command below.

```
$ sudo daxctl online-memory dax0.1
dax0.1: 5 sections already online
dax0.1: 0 new sections onlined
onlined memory for 1 device
```

9\. Verify the system volatile memory capacity has grown

```
$ lsmem
RANGE                                  SIZE  STATE REMOVABLE   BLOCK
0x0000000000000000-0x000000007fffffff    2G online        no       0
0x0000000100000000-0x000000277fffffff  154G online       yes    2-78
0x0000002780000000-0x000000297fffffff    8G online        no   79-82
0x0000002980000000-0x0000002effffffff   22G online       yes   83-93
0x0000002f00000000-0x0000002fffffffff    4G online        no   94-95
0x0000003380000000-0x00000035ffffffff   10G online       yes 103-107 <-- new
0x000001aa80000000-0x000001d0ffffffff  154G online       yes 853-929
0x000001d100000000-0x000001d37fffffff   10G online        no 930-934
0x000001d380000000-0x000001d8ffffffff   22G online       yes 935-945
0x000001d900000000-0x000001d9ffffffff    4G online        no 946-947

Memory block size:         2G
Total online memory:     390G  <-- was 380GB, now 390GB
Total offline memory:      0B
```

We didn't add all 12GB because the memory block size is 2GB and we used a small region within the dax for metadata, so we couldn't completely add the remaining ~1.9GB as a new block.

Looking at the hardware layout of the system NUMA nodes shows we have two new memory-only nodes (nodes 2 & 3):

```
# numactl -H
available: 4 nodes (0-3)
node 0 cpus: 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 48 49 50 51 52 53 54 55 56 57 58 59 60 61 62 63 64 65 66 67 68 69 70 71
node 0 size: 192115 MB
node 0 free: 164188 MB
node 1 cpus: 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 43 44 45 46 47 72 73 74 75 76 77 78 79 80 81 82 83 84 85 86 87 88 89 90 91 92 93 94 95
node 1 size: 192011 MB
node 1 free: 165112 MB
node 2 cpus:
node 2 size: 311296 MB
node 2 free: 311295 MB
node 3 cpus:
node 3 size: 321536 MB
node 3 free: 321534 MB
node distances:
node   0   1   2   3
  0:  10  21  17  28
  1:  21  10  28  17
  2:  17  28  10  28
  3:  28  17  28  10
```

Bingo! It's really quite easy and simple.

## Using DRAM and Persistent Memory

With the memory configured, there are several ways to utilize it. The simplest is to use the `numactl` utility to bind an application or process to it. For example, we can start a new process and bind it to specific CPU NUMA nodes and Memory NUMA Nodes that use only persistent memory:

```
numactl --cpunodebind=0-1 --membind=2 command [options]
```

Another way to use the memory is to use the Memkind Library in your application which can then determine where to allocate memory from - DRAM or PMem. There's a fantastic introduction to this topic at [https://pmem.io/2020/01/20/memkind-dax-kmem.html](https://pmem.io/2020/01/20/memkind-dax-kmem.html).

## Unassigning Memory

Assigning new memory is far easier than trying to unassign or deallocate it as even a single allocated byte can prevent you from deallocating previously allocated memory. Those challenges will no doubt be addressed if this feature becomes popular. It'll require memory copies and updating virtual memory address pointer to achieve it correctly. For now, you may have to stop the application or restart the system to fully tear things down if you can't do it dynamically.

1\. Offline the Memory

```
$ sudo daxctl offline-memory dax0.1
dax0.0: 62 sections offlined
offlined memory for 1 device
```

2\. Destroy the DAX Device

```
$ sudo ndctl list -N
[
  {
    "dev":"namespace0.1",
    "mode":"devdax",
    "map":"dev",
    "size":12681478144,
    "uuid":"328c2736-c538-4772-ae73-ba0338d49efb",
    "chardev":"dax0.1",
    "align":2097152
  },
  ...
$ sudo ndctl destroy-namespace namespace0.1
```

An example of what a failure looks like is:

```
$ sudo daxctl offline-memory dax0.1
libdaxctl: offline_one_memblock: dax0.1: Failed to offline /sys/devices/system/node/node2/memory107/state: Device or resource busy
dax0.1: unable to offline memory: Device or resource busy
error offlining memory: Device or resource busy
offlined memory for 0 devices
```

In this particular example, the reason for the failure is that the Kernel has already used the new memory for running processes:

```
# fuser -c /dev/dax0.1
/dev/dax0.1:             1   491rc  1588  1636  2209  2212  2250  2278  2279  2280  2282  2293  2294  2297  2299  2301  2303  2305  2320  2324  2328  2330  2331  2334  2336  2362  2364  2370  2374  2380  2433  2434  2604  2606  9892  9895 14262 22846 22847 22849 30785 30789
```

There is no current solution to stop new allocations to the DAX backed memory address range and migrate existing allocations to DRAM or another DAX backed address range.

Rebooting the system will assist in removing the DAX backed memory.
