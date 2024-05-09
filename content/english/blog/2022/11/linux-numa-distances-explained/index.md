---
title: "Linux NUMA Distances Explained"
date: "2022-11-03"
categories: 
  - "cxl"
  - "how-to"
tags: 
  - "featured"
  - "numa"
image: "images/pexels-photo-2044443.jpeg"
author: Steve Scargall
---

**TL;DR:** The memory latency distances between a node and itself is normalized to 10 (1.0x). Every other distance is scaled relative to that 10 base value. For example, the distance between NUMA Node 0 and 1 is 21 (2.1x), meaning if node 0 accesses memory on node 1 or vice versa, the access latency will be 2.1x more than for local memory.

## Introduction

Non-Uniform Memory Access (NUMA) is a multiprocessor model in which each processor is connected to dedicated memory but may access memory attached to other processors in the system. To date, we've commonly used DRAM for main memory, but next-gen platforms will begin offering High-Bandwidth Memory (HBM) and Compute Express Link (CXL) attached memory. Accessing remote (to the CPU) memory takes much longer than accessing local memory, and not all remote memory has the same access latency. Depending on how the memory architecture is configured, NUMA nodes can be multiple hops away with each hop adding more latency. HBM and CXL devices will appear as memory-only (CPU-less) NUMA nodes.

## What are System Locality Information Tables (SLIT)?

System firmware provides ACPI SLIT tables, described in section 5.2.17 of the [ACPI 6.1 specification](https://uefi.org/sites/default/files/resources/ACPI_6_1.pdf), that describe the relative access latency differences between NUMA nodes. The Kernel reads the SLIT table at boot to build a map of NUMA memory latencies.

We can view this information with `numactl`. The following shows a dual-socket system with locally attached DDR memory.

```bash
# numactl -H
available: 2 nodes (0-1)
node 0 cpus: 0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 43 44 45 46 47 48 49 50 51 104 105 106 107 108 109 110 111 112 113 114 115 116 117 118 119 120 121 122 123 124 125 126 127 128 129 130 131 132 133 134 135 136 137 138 139 140 141 142 143 144 145 146 147 148 149 150 151 152 153 154 155
node 0 size: 64207 MB
node 0 free: 58582 MB
node 1 cpus: 52 53 54 55 56 57 58 59 60 61 62 63 64 65 66 67 68 69 70 71 72 73 74 75 76 77 78 79 80 81 82 83 84 85 86 87 88 89 90 91 92 93 94 95 96 97 98 99 100 101 102 103 156 157 158 159 160 161 162 163 164 165 166 167 168 169 170 171 172 173 174 175 176 177 178 179 180 181 182 183 184 185 186 187 188 189 190 191 192 193 194 195 196 197 198 199 200 201 202 203 204 205 206 207
node 1 size: 64434 MB
node 1 free: 61697 MB
node distances:
node   0   1 
  0:  10  21 
  1:  21  10 
```

We can also view the node distance tables directly through sysfs:

```bash
# cat /sys/devices/system/node/node*/distance
10 21
21 10
```

If we look at [distance.c](https://github.com/numactl/numactl/blob/master/distance.c) for [numactl](https://github.com/numactl/numactl), we see it opens and reads the sysfs tables:

```bash
static int read_distance_table(void)
{
	[... snip ...]
	for (nd = 0;; nd++) {
		char fn[100];
		FILE *dfh;
		sprintf(fn, "/sys/devices/system/node/node%d/distance", nd);
         [.. snip ...]
```

Installing acpia-tools provides the `acpidump` utility that we can use to see detailed ACPI table information

```bash
# dnf install -y acpica-tools
# which acpidump
/usr/bin/acpidump

# acpidump > acpidata.dat
# acpixtract -sSLIT acpidata.dat 

Intel ACPI Component Architecture
ACPI Binary Table Extraction Utility version 20220331
Copyright (c) 2000 - 2022 Intel Corporation

  SLIT - 60 bytes written (0x0000003C) - slit.dat

# iasl -d slit.dat 

Intel ACPI Component Architecture
ASL+ Optimizing Compiler/Disassembler version 20220331
Copyright (c) 2000 - 2022 Intel Corporation

File appears to be binary: found 32 non-ASCII characters, disassembling
Binary file appears to be a valid ACPI table, disassembling
Input file slit.dat, Length 0x3C (60) bytes
ACPI: SLIT 0x0000000000000000 00003C (v01 INTEL  INTEL ID 00000002 INTL 01000013)
Acpi Data Table [SLIT] decoded
Formatted output:  slit.dsl - 1498 bytes

# cat slit.dsl 
/*
 * Intel ACPI Component Architecture
 * AML/ASL+ Disassembler version 20220331 (64-bit version)
 * Copyright (c) 2000 - 2022 Intel Corporation
 * 
 * Disassembly of slit.dat, Thu Oct 27 16:38:09 2022
 *
 * ACPI Data Table [SLIT]
 *
 * Format: [HexOffset DecimalOffset ByteLength]  FieldName : FieldValue (in hex)
 */

[000h 0000   4]                    Signature : "SLIT"    [System Locality Information Table]
[004h 0004   4]                 Table Length : 0000003C
[008h 0008   1]                     Revision : 01
[009h 0009   1]                     Checksum : 53
[00Ah 0010   6]                       Oem ID : "INTEL "
[010h 0016   8]                 Oem Table ID : "INTEL ID"
[018h 0024   4]                 Oem Revision : 00000002
[01Ch 0028   4]              Asl Compiler ID : "INTL"
[020h 0032   4]        Asl Compiler Revision : 01000013

[024h 0036   8]                   Localities : 0000000000000004
[02Ch 0044   4]                 Locality   0 : 0A 15 0E 18
[030h 0048   4]                 Locality   1 : 15 0A 18 0E
[034h 0052   4]                 Locality   2 : 0E 18 0A 1A
[038h 0056   4]                 Locality   3 : 18 0E 1A 0A

Raw Table Data: Length 60 (0x3C)

    0000: 53 4C 49 54 3C 00 00 00 01 53 49 4E 54 45 4C 20  // SLIT<....SINTEL 
    0010: 49 4E 54 45 4C 20 49 44 02 00 00 00 49 4E 54 4C  // INTEL ID....INTL
    0020: 13 00 00 01 04 00 00 00 00 00 00 00 0A 15 0E 18  // ................
    0030: 15 0A 18 0E 0E 18 0A 1A 18 0E 1A 0A              // ............
```

These values are programmed by the firmware/BIOS. Linux only reads the values, it does not set them.

## Interpreting the Distance Table

The memory latency distances between a node and itself is normalized to 10 (1.0x), and every other distance is scaled relative to that 10 base value. In the above example, the distance between NUMA Node 0 and 1 is 21 (2.1x), meaning if node 0 accesses memory on node 1 or vice versa, the access latency will be 2.1x more than for local memory.

According to the AMD NUMA Topology documentation:

SLIT distances are derived as follows:

- The local node is 10.

- Nodes within a given partition are 11.

- Nodes in other partitions within the same socket are 12.

- Nodes in the other socket are 20 or 32

Possible values are from 0-254, where 254 is undefined/unknown.

## How the Kernel uses Distance Information?

The Kernel scheduler uses the distance information to execute application threads on CPU cores close(est) to the memory resident data. Values over 30 do not get scheduled tasks as they're deemed too slow.

## Are the SLIT values accurate?

To determine if the values in the SLIT tables are accurate, I ran [Intel MLC](https://www.intel.com/content/www/us/en/download/736633/736634/intel-memory-latency-checker-intel-mlc.html), which performs idle latency tests.

```bash
# ./mlc --latency_matrix
Intel(R) Memory Latency Checker - v3.9a
Command line parameters: --latency_matrix 

Using buffer size of 2000.000MiB
Measuring idle latencies (in ns)...
		Numa node
Numa node	     0	     1	
       0	 108.2	 195.7	
       1	 195.7	 108.9	
```

As we can see from the results, the SLIT information is incorrect; where 195.7/108.2 = 1.81

## The Heterogeneous Memory Attribute Table (HMAT)

The Heterogeneous Memory Attribute Table (HMAT) table is newly defined in section 5.2.27 of the [ACPI 6.2](https://uefi.org/sites/default/files/resources/ACPI_6_2.pdf) specification. The HMAT table, in conjunction with the existing System Resource Affinity Table (SRAT), provides users with information about memory initiators and memory targets in the system. A “memory initiator” in this case is any device such as a CPU or a separate memory I/O device that can initiate a memory request. A “memory target” is a CPU-accessible physical address range. The HMAT provides performance information (expected latency and bandwidth, etc.) for various (initiator,target) pairs. This is mostly motivated by the need to optimally use performance-differentiated memory such as DRAM, PMem, or CXL.

Examining the HMAT tables follows the same process as viewing the raw SLIT tables, as shown above.

```bash
# acpidump > acpidata.dat
# acpixtract -sHMAT acpidata.dat

Intel ACPI Component Architecture
ACPI Binary Table Extraction Utility version 20220331
Copyright (c) 2000 - 2022 Intel Corporation

  HMAT - 488 bytes written (0x000001E8) - hmat.dat

# iasl -d hmat.dat

Intel ACPI Component Architecture
ASL+ Optimizing Compiler/Disassembler version 20220331
Copyright (c) 2000 - 2022 Intel Corporation

File appears to be binary: found 442 non-ASCII characters, disassembling
Binary file appears to be a valid ACPI table, disassembling
Input file hmat.dat, Length 0x1E8 (488) bytes
ACPI: HMAT 0x0000000000000000 0001E8 (v02 INTEL  INTEL ID 00000002 INTL 01000013)
Acpi Data Table [HMAT] decoded
Formatted output:  hmat.dsl - 12209 bytes

# cat hmat.dsl 
/*
 * Intel ACPI Component Architecture
 * AML/ASL+ Disassembler version 20220331 (64-bit version)
 * Copyright (c) 2000 - 2022 Intel Corporation
 * 
 * Disassembly of hmat.dat, Thu Nov  3 14:21:43 2022
 *
 * ACPI Data Table [HMAT]
 *
 * Format: [HexOffset DecimalOffset ByteLength]  FieldName : FieldValue (in hex)
 */

[000h 0000   4]                    Signature : "HMAT"    [Heterogeneous Memory Attributes Table]
[004h 0004   4]                 Table Length : 000001E8
[008h 0008   1]                     Revision : 02
[009h 0009   1]                     Checksum : 9A
[00Ah 0010   6]                       Oem ID : "INTEL "
[010h 0016   8]                 Oem Table ID : "INTEL ID"
[018h 0024   4]                 Oem Revision : 00000002
[01Ch 0028   4]              Asl Compiler ID : "INTL"
[020h 0032   4]        Asl Compiler Revision : 01000013

[024h 0036   4]                     Reserved : 00000000

[028h 0040   2]               Structure Type : 0000 [Memory Proximity Domain Attributes]
[02Ah 0042   2]                     Reserved : 0000
[02Ch 0044   4]                       Length : 00000028
[030h 0048   2]        Flags (decoded below) : 0001
            Processor Proximity Domain Valid : 1
[032h 0050   2]                    Reserved1 : 0000
[034h 0052   4] Attached Initiator Proximity Domain : 00000000
[038h 0056   4]      Memory Proximity Domain : 00000000
[03Ch 0060   4]                    Reserved2 : 00000000
[040h 0064   8]                    Reserved3 : 0000000000000000
[048h 0072   8]                    Reserved4 : 0000000000000000

[050h 0080   2]               Structure Type : 0000 [Memory Proximity Domain Attributes]
[052h 0082   2]                     Reserved : 0000
[054h 0084   4]                       Length : 00000028
[058h 0088   2]        Flags (decoded below) : 0001
            Processor Proximity Domain Valid : 1
[05Ah 0090   2]                    Reserved1 : 0000
[05Ch 0092   4] Attached Initiator Proximity Domain : 00000001
[060h 0096   4]      Memory Proximity Domain : 00000001
[064h 0100   4]                    Reserved2 : 00000000
[068h 0104   8]                    Reserved3 : 0000000000000000
[070h 0112   8]                    Reserved4 : 0000000000000000

[078h 0120   2]               Structure Type : 0000 [Memory Proximity Domain Attributes]
[07Ah 0122   2]                     Reserved : 0000
[07Ch 0124   4]                       Length : 00000028
[080h 0128   2]        Flags (decoded below) : 0000
            Processor Proximity Domain Valid : 0
[082h 0130   2]                    Reserved1 : 0000
[084h 0132   4] Attached Initiator Proximity Domain : 00000000
[088h 0136   4]      Memory Proximity Domain : 00000002
[08Ch 0140   4]                    Reserved2 : 00000000
[090h 0144   8]                    Reserved3 : 0000000000000000
[098h 0152   8]                    Reserved4 : 0000000000000000

[0A0h 0160   2]               Structure Type : 0000 [Memory Proximity Domain Attributes]
[0A2h 0162   2]                     Reserved : 0000
[0A4h 0164   4]                       Length : 00000028
[0A8h 0168   2]        Flags (decoded below) : 0000
            Processor Proximity Domain Valid : 0
[0AAh 0170   2]                    Reserved1 : 0000
[0ACh 0172   4] Attached Initiator Proximity Domain : 00000000
[0B0h 0176   4]      Memory Proximity Domain : 00000003
[0B4h 0180   4]                    Reserved2 : 00000000
[0B8h 0184   8]                    Reserved3 : 0000000000000000
[0C0h 0192   8]                    Reserved4 : 0000000000000000

[0C8h 0200   2]               Structure Type : 0001 [System Locality Latency and Bandwidth Information]
[0CAh 0202   2]                     Reserved : 0000
[0CCh 0204   4]                       Length : 00000048
[0D0h 0208   1]        Flags (decoded below) : 00
                            Memory Hierarchy : 0
                   Use Minimum Transfer Size : 0
                    Non-sequential Transfers : 0
[0D1h 0209   1]                    Data Type : 01
[0D2h 0210   1]        Minimum Transfer Size : 00
[0D3h 0211   1]                    Reserved1 : 00
[0D4h 0212   4] Initiator Proximity Domains # : 00000002
[0D8h 0216   4]   Target Proximity Domains # : 00000004
[0DCh 0220   4]                    Reserved2 : 00000000
[0E0h 0224   8]              Entry Base Unit : 0000000000000064
[0E8h 0232   4] Initiator Proximity Domain List : 00000000
[0ECh 0236   4] Initiator Proximity Domain List : 00000001
[0F0h 0240   4] Target Proximity Domain List : 00000000
[0F4h 0244   4] Target Proximity Domain List : 00000001
[0F8h 0248   4] Target Proximity Domain List : 00000002
[0FCh 0252   4] Target Proximity Domain List : 00000003
[100h 0256   2]                        Entry : 038B
[102h 0258   2]                        Entry : 0680
[104h 0260   2]                        Entry : 03E8
[106h 0262   2]                        Entry : 06DD
[108h 0264   2]                        Entry : 0680
[10Ah 0266   2]                        Entry : 038B
[10Ch 0268   2]                        Entry : 06DD
[10Eh 0270   2]                        Entry : 03E8

[110h 0272   2]               Structure Type : 0001 [System Locality Latency and Bandwidth Information]
[112h 0274   2]                     Reserved : 0000
[114h 0276   4]                       Length : 00000048
[118h 0280   1]        Flags (decoded below) : 00
                            Memory Hierarchy : 0
                   Use Minimum Transfer Size : 0
                    Non-sequential Transfers : 0
[119h 0281   1]                    Data Type : 02
[11Ah 0282   1]        Minimum Transfer Size : 00
[11Bh 0283   1]                    Reserved1 : 00
[11Ch 0284   4] Initiator Proximity Domains # : 00000002
[120h 0288   4]   Target Proximity Domains # : 00000004
[124h 0292   4]                    Reserved2 : 00000000
[128h 0296   8]              Entry Base Unit : 0000000000000064
[130h 0304   4] Initiator Proximity Domain List : 00000000
[134h 0308   4] Initiator Proximity Domain List : 00000001
[138h 0312   4] Target Proximity Domain List : 00000000
[13Ch 0316   4] Target Proximity Domain List : 00000001
[140h 0320   4] Target Proximity Domain List : 00000002
[144h 0324   4] Target Proximity Domain List : 00000003
[148h 0328   2]                        Entry : 038B
[14Ah 0330   2]                        Entry : 0680
[14Ch 0332   2]                        Entry : 03E8
[14Eh 0334   2]                        Entry : 06DD
[150h 0336   2]                        Entry : 0680
[152h 0338   2]                        Entry : 038B
[154h 0340   2]                        Entry : 06DD
[156h 0342   2]                        Entry : 03E8

[158h 0344   2]               Structure Type : 0001 [System Locality Latency and Bandwidth Information]
[15Ah 0346   2]                     Reserved : 0000
[15Ch 0348   4]                       Length : 00000048
[160h 0352   1]        Flags (decoded below) : 00
                            Memory Hierarchy : 0
                   Use Minimum Transfer Size : 0
                    Non-sequential Transfers : 0
[161h 0353   1]                    Data Type : 04
[162h 0354   1]        Minimum Transfer Size : 00
[163h 0355   1]                    Reserved1 : 00
[164h 0356   4] Initiator Proximity Domains # : 00000002
[168h 0360   4]   Target Proximity Domains # : 00000004
[16Ch 0364   4]                    Reserved2 : 00000000
[170h 0368   8]              Entry Base Unit : 0000000000000064
[178h 0376   4] Initiator Proximity Domain List : 00000000
[17Ch 0380   4] Initiator Proximity Domain List : 00000001
[180h 0384   4] Target Proximity Domain List : 00000000
[184h 0388   4] Target Proximity Domain List : 00000001
[188h 0392   4] Target Proximity Domain List : 00000002
[18Ch 0396   4] Target Proximity Domain List : 00000003
[190h 0400   2]                        Entry : 0A3D
[192h 0402   2]                        Entry : 04CD
[194h 0404   2]                        Entry : 012C
[196h 0406   2]                        Entry : 012C
[198h 0408   2]                        Entry : 04CD
[19Ah 0410   2]                        Entry : 0A3D
[19Ch 0412   2]                        Entry : 012C
[19Eh 0414   2]                        Entry : 012C

[1A0h 0416   2]               Structure Type : 0001 [System Locality Latency and Bandwidth Information]
[1A2h 0418   2]                     Reserved : 0000
[1A4h 0420   4]                       Length : 00000048
[1A8h 0424   1]        Flags (decoded below) : 00
                            Memory Hierarchy : 0
                   Use Minimum Transfer Size : 0
                    Non-sequential Transfers : 0
[1A9h 0425   1]                    Data Type : 05
[1AAh 0426   1]        Minimum Transfer Size : 00
[1ABh 0427   1]                    Reserved1 : 00
[1ACh 0428   4] Initiator Proximity Domains # : 00000002
[1B0h 0432   4]   Target Proximity Domains # : 00000004
[1B4h 0436   4]                    Reserved2 : 00000000
[1B8h 0440   8]              Entry Base Unit : 0000000000000064
[1C0h 0448   4] Initiator Proximity Domain List : 00000000
[1C4h 0452   4] Initiator Proximity Domain List : 00000001
[1C8h 0456   4] Target Proximity Domain List : 00000000
[1CCh 0460   4] Target Proximity Domain List : 00000001
[1D0h 0464   4] Target Proximity Domain List : 00000002
[1D4h 0468   4] Target Proximity Domain List : 00000003
[1D8h 0472   2]                        Entry : 06E1
[1DAh 0474   2]                        Entry : 03D7
[1DCh 0476   2]                        Entry : 012C
[1DEh 0478   2]                        Entry : 012C
[1E0h 0480   2]                        Entry : 03D7
[1E2h 0482   2]                        Entry : 06E1
[1E4h 0484   2]                        Entry : 012C
[1E6h 0486   2]                        Entry : 012C

Raw Table Data: Length 488 (0x1E8)

    0000: 48 4D 41 54 E8 01 00 00 02 9A 49 4E 54 45 4C 20  // HMAT......INTEL 
    0010: 49 4E 54 45 4C 20 49 44 02 00 00 00 49 4E 54 4C  // INTEL ID....INTL
    0020: 13 00 00 01 00 00 00 00 00 00 00 00 28 00 00 00  // ............(...
    0030: 01 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00  // ................
    0040: 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00  // ................
    0050: 00 00 00 00 28 00 00 00 01 00 00 00 01 00 00 00  // ....(...........
    0060: 01 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00  // ................
    0070: 00 00 00 00 00 00 00 00 00 00 00 00 28 00 00 00  // ............(...
    0080: 00 00 00 00 00 00 00 00 02 00 00 00 00 00 00 00  // ................
    0090: 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00  // ................
    00A0: 00 00 00 00 28 00 00 00 00 00 00 00 00 00 00 00  // ....(...........
    00B0: 03 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00  // ................
    00C0: 00 00 00 00 00 00 00 00 01 00 00 00 48 00 00 00  // ............H...
    00D0: 00 01 00 00 02 00 00 00 04 00 00 00 00 00 00 00  // ................
    00E0: 64 00 00 00 00 00 00 00 00 00 00 00 01 00 00 00  // d...............
    00F0: 00 00 00 00 01 00 00 00 02 00 00 00 03 00 00 00  // ................
    0100: 8B 03 80 06 E8 03 DD 06 80 06 8B 03 DD 06 E8 03  // ................
    0110: 01 00 00 00 48 00 00 00 00 02 00 00 02 00 00 00  // ....H...........
    0120: 04 00 00 00 00 00 00 00 64 00 00 00 00 00 00 00  // ........d.......
    0130: 00 00 00 00 01 00 00 00 00 00 00 00 01 00 00 00  // ................
    0140: 02 00 00 00 03 00 00 00 8B 03 80 06 E8 03 DD 06  // ................
    0150: 80 06 8B 03 DD 06 E8 03 01 00 00 00 48 00 00 00  // ............H...
    0160: 00 04 00 00 02 00 00 00 04 00 00 00 00 00 00 00  // ................
    0170: 64 00 00 00 00 00 00 00 00 00 00 00 01 00 00 00  // d...............
    0180: 00 00 00 00 01 00 00 00 02 00 00 00 03 00 00 00  // ................
    0190: 3D 0A CD 04 2C 01 2C 01 CD 04 3D 0A 2C 01 2C 01  // =...,.,...=.,.,.
    01A0: 01 00 00 00 48 00 00 00 00 05 00 00 02 00 00 00  // ....H...........
    01B0: 04 00 00 00 00 00 00 00 64 00 00 00 00 00 00 00  // ........d.......
    01C0: 00 00 00 00 01 00 00 00 00 00 00 00 01 00 00 00  // ................
    01D0: 02 00 00 00 03 00 00 00 E1 06 D7 03 2C 01 2C 01  // ............,.,.
    01E0: D7 03 E1 06 2C 01 2C 01                          // ....,.,.
```

As of Linux Kernel 6.0, there is no sysfs interface to view the HMAT. This may become available in future releases. Patches to surface HMAT through sysfs were proposed several years ago [here](https://lwn.net/Articles/724562/) and [here](https://lwn.net/Articles/724562/).

You can find HMAT information in the boot logs, such as `dmesg`, that show somewhat more accurate values.

```bash
# dmesg | grep "acpi/hmat"
[    8.544245] acpi/hmat: HMAT: Memory Flags:0001 Processor Domain:0 Memory Domain:0
[    8.544248] acpi/hmat: HMAT: Memory Flags:0001 Processor Domain:1 Memory Domain:1
[    8.544250] acpi/hmat: HMAT: Memory Flags:0000 Processor Domain:0 Memory Domain:2
[    8.544251] acpi/hmat: HMAT: Memory Flags:0000 Processor Domain:0 Memory Domain:3
[    8.544252] acpi/hmat: HMAT: Locality: Flags:00 Type:Read Latency Initiator Domains:2 Target Domains:4 Base:100
[    8.544254] acpi/hmat:   Initiator-Target[0-0]:91 nsec
[    8.544255] acpi/hmat:   Initiator-Target[0-1]:167 nsec
[    8.544257] acpi/hmat:   Initiator-Target[0-2]:100 nsec
[    8.544257] acpi/hmat:   Initiator-Target[0-3]:176 nsec
[    8.544258] acpi/hmat:   Initiator-Target[1-0]:167 nsec
[    8.544259] acpi/hmat:   Initiator-Target[1-1]:91 nsec
[    8.544260] acpi/hmat:   Initiator-Target[1-2]:176 nsec
[    8.544261] acpi/hmat:   Initiator-Target[1-3]:100 nsec
[    8.544261] acpi/hmat: HMAT: Locality: Flags:00 Type:Write Latency Initiator Domains:2 Target Domains:4 Base:100
[    8.544263] acpi/hmat:   Initiator-Target[0-0]:91 nsec
[    8.544264] acpi/hmat:   Initiator-Target[0-1]:167 nsec
[    8.544264] acpi/hmat:   Initiator-Target[0-2]:100 nsec
[    8.544265] acpi/hmat:   Initiator-Target[0-3]:176 nsec
[    8.544266] acpi/hmat:   Initiator-Target[1-0]:167 nsec
[    8.544267] acpi/hmat:   Initiator-Target[1-1]:91 nsec
[    8.544267] acpi/hmat:   Initiator-Target[1-2]:176 nsec
[    8.544268] acpi/hmat:   Initiator-Target[1-3]:100 nsec
[    8.544269] acpi/hmat: HMAT: Locality: Flags:00 Type:Read Bandwidth Initiator Domains:2 Target Domains:4 Base:100
[    8.544270] acpi/hmat:   Initiator-Target[0-0]:262100 MB/s
[    8.544271] acpi/hmat:   Initiator-Target[0-1]:122900 MB/s
[    8.544272] acpi/hmat:   Initiator-Target[0-2]:30000 MB/s
[    8.544272] acpi/hmat:   Initiator-Target[0-3]:30000 MB/s
[    8.544273] acpi/hmat:   Initiator-Target[1-0]:122900 MB/s
[    8.544274] acpi/hmat:   Initiator-Target[1-1]:262100 MB/s
[    8.544275] acpi/hmat:   Initiator-Target[1-2]:30000 MB/s
[    8.544275] acpi/hmat:   Initiator-Target[1-3]:30000 MB/s
[    8.544276] acpi/hmat: HMAT: Locality: Flags:00 Type:Write Bandwidth Initiator Domains:2 Target Domains:4 Base:100
[    8.544277] acpi/hmat:   Initiator-Target[0-0]:176100 MB/s
[    8.544278] acpi/hmat:   Initiator-Target[0-1]:98300 MB/s
[    8.544279] acpi/hmat:   Initiator-Target[0-2]:30000 MB/s
[    8.544279] acpi/hmat:   Initiator-Target[0-3]:30000 MB/s
[    8.544280] acpi/hmat:   Initiator-Target[1-0]:98300 MB/s
[    8.544281] acpi/hmat:   Initiator-Target[1-1]:176100 MB/s
[    8.544282] acpi/hmat:   Initiator-Target[1-2]:30000 MB/s
[    8.544283] acpi/hmat:   Initiator-Target[1-3]:30000 MB/s
```

## Summary

In this article, I show two ACPI tables for understanding the latency and bandwidth of different types of memory in a system. As systems enter the market that have different types of memory - HBM, DRAM, and CXL - this information can be used by the Kernel and NUMA-aware applications to make intelligent data placement or migration decisions.

## References:

- [AMD Socket SP3 Platform NUMA Topology for AMD Family 17h Models 30h–3Fh](https://developer.amd.com/wp-content/resources/56338_1.00_pub.pdf)

- [Linux Kernel ACPI Drivers (SRAT & HMAT)](https://github.com/torvalds/linux/tree/master/drivers/acpi/numa)

- [ACPI 6.4 Spec](https://uefi.org/htmlspecs/ACPI_Spec_6_4_html/index.html) (HTML Version)
