+++
# Post Title - Auto-generated from the file name
title = "A Practical Guide to Identify Compute Express Link (CXL) Devices in Your Server"

# Post creation date
date = 2023-05-02T18:21:36Z

# Post is a Draft = True|False
draft = false

# Authors. Comma separated list, e.g. `["Bob Smith", "David Jones"]`.
authors = ["Steve Scargall"]

# Tags and categories
# For example, use `tags = []` for no tags, or the form `tags = ["A Tag", "Another Tag"]` for one or more tags.
tags = ["cxl"]
categories = ['how to', 'linux']

# Featured Image
image = 'server_featured_image_900x600-min.jpeg'

author = "Steve Scargall"

aliases = [
	"/blog/2023/05/02/a-practical-guide-to-identify-compute-express-link-cxl-devices-in-your-server/"
]
+++


In this article, we will provide four methods for identifying CXL devices in your server and how to determine which CPU socket and NUMA node each CXL device is connected.  We will use CXL memory expansion (CXL.mem) devices for this article. The server was running Ubuntu 22.04.2 (Jammy Jellyfish) with Kernel 6.3 and '[cxl-cli](https://github.com/pmem/ndctl)' version 75 built from source code. Many of the procedures will work on Kernel versions 5.16 or newer.

## How to identify CXL devices in your server using PCI enumeration and CXL device class codes

CXL devices are built on the serial PCI Express (PCIe) physical and electrical interface and include PCIe-based block input/output protocol (CXL.io) and new cache-coherent protocols for accessing system memory (CXL.cache) and device memory (CXL.mem). Therefore, you can use PCI enumeration to identify CXL devices in your server.

CXL devices are available in different form factors - commonly, E3.S or Add-in Card (AIC) - and can be installed physically within the host or externally via a CXL fabric device such as a Just a Bunch of Memory (JBOM) or an intelligent CXL memory appliance. 

PCI enumeration is the process of detecting and assigning resources to PCI devices connected to the system. You can use various Linux commands or tools to perform PCI enumeration, such as `lspci`, sysfs, or `cxl list`. 

### Method 1: Using 'lspci' to find CXL devices

For example, you can use the following command to list all the PCI devices in your system:

```bash
$ lspci | grep CXL
99:00.0 CXL: <Vendor> 0000
```

In this example, the CXL device bus:device.function is '99:00.0'. If you want more information for this specific device run:

```bash
$ lspci -s 99:00.0 -vvv
```

The "NUMA node" field reports which physical NUMA node the PCI/CXL device is attached to. For example, the following show the CXL device is on node 1:

```bash
# lspci -s 99:00.0 -vvv | grep "NUMA node"
NUMA node: 1
```

### Method 2: Using 'cxl list' to find CXL devices

Linux has a `cxl` command utility specifically designed to identify and manage CXL devices, though you will need to install the package. Read the `cxl-list(1)` man page or run `cxl list --help` to understand the usage and arguments. Early versions of the cxl utility had limited functionality as they supported older Kernel versions with limited CXL functionality. 

The following `cxl list -vvv` output shows very verbose information. The output also shows `"numa_node":1` to indicate this memory device (CXL Device) is attached to NUMA Node 1.

```bash
./cxl list -vvv
[
	{
		"memdev":"mem0",
		"ram_size":137438953472,
		"health":{
			"maintenance_needed":false,
			"performance_degraded":false,
			"hw_replacement_needed":false,
			"media_normal":true,
			"media_not_ready":false,
			"media_persistence_lost":false,
			"media_data_lost":false,
			"media_powerloss_persistence_loss":false,
			"media_shutdown_persistence_loss":false,
			"media_persistence_loss_imminent":false,
			"media_powerloss_data_loss":false,
			"media_shutdown_data_loss":false,
			"media_data_loss_imminent":false,
			"ext_life_used":"normal",
			"ext_temperature":"normal",
			"ext_corrected_volatile":"normal",
			"ext_corrected_persistent":"normal",
			"life_used_percent":-95,
			"temperature":-95,
			"dirty_shutdowns":0,
			"volatile_errors":0,
			"pmem_errors":0
		},
		"alert_config":{
			"life_used_prog_warn_threshold_valid":true,
			"dev_over_temperature_prog_warn_threshold_valid":true,
			"dev_under_temperature_prog_warn_threshold_valid":true,
			"corrected_volatile_mem_err_prog_warn_threshold_valid":true,
			"corrected_pmem_err_prog_warn_threshold_valid":true,
			"life_used_prog_warn_threshold_writable":true,
			"dev_over_temperature_prog_warn_threshold_writable":true,
			"dev_under_temperature_prog_warn_threshold_writable":true,
			"corrected_volatile_mem_err_prog_warn_threshold_writable":true,
			"corrected_pmem_err_prog_warn_threshold_writable":true,
			"life_used_crit_alert_threshold":0,
			"life_used_prog_warn_threshold":0,
			"dev_over_temperature_crit_alert_threshold":0,
			"dev_under_temperature_crit_alert_threshold":0,
			"dev_over_temperature_prog_warn_threshold":0,
			"dev_under_temperature_prog_warn_threshold":0,
			"corrected_volatile_mem_err_prog_warn_threshold":0,
			"corrected_pmem_err_prog_warn_threshold":0
		},
		"serial":0,
		"numa_node":1,
		"host":"0000:99:00.0",
		"state":"disabled",
		"partition_info":{
			"total_size":137438953472,
			"volatile_only_size":137438953472,
			"persistent_only_size":0,
			"partition_alignment_size":0
		}
	}
]
```

### Method 3: Using sysfs

Both `lspci` and `cxl list` collect their data from sysfs (`/sys`). Using the bus:device.function identifier from `lspci` (0000:99.0), we can traverse the /sys file system to look at the information the Kernel and drivers expose.

```bash
# cd /sys/bus/pci/devices/0000:99:00.0
# ls
aer_dev_correctable
aer_dev_fatal
aer_dev_nonfatal
ari_enabled
broken_parity_status
class
config
consistent_dma_mask_bits
current_link_speed
current_link_width
d3cold_allowed
device
dma_mask_bits
driver
driver_override
enable
irq
link
local_cpulist
local_cpus
max_link_speed
max_link_width
mem0
modalias
msi_bus
msi_irqs
numa_node
power
power_state
remove
rescan
resource
resource0
resource2
resource2_wc
revision
subsystem
subsystem_device
subsystem_vendor
uevent
vendor
```

We won't go through each option. The focus here is to look at the contents of `numa_node`:

```bash
# cat numa_node
1
```

Another approach is to use the memory device (memdev), for example:

```bash
# cd /sys/bus/cxl/devices/mem0
# cat numa_node
1
```

### Mapping NUMA Node to a CPU Socket

Once you have identified the CXL devices and NUMA node in your server, we want to know which CPU socket the NUMA node is connected to. Use `lscpu` to collect the NUMA mappings:

```bash
# lscpu | grep NUMA
NUMA node(s):  3
NUMA node0 CPU(s): 0-31,64-95
NUMA node1 CPU(s): 32-63,96-127
NUMA node2 CPU(s):
```

Alternatively, use `numactl -H` to display the hardware structures:

```bash
available: 3 nodes (0-2)

node 0 cpus: 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 64 65 66 67 68 69 70 71 72 73 74 75 76 77 78 79 80 81 82 83 84 85 86 87 88 89 90 91 92 93 94 95
node 0 size: 1031618 MB
node 0 free: 1029690 MB
node 1 cpus: 32 33 34 35 36 37 38 39 40 41 42 43 44 45 46 47 48 49 50 51 52 53 54 55 56 57 58 59 60 61 62 63 96 97 98 99 100 101 102 103 104 105 106 107 108 109 110 111 112 113 114 115 116 117 118 119 120 121 122 123 124 125 126 127
node 1 size: 1032121 MB
node 1 free: 1028490 MB
node 2 cpus:
node 2 size: 32768 MB
node 2 free: 32768 MB
node distances:
node 0 1 2
0:  10  21  24
1:  21  10  14
2:  24  14  10
```

NUMA node 1 has CPUs 32-63 and 96-127. Using `lscpu --extended`, we can see these CPUs belong to socket 1:

```bash
# lscpu --extended | egrep -E "CPU|^ *32"
CPU NODE SOCKET CORE L1d:L1i:L2:L3 ONLINE  MAXMHZ MINMHZ MHZ
32 1  1 32 64:64:64:1 yes 4000.0000 800.0000 800.000
```

### Method 4: Using lstopo

The lstopo utility can be installed to provide a visual or hierarchical structure of your system. It's a more visual approach than what we demonstrated above. The following shows physical and logical devices in a tree-like output making it easy to identify PCI and CXL devices on each socket (package). The following example shows the CXL device is virtual NUMA node 2, which matches `numactl -H`, and belongs to CPU Socket (package) L#1 which also has NUMA node 1.

```bash
# lstopo-no-graphics --no-caches --no-icaches --no-useless-caches --no-smt | grep -v Core
Authorization required, but no authorization protocol specified
Machine (2047GB total)
	Package L#0
		NUMANode L#0 (P#0 1007GB) <-- DRAM
		HostBridge
			PCIBridge
				PCIBridge
					PCI 02:00.0 (VGA)
			PCI 00:17.0 (SATA)
				Block(Disk) "sdb"
				Block(Disk) "sda"
		HostBridge
			PCIBridge
				PCI 17:00.0 (Ethernet)
					Net "enp23s0f0"
				PCI 17:00.1 (Ethernet)
					Net "enp23s0f1"
				PCI 17:00.2 (Ethernet)
					Net "enp23s0f2"
				PCI 17:00.3 (Ethernet)
					Net "enp23s0f3"
		HostBridge
			PCI 76:00.0 (Co-Processor)
		HostBridge
			PCI 78:00.0 (Co-Processor)
	Package L#1
		NUMANode L#1 (P#1 1008GB) <-- DRAM
		NUMANode L#2 (P#2 32GB).  <-- CXL
		HostBridge
			PCIBridge
				PCI cf:00.0 (NVMExp)
					Block(Disk) "nvme0n1"
			PCIBridge
				PCI d0:00.0 (NVMExp)
					Block(Disk) "nvme1n1"
		HostBridge
			PCIBridge
				PCI e1:00.0 (NVMExp)
					Block(Disk) "nvme2n1"
		HostBridge
			PCI f3:00.0 (Co-Processor)
		HostBridge
			PCI f5:00.0 (Co-Processor)
```

## Conclusion

In this article, we have shown you how to identify CXL devices in your server using PCI enumeration and CXL device class codes, and how to determine which CPU socket and NUMA node each CXL device is connected to using several Linux commands or tools.

We hope that this article has been helpful for you to understand and work with CXL devices in your server. If you have any questions or feedback, please feel free to contact us.
