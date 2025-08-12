---
title: "How to Build acpidump from Source and use it to Debug Complex CXL and PCI Issues"
meta_title: "Linux: Build ACPI Tools from Source"
description: "A step-by-step guide to building, installing, and using the latest acpidump and iasl tools from source on Linux, essential for working with and debugging ACPI tables like CXL."
date: 2025-08-11T00:00:00-06:00
image: "featured_image.webp"
categories: ["Linux", "CXL"]
author: "Steve Scargall"
tags: ["ACPI", "acpidump", "iasl", "ACPI-CA", "Linux", "Build from Source", "CXL", "Firmware"]
draft: false
aliases:
---

This article is a detailed guide on how to build the latest version of the `acpidump` tool from its source code. While many Linux distributions, like Ubuntu, offer a packaged version of this utility, it's often outdated. For developers and enthusiasts working with modern hardware features, particularly those related to Compute Express Link (CXL), having the most current version is essential.

Before you begin, it's important to remove any old, conflicting versions of the tools. If you have previously installed the `acpica-tools` package from your distribution's repository, you should remove it to prevent conflicts.

```
sudo apt remove acpica-tools
```

Now you're ready to build the latest version, which ensures you have the most up-to-date toolset.

## What is `acpidump`?

`acpidump` is a command-line utility that's part of the **ACPI Component Architecture (ACPI-CA)** toolset. Its primary function is to extract the **Advanced Configuration and Power Interface (ACPI)** tables from a running system's firmware (BIOS/UEFI) and save them to a file. ACPI tables contain crucial information about the system's hardware, including its power management features, device configuration, and other platform-specific details. The `acpidump` utility provides a way to inspect these tables, which is invaluable for debugging and understanding how the operating system interacts with the platform firmware.

## Building and Installing `acpidump` from Source Code

The packaged version of `acpidump` on many Linux distributions, such as the one from `acpica-tools` on Ubuntu, is often several years old. To access the latest features and bug fixes, especially those related to newer technologies like CXL, you need to **build `acpidump` from source**.

### Prerequisites

First, ensure you have the necessary build tools installed. For an Ubuntu system, you can install them with the following command:

```
sudo apt install git build-essential
```

- **`git`**: Used to clone the source code repository from GitHub.
- **`build-essential`**: A meta-package that includes essential development tools like `gcc`, `g++`, and `make`.

### Step 1: Clone the ACPICA Repository

Use `git` to clone the official ACPICA repository from GitHub. This will download the entire source code to your machine.

```
git clone https://github.com/acpica/acpica
```

### Step 2: Navigate to the Source Directory

After cloning, a new directory named `acpica` will be created. Change into this directory to start the build and installation process.

```
cd acpica
```

### Step 3: Build and Install the Tools

The ACPICA repository includes a simple build system. To compile all the tools, including `acpidump` and `iasl`, you just need to run `make`. After the compilation is complete, you can install the binaries to a system directory using `make install`.

You can install the binaries to the default system locations (e.g., `/usr/local/bin`) with this command:

```
sudo make install
```

Alternatively, to avoid conflicts with your system's package manager, you can install the binaries to a custom location, such as `/opt`. This is a great practice for keeping your system clean.

```
sudo make install PREFIX=/opt
```

### Step 4: Verify the Installation

To confirm that you have successfully installed the latest version, run the newly installed `acpidump` tool and check its version.

```
acpidump -vd
```

The output should show a recent build date, confirming you are using the latest version from the source. For example:

```
$ acpidump -vd

Intel ACPI Component Architecture
ACPI Binary Table Dump Utility version 20250807
Copyright (c) 2000 - 2025 Intel Corporation

Build date/time: Aug 11 2025 23:47:07
```

## Using the New `acpidump` and `iasl` Tools

Now that you have the latest versions of the ACPICA tools installed, you can use them to extract and decode ACPI tables.

### Step 1: Dump ACPI Tables to a File

To capture all the ACPI tables on your system, you need to run `acpidump` with root privileges. The output is redirected to a file, which we'll name `acpi.dump`.

```
sudo acpidump > acpi.dump
```

### Step 2: List the Tables in the Dump File

The `acpixtract` utility can be used to extract binary ACPI tables from the `acpi.dump` file. The following command lists the available tables and their signatures within the `acpi.dump` file.

```
acpixtract -l acpi.dump
```

The output will be a list of all the ACPI tables, including their signatures (e.g., `DSDT`, `SSDT`, `CEDT`), length, and other metadata.

**Example:**

```bash
$ acpixtract -l acpi.dump

Intel ACPI Component Architecture
ACPI Binary Table Extraction Utility version 20250807
Copyright (c) 2000 - 2025 Intel Corporation

 Signature  Length    Version Oem       Oem         Oem         Compiler Compiler
                              Id        TableId     RevisionId  Name     Revision
 _________  __________  ____  ________  __________  __________  _______  __________
 01)  IRDT  0x0000066C  0x01  "INTEL "  "INTEL ID"  0x00000002  "INTL"   0x20230628
 02)  SSDT  0x0000031C  0x02  "INTEL "  "INTEL ID"  0x00000000  "MSFT"   0x20230628
 03)  SPCR  0x00000050  0x02  "INTEL "  "INTEL ID"  0x00000000  "INTL"   0x20230628
 04)  MCFG  0x0000003C  0x01  "INTEL "  "INTEL ID"  0x00000001  "INTL"   0x20230628
 05)  PMTT  0x00001368  0x02  "INTEL "  "INTEL ID"  0x00000001  "INTL"   0x20230628
 06)  PRMT  0x0000018A  0x00  "INTEL "  "INTEL ID"  0x00000002  "INTL"   0x20230628
 07)  APIC  0x0000105E  0x06  "INTEL "  "INTEL ID"  0x00000000  "INTL"   0x20230628
 08)  SSDT  0x00000145  0x02  "INTEL "  "PRMSAMPL"  0x00001000  "INTL"   0x20230628
 09)  HMAT  0x000007E0  0x02  "INTEL "  "INTEL ID"  0x00000002  "INTL"   0x20230628
 10)  TPM2  0x0000004C  0x04  "INTEL "  "INTEL ID"  0x00000002  "INTL"   0x20230628
 11)  CEDT  0x00000444  0x01  "INTEL "  "INTEL ID"  0x00000002  "INTL"   0x20230628
 12)  SLIT  0x000000D5  0x01  "INTEL "  "INTEL ID"  0x00000002  "INTL"   0x20230628
 13)  OEM1  0x00439069  0x02  "INTEL "  "CPU EIST"  0x00003000  "INTL"   0x20230628
 14)  SSDT  0x00000632  0x02  "INTEL "  "Tpm2Tabl"  0x00001000  "INTL"   0x20230628
 15)  MSCT  0x00000248  0x01  "INTEL "  "INTEL ID"  0x00000001  "INTL"   0x20230628
 16)  ERST  0x00000230  0x01  "INTEL "  "INTEL ID"  0x00000001  "INTL"   0x00000001
 17)  DSDT  0x0009A588  0x02  "INTEL "  "INTEL ID"  0x00000003  "INTL"   0x20230628
 18)  SSDT  0x00000397  0x02  "INTEL "  "SstsTbl "  0x00001000  "INTL"   0x20230628
 19)  SRAT  0x00014220  0x03  "INTEL "  "INTEL ID"  0x00000002  "INTL"   0x20230628
 20)  WSMT  0x00000028  0x01  "INTEL "  "INTEL ID"  0x00000000  "INTL"   0x20230628
 21)  SSDT  0x000007FC  0x02  "INTEL "  "RAS_ACPI"  0x00000001  "INTL"   0x20230628
 22)  DBG2  0x0000005C  0x00  "INTEL "  "INTEL ID"  0x00000002  "INTL"   0x20230628
 23)  HEST  0x00000174  0x01  "INTEL "  "INTEL ID"  0x00000001  "INTL"   0x00000001
 24)  KEYP  0x0000006C  0x01  "INTEL "  "INTEL ID"  0x00000002  "INTL"   0x20230628
 25)  SSDT  0x0000026C  0x02  "INTEL "  "XHCI_BHS"  0x00000000  "INTL"   0x20230628
 26)  BERT  0x00000030  0x01  "INTEL "  "INTEL ID"  0x00000001  "INTL"   0x00000001
 27)  SSDT  0x00000041  0x02  "INTEL "  "INTEL ID"  0x00000002  "INTL"   0x20230628
 28)  OEM4  0x002D1041  0x02  "INTEL "  "CPU  CST"  0x00003000  "INTL"   0x20230628
 29)  DMAR  0x000008B0  0x01  "INTEL "  "INTEL ID"  0x00000001  "INTL"   0x20230628
 30)  FACP  0x00000114  0x06  "INTEL "  "INTEL ID"  0x00000000  "INTL"   0x20230628
 31)  FPDT  0x00000044  0x01  "INTEL "  "EDK2    "  0x00000002  "    "   0x01000013
 32)  SSDT  0x00000156  0x02  "INTEL "  "PRMOPREG"  0x00001000  "INTL"   0x20230628
 33)  OEM2  0x00118031  0x02  "INTEL "  "CPU  HWP"  0x00003000  "INTL"   0x20230628
 34)  SSDT  0x000008BB  0x02  "INTEL "  "ADDRXLAT"  0x00000001  "INTL"   0x20230628
 35)  HPET  0x00000038  0x01  "INTEL "  "INTEL ID"  0x00000001  "INTL"   0x20230628
 36)  BDAT  0x00000030  0x01  "INTEL "  "INTEL ID"  0x00000000  "INTL"   0x20230628
 37)  SSDT  0x0000040F  0x02  "INTEL "  "SruTable"  0x00001000  "INTL"   0x20230628
 38)  FACS  0x00000040  0x02
 39)  SSDT  0x00197850  0x02  "INTEL "  "SSDT  PM"  0x00004000  "INTL"   0x20230628

Found 39 ACPI tables in acpi.dump
```

The column headings in the `acpixtract -l acpi.dump` output provides metadata for each ACPI table found in the dump file. Here is a breakdown of what each column represents:

- **Signature**: A 4-character ASCII string that uniquely identifies the type of ACPI table. For example, `DSDT` (Differentiated System Description Table), `SSDT` (Secondary System Description Table), or `CEDT` (CXL Early Discovery Table).
- **Length**: The total size of the ACPI table in bytes, displayed in hexadecimal format.
- **Version**: The revision of the ACPI table specification that the table conforms to.
- **Oem Id**: A 6-character ASCII string identifying the Original Equipment Manufacturer (OEM) of the platform, typically a vendor like "INTEL ".
- **Oem TableId**: An 8-character ASCII string, defined by the OEM, to uniquely identify the specific table within their platform.
- **Oem RevisionId**: An OEM-specific revision number for the table. This value is used to track changes made by the OEM to the table's contents.
- **Compiler Name**: A 4-character ASCII string that identifies the name of the ACPI compiler used to generate the table, such as "INTL" for Intel.
- **Compiler Revision**: The revision number of the compiler that produced the table. This is often a date or version number in hexadecimal format.

See [Appendix A](#appendix-a) for an explanation of each table signature in the above output.

### Step 3: Extract and Decode a Specific Table

Let's say you're interested in a specific table, like the **CXL Early Discovery Table (CEDT)**, which is crucial for systems with CXL technology. You can extract it using the table's signature and then decode it with `iasl`.

#### Extract the Table

Use `acpixtract` with the `-s` flag to specify the table signature you want to extract.

```
acpixtract -sCEDT acpi.dump
```

This command will create a file named `cedt.dat` containing the raw binary data of the CEDT table.

Example:

```bash
$ acpixtract -sCEDT acpi.dump

Intel ACPI Component Architecture
ACPI Binary Table Extraction Utility version 20250807
Copyright (c) 2000 - 2025 Intel Corporation

 CEDT -  1092 bytes written (0x00000444) - cedt.dat
```

#### Decode the Table

Now, use the `iasl` (ACPI Source Language) compiler/decompiler to convert the binary `cedt.dat` file into a human-readable **ACPI Source Language (ASL)** file.

```
iasl -d cedt.dat
```

This will generate a file named `cedt.dsl`, which contains the decoded, human-readable contents of the table.

**Example**

```bash
$ iasl -d cedt.dat

Intel ACPI Component Architecture
ASL+ Optimizing Compiler/Disassembler version 20250807
Copyright (c) 2000 - 2025 Intel Corporation

File appears to be binary: found 978 non-ASCII characters, disassembling
Binary file appears to be a valid ACPI table, disassembling
Input file cedt.dat, Length 0x444 (1092) bytes
ACPI: CEDT 0x0000000000000000 000444 (v01 INTEL INTEL ID 00000002 INTL 20230628)
Acpi Data Table [CEDT] decoded
Formatted output: cedt.dsl - 24730 bytes
```

#### View the Decoded Table

Finally, you can read the contents of the `cedt.dsl` file using a text viewer like `cat` to inspect the ACPI table's data.

```
cat cedt.dsl
```

The output will show the decoded ASL code, allowing you to understand the platform configuration and resources related to CXL. This process is the same for any other ACPI table you want to inspect.

Example:

```bash
$ cat cedt.dsl 
/*
 * Intel ACPI Component Architecture
 * AML/ASL+ Disassembler version 20250807 (64-bit version)
 * Copyright (c) 2000 - 2025 Intel Corporation
 * 
 * Disassembly of cedt.dat
 *
 * ACPI Data Table [CEDT]
 *
 * Format: [HexOffset DecimalOffset ByteLength]  FieldName : FieldValue (in hex)
 */

[000h 0000 004h]                   Signature : "CEDT"    [CXL Early Discovery Table]
[004h 0004 004h]                Table Length : 00000444
[008h 0008 001h]                    Revision : 01
[009h 0009 001h]                    Checksum : F5
[00Ah 0010 006h]                      Oem ID : "INTEL "
[010h 0016 008h]                Oem Table ID : "INTEL ID"
[018h 0024 004h]                Oem Revision : 00000002
[01Ch 0028 004h]             Asl Compiler ID : "INTL"
[020h 0032 004h]       Asl Compiler Revision : 20230628


[024h 0036 001h]               Subtable Type : 00 [CXL Host Bridge Structure]
[025h 0037 001h]                    Reserved : 00
[026h 0038 002h]                      Length : 0020
[028h 0040 004h]      Associated host bridge : 00000003
[02Ch 0044 004h]       Specification version : 00000001
[030h 0048 004h]                    Reserved : 00000000
[034h 0052 008h]               Register base : 000000009A3F0000
[03Ch 0060 008h]             Register length : 0000000000010000

[044h 0068 001h]               Subtable Type : 00 [CXL Host Bridge Structure]
[045h 0069 001h]                    Reserved : 00
[046h 0070 002h]                      Length : 0020
[048h 0072 004h]      Associated host bridge : 00000023
[04Ch 0076 004h]       Specification version : 00000001
[050h 0080 004h]                    Reserved : 00000000
[054h 0084 008h]               Register base : 00000000AABF0000
[05Ch 0092 008h]             Register length : 0000000000010000

[064h 0100 001h]               Subtable Type : 00 [CXL Host Bridge Structure]
[065h 0101 001h]                    Reserved : 00
[066h 0102 002h]                      Length : 0020
[068h 0104 004h]      Associated host bridge : 00000043
[06Ch 0108 004h]       Specification version : 00000001
[070h 0112 004h]                    Reserved : 00000000
[074h 0116 008h]               Register base : 00000000BAFF0000
[07Ch 0124 008h]             Register length : 0000000000010000

[084h 0132 001h]               Subtable Type : 00 [CXL Host Bridge Structure]
[085h 0133 001h]                    Reserved : 00
[086h 0134 002h]                      Length : 0020
[088h 0136 004h]      Associated host bridge : 00000053
[08Ch 0140 004h]       Specification version : 00000001
[090h 0144 004h]                    Reserved : 00000000
[094h 0148 008h]               Register base : 00000000C2FF0000
[09Ch 0156 008h]             Register length : 0000000000010000

[0A4h 0164 001h]               Subtable Type : 00 [CXL Host Bridge Structure]
[0A5h 0165 001h]                    Reserved : 00
[0A6h 0166 002h]                      Length : 0020
[0A8h 0168 004h]      Associated host bridge : 00000103
[0ACh 0172 004h]       Specification version : 00000001
[0B0h 0176 004h]                    Reserved : 00000000
[0B4h 0180 008h]               Register base : 00000000CDBF0000
[0BCh 0188 008h]             Register length : 0000000000010000

[0C4h 0196 001h]               Subtable Type : 00 [CXL Host Bridge Structure]
[0C5h 0197 001h]                    Reserved : 00
[0C6h 0198 002h]                      Length : 0020
[0C8h 0200 004h]      Associated host bridge : 00000123
[0CCh 0204 004h]       Specification version : 00000001
[0D0h 0208 004h]                    Reserved : 00000000
[0D4h 0212 008h]               Register base : 00000000DDFF0000
[0DCh 0220 008h]             Register length : 0000000000010000

[0E4h 0228 001h]               Subtable Type : 00 [CXL Host Bridge Structure]
[0E5h 0229 001h]                    Reserved : 00
[0E6h 0230 002h]                      Length : 0020
[0E8h 0232 004h]      Associated host bridge : 00000143
[0ECh 0236 004h]       Specification version : 00000001
[0F0h 0240 004h]                    Reserved : 00000000
[0F4h 0244 008h]               Register base : 00000000EDFF0000
[0FCh 0252 008h]             Register length : 0000000000010000

[104h 0260 001h]               Subtable Type : 00 [CXL Host Bridge Structure]
[105h 0261 001h]                    Reserved : 00
[106h 0262 002h]                      Length : 0020
[108h 0264 004h]      Associated host bridge : 00000153
[10Ch 0268 004h]       Specification version : 00000001
[110h 0272 004h]                    Reserved : 00000000
[114h 0276 008h]               Register base : 00000000F5FF0000
[11Ch 0284 008h]             Register length : 0000000000010000

[124h 0292 001h]               Subtable Type : 00 [CXL Host Bridge Structure]
[125h 0293 001h]                    Reserved : 00
[126h 0294 002h]                      Length : 0020
[128h 0296 004h]      Associated host bridge : 00000122
[12Ch 0300 004h]       Specification version : 00000000
[130h 0304 004h]                    Reserved : 00000000
[134h 0308 008h]               Register base : 00000000DDFBE000
[13Ch 0316 008h]             Register length : 0000000000002000

[144h 0324 001h]               Subtable Type : 01 [CXL Fixed Memory Window Structure]
[145h 0325 001h]                    Reserved : 00
[146h 0326 002h]                      Length : 0034
[148h 0328 004h]                    Reserved : 00000000
[14Ch 0332 008h]         Window base address : 0000010080000000
[154h 0340 008h]                 Window size : 000002DF00000000
[15Ch 0348 001h]          Interleave Members : 02
[15Dh 0349 001h]       Interleave Arithmetic : 01
[15Eh 0350 002h]                    Reserved : 0000
[160h 0352 004h]                 Granularity : 00000000
[164h 0356 002h]                Restrictions : 0006
[166h 0358 002h]                       QtgId : 0000
[168h 0360 004h]                First Target : 00000003
[16Ch 0364 004h]                 Next Target : 00000023
[170h 0368 004h]                 Next Target : 00000043
[174h 0372 004h]                 Next Target : 00000053

[178h 0376 001h]               Subtable Type : 01 [CXL Fixed Memory Window Structure]
[179h 0377 001h]                    Reserved : 00
[17Ah 0378 002h]                      Length : 0028
[17Ch 0380 004h]                    Reserved : 00000000
[180h 0384 008h]         Window base address : 000003DF80000000
[188h 0392 008h]                 Window size : 000000B7C0000000
[190h 0400 001h]          Interleave Members : 00
[191h 0401 001h]       Interleave Arithmetic : 00
[192h 0402 002h]                    Reserved : 0000
[194h 0404 004h]                 Granularity : 00000000
[198h 0408 002h]                Restrictions : 0006
[19Ah 0410 002h]                       QtgId : 0000
[19Ch 0412 004h]                First Target : 00000003

[1A0h 0416 001h]               Subtable Type : 01 [CXL Fixed Memory Window Structure]
[1A1h 0417 001h]                    Reserved : 00
[1A2h 0418 002h]                      Length : 0028
[1A4h 0420 004h]                    Reserved : 00000000
[1A8h 0424 008h]         Window base address : 0000049740000000
[1B0h 0432 008h]                 Window size : 000000B7C0000000
[1B8h 0440 001h]          Interleave Members : 00
[1B9h 0441 001h]       Interleave Arithmetic : 00
[1BAh 0442 002h]                    Reserved : 0000
[1BCh 0444 004h]                 Granularity : 00000000
[1C0h 0448 002h]                Restrictions : 0006
[1C2h 0450 002h]                       QtgId : 0000
[1C4h 0452 004h]                First Target : 00000023

[1C8h 0456 001h]               Subtable Type : 01 [CXL Fixed Memory Window Structure]
[1C9h 0457 001h]                    Reserved : 00
[1CAh 0458 002h]                      Length : 0028
[1CCh 0460 004h]                    Reserved : 00000000
[1D0h 0464 008h]         Window base address : 0000054F00000000
[1D8h 0472 008h]                 Window size : 000000B7C0000000
[1E0h 0480 001h]          Interleave Members : 00
[1E1h 0481 001h]       Interleave Arithmetic : 00
[1E2h 0482 002h]                    Reserved : 0000
[1E4h 0484 004h]                 Granularity : 00000000
[1E8h 0488 002h]                Restrictions : 0006
[1EAh 0490 002h]                       QtgId : 0000
[1ECh 0492 004h]                First Target : 00000043

[1F0h 0496 001h]               Subtable Type : 01 [CXL Fixed Memory Window Structure]
[1F1h 0497 001h]                    Reserved : 00
[1F2h 0498 002h]                      Length : 0028
[1F4h 0500 004h]                    Reserved : 00000000
[1F8h 0504 008h]         Window base address : 00000606C0000000
[200h 0512 008h]                 Window size : 000000B7C0000000
[208h 0520 001h]          Interleave Members : 00
[209h 0521 001h]       Interleave Arithmetic : 00
[20Ah 0522 002h]                    Reserved : 0000
[20Ch 0524 004h]                 Granularity : 00000000
[210h 0528 002h]                Restrictions : 0006
[212h 0530 002h]                       QtgId : 0000
[214h 0532 004h]                First Target : 00000053

[218h 0536 001h]               Subtable Type : 01 [CXL Fixed Memory Window Structure]
[219h 0537 001h]                    Reserved : 00
[21Ah 0538 002h]                      Length : 0028
[21Ch 0540 004h]                    Reserved : 00000000
[220h 0544 008h]         Window base address : 00000C7E80000000
[228h 0552 008h]                 Window size : 0000017040000000
[230h 0560 001h]          Interleave Members : 00
[231h 0561 001h]       Interleave Arithmetic : 00
[232h 0562 002h]                    Reserved : 0000
[234h 0564 004h]                 Granularity : 00000000
[238h 0568 002h]                Restrictions : 000A
[23Ah 0570 002h]                       QtgId : 0001
[23Ch 0572 004h]                First Target : 00000003

[240h 0576 001h]               Subtable Type : 01 [CXL Fixed Memory Window Structure]
[241h 0577 001h]                    Reserved : 00
[242h 0578 002h]                      Length : 0028
[244h 0580 004h]                    Reserved : 00000000
[248h 0584 008h]         Window base address : 00000DEEC0000000
[250h 0592 008h]                 Window size : 0000017040000000
[258h 0600 001h]          Interleave Members : 00
[259h 0601 001h]       Interleave Arithmetic : 00
[25Ah 0602 002h]                    Reserved : 0000
[25Ch 0604 004h]                 Granularity : 00000000
[260h 0608 002h]                Restrictions : 000A
[262h 0610 002h]                       QtgId : 0001
[264h 0612 004h]                First Target : 00000023

[268h 0616 001h]               Subtable Type : 01 [CXL Fixed Memory Window Structure]
[269h 0617 001h]                    Reserved : 00
[26Ah 0618 002h]                      Length : 0028
[26Ch 0620 004h]                    Reserved : 00000000
[270h 0624 008h]         Window base address : 00000F5F00000000
[278h 0632 008h]                 Window size : 0000017040000000
[280h 0640 001h]          Interleave Members : 00
[281h 0641 001h]       Interleave Arithmetic : 00
[282h 0642 002h]                    Reserved : 0000
[284h 0644 004h]                 Granularity : 00000000
[288h 0648 002h]                Restrictions : 000A
[28Ah 0650 002h]                       QtgId : 0001
[28Ch 0652 004h]                First Target : 00000043

[290h 0656 001h]               Subtable Type : 01 [CXL Fixed Memory Window Structure]
[291h 0657 001h]                    Reserved : 00
[292h 0658 002h]                      Length : 0028
[294h 0660 004h]                    Reserved : 00000000
[298h 0664 008h]         Window base address : 000010CF40000000
[2A0h 0672 008h]                 Window size : 0000017040000000
[2A8h 0680 001h]          Interleave Members : 00
[2A9h 0681 001h]       Interleave Arithmetic : 00
[2AAh 0682 002h]                    Reserved : 0000
[2ACh 0684 004h]                 Granularity : 00000000
[2B0h 0688 002h]                Restrictions : 000A
[2B2h 0690 002h]                       QtgId : 0001
[2B4h 0692 004h]                First Target : 00000053

[2B8h 0696 001h]               Subtable Type : 01 [CXL Fixed Memory Window Structure]
[2B9h 0697 001h]                    Reserved : 00
[2BAh 0698 002h]                      Length : 0028
[2BCh 0700 004h]                    Reserved : 00000000
[2C0h 0704 008h]         Window base address : 000006BE80000000
[2C8h 0712 008h]                 Window size : 000000D400000000
[2D0h 0720 001h]          Interleave Members : 00
[2D1h 0721 001h]       Interleave Arithmetic : 00
[2D2h 0722 002h]                    Reserved : 0000
[2D4h 0724 004h]                 Granularity : 00000000
[2D8h 0728 002h]                Restrictions : 0006
[2DAh 0730 002h]                       QtgId : 0000
[2DCh 0732 004h]                First Target : 00000122

[2E0h 0736 001h]               Subtable Type : 01 [CXL Fixed Memory Window Structure]
[2E1h 0737 001h]                    Reserved : 00
[2E2h 0738 002h]                      Length : 0034
[2E4h 0740 004h]                    Reserved : 00000000
[2E8h 0744 008h]         Window base address : 0000079280000000
[2F0h 0752 008h]                 Window size : 000002D000000000
[2F8h 0760 001h]          Interleave Members : 02
[2F9h 0761 001h]       Interleave Arithmetic : 01
[2FAh 0762 002h]                    Reserved : 0000
[2FCh 0764 004h]                 Granularity : 00000000
[300h 0768 002h]                Restrictions : 0006
[302h 0770 002h]                       QtgId : 0000
[304h 0772 004h]                First Target : 00000123
[308h 0776 004h]                 Next Target : 00000103
[30Ch 0780 004h]                 Next Target : 00000143
[310h 0784 004h]                 Next Target : 00000153

[314h 0788 001h]               Subtable Type : 01 [CXL Fixed Memory Window Structure]
[315h 0789 001h]                    Reserved : 00
[316h 0790 002h]                      Length : 0028
[318h 0792 004h]                    Reserved : 00000000
[31Ch 0796 008h]         Window base address : 00000A6280000000
[324h 0804 008h]                 Window size : 000000B400000000
[32Ch 0812 001h]          Interleave Members : 00
[32Dh 0813 001h]       Interleave Arithmetic : 00
[32Eh 0814 002h]                    Reserved : 0000
[330h 0816 004h]                 Granularity : 00000000
[334h 0820 002h]                Restrictions : 0006
[336h 0822 002h]                       QtgId : 0000
[338h 0824 004h]                First Target : 00000103

[33Ch 0828 001h]               Subtable Type : 01 [CXL Fixed Memory Window Structure]
[33Dh 0829 001h]                    Reserved : 00
[33Eh 0830 002h]                      Length : 0028
[340h 0832 004h]                    Reserved : 00000000
[344h 0836 008h]         Window base address : 00000B1680000000
[34Ch 0844 008h]                 Window size : 000000B400000000
[354h 0852 001h]          Interleave Members : 00
[355h 0853 001h]       Interleave Arithmetic : 00
[356h 0854 002h]                    Reserved : 0000
[358h 0856 004h]                 Granularity : 00000000
[35Ch 0860 002h]                Restrictions : 0006
[35Eh 0862 002h]                       QtgId : 0000
[360h 0864 004h]                First Target : 00000143

[364h 0868 001h]               Subtable Type : 01 [CXL Fixed Memory Window Structure]
[365h 0869 001h]                    Reserved : 00
[366h 0870 002h]                      Length : 0028
[368h 0872 004h]                    Reserved : 00000000
[36Ch 0876 008h]         Window base address : 00000BCA80000000
[374h 0884 008h]                 Window size : 000000B400000000
[37Ch 0892 001h]          Interleave Members : 00
[37Dh 0893 001h]       Interleave Arithmetic : 00
[37Eh 0894 002h]                    Reserved : 0000
[380h 0896 004h]                 Granularity : 00000000
[384h 0900 002h]                Restrictions : 0006
[386h 0902 002h]                       QtgId : 0000
[388h 0904 004h]                First Target : 00000153

[38Ch 0908 001h]               Subtable Type : 01 [CXL Fixed Memory Window Structure]
[38Dh 0909 001h]                    Reserved : 00
[38Eh 0910 002h]                      Length : 0028
[390h 0912 004h]                    Reserved : 00000000
[394h 0916 008h]         Window base address : 0000123F80000000
[39Ch 0924 008h]                 Window size : 0000017000000000
[3A4h 0932 001h]          Interleave Members : 00
[3A5h 0933 001h]       Interleave Arithmetic : 00
[3A6h 0934 002h]                    Reserved : 0000
[3A8h 0936 004h]                 Granularity : 00000000
[3ACh 0940 002h]                Restrictions : 000A
[3AEh 0942 002h]                       QtgId : 0001
[3B0h 0944 004h]                First Target : 00000103

[3B4h 0948 001h]               Subtable Type : 01 [CXL Fixed Memory Window Structure]
[3B5h 0949 001h]                    Reserved : 00
[3B6h 0950 002h]                      Length : 0028
[3B8h 0952 004h]                    Reserved : 00000000
[3BCh 0956 008h]         Window base address : 000013AF80000000
[3C4h 0964 008h]                 Window size : 0000017000000000
[3CCh 0972 001h]          Interleave Members : 00
[3CDh 0973 001h]       Interleave Arithmetic : 00
[3CEh 0974 002h]                    Reserved : 0000
[3D0h 0976 004h]                 Granularity : 00000000
[3D4h 0980 002h]                Restrictions : 000A
[3D6h 0982 002h]                       QtgId : 0001
[3D8h 0984 004h]                First Target : 00000123

[3DCh 0988 001h]               Subtable Type : 01 [CXL Fixed Memory Window Structure]
[3DDh 0989 001h]                    Reserved : 00
[3DEh 0990 002h]                      Length : 0028
[3E0h 0992 004h]                    Reserved : 00000000
[3E4h 0996 008h]         Window base address : 0000151F80000000
[3ECh 1004 008h]                 Window size : 0000017000000000
[3F4h 1012 001h]          Interleave Members : 00
[3F5h 1013 001h]       Interleave Arithmetic : 00
[3F6h 1014 002h]                    Reserved : 0000
[3F8h 1016 004h]                 Granularity : 00000000
[3FCh 1020 002h]                Restrictions : 000A
[3FEh 1022 002h]                       QtgId : 0001
[400h 1024 004h]                First Target : 00000143

[404h 1028 001h]               Subtable Type : 01 [CXL Fixed Memory Window Structure]
[405h 1029 001h]                    Reserved : 00
[406h 1030 002h]                      Length : 0028
[408h 1032 004h]                    Reserved : 00000000
[40Ch 1036 008h]         Window base address : 0000168F80000000
[414h 1044 008h]                 Window size : 0000017080000000
[41Ch 1052 001h]          Interleave Members : 00
[41Dh 1053 001h]       Interleave Arithmetic : 00
[41Eh 1054 002h]                    Reserved : 0000
[420h 1056 004h]                 Granularity : 00000000
[424h 1060 002h]                Restrictions : 000A
[426h 1062 002h]                       QtgId : 0001
[428h 1064 004h]                First Target : 00000153

[42Ch 1068 001h]               Subtable Type : 02 [CXL XOR Interleave Math Structure]
[42Dh 1069 001h]                    Reserved : 00
[42Eh 1070 002h]                      Length : 0018
[430h 1072 002h]                    Reserved : 0000
[432h 1074 001h]      Interleave Granularity : 00
[433h 1075 001h]           Xormap List Count : 02
[434h 1076 008h]                First Xormap : 0000000000404100
[435h 1077 008h]                 Next Xormap : 0000000000808200

Raw Table Data: Length 1092 (0x444)

    0000: 43 45 44 54 44 04 00 00 01 F5 49 4E 54 45 4C 20  // CEDTD.....INTEL 
    0010: 49 4E 54 45 4C 20 49 44 02 00 00 00 49 4E 54 4C  // INTEL ID....INTL
    0020: 28 06 23 20 00 00 20 00 03 00 00 00 01 00 00 00  // (.# .. .........
    0030: 00 00 00 00 00 00 3F 9A 00 00 00 00 00 00 01 00  // ......?.........
    0040: 00 00 00 00 00 00 20 00 23 00 00 00 01 00 00 00  // ...... .#.......
    0050: 00 00 00 00 00 00 BF AA 00 00 00 00 00 00 01 00  // ................
    0060: 00 00 00 00 00 00 20 00 43 00 00 00 01 00 00 00  // ...... .C.......
    0070: 00 00 00 00 00 00 FF BA 00 00 00 00 00 00 01 00  // ................
    0080: 00 00 00 00 00 00 20 00 53 00 00 00 01 00 00 00  // ...... .S.......
    0090: 00 00 00 00 00 00 FF C2 00 00 00 00 00 00 01 00  // ................
    00A0: 00 00 00 00 00 00 20 00 03 01 00 00 01 00 00 00  // ...... .........
    00B0: 00 00 00 00 00 00 BF CD 00 00 00 00 00 00 01 00  // ................
    00C0: 00 00 00 00 00 00 20 00 23 01 00 00 01 00 00 00  // ...... .#.......
    00D0: 00 00 00 00 00 00 FF DD 00 00 00 00 00 00 01 00  // ................
    00E0: 00 00 00 00 00 00 20 00 43 01 00 00 01 00 00 00  // ...... .C.......
    00F0: 00 00 00 00 00 00 FF ED 00 00 00 00 00 00 01 00  // ................
    0100: 00 00 00 00 00 00 20 00 53 01 00 00 01 00 00 00  // ...... .S.......
    0110: 00 00 00 00 00 00 FF F5 00 00 00 00 00 00 01 00  // ................
    0120: 00 00 00 00 00 00 20 00 22 01 00 00 00 00 00 00  // ...... .".......
    0130: 00 00 00 00 00 E0 FB DD 00 00 00 00 00 20 00 00  // ............. ..
    0140: 00 00 00 00 01 00 34 00 00 00 00 00 00 00 00 80  // ......4.........
    0150: 00 01 00 00 00 00 00 00 DF 02 00 00 02 01 00 00  // ................
    0160: 00 00 00 00 06 00 00 00 03 00 00 00 23 00 00 00  // ............#...
    0170: 43 00 00 00 53 00 00 00 01 00 28 00 00 00 00 00  // C...S.....(.....
    0180: 00 00 00 80 DF 03 00 00 00 00 00 C0 B7 00 00 00  // ................
    0190: 00 00 00 00 00 00 00 00 06 00 00 00 03 00 00 00  // ................
    01A0: 01 00 28 00 00 00 00 00 00 00 00 40 97 04 00 00  // ..(........@....
    01B0: 00 00 00 C0 B7 00 00 00 00 00 00 00 00 00 00 00  // ................
    01C0: 06 00 00 00 23 00 00 00 01 00 28 00 00 00 00 00  // ....#.....(.....
    01D0: 00 00 00 00 4F 05 00 00 00 00 00 C0 B7 00 00 00  // ....O...........
    01E0: 00 00 00 00 00 00 00 00 06 00 00 00 43 00 00 00  // ............C...
    01F0: 01 00 28 00 00 00 00 00 00 00 00 C0 06 06 00 00  // ..(.............
    0200: 00 00 00 C0 B7 00 00 00 00 00 00 00 00 00 00 00  // ................
    0210: 06 00 00 00 53 00 00 00 01 00 28 00 00 00 00 00  // ....S.....(.....
    0220: 00 00 00 80 7E 0C 00 00 00 00 00 40 70 01 00 00  // ....~......@p...
    0230: 00 00 00 00 00 00 00 00 0A 00 01 00 03 00 00 00  // ................
    0240: 01 00 28 00 00 00 00 00 00 00 00 C0 EE 0D 00 00  // ..(.............
    0250: 00 00 00 40 70 01 00 00 00 00 00 00 00 00 00 00  // ...@p...........
    0260: 0A 00 01 00 23 00 00 00 01 00 28 00 00 00 00 00  // ....#.....(.....
    0270: 00 00 00 00 5F 0F 00 00 00 00 00 40 70 01 00 00  // ...._......@p...
    0280: 00 00 00 00 00 00 00 00 0A 00 01 00 43 00 00 00  // ............C...
    0290: 01 00 28 00 00 00 00 00 00 00 00 40 CF 10 00 00  // ..(........@....
    02A0: 00 00 00 40 70 01 00 00 00 00 00 00 00 00 00 00  // ...@p...........
    02B0: 0A 00 01 00 53 00 00 00 01 00 28 00 00 00 00 00  // ....S.....(.....
    02C0: 00 00 00 80 BE 06 00 00 00 00 00 00 D4 00 00 00  // ................
    02D0: 00 00 00 00 00 00 00 00 06 00 00 00 22 01 00 00  // ............"...
    02E0: 01 00 34 00 00 00 00 00 00 00 00 80 92 07 00 00  // ..4.............
    02F0: 00 00 00 00 D0 02 00 00 02 01 00 00 00 00 00 00  // ................
    0300: 06 00 00 00 23 01 00 00 03 01 00 00 43 01 00 00  // ....#.......C...
    0310: 53 01 00 00 01 00 28 00 00 00 00 00 00 00 00 80  // S.....(.........
    0320: 62 0A 00 00 00 00 00 00 B4 00 00 00 00 00 00 00  // b...............
    0330: 00 00 00 00 06 00 00 00 03 01 00 00 01 00 28 00  // ..............(.
    0340: 00 00 00 00 00 00 00 80 16 0B 00 00 00 00 00 00  // ................
    0350: B4 00 00 00 00 00 00 00 00 00 00 00 06 00 00 00  // ................
    0360: 43 01 00 00 01 00 28 00 00 00 00 00 00 00 00 80  // C.....(.........
    0370: CA 0B 00 00 00 00 00 00 B4 00 00 00 00 00 00 00  // ................
    0380: 00 00 00 00 06 00 00 00 53 01 00 00 01 00 28 00  // ........S.....(.
    0390: 00 00 00 00 00 00 00 80 3F 12 00 00 00 00 00 00  // ........?.......
    03A0: 70 01 00 00 00 00 00 00 00 00 00 00 0A 00 01 00  // p...............
    03B0: 03 01 00 00 01 00 28 00 00 00 00 00 00 00 00 80  // ......(.........
    03C0: AF 13 00 00 00 00 00 00 70 01 00 00 00 00 00 00  // ........p.......
    03D0: 00 00 00 00 0A 00 01 00 23 01 00 00 01 00 28 00  // ........#.....(.
    03E0: 00 00 00 00 00 00 00 80 1F 15 00 00 00 00 00 00  // ................
    03F0: 70 01 00 00 00 00 00 00 00 00 00 00 0A 00 01 00  // p...............
    0400: 43 01 00 00 01 00 28 00 00 00 00 00 00 00 00 80  // C.....(.........
    0410: 8F 16 00 00 00 00 00 80 70 01 00 00 00 00 00 00  // ........p.......
    0420: 00 00 00 00 0A 00 01 00 53 01 00 00 02 00 18 00  // ........S.......
    0430: 00 00 00 02 00 41 40 00 00 00 00 00 00 82 80 00  // .....A@.........
    0440: 00 00 00 00                                      // ....

```



### Summary

By following these steps, you've successfully built and installed the latest ACPICA tools directly from the source code. This gives you a powerful and up-to-date set of utilities, enabling you to inspect modern hardware features like CXL that may not be supported by older, packaged versions.

Now you have the knowledge to dump all of your system's ACPI tables, list their contents, and extract and decode any specific table you need. This process is a fundamental skill for anyone doing low-level system debugging or firmware analysis.

### References

Here are some official resources to learn more about ACPI, the ACPICA project, and the specifications mentioned in this article.

- [**ACPI Specification**](https://uefi.org/specifications): The official home for the latest ACPI specifications, hosted by the UEFI Forum. This is the definitive source for understanding the structure and content of all ACPI tables.
- [**ACPICA Project Website**](https://www.acpica.org/): The main website for the ACPI Component Architecture project. It provides downloads, documentation, and information about the tools and the project itself.
- [**ACPICA GitHub Repository**](https://github.com/acpica/acpica): The source code repository for the ACPICA project. You can clone this to get the latest tools, as detailed in this blog post.
- [CXL Consortium](https://computeexpresslink.org/): The official place to download the latest Compute Express Link (CXL) specification document.

### Appendix A

Here is a table explaining the common ACPI table signatures you'll find in the `acpixtract -l acpi.dump` output, based on the example above.

| Signature          | Description                                                  |
| ------------------ | ------------------------------------------------------------ |
| **IRDT**           | **I/O Resource Director Technology Table.** This table provides information to the operating system about the topology and configuration of I/O devices that support Intel's Resource Director Technology (RDT) for non-CPU agents, such as PCIe and CXL devices. |
| **SSDT**           | **Secondary System Description Table.** These tables contain additional ACPI Machine Language (AML) code and data that extend the `DSDT` (Differentiated System Description Table). They cannot modify or overwrite anything defined in the `DSDT` but can add new devices or functions. A system can have multiple `SSDT` tables. |
| **SPCR**           | **Serial Port Console Redirection Table.** This table provides information about a debug serial port, allowing the operating system to redirect its console output to that port for debugging purposes. |
| **MCFG**           | **PCI Express Memory-Mapped Configuration Space Base Address Description Table.** This table provides the base address for the PCI Express configuration space, allowing the operating system to access and configure PCIe devices. |
| **PMTT**           | **Platform Memory Topology Table.** This table provides details about the memory architecture of the system, including information about the physical layout and attributes of memory devices, often used in systems with persistent memory (NVDIMMs). |
| **PRMT**           | **Platform Runtime Mechanism Table.** A vendor-specific table that can define various runtime mechanisms and features on a platform. It is often used to describe platform-specific features that are not covered by other standard ACPI tables. |
| **APIC**           | **Multiple APIC Description Table.** This table, also known as `MADT`, describes the interrupt controller(s) in the system. It defines the available processors, local APICs, I/O APICs, and the interrupt routing information. |
| **HMAT**           | **Heterogeneous Memory Attribute Table.** This table provides information about the memory hierarchy, including latency and bandwidth, between different memory localities (NUMA nodes). It helps the operating system make more efficient resource management decisions, especially with technologies like CXL. |
| **TPM2**           | **Trusted Platform Module 2.0 Table.** This table defines the communication interface between the operating system and a TPM 2.0 device, enabling the OS to interact with the security features of the TPM. |
| **CEDT**           | **CXL Early Discovery Table.** This table is crucial for systems with Compute Express Link (CXL) technology. It describes the CXL host bridges, memory windows, and other CXL-related topology information to the operating system. |
| **SLIT**           | **System Locality Information Table.** This table provides a matrix of distances (latencies) between different NUMA nodes in the system, helping the operating system optimize data placement and task scheduling for better performance. |
| **OEM1/OEM2/OEM4** | **OEM-specific tables.** These are vendor-defined tables (often used by the manufacturer, like "INTEL ") that contain proprietary information and control methods for specific platform features not covered by standard ACPI specifications. Their contents vary widely between manufacturers and platforms. |
| **MSCT**           | **Maximum System Characteristics Table.** This table provides details about the maximum capabilities of the system, such as the number of processors and memory size. |
| **ERST**           | **Error Record Serialization Table.** This table defines an interface for the operating system to save and retrieve hardware error information to and from a persistent store, which is particularly useful for debugging server-class systems that support RAS (Reliability, Availability, Serviceability). |
| **DSDT**           | **Differentiated System Description Table.** The primary ACPI table that contains the core definition of the system's hardware. It includes AML code that describes devices, power management methods, and other platform-specific functions. It is a required table for any ACPI-compliant system. |
| **SRAT**           | **Static Resource Affinity Table.** This table provides information about the system's resource affinity, mapping processors and memory to specific NUMA nodes. This is critical for operating systems to correctly set up their memory management and scheduling for Non-Uniform Memory Access (NUMA) architectures. |
| **WSMT**           | **Windows SMM Security Mitigation Table.** A Microsoft-defined table that confirms to the operating system that certain security best practices have been implemented in the System Management Mode (SMM) firmware, which is important for enabling features like Windows Virtualization-based Security (VBS). |
| **DBG2**           | **Debug Port Table 2.** A table that describes one or more debug ports available on the platform, providing the operating system with the necessary information to configure and use them for kernel debugging. |
| **HEST**           | **Hardware Error Source Table.** This table defines a generic framework for the platform to report hardware errors to the operating system, allowing the OS to handle and log these errors. |
| **KEYP**           | **Keyboard Port Table.** A table that describes the presence and configuration of keyboard controller-related hardware. |
| **BERT**           | **Boot Error Record Table.** This table is used by the operating system to retrieve hardware error logs that occurred during a previous boot and were not reported to the kernel at runtime, such as errors that caused a surprise system reset. |
| **DMAR**           | **DMA Remapping Table.** This table provides information about the Direct Memory Access (DMA) remapping hardware (e.g., Intel VT-d), which is used by the operating system and hypervisors to secure devices and provide I/O virtualization. |
| **FACP**           | **Fixed ACPI Description Table.** This table contains crucial information about the system's fixed hardware features and power management capabilities. It also holds pointers to other essential tables, like the `DSDT` and `FACS`. |
| **FPDT**           | **Firmware Performance Data Table.** This table records information about the time spent by the firmware in various stages of the boot process, allowing the operating system to analyze and optimize boot performance. |
| **HPET**           | **High Precision Event Timer Table.** This table describes the presence and capabilities of the High Precision Event Timer, a hardware component that provides a more accurate and stable time source than older timers, which the OS can use for scheduling and other time-critical tasks. |
| **BDAT**           | **BIOS Data ACPI Table.** A vendor-specific table that allows the BIOS to expose various configuration and training data (such as DDR training margins) to the operating system, often in a proprietary format. |
| **FACS**           | **Firmware ACPI Control Structure.** This is not a table in the same way as the others; it's a shared data structure that resides in system memory and contains a lock (`Global Lock`) and other data that the OS and firmware use to coordinate ACPI operations. |