---
title: "Linux Kernel v6.18 is Released: This is What's New for Compute Express Link (CXL)"
meta_title: "Linux Kernel v6.18 CXL Changes: New Features & Fixes"
description: "Explore all CXL and DAX subsystem changes in Linux Kernel v6.18: 4 bug fixes, 5 cleanup patches, and 20 feature updates advancing Compute Express Link support."
date: 2025-11-30T00:00:00Z
image: "featured_image.webp"
categories: ["CXL"]
author: "Steve Scargall"
tags: ["CXL", "Linux", "Kernel"]
draft: false
aliases:
---

The Linux Kernel v6.18 release brings several improvements and additions related to Compute Express Link (CXL) technology.

## Release Highlights

Linux Kernel v6.18 includes **32 commits** to the CXL and DAX subsystems:

| Category | Commits |
|---|---|
| New Features & Hardware | 1 |
| Bug Fixes | 4 |
| Refactoring & Cleanup | 5 |
| Testing | 2 |
| Other | 20 |

The v6.18 kernel cycle for CXL/DAX is defined by two architectural threads running in parallel: hardening the address-translation stack and untangling port initialization from topology discovery. On the translation side, the new SPA-to-DPA region mapping infrastructure lands alongside a dedicated root-decoder ops structure that formalizes how the host physical address space is projected into CXL's device physical address space — including XOR-interleaving math that was previously implicit. These foundations make region geometry computable and auditable in ways that earlier releases left to convention.

Port and dport lifecycle management received significant rework. Register setup for switch ports is now deferred until the first downstream port actually appears, rather than being triggered speculatively at port creation time. A matching helper to delete dports and a topology-detection helper for the root of the CXL device tree give drivers cleaner primitives to reason about partially-populated fabrics. The SSLBIS handler was simultaneously narrowed to a single-dport model, removing ambiguity in how system locality information propagates through switches.

The HMAT coupling that previously forced CXL access-coordinate updates to travel through the ACPI HMAT path is gone. CXL now writes its access coordinates directly, which removes a layering dependency and eliminates the now-dead `hmat_update_target_coordinates()` helper. On the observability side, poison injection gains region-level offset addressing and locked variants of the inject/clear functions, while the `cxl_poison` trace event correctly subtracts to recover the `hpa_alias0` — fixing a latent calculation error in the tracing path.

### Key Changes

- **SPA-to-DPA address translation**: A new region-level mapping between System Physical Addresses and Device Physical Addresses is introduced, giving the CXL subsystem a formal, queryable translation layer rather than relying on implicit arithmetic scattered across drivers.

- **Root decoder ops and XOR math**: The `hpa_to_spa` callback is promoted into a structured `cxl_root_decoder_ops`, and a dedicated callback for XOR-based interleave math is wired in. This makes non-standard interleave topologies first-class citizens in the decoder model.

- **Deferred dport and port register setup**: Switch port component registers are now set up only when the first downstream port is discovered, rather than at port creation. Combined with a new dport-deletion helper, this makes hot-plug and partial-topology scenarios substantially less error-prone.

- **Direct CXL access coordinate updates**: CXL no longer routes access-coordinate data through HMAT; it writes coordinates directly. This removes an ACPI layering dependency and deletes `hmat_update_target_coordinates()`, which had become dead code.

- **Region-level poison injection**: Poison can now be injected and cleared by region offset rather than only by raw device address. Locked variants of the inject/clear functions are also added so callers that already hold the region lock do not need to drop it.

- **SSLBIS single-dport enforcement**: The system-locality-based bandwidth and latency information (SSLBIS) handler is restricted to operate on a single downstream port, fixing an implicit assumption that previously allowed multi-dport ambiguity to silently produce incorrect locality data.

- **ACPI and resource fixes**: `cxl_acpi_set_cache_size()` had an incorrect memory resource setup that could misconfigure cache-capable regions; this is corrected. The CFMW coherency restriction fields are also renamed to match the current CXL specification terminology, reducing confusion when reading ACPI CEDT tables.

- **`match_region_by_range()` fix**: The region-range matching function was not calling `region_res_match_cxl_range()`, meaning region lookups could silently return incorrect results for non-trivial interleave configurations. The fix ensures the correct range-comparison helper is always used.

## CXL related changes from Kernel v6.17 to v6.18

Here is the detailed list of all commits merged into the 6.18 Kernel for CXL and DAX. This list was generated by the [Linux Kernel CXL Feature Tracker](https://github.com/sscargal/linux-cxl-tracker).

- [cxl: Adjust offset calculation for poison injection](https://github.com/torvalds/linux/commit/b6cfddd26ec55e865b4715f73e9bbb17a15091ed)
- [cxl/trace: Subtract to find an hpa_alias0 in cxl_poison events](https://github.com/torvalds/linux/commit/a4bbb493a3247ef32f6191fd8b2a0657139f8e08)
- [cxl/region: Use %pa printk format to emit resource_size_t](https://github.com/torvalds/linux/commit/257c4b03a2f7d8c15f79c79b09a561af9734f6c4)
- [cxl: Fix match_region_by_range() to use region_res_match_cxl_range()](https://github.com/torvalds/linux/commit/f4d027921c811ff7fc16e4d03c6bbbf4347cf37a)
- [cxl: Set range param for region_res_match_cxl_range() as const](https://github.com/torvalds/linux/commit/0f6f1982cb28abf1b8a3a8ba906e2c6ade6a70e8)
- [cxl/acpi: Fix setup of memory resource in cxl_acpi_set_cache_size()](https://github.com/torvalds/linux/commit/2e41e5a91a37202ff6743c3ae5329e106aeb1c6c)
- [cxl/features: Add check for no entries in cxl_feature_info](https://github.com/torvalds/linux/commit/a375246fcf2bbdaeb1df7fa7ee5a8b884a89085e)
- [cxl/port: Avoid missing port component registers setup](https://github.com/torvalds/linux/commit/02e7567f5da023524476053a38c54f4f19130959)
- [Merge branch 'for-6.18/cxl-delay-dport' into cxl-for-next](https://github.com/torvalds/linux/commit/46037455cbb748c5e85071c95f2244e81986eb58)
- [cxl: Move port register setup to when first dport appear](https://github.com/torvalds/linux/commit/f6ee24913de24dbda8d49213e1a27f5e1a5204cc)
- [cxl: Change sslbis handler to only handle single dport](https://github.com/torvalds/linux/commit/d64035a5a37741b25712fb9c2f6aca535c2967ea)
- [cxl/test: Adjust the mock version of devm_cxl_switch_port_decoders_setup()](https://github.com/torvalds/linux/commit/644685abc16b58b3afcc2feb0ac14e86476ca2ed)
- [cxl/test: Add mock version of devm_cxl_add_dport_by_dev()](https://github.com/torvalds/linux/commit/d96eb90d9ca6e4652c8a23d48c94364aa061fdc4)
- [cxl: Defer dport allocation for switch ports](https://github.com/torvalds/linux/commit/4f06d81e7c6a02f850bfe9812295b1e859ab2db0)
- [cxl/test: Refactor decoder setup to reduce cxl_test burden](https://github.com/torvalds/linux/commit/68d5d9734c12fce20ad493fe24738ab2019108c0)
- [cxl: Add a cached copy of target_map to cxl_decoder](https://github.com/torvalds/linux/commit/02edab6ceefaaf8cb917e864d8c26dbac0ea9686)
- [cxl: Add helper to delete dport](https://github.com/torvalds/linux/commit/8330671c57c7056ef5e1e8dccfcdda7d5fe6d0b0)
- [cxl: Add helper to detect top of CXL device topology](https://github.com/torvalds/linux/commit/4fde89539a18d39169a511fda00db65eeba1a8e0)
- [cxl/acpi: Rename CFMW coherency restrictions](https://github.com/torvalds/linux/commit/c4272905c37930c19b54fa3549b22899122ce69e)
- [Merge branch 'for-6.18/cxl-update-access-coordinates' into cxl-for-next](https://github.com/torvalds/linux/commit/4dfa64181f23079077c7c1f7e9c342661f66f1d5)
- [acpi/hmat: Remove now unused hmat_update_target_coordinates()](https://github.com/torvalds/linux/commit/e99ecbc4c89adf551cccbbc00b5cb08c50969af6)
- [cxl, acpi/hmat: Update CXL access coordinates directly instead of through HMAT](https://github.com/torvalds/linux/commit/2e454fb8056df6da4bba7d89a57bf60e217463c0)
- [cxl: Fix emit of type resource_size_t argument for validate_region_offset()](https://github.com/torvalds/linux/commit/e6a9530b3ee7407b70b60e4df70688db0d239e1a)
- [Merge branch 'for-6.18/cxl-poison-inject' into cxl-for-next](https://github.com/torvalds/linux/commit/d9412f08e25a5b66f9021739c090cc9b8f1089b1)
- [cxl/region: Add inject and clear poison by region offset](https://github.com/torvalds/linux/commit/c3dd67681c70cc95cc2c889b1b58a1667bb1c48b)
- [cxl/core: Add locked variants of the poison inject and clear funcs](https://github.com/torvalds/linux/commit/25a0207828bc52f1ebb6588f9417eb43ca4960a3)
- [cxl/region: Introduce SPA to DPA address translation](https://github.com/torvalds/linux/commit/dc181170491bda9944f95ca39017667fe7fd767d)
- [cxl: Define a SPA->CXL HPA root decoder callback for XOR Math](https://github.com/torvalds/linux/commit/b83ee9614a3ec196111f0ae54335b99700f78b45)
- [cxl: Move hpa_to_spa callback to a new root decoder ops structure](https://github.com/torvalds/linux/commit/524b2b76f365fb90a7f894ac17261ea760464e2c)
- [cxl/region: use str_enabled_disabled() instead of ternary operator](https://github.com/torvalds/linux/commit/733c4e9bcec9c481afee3891218277d9ecd06599)
- [cxl/hdm: Use str_plural() to simplify the code](https://github.com/torvalds/linux/commit/22fb4ad898853323f4943de3e0dc555915547ccc)
- [fs: rename generic_delete_inode() and generic_drop_inode()](https://github.com/torvalds/linux/commit/f99b3917789d83ea89b24b722d784956f8289f45)
