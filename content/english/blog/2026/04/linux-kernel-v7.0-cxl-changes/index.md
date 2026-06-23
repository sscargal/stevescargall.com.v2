---
title: "Linux Kernel v7.0 is Released: This is What's New for Compute Express Link (CXL)"
meta_title: "Linux Kernel 7.0 CXL Changes: New Features & Bug Fixes"
description: "Linux Kernel 7.0 brings 71 CXL and DAX subsystem commits: 3 new hardware features, 11 bug fixes, 9 refactoring cleanups, and 48 general improvements over v6.19."
date: 2026-04-12T00:00:00Z
image: "featured_image.webp"
categories: ["CXL"]
author: "Steve Scargall"
tags: ["CXL", "Linux", "Kernel"]
draft: false
aliases:
---

The Linux Kernel v7.0 release brings several improvements and additions related to Compute Express Link (CXL) technology.

## Release Highlights

Linux Kernel v7.0 includes **73 commits** to the CXL and DAX subsystems:

| Category | Commits |
|---|---|
| New Features & Hardware | 3 |
| Bug Fixes | 11 |
| Refactoring & Cleanup | 9 |
| Testing | 2 |
| Other | 48 |

Linux v7.0 brings focused but meaningful progress to the CXL/DAX subsystem, with the headline work centered on platform-specific address translation. The `cxl/atl` subsystem gains AMD Zen5 support through the ACPI Platform Runtime Mechanism Table (PRMT), enabling hardware-assisted Host Physical Address (HPA) to System Physical Address (SPA) translation on AMD's latest server platforms. This required scaffolding across several layers: EFI runtime services preparation in `cxl/acpi`, new translation callback hooks, decoder locking for address translation paths, and explicit disabling of these handlers when Normalized Addressing is active — a sign the translation infrastructure is maturing toward multi-vendor, multi-mode support.

Stability receives serious attention in this release. Eleven bug fixes address a range of correctness issues, including a use-after-free in `cxl_detach_ep()` during port teardown, a deadlock in `cxl_memdev_autoremove()` triggered on attach failure, and a race condition around `nvdimm_bus` object creation during nvdimm registration. A fix to HDM decoder fallback logic prevents incorrect DVSEC-based configuration when HDM decoders are already enabled — a subtle but important correctness fix for systems where both mechanisms coexist. Region construction also sees a leak fix and improved separation between parameter setup and construction phases.

On the cleanup front, v7.0 continues consolidating the CXL PCI stack by removing now-redundant helper functions for CXL Virtual Hierarchy, Restricted CXL Host, and Endpoint handling paths that had accumulated in `core/pci.c`. The port subsystem moves dport removal to `devres` groups, and `devm_cxl_add_memdev()` is converted to scope-based cleanup — both reducing manual teardown logic and aligning with modern kernel resource management conventions. Treewide memory allocation modernizations (`kmalloc_obj`, updated default GFP_KERNEL arguments) also sweep through CXL code as part of broader kernel hygiene work.

### Key Changes

- **AMD Zen5 Address Translation via ACPI PRMT**: `cxl/atl` now supports AMD Zen5 platforms using the ACPI Platform Runtime Mechanism Table, enabling hardware-assisted HPA-to-SPA translation for CXL memory. This brings proper CXL interleaving support to AMD's current server-class processors.

- **HPA Translation Callback Infrastructure**: New callback hooks for HPA address range translation are introduced alongside decoder locking for translation paths. Normalized Addressing mode explicitly disables these handlers, establishing a clean separation between address translation modes across different platform configurations.

- **HDM Decoder DVSEC Fallback Correctness Fix**: `cxl/hdm` was incorrectly falling back to DVSEC-based decoder configuration even when HDM decoders were already enabled and active. The fix prevents misconfigured decoder paths on systems where both mechanisms are present.

- **Port and Region Lifecycle Safety**: A use-after-free of `parent_port` in `cxl_detach_ep()` and a memory leak in `__construct_region()` are both resolved. These fixes matter for reliable hotplug and region teardown on production systems.

- **Deadlock and Race Condition Fixes**: `cxl_memdev_autoremove()` could deadlock when an attach operation failed mid-flight; that code path is now corrected. A separate race in nvdimm object creation — where `nvdimm_bus` could be freed while nvdimm objects were still being registered — is also fixed.

- **CXL PCI Stack Consolidation**: Redundant helper functions for CXL VH, RCH, and Endpoint handling are removed from `core/pci.c`, along with a stale `FIXME` comment and its associated `BUILD_BUG_ON`. This trims dead code and simplifies the boundary between the CXL core and the PCI integration layer.

- **`cxl_memdev_attach` for Ordered Device Initialization**: A new `cxl_memdev_attach` interface coordinates setup of CXL-dependent operations, giving drivers a structured hook for initialization that depends on memory device attachment completing successfully.

- **Port and Memdev Resource Management Improvements**: Dport removal in `cxl/port` is now managed via `devres` groups rather than manual teardown, and `devm_cxl_add_memdev()` is converted to scope-based cleanup. Both changes reduce error-prone manual resource ordering in teardown paths.

## CXL related changes from Kernel v6.19 to v7.0

Here is the detailed list of all commits merged into the 7.0 Kernel for CXL and DAX. This list was generated by the [Linux Kernel CXL Feature Tracker](https://github.com/sscargal/linux-cxl-tracker).

- [cxl: Adjust the startup priority of cxl_pmem to be higher than that of cxl_acpi](https://github.com/torvalds/linux/commit/be5c5280cf2b20e363dc8e2a424dd200a29b1c77)
- [cxl/mbox: Use proper endpoint validity check upon sanitize](https://github.com/torvalds/linux/commit/9a6a2091324ab6525951651b3700e3bea0fe9a89)
- [cxl/hdm: Avoid incorrect DVSEC fallback when HDM decoders are enabled](https://github.com/torvalds/linux/commit/75cea0776de502f2a1be5ca02d37c586dc81887e)
- [cxl/acpi: Fix CXL_ACPI and CXL_PMEM Kconfig tristate mismatch](https://github.com/torvalds/linux/commit/93d0fcdddc9e7be9d4f42acbe57bc90dbb0fe75d)
- [cxl/region: Fix leakage in __construct_region()](https://github.com/torvalds/linux/commit/77b310bb7b5ff8c017524df83292e0242ba89791)
- [cxl/port: Fix use after free of parent_port in cxl_detach_ep()](https://github.com/torvalds/linux/commit/19d2f0b97a131198efc2c4ca3eb7f980bba8c2b4)
- [cxl/region: Test CXL_DECODER_F_NORMALIZED_ADDRESSING as a bitmask](https://github.com/torvalds/linux/commit/e46f25f5a81f6f1a9ab93bcda80d5dfaea9f4897)
- [cxl: Test CXL_DECODER_F_LOCK as a bitmask](https://github.com/torvalds/linux/commit/0a70b7cd397e545e926c93715ff6366b67c716f6)
- [cxl/mbox: validate payload size before accessing contents in cxl_payload_from_user_allowed()](https://github.com/torvalds/linux/commit/60b5d1f68338aff2c5af0113f04aefa7169c50c2)
- [cxl: Fix race of nvdimm_bus object when creating nvdimm objects](https://github.com/torvalds/linux/commit/96a1fd0d84b17360840f344826897fa71049870e)
- [cxl: Move devm_cxl_add_nvdimm_bridge() to cxl_pmem.ko](https://github.com/torvalds/linux/commit/e7e222ad73d93fe54d6e6e3a15253a0ecf081a1b)
- [cxl/port: Hold port host lock during dport adding.](https://github.com/torvalds/linux/commit/0066688dbcdcf51680f499936faffe6d0e94194e)
- [cxl/port: Introduce port_to_host() helper](https://github.com/torvalds/linux/commit/822655e6751dde2df7ddaa828c5aba217726c5a2)
- [cxl/memdev: fix deadlock in cxl_memdev_autoremove() on attach failure](https://github.com/torvalds/linux/commit/318c58852e686c009825ae8c071080b9ccdd2af0)
- [Convert 'alloc_flex' family to use the new default GFP_KERNEL argument](https://github.com/torvalds/linux/commit/323bbfcf1ef8836d0d2ad9e2c1f1c684f0e3b5b3)
- [Convert 'alloc_obj' family to use the new default GFP_KERNEL argument](https://github.com/torvalds/linux/commit/bf4afc53b77aeaa48b5409da5c8da6bb4eff7f43)
- [treewide: Replace kmalloc with kmalloc_obj for non-scalar types](https://github.com/torvalds/linux/commit/69050f8d6d075dc01af7a5f2f550a8067510366f)
- [Merge tag 'cxl-for-7.0' of git://git.kernel.org/pub/scm/linux/kernel/git/cxl/cxl](https://github.com/torvalds/linux/commit/e812928be2ee1c2744adf20ed04e0ce1e2fc5c13)
- [Merge branch 'acpi-apei'](https://github.com/torvalds/linux/commit/dfa5dc3ad3b15a519101f134ed76c068526004e4)
- [Merge branch 'for-7.0/cxl-prm-translation' into cxl-for-next](https://github.com/torvalds/linux/commit/63fbf275fa9f18f7020fb8acf54fa107e51d0f23)
- [cxl: Disable HPA/SPA translation handlers for Normalized Addressing](https://github.com/torvalds/linux/commit/208f432406b7ed446c061d68cc73efd85b575d3f)
- [cxl/region: Factor out code into cxl_region_setup_poison()](https://github.com/torvalds/linux/commit/d1c9ba46d6c36ff8d5b5f83ae28eae4132e46988)
- [cxl/atl: Lock decoders that need address translation](https://github.com/torvalds/linux/commit/a2e794895089c1356b7687e8df1fa7d224d40bb6)
- [cxl: Enable AMD Zen5 address translation using ACPI PRMT](https://github.com/torvalds/linux/commit/af74daf91652f15b82560bb93850d2ec8bbfa976)
- [cxl/acpi: Prepare use of EFI runtime services](https://github.com/torvalds/linux/commit/7be03eae1fdb690dff8f102a7306ca61b55a810c)
- [cxl: Introduce callback for HPA address ranges translation](https://github.com/torvalds/linux/commit/a31af41115b0f7021a86f5439cb8720b93314f91)
- [cxl/region: Use region data to get the root decoder](https://github.com/torvalds/linux/commit/d01149bbe76d81d360ed24853d5247fcaad873e4)
- [cxl/region: Add @hpa_range argument to function cxl_calc_interleave_pos()](https://github.com/torvalds/linux/commit/1fd6c38fc5e18a9904bc1bd447bb4c2708f0292d)
- [cxl/region: Separate region parameter setup and region construction](https://github.com/torvalds/linux/commit/bc01fd5019faa14f4253de6f6abcae6d957c3a12)
- [cxl: Simplify cxl_root_ops allocation and handling](https://github.com/torvalds/linux/commit/3e422caa40d0d4bf25ece6e82418ce642d56524a)
- [cxl/region: Store HPA range in struct cxl_region](https://github.com/torvalds/linux/commit/98ceb1a42dab91c6dcf95d1d424cba61b0f9bc5c)
- [cxl/region: Store root decoder in struct cxl_region](https://github.com/torvalds/linux/commit/4fe82279580d10ba63c1461ff404f2c6c82ff1d5)
- [cxl/region: Rename misleading variable name @hpa to @hpa_range](https://github.com/torvalds/linux/commit/df8b57c34b47e0acbe1133ca58ac75ec3c56771f)
- [Merge branch 'for-7.0/cxl-aer-prep' into cxl-for-next](https://github.com/torvalds/linux/commit/0da3050bdded5f121aaca6b5247ea50681d7129e)
- [cxl/port: Unify endpoint and switch port lookup](https://github.com/torvalds/linux/commit/2d2b3fe002797c8de2c71236662593bf36de834d)
- [cxl/port: Move endpoint component register management to cxl_port](https://github.com/torvalds/linux/commit/dab7162d0ae782295c2c2cff4bb386ee6ae5d566)
- [cxl/port: Map Port RAS registers](https://github.com/torvalds/linux/commit/ef1df6cf69785ec6c949ecfa92c49cfc5e237576)
- [cxl/port: Move dport RAS setup to dport add time](https://github.com/torvalds/linux/commit/7f5ff740ce0bcde242dafcc3f9bb3cbe6b5b8f3a)
- [cxl/port: Move dport probe operations to a driver event](https://github.com/torvalds/linux/commit/3864cb60dad5a6c1bd9f444740cf541a1d8cda99)
- [cxl/port: Move decoder setup before dport creation](https://github.com/torvalds/linux/commit/86e756715db22cd79a9726c22644415c46b6b149)
- [cxl/port: Cleanup dport removal with a devres group](https://github.com/torvalds/linux/commit/afa2bdba1ee28e21f30fe5391b0273b58b32e0d3)
- [cxl/port: Reduce number of @dport variables in cxl_port_add_dport()](https://github.com/torvalds/linux/commit/83ccbaf1a1075ded82329d27de01d3b2681986ec)
- [cxl/port: Cleanup handling of the nr_dports 0 -> 1 transition](https://github.com/torvalds/linux/commit/47fec713d97fb6b823026f723435b58af541bd8d)
- [Merge branch 'for-7.0/cxl-misc' into cxl-for-next](https://github.com/torvalds/linux/commit/63050be0bfe0b280cce5d701b31940fd84858609)
- [cxl: Fix premature commit_end increment on decoder commit failure](https://github.com/torvalds/linux/commit/7b6f9d9b1ea05c9c22570126547c780e8c6c3f62)
- [Merge branch 'for-7.0/cxl-init' into cxl-for-next](https://github.com/torvalds/linux/commit/3f7938b1aec7f06d5b23adca83e4542fcf027001)
- [Merge branch 'for-7.0/cxl-aer-prep' into cxl-for-next](https://github.com/torvalds/linux/commit/914c743509d56067eeeb2b5e341a44a68ef8377d)
- [cxl/region: Use do_div() for 64-bit modulo operation](https://github.com/torvalds/linux/commit/064c098790944fa44f6aa704eb55a5c3ed65a2fa)
- [cxl/region: Translate HPA to DPA and memdev in unaligned regions](https://github.com/torvalds/linux/commit/b51792fd9168e581e51be98e22df5f79454e22de)
- [cxl/region: Translate DPA->HPA in unaligned MOD3 regions](https://github.com/torvalds/linux/commit/e639055f1f30311db91cafb36e408cc727c7d445)
- [cxl/core: Fix cxl_dport debugfs EINJ entries](https://github.com/torvalds/linux/commit/4ed7952b9e87cf731ebc8251874416e60eb15230)
- [cxl/acpi: Remove cxl_acpi_set_cache_size()](https://github.com/torvalds/linux/commit/99698e70148fbce4410799570adac8456204fa37)
- [cxl/hdm: Fix newline character in dev_err() messages](https://github.com/torvalds/linux/commit/e5b1887619403c2da25a5899cad3e1ab34e7717f)
- [cxl/pci: Remove outdated FIXME comment and BUILD_BUG_ON](https://github.com/torvalds/linux/commit/4dd05f02f1d618da610e7d3bd479c47a96b4fc3f)
- [cxl: Update RAS handler interfaces to also support CXL Ports](https://github.com/torvalds/linux/commit/9a8920ca8ebfb99604f639e7fbc681d0d04518a0)
- [cxl/mem: Clarify @host for devm_cxl_add_nvdimm()](https://github.com/torvalds/linux/commit/f953b7d5e19a1310dd5d92b86bafc5957847b4d6)
- [cxl/pci: Move CXL driver's RCH error handling into core/ras_rch.c](https://github.com/torvalds/linux/commit/0ff60f2ec3e4043a442e805f80f8a2445113ec8f)
- [PCI/AER: Replace PCIEAER_CXL symbol with CXL_RAS](https://github.com/torvalds/linux/commit/d18f1b7beadf1af1cd334ff789ba5a07ce285bbc)
- [cxl/pci: Remove CXL VH handling in CONFIG_PCIEAER_CXL conditional blocks from core/pci.c](https://github.com/torvalds/linux/commit/7ff8b1d60881c5f97b5ae426e14d2822917d3b69)
- [cxl/pci: Remove unnecessary CXL RCH handling helper functions](https://github.com/torvalds/linux/commit/eb78ef4d6f0e51243c1ee117f801dbc503e886ab)
- [cxl/pci: Remove unnecessary CXL Endpoint handling helper functions](https://github.com/torvalds/linux/commit/ca3d1a53e62093d17436abd447463da9c0f4e56b)
- [PCI: Update CXL DVSEC definitions](https://github.com/torvalds/linux/commit/6612bd9ff0b1001cff5f5d79db6ce44427d2e99c)
- [PCI: Move CXL DVSEC definitions into uapi/linux/pci_regs.h](https://github.com/torvalds/linux/commit/0f7afd80d81b739c4a9a6e4e24109ba1030c9c56)
- [ACPI: extlog: Trace CPER CXL Protocol Error Section](https://github.com/torvalds/linux/commit/95350effc3ad62582411f59fd08a7621ac82f314)
- [cxl/mem: Introduce cxl_memdev_attach for CXL-dependent operation](https://github.com/torvalds/linux/commit/29317f8dc6ed601ec54575689c2cd55cc470bcce)
- [cxl/mem: Drop @host argument to devm_cxl_add_memdev()](https://github.com/torvalds/linux/commit/f2546eba53bbe38c4bb950f78625ccf4b1a2cbc8)
- [cxl/mem: Convert devm_cxl_add_memdev() to scope-based-cleanup](https://github.com/torvalds/linux/commit/6e1d21903ff213f1384ce43daa279c0965904116)
- [cxl/port: Arrange for always synchronous endpoint attach](https://github.com/torvalds/linux/commit/ae201a0092362ffdec7206efa1ec85e260fab8d2)
- [cxl/mem: Arrange for always-synchronous memdev attach](https://github.com/torvalds/linux/commit/1f1cb7f0c25574cf51501f8c8cece0047d7e8848)
- [cxl/mem: Fix devm_cxl_memdev_edac_release() confusion](https://github.com/torvalds/linux/commit/10016118b6fade907143a32a7aeaa777063dc79c)
- [Merge tag 'mm-stable-2026-02-18-19-48' of git://git.kernel.org/pub/scm/linux/kernel/git/akpm/mm](https://github.com/torvalds/linux/commit/eeccf287a2a517954b57cf9d733b3cf5d47afa34)
- [mm: update all remaining mmap_prepare users to use vma_flags_t](https://github.com/torvalds/linux/commit/5bd2c0650a9030007af5c2cf2a01dccdc67a6991)
- [dax/hmem, e820, resource: Defer Soft Reserved insertion until hmem is ready](https://github.com/torvalds/linux/commit/bc62f5b308cbdedf29132fe96e9d591e526527e1)
