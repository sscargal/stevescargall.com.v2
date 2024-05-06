---
title: "How To Map a CXL Endpoint to a CPU Socket in Linux"
date: "2022-12-27"
categories: 
  - "cxl"
  - "how-to"
  - "linux"
image: "images/PCI-Express-slots-on-motherboard.jpeg"
---

When working with CXL Type 3 Memory Expander endpoints, it's nice to know which CPU Socket owns the root complex for the endpoint. This is very useful for memory tiering solutions where we want to keep the execution of application processes and threads 'local' to the memory.

CXL memory expanders appear in Linux as memory-only or cpu-less NUMA Nodes. For example, NUMA nodes 2 & 3 do not have any CPUs assigned to them.

```
# numactl -H
available: 4 nodes (0-3)
node 0 cpus: 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 43 44 45 46 47 48 49 50 51 104 105 106 107 108 109 110 111 112 113 114 115 116 117 118 119 120 121 122 123 124 125 126 127 128 129 130 131 132 133 134 135 136 137 138 139 140 141 142 143 144 145 146 147 148 149 150 151 152 153 154 155
node 0 size: 64167 MB
node 0 free: 62245 MB
node 1 cpus: 52 53 54 55 56 57 58 59 60 61 62 63 64 65 66 67 68 69 70 71 72 73 74 75 76 77 78 79 80 81 82 83 84 85 86 87 88 89 90 91 92 93 94 95 96 97 98 99 100 101 102 103 156 157 158 159 160 161 162 163 164 165 166 167 168 169 170 171 172 173 174 175 176 177 178 179 180 181 182 183 184 185 186 187 188 189 190 191 192 193 194 195 196 197 198 199 200 201 202 203 204 205 206 207
node 1 size: 64472 MB
node 1 free: 61391 MB
node 2 cpus:
node 2 size: 65536 MB
node 2 free: 65535 MB
node 3 cpus:
node 3 size: 131072 MB
node 3 free: 131070 MB
node distances:
node   0   1   2   3 
  0:  10  21  14  24 
  1:  21  10  24  14 
  2:  14  24  10  26 
  3:  24  14  26  10 
```

In a [previous post](https://stevescargall.com/2019/07/09/how-to-extend-volatile-system-memory-ram-using-persistent-memory-on-linux/), I described how to use Persistent Memory to expand the main memory available to the system and showed a similar example. CXL memory expanders work similarly, however, they are physical devices on the PCIe bus, either locally attached to a physical PCIe slot or through a PCIe switch. The question becomes, which CPU has the ownership (root complex/port) for the endpoint? Have we successfully balanced the CXL devices across CPU sockets, or did we intentionally or accidentally put everything on the same CPU socket, which could lead to memory performance problems.

In this host, we have two physical CXL memory expansion devices (I intentionally removed the vendor information and replaced it with 'x')

```
# lspci | grep CXL 
38:00.0 CXL: xxxxxxxxxx Device c000 (rev 01)
b8:00.0 CXL: xxxxxxxxxx Device c000 (rev 01)
```

## Method 1 - Using the PCIe sysfs interface

If we examine each device through the sysfs interface, we can obtain the list of CPUs and primary NUMA Node, ie:

```
# cd /sys/devices/pci0000:38/0000:38:00.0
# cat numa_node 
0
# cat local_cpulist 
0-51,104-155

# cd /sys/devices/pci0000:b8/0000:b8:00.0
# cat numa_node 
1
# cat local_cpulist
52-103,156-207
```

## Method 2 - Using the CXL memdev sysfs interface

If the CXL device is managed by the `cxl_mem` driver, we can get the primary NUMA Node from that entry, but not the list of CPUs, eg:

```
# cat /sys/bus/cxl/devices/mem0/numa_node
0
# cat /sys/bus/cxl/devices/mem1/numa_node 
1
```

## Method 3 - Using lspci

Using the `lspci` utility to obtain the 'NUMA' information, eg:

```
# lspci -s 38:00.0 -vvv | grep -i numa
	NUMA node: 0
# lspci -s b8:00.0 -vvv | grep -i numa
	NUMA node: 1
```

The `lspci -t` command to show the tree doesn't show the root complex/port for each CPU.
