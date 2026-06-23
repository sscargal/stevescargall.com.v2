---
title: "Linux Kernel v6.16 is Released: This is What's New for Compute Express Link (CXL)"
meta_title: "Linux Kernel v6.16: CXL & DAX Driver Changes"
description: "Explore all 35 CXL and DAX driver changes in Linux Kernel v6.16: 6 bug fixes, 8 refactoring cleanups, 3 documentation updates, and 18 new feature improvements."
date: 2025-07-27T00:00:00Z
image: "featured_image.webp"
categories: ["CXL"]
author: "Steve Scargall"
tags: ["CXL", "Linux", "Kernel"]
draft: false
aliases:
---

The Linux Kernel v6.16 release brings several improvements and additions related to Compute Express Link (CXL) technology.

## Release Highlights

Linux Kernel v6.16 includes **37 commits** to the CXL and DAX subsystems:

| Category | Commits |
|---|---|
| New Features & Hardware | 2 |
| Bug Fixes | 6 |
| Refactoring & Cleanup | 8 |
| Documentation | 3 |
| Other | 18 |

The Linux v6.16 kernel cycle is dominated by one clear theme: hardening CXL memory device reliability and serviceability through the EDAC subsystem. Four new control features land in this release — patrol scrub, Error Check Scrub (ECS), soft Post Package Repair (PPR), and memory sparing — each exposing a distinct class of CXL 3.0 memory maintenance operations to userspace through a consistent sysfs interface. Alongside these, support for the `PERFORM_MAINTENANCE` command provides the underlying mechanism that drives scrub and repair operations on compliant devices. Taken together, this work moves CXL from a device class that Linux can merely enumerate and map to one where the kernel actively participates in proactive memory health management.

The EDAC additions are not without rough edges that needed immediate attention. Several fixes accompany the new code: a wrong repair type being passed when checking DRAM event records, a miscalculation in the minimum scrub cycle for a region, memory leaks in error paths, and a return value bug in `cxlctl_validate_set_features()`. This pattern of feature-plus-fixes in the same release reflects the pace at which CXL 3.0 RAS infrastructure is being built out — the plumbing is going in fast, and correctness gaps are being closed in the same merge window. The `cxl/ras` CPER handler also received a fix for device confusion, where error records were being attributed to the wrong device under certain topologies.

Outside of EDAC, the `cxl/region` code saw meaningful internal restructuring. Decoder lookup logic was factored into dedicated helpers (`cxl_port_pick_region_decoder()`, a new function to find a switch decoder by range, and root decoder extraction routines), reducing duplication and making the region assembly path easier to reason about. A correctness fix eliminates unnecessary interleave granularity constraints when `ways=1`, and the ACPI path now validates CHBS structure length for CXL 2.0 hosts. The CXL Maturity Map documentation was also updated, reflecting the growing breadth of what the driver actually implements.

### Key Changes

- **Patrol scrub and ECS control features**: New sysfs-exposed interfaces allow userspace to configure and trigger patrol scrub and Error Check Scrub on CXL memory devices, enabling scheduled background error detection without requiring a reboot or vendor-specific tooling.

- **Soft PPR and memory sparing control**: Soft Post Package Repair and memory sparing can now be initiated through the kernel's EDAC interface, giving RAS frameworks the ability to retire faulty DRAM rows or activate spare banks on CXL 3.0 devices in response to correctable error thresholds.

- **`PERFORM_MAINTENANCE` command support**: The CXL mailbox command that drives scrub and repair operations is now wired up in `cxl/edac`, providing the execution path that the patrol scrub and PPR control features depend on.

- **Memory operation attribute discovery**: The driver can now query a device's current-boot memory operation attributes, allowing it to reconcile in-flight maintenance state across a kexec or driver reload rather than starting blind.

- **CPER handler device confusion fix**: The `cxl/ras` CPER error record handler was misidentifying the target device under multi-device topologies; the fix ensures correctable and uncorrectable errors are charged to the correct CXL endpoint.

- **Region decoder lookup refactoring**: Root and switch decoder selection logic in `cxl/region` has been extracted into named helpers and deduplicated, removing a redundant call to `cxl_port_pick_region_decoder()` that could produce incorrect results during region assembly.

- **Interleave granularity relaxed for single-way regions**: When a CXL region uses only one interleave way, granularity constraints are now ignored during validation, unblocking configurations that were incorrectly rejected.

- **DAX kmem truncation warning**: The DAX subsystem now emits a warning when a `kmem` region must be truncated to align with memory block boundaries, making a previously silent data-availability reduction visible to system administrators.

## CXL related changes from Kernel v6.15 to v6.16

Here is the detailed list of all commits merged into the 6.16 Kernel for CXL and DAX. This list was generated by the [Linux Kernel CXL Feature Tracker](https://github.com/sscargal/linux-cxl-tracker).

- [cxl/edac: Fix using wrong repair type to check dram event record](https://github.com/torvalds/linux/commit/0a46f60a9fe16f5596b6b4b3ee1a483ea7854136)
- [cxl/ras: Fix CPER handler device confusion](https://github.com/torvalds/linux/commit/3c70ec71abdaf4e4fa48cd8fdfbbd864d78235a8)
- [cxl/edac: Fix potential memory leak issues](https://github.com/torvalds/linux/commit/a403fe6c0b17f472e01246eb350f5eef105243ac)
- [cxl/edac: Fix the min_scrub_cycle of a region miscalculation](https://github.com/torvalds/linux/commit/fdc9be90929081ed5a9658583aa5f3121d5e8365)
- [cxl: fix return value in cxlctl_validate_set_features()](https://github.com/torvalds/linux/commit/87b42c114cdda76c8ad3002f2096699ad5146cb3)
- [Merge branch 'for-6.16/cxl-features-ras' into cxl-for-next](https://github.com/torvalds/linux/commit/9f153b7fb5ae45c7d426851f896487927f40e501)
- [cxl/edac: Add CXL memory device soft PPR control feature](https://github.com/torvalds/linux/commit/be9b359e056a78bb6cc2e17cf457338f6aef57f9)
- [cxl/edac: Add CXL memory device memory sparing control feature](https://github.com/torvalds/linux/commit/588ca944c27729c7f950d1f44c6d6700a919969a)
- [cxl/edac: Support for finding memory operation attributes from the current boot](https://github.com/torvalds/linux/commit/0b5ccb0de1e2cf83f18f012f0e6ba4365be9dd4b)
- [cxl/edac: Add support for PERFORM_MAINTENANCE command](https://github.com/torvalds/linux/commit/077ee5f7ddcfd482ecac504b3f711aa5e4c049fe)
- [cxl/edac: Add CXL memory device ECS control feature](https://github.com/torvalds/linux/commit/85fb6a16ad14eab95e98bbba4f7d361f5cb83746)
- [cxl/edac: Add CXL memory device patrol scrub control feature](https://github.com/torvalds/linux/commit/0c6e6f1357cbdc158d555346a728aa4aeb0d7011)
- [cxl: Update prototype of function get_support_feature_info()](https://github.com/torvalds/linux/commit/f76e0bbc8bc34c55fd5da569b9e1126cf42b09ec)
- [cxl/features: Remove the inline specifier from to_cxlfs()](https://github.com/torvalds/linux/commit/bfc6270ab3ff9478a4cad4d49482854d632dbce3)
- [cxl/feature: Remove redundant code of get supported features](https://github.com/torvalds/linux/commit/6eed708a5693709ff0d4dd8512b6934be30d4283)
- [Documentation: Update the CXL Maturity Map](https://github.com/torvalds/linux/commit/f97bdc61c76f654effa7b78e10338e64794da9fd)
- [cxl: Sync up the driver-api/cxl documentation](https://github.com/torvalds/linux/commit/d542461211543522daecb34b7972d8ac1044bc97)
- [cxl/hdm: Clean up a debug printk](https://github.com/torvalds/linux/commit/a223ce195741ca4f1a0e1a44f3e75ce5662b6c06)
- [Merge branch 'for-6.16/cxl-cleanups' into cxl-for-next](https://github.com/torvalds/linux/commit/68d8b4f399e78a7be2bc69530c7e4b3e79fde9db)
- [cxl: Add a dev_dbg() when a decoder was added to a port](https://github.com/torvalds/linux/commit/98a863fee2406f92cf172659b2390212e72a3313)
- [cxl/region: Add a dev_err() on missing target list entries](https://github.com/torvalds/linux/commit/d90acdf49e18029cfe4194475c45ef143657737a)
- [cxl/region: Add a dev_warn() on registration failure](https://github.com/torvalds/linux/commit/9efefa1c6f2c30e8c8adc0236b27fef4c458c148)
- [cxl/region: Add function to find a port's switch decoder by range](https://github.com/torvalds/linux/commit/d6879d8cfb81b759fee5532ec143b520edfd6905)
- [cxl/region: Factor out code to find a root decoder's region](https://github.com/torvalds/linux/commit/868a8f1f045bce791c3123845075ee9a82a9fe4c)
- [cxl/region: Factor out code to find the root decoder](https://github.com/torvalds/linux/commit/9466ee981647a8655e7f8312ae89aba665d78918)
- [cxl/port: Replace put_cxl_root() by a cleanup helper](https://github.com/torvalds/linux/commit/74bf125abd87297b559eb72043e4677550d3a790)
- [cxl/region: Move find_cxl_root() to cxl_add_to_region()](https://github.com/torvalds/linux/commit/5ed826fc4bc6073e0083ed30c10f6a54da06b83b)
- [cxl/region: Avoid duplicate call of cxl_port_pick_region_decoder()](https://github.com/torvalds/linux/commit/0ee2d97810b9b1626d31a63f4a166f0a310b78e5)
- [cxl/region: Rename function to cxl_port_pick_region_decoder()](https://github.com/torvalds/linux/commit/a3a96873b21ebd5ddac694faf62fcccc60b84254)
- [cxl: Introduce parent_port_of() helper](https://github.com/torvalds/linux/commit/99ff9060b2c9d1e598cb0dc74187d3400aae26d6)
- [cxl/pci: Add comments to cxl_hdm_decode_init()](https://github.com/torvalds/linux/commit/88bc0503c464a261ecac3bf2a4dabcf082f1b0d9)
- [cxl/pci: Moving code in cxl_hdm_decode_init()](https://github.com/torvalds/linux/commit/d858631b1caed429c519f9e8f59b4848b27bc5a5)
- [cxl: Remove else after return](https://github.com/torvalds/linux/commit/21339b30f027dccab55cfe6d9bb69825e4d17fb7)
- [cxl: core/region - ignore interleave granularity when ways=1](https://github.com/torvalds/linux/commit/ce32b0c9c522e5a69ef9c62a56d6ca08fb036d67)
- [cxl/acpi: Verify CHBS length for CXL2.0](https://github.com/torvalds/linux/commit/89963d5e6906241f5f68fa0899e2895437c7fd4b)
- [cxl: Remove always true condition for cxlctl_validate_hw_command()](https://github.com/torvalds/linux/commit/cdafa67c0270116b0f4cdbd00b6170eb9aa92edf)
- [DAX: warn when kmem regions are truncated for memory block alignment](https://github.com/torvalds/linux/commit/3592a86a2b6be115000b82af78fe7f96fbc658a4)
