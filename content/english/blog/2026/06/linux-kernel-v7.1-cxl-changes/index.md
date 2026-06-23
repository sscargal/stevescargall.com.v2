---
title: "Linux Kernel v7.1 is Released: This is What's New for Compute Express Link (CXL)"
meta_title: "Linux Kernel v7.1 CXL & DAX Subsystem Changes"
description: "Linux Kernel v7.1 brings 46 CXL and DAX commits: stability improvements, bug fixes, code cleanup, and new hardware support. Full commit-by-commit analysis."
date: 2026-06-14T00:00:00Z
image: "featured_image.webp"
categories: ["CXL"]
author: "Steve Scargall"
tags: ["CXL", "Linux", "Kernel"]
draft: false
aliases:
---

The Linux Kernel v7.1 release brings several improvements and additions related to Compute Express Link (CXL) technology.

## Release Highlights

Linux Kernel v7.1 includes **47 commits** to the CXL and DAX subsystems:

| Category | Commits |
|---|---|
| New Features & Hardware | 1 |
| Bug Fixes | 5 |
| Refactoring & Cleanup | 5 |
| Testing | 1 |
| Other | 35 |

The v7.1 CXL/DAX cycle is defined by three interlocking themes: laying the groundwork for Type 2 accelerator support, hardening the DAX/HMEM subsystem against a cluster of correctness bugs, and a focused refactoring of the region layer that splits a monolithic file into purpose-specific translation units. None of these is a headline splash feature on its own, but together they represent the kind of steady, unglamorous investment that makes the subsystem reliable enough to build production systems on.

Type 2 support — CXL devices that expose accelerator-attached memory rather than pure memory expanders — takes a significant step forward. Internal structures previously locked inside `cxl_pci` are now exported so that out-of-tree and in-tree Type 2 drivers can bind against them, and `cxl_dev_state` initialization now accounts for the Type 2 device class from the start. Alongside this, generic PCI utility code migrates from `cxl_pci` into `core/cxl_pci`, giving both the core and Type 2 drivers a shared, stable foundation without duplication.

On the DAX/HMEM side, this release resolves a longstanding ambiguity around Soft Reserved memory ownership — the question of whether a given ACPI-advertised memory range belongs to CXL region management or to the legacy `dax_hmem` driver. A new containment helper in `cxl/region` allows that decision to be deferred and resolved cleanly at driver bind time rather than at boot, eliminating a class of singleton confusion bugs and fixing a dependency ordering issue between `dax/cxl` and `dax/hmem` that could cause incorrect initialization ordering in multi-device configurations.

### Key Changes

- **Type 2 accelerator device support**: Internal CXL structs are now exported to allow external Type 2 drivers to participate in the CXL stack, and `cxl_dev_state` initialization correctly identifies Type 2 devices. This is a prerequisite for CXL-attached accelerators (GPUs, FPGAs, smart NICs) to interoperate with the kernel's memory management and RAS infrastructure.

- **32-switch decoder support**: `cxl/hdm` now supports up to 32 switch-level decoders, up from the previous limit. This matters for large fabric topologies — multi-host CXL switches in disaggregated memory configurations — where the old cap became a real constraint.

- **Soft Reserved ownership resolution**: A new helper checks whether a Soft Reserved EFI memory range is already covered by a CXL region, and `dax_hmem` defers claiming those ranges until CXL binding has had a chance to run. This eliminates a race where `dax_hmem` could steal memory that the CXL region driver was entitled to manage.

- **Region lock status sysfs interface**: A new sysfs attribute exposes whether a CXL region is locked, giving userspace tools (and udev rules) a reliable, race-free way to query region state without parsing kernel log output.

- **Region code split into `region_dax.c` and `region_pmem.c`**: The DAX and PMEM region driver logic is extracted from a single sprawling file into two focused translation units. This is maintenance work, but it reduces the cognitive overhead for contributors working on only one media type and makes future specialization easier.

- **PCI reset decoder flag clearing**: When a `cxl_memdev` undergoes a PCI-level reset, endpoint decoder flags are now explicitly cleared. Without this, stale flag state could cause the driver to misinterpret post-reset device status, leading to incorrect region assembly or missed error events.

- **Use-after-free fix in region auto assembly**: A reference-counting bug in the region auto-assembly failure path could cause a freed region object to be accessed during cleanup. The fix ensures teardown ordering is correct and is a straightforward but important memory safety correction.

- **`fsdev_dax_zero_page_range()` uninitialized kaddr fix**: A missing initialization in the DAX filesystem zero-page path left `kaddr` undefined under certain conditions, producing unpredictable behavior when zeroing page ranges through a DAX-mapped filesystem. The fix initializes `kaddr` unconditionally before use.

## CXL related changes from Kernel v7.0 to v7.1

Here is the detailed list of all commits merged into the 7.1 Kernel for CXL and DAX. This list was generated by the [Linux Kernel CXL Feature Tracker](https://github.com/sscargal/linux-cxl-tracker).

- [Merge tag 'cxl-for-7.1' of git://git.kernel.org/pub/scm/linux/kernel/git/cxl/cxl](https://github.com/torvalds/linux/commit/12bffaef28820e0b94c644c75708195c61af78f7)
- [Merge branch 'for-7.1/cxl-misc' into cxl-for-next](https://github.com/torvalds/linux/commit/3939dba00f981c26d1748769f2f28a3cc0afb6a8)
- [cxl/hdm: Add support for 32 switch decoders](https://github.com/torvalds/linux/commit/3624a22783b74ffebaa7d9f286e203604baa06c7)
- [Merge branch 'for-7.1/cxl-region-refactor' into cxl-for-next](https://github.com/torvalds/linux/commit/202432ae8a6948ab6c88b56eaf2848a23637d9f0)
- [Merge branch 'for-7.1/dax-hmem' into cxl-for-next](https://github.com/torvalds/linux/commit/303d32843b831ba86c28aea188db95da65d88f31)
- [Merge branch 'for-7.1/cxl-type2-support' into cxl-for-next](https://github.com/torvalds/linux/commit/7aacc625576d4dc9c7d8a687f168ff72b30ca353)
- [Merge branch 'for-7.1/cxl-consolidate-endpoint' into cxl-for-next](https://github.com/torvalds/linux/commit/2fb3bdeb00111519965601389a7b60afb97bafc0)
- [cxl/region: Add a region sysfs interface for region lock status](https://github.com/torvalds/linux/commit/d585bc86fb9f405ed1f2f56cc50c82d9aaada297)
- [cxl/region: Constify cxl_region_resource_contains()](https://github.com/torvalds/linux/commit/471d88441eb990ef1b64713e6975cb3549b1824b)
- [cxl/region: Limit visibility of cxl_region_contains_resource()](https://github.com/torvalds/linux/commit/b6a61d5baf99c012c61ee93f8295185942cd7495)
- [cxl/region: Fix use-after-free from auto assembly failure](https://github.com/torvalds/linux/commit/87805c32e6ad7b5ce2d9f7f47e76081857a4a335)
- [cxl/core: Check existence of cxl_memdev_state in poison test](https://github.com/torvalds/linux/commit/261a02b93d9b6dfdc49b3e675be1a0e677cf71f3)
- [cxl/core: use cleanup.h for devm_cxl_add_dax_region](https://github.com/torvalds/linux/commit/29990ab5cb408d5aa15939d6535e3291aeef748b)
- [cxl/core/region: move dax region device logic into region_dax.c](https://github.com/torvalds/linux/commit/d747cf98f091e56beeed5233e8992fea59401011)
- [cxl/core/region: move pmem region driver logic into region_pmem.c](https://github.com/torvalds/linux/commit/8a1ec5fb2360d6fc0183cbe7de68c7a4e611d120)
- [cxl/region: Add helper to check Soft Reserved containment by CXL regions](https://github.com/torvalds/linux/commit/8e65f99b525b3f49b87db0db0d0e0fc1a0c53e40)
- [cxl: Add endpoint decoder flags clear when PCI reset happens](https://github.com/torvalds/linux/commit/7974835aa9d54125a1b6a2948f927d745748bf46)
- [cxl/pci: Check memdev driver binding status in cxl_reset_done()](https://github.com/torvalds/linux/commit/e8069c66d09309579e53567be8ddfa6ccb2f452a)
- [cxl/pci: Hold memdev lock in cxl_event_trace_record()](https://github.com/torvalds/linux/commit/dc372e5f429ced834d81ff12a945397dc43585a8)
- [cxl/region: Factor out interleave granularity setup](https://github.com/torvalds/linux/commit/64584273dfb8a1e5fc7d78094ba22a93c204b44e)
- [cxl/region: Factor out interleave ways setup](https://github.com/torvalds/linux/commit/29f0724c4592a5ab9076e1ff6e4e39f0de60cc9e)
- [cxl: Make region type based on endpoint type](https://github.com/torvalds/linux/commit/09d065d256b1d5965fe6512cfd1c23ef44d2efc9)
- [cxl/pci: Remove redundant cxl_pci_find_port() call](https://github.com/torvalds/linux/commit/d537d953c47866bafc89feb66d8ef34baf17659a)
- [cxl: Move pci generic code from cxl_pci to core/cxl_pci](https://github.com/torvalds/linux/commit/58f28930c7fb0e24cdf2972a9c3b7c91aeef4539)
- [cxl: export internal structs for external Type2 drivers](https://github.com/torvalds/linux/commit/005869886d1d370afb6c10cd40709d956960e9c2)
- [cxl: support Type2 when initializing cxl_dev_state](https://github.com/torvalds/linux/commit/9a775c07bb04384f7c03a35dd04818ed818c1f71)
- [Merge tag 'libnvdimm-for-7.1' of git://git.kernel.org/pub/scm/linux/kernel/git/nvdimm/nvdimm](https://github.com/torvalds/linux/commit/bb0bc49a1cef574646eb25d74709c5ff200903a8)
- [dax/fsdev: fix uninitialized kaddr in fsdev_dax_zero_page_range()](https://github.com/torvalds/linux/commit/45df9111692c62d5f09fc4345ae36dae31024797)
- [mm: rename VMA flag helpers to be more readable](https://github.com/torvalds/linux/commit/e650bb30ca532901da6def04c7d1de72ae59ea4e)
- [dax/hmem: Parent dax_hmem devices](https://github.com/torvalds/linux/commit/059edcc405e46cc10ee65ab2c039aa6bccfbb3a0)
- [dax/hmem: Fix singleton confusion between dax_hmem_work and hmem devices](https://github.com/torvalds/linux/commit/f8dc1bde187310e0345beb08df949e0c2a4c86ce)
- [dax/hmem: Reduce visibility of dax_cxl coordination symbols](https://github.com/torvalds/linux/commit/3cba30eed56df3af80ae8d4fde9cf4039eace82a)
- [dax/cxl: Fix HMEM dependencies](https://github.com/torvalds/linux/commit/1eaef15b2349087d9ce583b9153970d5cf5c5329)
- [dax: export dax_dev_get()](https://github.com/torvalds/linux/commit/2ae624d5a555d47a735fb3f4d850402859a4db77)
- [dax: Add fs_dax_get() func to prepare dax for fs-dax usage](https://github.com/torvalds/linux/commit/eec38f5d86d27535509c99f02ccc642ceb0c3e2a)
- [dax: Add dax_set_ops() for setting dax_operations at bind time](https://github.com/torvalds/linux/commit/700ecbc1f5aa02ba9ad68d7be1ef7a9c8eae07e9)
- [dax: Add dax_operations for use by fs-dax on fsdev dax](https://github.com/torvalds/linux/commit/099c81a1f0ab3e948d73c5ab2b7a3b702af36e64)
- [dax: Save the kva from memremap](https://github.com/torvalds/linux/commit/759455848df0b9ac3acabdbedcdc4a55af67935f)
- [dax: add fsdev.c driver for fs-dax on character dax](https://github.com/torvalds/linux/commit/d5406bd458b0ac10b1301a4d5801d85c8f648637)
- [dax: move dax_pgoff_to_phys from [drivers/dax/] device.c to bus.c](https://github.com/torvalds/linux/commit/a73cc506ad9f3798d33c78b212149b80d212111a)
- [dax/hmem, cxl: Defer and resolve Soft Reserved ownership](https://github.com/torvalds/linux/commit/e4de6b910bf3645c224cd873d4e03ce3dd81fbe0)
- [dax: Track all dax_region allocations under a global resource tree](https://github.com/torvalds/linux/commit/34f80bb969cc1710f336ea1878781780a59fc8e7)
- [dax/cxl, hmem: Initialize hmem early and defer dax_cxl binding](https://github.com/torvalds/linux/commit/39aa1d4be12bf9f685adaa06aa2d997c1c611b16)
- [dax/hmem: Gate Soft Reserved deferral on DEV_DAX_CXL](https://github.com/torvalds/linux/commit/edfcf1e21e79ddd6990a1330597c2eb072330832)
- [dax/hmem: Request cxl_acpi and cxl_pci before walking Soft Reserved ranges](https://github.com/torvalds/linux/commit/7b4bcaadfe00e2447c84378291e854ea87a2a41c)
- [dax/hmem: Factor HMEM registration into __hmem_register_device()](https://github.com/torvalds/linux/commit/116be1e112cbcb664887e44b74f27316a5fef861)
- [dax/bus: Use dax_region_put() in alloc_dax_region() error path](https://github.com/torvalds/linux/commit/14f2e2ebf31157a873536a7212502bd955b69647)
