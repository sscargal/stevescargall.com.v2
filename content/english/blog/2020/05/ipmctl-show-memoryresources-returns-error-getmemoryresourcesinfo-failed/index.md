---
title: "\"ipmctl show -memoryresources\" returns \"Error: GetMemoryResourcesInfo Failed\""
date: "2020-05-30"
categories: 
  - "linux"
  - "troubleshooting"
tags: 
  - "ipmctl"
  - "optane"
  - "persistent-memory"
  - "pmem"
  - "windows"
image: "images/pexels-photo-4439425.jpeg"
author: Steve Scargall
---

## Issue:

Running `ipmctl show -memoryresources` returns an error similar to the following:

```
# ipmctl show -memoryresources

Error: GetMemoryResourcesInfo Failed
```

## Applies To:

- Linux & Microsoft Windows

- Intel Optane Persistent Memory

- ipmctl utility

## Cause:

The Platform Configuration Data (PCD) is invalid or has been erased using a previously executed `ipmctl delete -dimm -pcd` command or the system has new persistent memory modules that have not been initialized yet.

A module with an empty PCD will show information similar to the following. This shows an example of PCD of DIMM ID 0x0001. To review the PCD for all modules in the system use `ipmctl show -dimm -pcd`.

```
# ipmctl show -dimm 0x0001 -pcd

--DimmID:0x0001--
--Pcd:LSA--
   Label Storage Area : Current Index
   Signature          : NAMESPACE_INDEX
   Flags              : 0x0
   LabelSize          : 0x1
   Sequence           : 0x1
   MyOffset           : 0x100
   MySize             : 0x100
   OtherOffset        : 0x0
   LabelOffset        : 0x200
   NumOfLabel         : 0x1fe
   Major              : 0x1
   Minor              : 0x2
   Checksum           : 0x2793e71bd8323c18
   Hexdump: For 64 bytes
   000:  fdffffffffffffff ffffffffffffffff ........ ........
   016:  ffffffffffffffff ffffffffffffffff ........ ........
   032:  ffffffffffffffff ffffffffffffffff ........ ........
   048:  ffffffffffffffff ffffffffffffffff ........ ........
   Labels: Label Storage Area
   ---Table: Namespace Label Info---
      Uuid               : 1a550627-001e-0f43-8c7a-e51771aabcb5
      Name               :
      LabelFlags         : 0x0
      NumOfLabels        : 0x6
      Position           : 0x0
      ISetCookie         : 0x2d3c7f48f4e22ccc
      LbaSize            : 0x200
      Dpa                : 0x10000000
      RawSize            : 0x3f00000000
      Slot               : 0x1
      Alignment          : 0x0
      TypeGuid           : 66f0d379-b4f3-4074-ac43-0d3318b78cdb
      AddrAbstrGuid      : 266400ba-fb9f-4677-bcb0-968f11d0d225
      LabelChecksum      : 0xa949d903019dd9f2

--Pcd:Config--
   Table                     : PCD Config Header
   Signature                 : DMHD
   Length                    : 0x3c
   Revision                  : 0x1
   Checksum                  : 0xff
   OemId                     : INTEL
   OemTableId                : EDK2
   OemRevision               : 0x2
   CreatorId                 : INTL
   CreatorRevision           : 0x20091013
   CurrentConfDataSize       : 0x0
   CurrentConfStartOffset    : 0x0
   ConfInputDataSize         : 0x0
   ConfInputDataOffset       : 0x0
   ConfOutputDataSize        : 0x0
   ConfOutputDataOffset      : 0x0
```

A valid PCD looks similar to the following:

```
# ipmctl show -dimm 0x0001 -pcd

--DimmID:0x0001--
--Pcd:LSA--
   Label Storage Area : Current Index
   Signature          : NAMESPACE_INDEX
   Flags              : 0x0
   LabelSize          : 0x1
   Sequence           : 0x2
   MyOffset           : 0x100
   MySize             : 0x100
   OtherOffset        : 0x0
   LabelOffset        : 0x200
   NumOfLabel         : 0x1fe
   Major              : 0x1
   Minor              : 0x2
   Checksum           : 0x2793e7b2d8323c1b
   Hexdump: For 64 bytes
   000:  ffffffffffffffff ffffffffffffffff ........ ........
   016:  ffffffffffffffff ffffffffffffffff ........ ........
   032:  ffffffffffffffff ffffffffffffffff ........ ........
   048:  ffffffffffffffff ffffffffffffffff ........ ........
--Pcd:Config--
   Table                     : PCD Config Header
   Signature                 : DMHD
   Length                    : 0x3c
   Revision                  : 0x1
   Checksum                  : 0x8c
   OemId                     : INTEL
   OemTableId                : EDK2
   OemRevision               : 0x2
   CreatorId                 : INTL
   CreatorRevision           : 0x20091013
   CurrentConfDataSize       : 0x170
   CurrentConfStartOffset    : 0x3c
   ConfInputDataSize         : 0x178
   ConfInputDataOffset       : 0x1ac
   ConfOutputDataSize        : 0x178
   ConfOutputDataOffset      : 0x324

   ---Table: PCD Current Config---
      Signature                 : CCUR
      Length                    : 0x138
      Revision                  : 0x2
      Checksum                  : 0x2
      OemId                     : INTEL
      OemTableId                : S2600W
      OemRevision               : 0x2
      CreatorId                 : INTL
      CreatorRevision           : 0x20091013
      ConfigError               : 0x1
      VolatileMemSizeIntoSpa    : 0x0
      PersistentMemSizeIntoSpa  : 0x0

      Interleave Table          : PCD Interleave Info
      Type                      : 0x5
      InterleaveSetIndex        : 0x1
      NumOfDimmsInInterleaveSet : 0x6
      InterleaveMemoryType      : 0x2
      InterleaveFormatChannel   : 0x40
      InterleaveFormatImc       : 0x40
      InterleaveFormatWays      : 0x10
      MirrorEnable              : 0x0
      InterleaveChangeStatus    : 0x0
      Indentification Table     : PCD Identification Info
      DimmUniqueIdentifer       : 0x3f00000000

      PartitionOffset           : 0x0
   ---Table: Platform Config Data Conf Input table---
      Signature                 : CIN_
      Length                    : 0x138
      Revision                  : 0x2
      Checksum                  : 0xfb
      OemId                     : INTEL
      OemTableId                : EDK2
      OemRevision               : 0x2
      CreatorId                 : INTL
      CreatorRevision           : 0x20091013
      SequenceNumber               : 0x1

      Size Table                : PCD Partition Size Change
      Type                      : 0x5
      PartitionSizeChangeStatus : 0x0
      PartitionSize             : 0x3f1d140000

      Interleave Table          : PCD Interleave Info
      InterleaveSetIndex        : 0x1
      NumOfDimmsInInterleaveSet : 0x6
      InterleaveMemoryType      : 0x2
      InterleaveFormatChannel   : 0x40
      InterleaveFormatImc       : 0x40
      InterleaveFormatWays      : 0x10
      MirrorEnable              : 0x0
      InterleaveChangeStatus    : 0x0
      Indentification Table     : PCD Identification Info
      DimmUniqueIdentifer       : 0x3f00000000

      PartitionOffset           : 0x0
   ---Table: Platform Config Data Conf Output table---
      Signature                 : COUT
      Length                    : 0x138
      Revision                  : 0x2
      Checksum                  : 0xa4
      OemId                     : INTEL
      OemTableId                : S2600W
      OemRevision               : 0x2
      CreatorId                 : INTL
      CreatorRevision           : 0x20091013
      SequenceNumber               : 0x1
      ValidationStatus             : 0x1

      Size Table                : PCD Partition Size Change
      Type                      : 0x5
      PartitionSizeChangeStatus : 0x1
      PartitionSize             : 0x3f1d140000

      Interleave Table          : PCD Interleave Info
      InterleaveSetIndex        : 0x1
      NumOfDimmsInInterleaveSet : 0x6
      InterleaveMemoryType      : 0x2
      InterleaveFormatChannel   : 0x40
      InterleaveFormatImc       : 0x40
      InterleaveFormatWays      : 0x10
      MirrorEnable              : 0x0
      InterleaveChangeStatus    : 0x1
      Indentification Table     : PCD Identification Info
      DimmUniqueIdentifer       : 0x3f00000000

      PartitionOffset           : 0x0
```

## Solution:

Recreate the configuration. For example, the following creates an interleaved set of persistent memory modules in an AppDirect mode for each CPU socket. Read the ipmctl-create-goal(1) man page or the [provisioning documentation](https://docs.pmem.io/ipmctl-user-guide/provisioning/create-memory-allocation-goal) for more information on the different configuration options.

```
# ipmctl create -goal persistentmemorytype=appdirect

The following configuration will be applied:
 SocketID | DimmID | MemorySize | AppDirect1Size | AppDirect2Size
==================================================================
 0x0000   | 0x0001 | 0.0 GiB    | 252.0 GiB      | 0.0 GiB
 0x0000   | 0x0011 | 0.0 GiB    | 252.0 GiB      | 0.0 GiB
 0x0000   | 0x0021 | 0.0 GiB    | 252.0 GiB      | 0.0 GiB
 0x0000   | 0x0101 | 0.0 GiB    | 252.0 GiB      | 0.0 GiB
 0x0000   | 0x0111 | 0.0 GiB    | 252.0 GiB      | 0.0 GiB
 0x0000   | 0x0121 | 0.0 GiB    | 252.0 GiB      | 0.0 GiB
 0x0001   | 0x1001 | 0.0 GiB    | 252.0 GiB      | 0.0 GiB
 0x0001   | 0x1011 | 0.0 GiB    | 252.0 GiB      | 0.0 GiB
 0x0001   | 0x1021 | 0.0 GiB    | 252.0 GiB      | 0.0 GiB
 0x0001   | 0x1101 | 0.0 GiB    | 252.0 GiB      | 0.0 GiB
 0x0001   | 0x1111 | 0.0 GiB    | 252.0 GiB      | 0.0 GiB
 0x0001   | 0x1121 | 0.0 GiB    | 252.0 GiB      | 0.0 GiB
Do you want to continue? [y/n] y
Created following region configuration goal
 SocketID | DimmID | MemorySize | AppDirect1Size | AppDirect2Size
==================================================================
 0x0000   | 0x0001 | 0.0 GiB    | 252.0 GiB      | 0.0 GiB
 0x0000   | 0x0011 | 0.0 GiB    | 252.0 GiB      | 0.0 GiB
 0x0000   | 0x0021 | 0.0 GiB    | 252.0 GiB      | 0.0 GiB
 0x0000   | 0x0101 | 0.0 GiB    | 252.0 GiB      | 0.0 GiB
 0x0000   | 0x0111 | 0.0 GiB    | 252.0 GiB      | 0.0 GiB
 0x0000   | 0x0121 | 0.0 GiB    | 252.0 GiB      | 0.0 GiB
 0x0001   | 0x1001 | 0.0 GiB    | 252.0 GiB      | 0.0 GiB
 0x0001   | 0x1011 | 0.0 GiB    | 252.0 GiB      | 0.0 GiB
 0x0001   | 0x1021 | 0.0 GiB    | 252.0 GiB      | 0.0 GiB
 0x0001   | 0x1101 | 0.0 GiB    | 252.0 GiB      | 0.0 GiB
 0x0001   | 0x1111 | 0.0 GiB    | 252.0 GiB      | 0.0 GiB
 0x0001   | 0x1121 | 0.0 GiB    | 252.0 GiB      | 0.0 GiB
A reboot is required to process new memory allocation goals.
```

Reboot the host for the changes to take effect:

```
$ sudo systemctl reboot
```

After the host reboots, verify the `ipmctl show -memoryresources` command works as expected, eg:

```
# ipmctl show -memoryresources

Capacity=3029.5 GiB
MemoryCapacity=0.0 GiB
AppDirectCapacity=3024.0 GiB
UnconfiguredCapacity=0.0 GiB
InaccessibleCapacity=5.5 GiB
ReservedCapacity=0.0 GiB
```
