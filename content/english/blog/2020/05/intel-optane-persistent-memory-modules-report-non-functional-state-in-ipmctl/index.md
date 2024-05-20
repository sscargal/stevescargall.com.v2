---
title: "Intel Optane Persistent Memory Modules report \"Non-functional\" state in ipmctl"
date: "2020-05-30"
categories: 
  - "linux"
  - "troubleshooting"
tags: 
  - "ipmctl"
  - "kernel"
  - "optane"
  - "persistent-memory"
  - "pmem"
author: Steve Scargall
asliases:
  - /blog/2020/05/30/intel-optane-persistent-memory-modules-report-non-functional-state-in-ipmctl/
---

## Issue

Executing `ipmctl show-dimm` to get device information shows the persistent memory modules in a 'Non-functional' health state, eg:

```bash
# ipmctl show -dimm

 DimmID | Capacity | HealthState    | ActionRequired | LockState | FWVersion
=============================================================================
 0x0001 | 0.0 GiB  | Non-functional | N/A            | N/A       | N/A
 0x0011 | 0.0 GiB  | Non-functional | N/A            | N/A       | N/A
 0x0021 | 0.0 GiB  | Non-functional | N/A            | N/A       | N/A
 0x0101 | 0.0 GiB  | Non-functional | N/A            | N/A       | N/A
 0x0111 | 0.0 GiB  | Non-functional | N/A            | N/A       | N/A
 0x0121 | 0.0 GiB  | Non-functional | N/A            | N/A       | N/A
 0x1001 | 0.0 GiB  | Non-functional | N/A            | N/A       | N/A
 0x1011 | 0.0 GiB  | Non-functional | N/A            | N/A       | N/A
 0x1021 | 0.0 GiB  | Non-functional | N/A            | N/A       | N/A
 0x1101 | 0.0 GiB  | Non-functional | N/A            | N/A       | N/A
 0x1111 | 0.0 GiB  | Non-functional | N/A            | N/A       | N/A
 0x1121 | 0.0 GiB  | Non-functional | N/A            | N/A       | N/A
```

Other `ipmctl` commands may fail and return "No functional DIMMs in the system.", eg:

```bash
# ipmctl show -sensor health

No functional DIMMs in the system.
```

## Applies To

This issue applies to systems with the following components:

- Linux

- Intel Optane Persistent Memory

- ipmctl utility

## Cause(s)

The ipmctl-show-device(1) man page has the following description for 'Non-functional':

- Non-functional: The DCPMM is present but is non-responsive via the DDRT communication path. It may be possible to communicate with this DCPMM via SMBus for a subset of commands.

**_Note:_** Linux does not support the SMBus interface. It only supports the DDRT protocol (default). Attempts to use the `-smbus` option will fail with the following error:

```bash
# ipmctl show -smbus -dimm

The following protocol -smbus is unsupported on this OS. Please use -ddrt instead.
```

There are several possible causes for this issue, including:

- The operating system does not support persistent memory. Refer to the [Operating System Support Matrix](https://kb.pmem.io/faq/100000006-Intel-Optane-Persistent-Memory-Operating-System-Support-Matrix/) to confirm compatibility.

- The BIOS does not support NFIT (NVDIMM Firmware Interface Table)

- The nfit and libnvdimm drivers are not loaded in Linux. This can occur when using custom kernels where the drivers have been manually excluded from the kernel config.

## Solution(s)

Here are some troubleshooting steps to verify the working functionality of the persistent memory hardware and operating system.

### Step 1 - Verify the Persistent Memory is seen by the BIOS

Reboot the host and enter the BIOS (usually F1 or F2 during power-on). Navigate to the Memory section and you should see both the DDR and Persistent Memory (DDRT) modules listed, eg:

![](https://stevescargall.com/wp-content/uploads/2020/05/bios-main.png?w=808)

BIOS Main Menu showing DDR and DCPM (Persistent Memory) capacity

![](https://stevescargall.com/wp-content/uploads/2020/05/bios-memory.png?w=804)

BIOS -> Advanced -> Memory Configuration showing DIMM Information

If you have access to the BMC or equivalent, such as iDRAC on Dell systems, you can get the information without rebooting the host:

![](https://stevescargall.com/wp-content/uploads/2020/05/bios-dimms-information.png?w=1024)

Intel BMC showing DIMM Information (DDR & DCPMM Persistent Memory)

### Step 2 - Verify the NFIT bus is available in the Kernel

If you have the `ndctl` utility installed, use it to determine whether the NFIT bus is available. If so, you should see output similar to the following:

```bash
# ndctl list --buses
[
  {
    "provider":"ACPI.NFIT",
    "dev":"ndbus0",
    "scrub_state":"idle"
  }
]
```

If ndctl returns no output, then this is the cause of the 'Non-functional' health status. See 'Step 3' to verify the nfit driver is loaded.

### Step 3 - Verify the 'nfit' driver is loaded

There are several drives that will be loaded by the Kernel depending on the operational mode of Persistent Memory.

The following shows the loaded drivers for a Linux operating system when persistent memory is in AppDirect mode:

```bash
# lsmod | egrep -i "nv|pmem"
dax_pmem               16384  0
dax_pmem_core          16384  1 dax_pmem
nd_pmem                24576  0
nd_btt                 28672  1 nd_pmem
nvme                   49152  0
nvme_core             110592  1 nvme
libnvdimm             192512  5 dax_pmem,dax_pmem_core,nd_btt,nd_pmem,nfit
```

Here's what to expect for a system in Memory Mode:

```bash
# lsmod | egrep -i "nv|pmem"
nvme                   49152  0
nvme_core             110592  1 nvme
libnvdimm             192512  1 nfit
```

If the 'nfit' driver is not shown, it is not loaded. Both ndctl and ipmctl use the nfit driver to communicate with the persistent memory through the BIOS. A failure to communicate with the BIOS or modules will result in a 'Non-functional' health state.

### Step 4 - Determine if the drivers are installed

For all Linux distros that support persistent memory, the drivers should be available and loadable. If you use a custom kernel, it's very likely the kernel configuration file disabled the required NVDIMM feature and the drivers were not built. Confirm that your Linux distribution has the necessary 'acpi', 'nfit', and \*pmem\* drivers installed.

Most Linux distros keep their drivers in `/lib/modules/$(uname -r)/kernel/drivers`. On Fedora, for example, the drivers are installed by default:

```bash
# ls /lib/modules/$(uname -r)/kernel/drivers/acpi/nfit
nfit.ko.xz

# cd /lib/modules/$(uname -r)/kernel/drivers
$ find . -print |
 egrep -i "nvdimm|pmem|dax|acpi"
./nvdimm
./nvdimm/nd_pmem.ko.xz
./nvdimm/nd_e820.ko.xz
./nvdimm/libnvdimm.ko.xz
./nvdimm/nd_blk.ko.xz
./nvdimm/nd_btt.ko.xz
./dax
./dax/dax_hmem.ko.xz
./dax/device_dax.ko.xz
./dax/kmem.ko.xz
./dax/pmem
./dax/pmem/dax_pmem.ko.xz
./dax/pmem/dax_pmem_core.ko.xz
./acpi
./acpi/sbs.ko.xz
./acpi/sbshc.ko.xz
./acpi/apei
./acpi/apei/einj.ko.xz
./acpi/acpi_tad.ko.xz
./acpi/video.ko.xz
./acpi/acpi_configfs.ko.xz
./acpi/ec_sys.ko.xz
./acpi/custom_method.ko.xz
./acpi/acpi_ipmi.ko.xz
./acpi/nfit
./acpi/nfit/nfit.ko.xz
./acpi/acpi_pad.ko.xz
```

If the acpi, nfit, nvdimm, dax, and pmem directories are missing, the drivers are missing or were disabled when the kernel was built. This will result in communication issues to the BIOS and persistent memory modules, resulting in unexpected errors from ndctl and ipmctl.

The drivers are delivered as part of the Kernel package. On Fedora31, for example, we see the nfit driver is delivered by the kernel itself:

```bash
# dnf provides /lib/modules/$(uname -r)/kernel/drivers/acpi/nfit/nfit.ko.xz
Last metadata expiration check: 1:20:08 ago on Fri 29 May 2020 03:21:17 PM MDT.
kernel-core-5.6.13-200.fc31.x86_64 : The Linux kernel
Repo        : @System
Matched from:
Filename    : /lib/modules/5.6.13-200.fc31.x86_64/kernel/drivers/acpi/nfit/nfit.ko.xz

kernel-core-5.6.13-200.fc31.x86_64 : The Linux kernel
Repo        : updates
Matched from:
Filename    : /lib/modules/5.6.13-200.fc31.x86_64/kernel/drivers/acpi/nfit/nfit.ko.xz
```

### Step 5 - Determine if your kernel was configured to support persistent memory

See my previous post on '[How To Verify Linux Kernel Support for Persistent Memory](https://stevescargall.com/2020/02/11/how-to-verify-linux-kernel-support-for-persistent-memory/)'. The [NVDIMM Wiki on Kernel.org](https://nvdimm.wiki.kernel.org/) also has a section to help custom kernel developers.

Set up the correct kernel configuration options for PMEM and DAX in .config. To use huge pages for mmapped files, you'll need CONFIG\_FS\_DAX\_PMD selected, which is done automatically if you have the prerequisites marked below.

Options in make menuconfig:

- Device Drivers - NVDIMM (Non-Volatile Memory Device) Support
    - PMEM: Persistent memory block device support
    
    - BLK: Block data window (aperture) device support
    
    - BTT: Block Translation Table (atomic sector updates)

- Enable the block layer
    - Block device DAX support <not available in kernel-4.5 due to page cache issues>

- File systems
    - Direct Access (DAX) support

- Processor type and features
    - Support non-standard NVDIMMs and ADR protected memory <if using the memmap kernel parameter>
    
    - Transparent Hugepage Support <needed for huge pages>
    
    - Allow for memory hot-add
        
        - Allow for memory hot remove <needed for huge pages>
        
    
    - Device memory (pmem, HMM, etc…) hotplug support <needed for huge pages>

```bash
CONFIG_ZONE_DEVICE=y
CONFIG_MEMORY_HOTPLUG=y
CONFIG_MEMORY_HOTREMOVE=y
CONFIG_TRANSPARENT_HUGEPAGE=y
CONFIG_ACPI_NFIT=m
CONFIG_X86_PMEM_LEGACY=m
CONFIG_OF_PMEM=m
CONFIG_LIBNVDIMM=m
CONFIG_BLK_DEV_PMEM=m
CONFIG_BTT=y
CONFIG_NVDIMM_PFN=y
CONFIG_NVDIMM_DAX=y
CONFIG_FS_DAX=y
CONFIG_DAX=y
CONFIG_DEV_DAX=m
CONFIG_DEV_DAX_PMEM=m
CONFIG_DEV_DAX_KMEM=m
```

You can check what options were used to configure the Kernel using the config file that usually resides in the /boot file system. There are many more kernel options available than listed in the Wiki. For example, on Kernel 5.6.13, we have:

```bash
# egrep -i 'zone|memory|hugepage|nfit|pmem|nvdimm|btt|dax' /boot/config-$(uname -r)
CONFIG_CROSS_MEMORY_ATTACH=y
CONFIG_ZONE_DMA32=y
CONFIG_ZONE_DMA=y
CONFIG_X86_SUPPORTS_MEMORY_FAILURE=y
CONFIG_ARCH_SELECT_MEMORY_MODEL=y
# CONFIG_ARCH_MEMORY_PROBE is not set
CONFIG_X86_PMEM_LEGACY_DEVICE=y
CONFIG_X86_PMEM_LEGACY=m
# CONFIG_X86_BOOTPARAM_MEMORY_CORRUPTION_CHECK is not set
CONFIG_X86_INTEL_MEMORY_PROTECTION_KEYS=y
CONFIG_DYNAMIC_MEMORY_LAYOUT=y
CONFIG_RANDOMIZE_MEMORY=y
CONFIG_RANDOMIZE_MEMORY_PHYSICAL_PADDING=0xa
CONFIG_ARCH_ENABLE_MEMORY_HOTPLUG=y
CONFIG_ARCH_ENABLE_MEMORY_HOTREMOVE=y
CONFIG_ARCH_ENABLE_HUGEPAGE_MIGRATION=y
CONFIG_ACPI_HOTPLUG_MEMORY=y
CONFIG_ACPI_NFIT=m
# CONFIG_NFIT_SECURITY_DEBUG is not set
CONFIG_ACPI_APEI_MEMORY_FAILURE=y
CONFIG_ARCH_HAS_SET_MEMORY=y
CONFIG_HAVE_ARCH_TRANSPARENT_HUGEPAGE=y
CONFIG_HAVE_ARCH_TRANSPARENT_HUGEPAGE_PUD=y
CONFIG_BLK_DEV_ZONED=y
CONFIG_BLK_DEBUG_FS_ZONED=y
# Memory Management options
CONFIG_SELECT_MEMORY_MODEL=y
CONFIG_HAVE_MEMORY_PRESENT=y
CONFIG_MEMORY_ISOLATION=y
CONFIG_MEMORY_HOTPLUG=y
CONFIG_MEMORY_HOTPLUG_SPARSE=y
CONFIG_MEMORY_HOTPLUG_DEFAULT_ONLINE=y
CONFIG_MEMORY_HOTREMOVE=y
CONFIG_MEMORY_BALLOON=y
CONFIG_ARCH_SUPPORTS_MEMORY_FAILURE=y
CONFIG_MEMORY_FAILURE=y
CONFIG_TRANSPARENT_HUGEPAGE=y
# CONFIG_TRANSPARENT_HUGEPAGE_ALWAYS is not set
CONFIG_TRANSPARENT_HUGEPAGE_MADVISE=y
CONFIG_ZONE_DEVICE=y
# end of Memory Management options
CONFIG_NF_CONNTRACK_ZONES=y
# LPDDR & LPDDR2 PCM memory drivers
# end of LPDDR & LPDDR2 PCM memory drivers
# CONFIG_ZRAM_MEMORY_TRACKING is not set
CONFIG_DM_ZONED=m
# Memory mapped GPIO drivers
# end of Memory mapped GPIO drivers
# MemoryStick drivers
# MemoryStick Host Controller Drivers
# CONFIG_VIRTIO_PMEM is not set
# CONFIG_XEN_BALLOON_MEMORY_HOTPLUG is not set
# CONFIG_MEMORY is not set
CONFIG_LIBNVDIMM=m
CONFIG_BLK_DEV_PMEM=m
CONFIG_ND_BTT=m
CONFIG_BTT=y
CONFIG_NVDIMM_PFN=y
CONFIG_NVDIMM_DAX=y
CONFIG_NVDIMM_KEYS=y
CONFIG_DAX_DRIVER=y
CONFIG_DAX=y
CONFIG_DEV_DAX=m
CONFIG_DEV_DAX_PMEM=m
CONFIG_DEV_DAX_HMEM=m
CONFIG_DEV_DAX_KMEM=m
# CONFIG_DEV_DAX_PMEM_COMPAT is not set
# CONFIG_ZONEFS_FS is not set
CONFIG_FS_DAX=y
CONFIG_FS_DAX_PMD=y
# Memory initialization
# end of Memory initialization
# Default contiguous memory area size:
CONFIG_ARCH_HAS_PMEM_API=y
# Memory Debugging
CONFIG_DEBUG_MEMORY_INIT=y
# end of Memory Debugging
```
