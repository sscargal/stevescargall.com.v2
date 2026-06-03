---
title: "CXL Server Buyer's Guide: A Complete List of GA Platforms"
meta_title: "CXL Server Buyer's Guide: GA Vendor & Model List"
description: "Your complete buyer's guide to generally available (GA) CXL servers. Compare models, specs, and CXL features from top vendors like Dell, HPE, Lenovo, and Supermicro."
date: 2025-06-27T16:35:01Z
image: "featured_image.webp"
categories: ["CXL", "Servers", "Data Center"]
author: "Steve Scargall"
tags: ["CXL", "Servers", "Buyer's Guide", "Intel", "AMD", "Dell", "HPE", "Lenovo", "Supermicro", "Data Center", "CXL 2.0", "CXL 1.1", "CXL 1.0", "CXL 3.0"]
draft: false
---

**Last Updated: June 2, 2026**

This quick-reference guide provides a definitive, up-to-date list of generally available (GA) Compute Express Link (CXL) servers from major OEMs including Dell, HPE, Lenovo, and Supermicro. It is designed for data center architects, engineers, and IT decision-makers who need to identify and compare server platforms that support CXL 1.1 and CXL 2.0 for memory expansion and pooling.

[Compute Express Link (CXL)](https://computeexpresslink.org/) is an open-standard interconnect that enables high-speed, low-latency communication between processors and attached devices such as accelerators and memory expanders. CXL 2.0 adoption has accelerated significantly since 2025, with all major CPU platforms now supporting it natively and the first hyperscale cloud deployments validated in production.

If you know of a GA server that should be included on this list, [please let me know](https://stevescargall.com/contact/).

---

## Key Terminology

- **CXL (Compute Express Link):** An open standard interconnect built on the PCIe physical layer that allows coherent memory sharing between a host processor and attached devices.
- **GA (Generally Available):** The product is officially released and can be ordered from the vendor.
- **AIC (Add-In Card):** A CXL device packaged in a standard PCIe card format installed in a server's PCIe slots.
- **E3.S (EDSFF 3" Short):** A compact, hot-swappable form factor for CXL memory modules, designed for dense server designs.
- **MRDIMM (Multiplexed Registered DIMM):** A new DIMM type supported by Intel Xeon 6 offering higher memory bandwidth (up to 8800 MT/s) than standard RDIMMs.
- **CXL Flat Memory Mode:** An Intel Xeon 6 feature allowing the CPU to treat a mix of local DRAM and CXL-attached memory as a unified pool.

## Understanding the Table Columns

| Column | Description |
|---|---|
| **OEM Vendor** | The original equipment manufacturer of the server. |
| **Server Model** | The specific product name or model number. |
| **CPU Vendor** | The processor manufacturer (Intel or AMD). CXL support is tied directly to the CPU generation. |
| **CPU Generation** | The processor family (e.g., Xeon 6, EPYC Turin). Helps identify when a platform was introduced. |
| **Rack Height (U)** | The physical height of the server in standard rack units. |
| **CXL Version** | The CXL specification version supported by the server's CPU and motherboard. |
| **CXL Device Support** | Physical form factors supported for CXL devices (E3.S, AIC, or both). |
| **Year Introduced** | The year the server platform became generally available. |
| **Product Link** | Direct link to the official vendor product page. |

---

## CXL 2.0 Servers

CXL 2.0 introduces switching capabilities enabling memory pooling and the creation of fabric-attached memory solutions. Servers supporting CXL 2.0 are at the forefront of this architectural paradigm and are backward compatible with CXL 1.1 devices.

The dominant CXL 2.0 server generations as of mid-2026 are **Intel Xeon 6** (Granite Rapids P-core and Sierra Forest E-core, released 2024) and **AMD EPYC 9005 "Turin"** (released 2024). Intel's Xeon 6+ "Clearwater Forest" launched at Computex 2026 (June 2026) also carries CXL 2.0 support via 96 PCIe Gen5 lanes.

### Intel Xeon 6 Platform Servers

| OEM Vendor | Server Model | CPU Vendor | CPU Generation | Rack Height (U) | CXL Version | CXL Device Support | Year Introduced | Product Link |
|---|---|---|---|---|---|---|---|---|
| **AIC** | SB201-SU | Intel | Xeon 6 | 2U | 2.0 | AIC, E3.S | 2024 | [Link](https://www.aicipc.com/en/news/6172) |
| **Dell** | PowerEdge R670 | Intel | Xeon 6 | 1U | 2.0 | AIC, E3.S | 2024 | [Link](https://www.dell.com/en-us/shop/dell-poweredge-servers/poweredge-r670-rack-server/spd/poweredge-r670) |
| **Dell** | PowerEdge R770 | Intel | Xeon 6 | 2U | 2.0 | AIC, E3.S | 2024 | [Link](https://www.dell.com/en-us/shop/dell-poweredge-servers/poweredge-r770-rack-server/spd/poweredge-r770) |
| **HPE** | ProLiant Compute DL380 Gen12 | Intel | Xeon 6 | 2U | 2.0 | AIC, E3.S | 2025 | [Link](https://www.hpe.com/us/en/compute/hpe-proliant-compute/dl380-gen12.html) |
| **HPE** | ProLiant Compute DL380a Gen12 | Intel | Xeon 6 | 4U | 2.0 | AIC, E3.S | 2025 | [Link](https://www.hpe.com/us/en/compute/hpe-proliant-compute/dl380-gen12.html) |
| **Lenovo** | ThinkSystem SR630 V4 | Intel | Xeon 6 | 1U | 2.0 | E3.S, AIC | 2025 | [Link](https://lenovopress.lenovo.com/lp2125-thinksystem-sr630-v4-server) |
| **Lenovo** | ThinkSystem SR650 V4 | Intel | Xeon 6 | 2U | 2.0 | E3.S, AIC | 2025 | [Link](https://www.lenovo.com/us/en/p/servers-storage/servers/racks/thinksystem-sr650-v4/len102s0061) |
| **Lenovo** | ThinkSystem SR850 V4 | Intel | Xeon 6 (4-socket) | 2U | 2.0 | E3.S, AIC | 2025 | [Link](https://lenovopress.lenovo.com/lp2230-thinksystem-sr850-v4-server) |
| **Supermicro** | SYS-222H-TN (X14 Hyper) | Intel | Xeon 6700/6500 | 2U | 2.0 | AIC, E3.S | 2024 | [Link](https://store.supermicro.com/us_en/x14-2u-hyper-sys-222h-tn.html) |
| **Supermicro** | SYS-421GH-TNRT (X14 4-socket) | Intel | Xeon 6 P-core | 4U | 2.0 | AIC, E3.S | 2025 | [Link](https://www.supermicro.com/en/products/x14) |

### AMD EPYC Platform Servers

| OEM Vendor | Server Model | CPU Vendor | CPU Generation | Rack Height (U) | CXL Version | CXL Device Support | Year Introduced | Product Link |
|---|---|---|---|---|---|---|---|---|
| **Dell** | PowerEdge R6715 | AMD | EPYC 9005 (Turin) | 1U | 2.0 | AIC | 2024 | [Link](https://www.dell.com/en-us/shop/dell-poweredge-servers/poweredge-r6715-rack-server/spd/poweredge-r6715) |
| **Dell** | PowerEdge R7715 | AMD | EPYC 9005 (Turin) | 2U | 2.0 | AIC | 2024 | [Link](https://www.dell.com/en-us/shop/dell-poweredge-servers/poweredge-r7715-rack-server/spd/poweredge-r7715) |
| **Dell** | PowerEdge R6725 | AMD | EPYC 9005 (Turin) | 1U | 2.0 | AIC | 2024 | [Link](https://www.dell.com/en-us/shop/dell-poweredge-servers/poweredge-r6725-rack-server/spd/poweredge-r6725) |
| **Dell** | PowerEdge R7725 | AMD | EPYC 9005 (Turin) | 2U | 2.0 | AIC | 2024 | [Link](https://www.dell.com/en-us/shop/dell-poweredge-servers/poweredge-r7725-rack-server/spd/poweredge-r7725) |
| **KAYTUS** | KR2280V3 | Intel / AMD | Xeon 6 / EPYC 9005 | 2U | 2.0 | E3.S, AIC | 2024 | [Link](https://www.kaytus.com/products/servers/rack-servers/kr2280v3) |
| **MSI** | S2301 | AMD | EPYC Genoa | 2U | 2.0 | E3.S | 2023 | [Link](https://www.msi.com/Enterprise-Server/S2301-CXL-Memory-Expansion-Server) |
| **Penguin Solutions** | Altus XE4318GT-CXL | AMD | EPYC Genoa | 4U | 2.0 | AIC | 2024 | [Link](https://www.penguinsolutions.com/en-us/products/cxl-memory-expansion-servers) |
| **Supermicro** | AS-2125HS-TNR (H13) | AMD | EPYC Genoa | 2U | 2.0 | AIC | 2023 | [Link](https://www.supermicro.com/en/products/system/h13/2u/as-2125hs-tnr) |

---

## CXL 1.1 Servers

CXL 1.1 focuses on memory expansion for a single host and does not support multi-host pooling or switching. These servers remain valuable for workloads requiring large memory capacity attached directly to a single CPU complex. Note that CXL 2.0 servers are backward compatible with CXL 1.1 devices—when upgrading your server infrastructure, choosing a CXL 2.0 platform future-proofs your investment.

| OEM Vendor | Server Model | CPU Vendor | CPU Generation | Rack Height (U) | CXL Version | CXL Device Support | Year Introduced | Product Link |
|---|---|---|---|---|---|---|---|---|
| **Dell** | PowerEdge R760 | Intel | Xeon Scalable Gen 5 (Emerald Rapids) | 2U | 1.1 | AIC | 2024 | [Link](https://www.dell.com/en-us/shop/dell-poweredge-servers/poweredge-r760-rack-server/spd/poweredge-r760) |
| **HPE** | ProLiant DL380 Gen11 | Intel | Xeon Scalable Gen 5 (Emerald Rapids) | 2U | 1.1 | AIC | 2024 | [Link](https://www.hpe.com/us/en/product-catalog/servers/proliant-servers/pip.hpe-proliant-dl380-gen11-server.1014942634.html) |
| **Lenovo** | ThinkSystem SR650 V3 | Intel | Xeon Scalable Gen 4 (Sapphire Rapids) | 2U | 1.1 (Ready) | AIC | 2023 | [Link](https://lenovopress.lenovo.com/lp1601-thinksystem-sr650-v3-server) |
| **Lenovo** | ThinkSystem SR850 V3 | Intel | Xeon Scalable Gen 4 (Sapphire Rapids, 4-socket) | 2U | 1.1 (Ready) | AIC | 2023 | [Link](https://lenovopress.lenovo.com/lp1605-thinksystem-sr850-v3-server) |
| **Supermicro** | SYS-221H-TNR | Intel | Xeon Scalable Gen 5 (Emerald Rapids) | 2U | 1.1 | AIC | 2024 | [Link](https://www.supermicro.com/en/products/system/hyper/2u/sys-221h-tnr) |

---

## CPU Platform CXL Support Reference

CXL support is a CPU-level feature. The server OEM can only expose what the processor's I/O die natively implements, so understanding which generation you're deploying is critical before specifying CXL memory or switch products.

This section covers the four processor ecosystems relevant to CXL-enabled servers as of mid-2026: Intel Xeon, AMD EPYC, Arm Neoverse, and NVIDIA Vera. Arm and NVIDIA are IP providers or new entrants rather than the OEM server vendors listed earlier in this guide, so their CXL applicability is noted where relevant.

---

### Intel Xeon

Intel's official CXL support matrix is documented at [intel.com/content/www/us/en/support/articles/000059219](https://www.intel.com/content/www/us/en/support/articles/000059219/processors/intel-xeon-processors.html). All current Intel Xeon SKUs are browsable on the [Intel ARK database](https://www.intel.com/content/www/us/en/ark.html#@PanelLabel595).

| CPU Family | Code Name | Architecture | CXL Version | Key CXL Notes | Introduced |
|---|---|---|---|---|---|
| Xeon Scalable Gen 1–3 | Skylake / Cascade Lake / Ice Lake | — | None | No CXL support | 2017–2021 |
| Xeon Scalable Gen 4 | Sapphire Rapids | Golden Cove | 1.1 | First Intel gen with CXL; limited Type 3 device support; full support via firmware | 2023 |
| Xeon Scalable Gen 5 | Emerald Rapids | Redwood Cove | 1.1 | Full CXL Type 3 (memory expansion) support | 2024 |
| Xeon 6 (P-core) | Granite Rapids | Lion Cove | 2.0 | 12 DDR5 channels; MRDIMM support (up to 8800 MT/s); CXL Flat Memory Mode; up to 128 PCIe 5.0 / CXL lanes | 2024 |
| Xeon 6 (E-core) | Sierra Forest | Crestmont | 2.0 | High-density efficiency core; 96 PCIe 5.0 / CXL lanes per socket | 2024 |
| Xeon 6+ (E-core) | Clearwater Forest | Darkmont (18A) | 2.0 | Up to 288 E-cores per socket on Intel 18A process; 96 PCIe Gen5 lanes; launched Computex 2026 | 2026 |

**Notes:**
- All Xeon 6 generations support CXL 2.0 for Type 3 memory expansion devices (AIC and E3.S form factors).
- CXL Flat Memory Mode (Xeon 6 Granite Rapids) allows the OS to see local DDR5 and CXL-attached memory as a single pool with no special application changes.
- For the full list of Xeon 6 SKUs including core counts, TDPs, and PCIe lane counts, see [Intel ARK Xeon 6 series](https://ark.intel.com/content/www/us/en/ark/products/series/240357/intel-xeon-6.html).

---

### AMD EPYC

AMD's EPYC product pages are at [amd.com/en/products/processors/server/epyc](https://www.amd.com/en/products/processors/server/epyc.html).

| CPU Family | Code Name | Architecture | CXL Version | Key CXL Notes | Introduced |
|---|---|---|---|---|---|
| EPYC 7001 / 7002 | Naples / Rome | Zen / Zen 2 | None | No CXL support | 2017–2019 |
| EPYC 7003 | Milan / Milan-X | Zen 3 | None | No CXL support | 2021 |
| EPYC 9004 (standard) | Genoa / Genoa-X | Zen 4 | 1.1+ | First AMD generation with CXL; implements CXL 1.1 with selected CXL 2.0 Type 3 features; 64 CXL-capable lanes; first-to-market with Type 3 memory expansion in late 2022 | 2022 |
| EPYC 9004 (cloud-density) | Bergamo | Zen 4c | 1.1+ | Same CXL capability as Genoa; dense 128-core Zen 4c variant optimized for cloud-native workloads | 2023 |
| EPYC 8004 | Siena | Zen 4c | 1.1+ | Single-socket SP6 platform; same CXL baseline as Genoa | 2023 |
| EPYC 9005 | Turin | Zen 5 / Zen 5c | 2.0 | Full CXL 2.0; up to 128 PCIe 5.0 / CXL lanes per socket; 192-core maximum; Type 3 memory expansion focus | 2024 |

**Notes on AMD CXL versioning:** AMD describes EPYC 9004 (Genoa/Bergamo) as supporting **CXL 1.1+** — meaning the hardware implements the CXL 1.1 specification plus a subset of CXL 2.0 features, specifically focused on Type 3 memory expansion (not multi-host pooling or switching). This is confirmed in AMD's [EPYC 9004 Memory and CXL White Paper](https://www.amd.com/content/dam/amd/en/documents/epyc-business-docs/white-papers/231963000-A_en_AMD-EPYC-9004-Series-Processors-Memory-and-CXL-Advances-White-Paper_pdf.pdf). Full CXL 2.0 capability with switching support arrived with Turin (EPYC 9005).

---

### Arm Neoverse

Unlike Intel and AMD, Arm does not sell CPUs directly — Arm licenses its IP to silicon partners (AWS, Ampere, NVIDIA, Qualcomm, Google, and others) who build their own server processors. Whether CXL IP blocks are instantiated in the final silicon **is the implementation choice of each silicon partner**, not a guarantee from Arm.

That said, Arm has included CXL support in its Neoverse IP since the N2 generation, making it available to any licensee who chooses to include it.

| IP Family | Arm Release | CXL Version | Key CXL Notes | Reference |
|---|---|---|---|---|
| Neoverse N1 | 2019 | None | No CXL in this generation | — |
| Neoverse V1 | 2020 | None | No CXL in this generation | — |
| Neoverse N2 | 2021 | 2.0 (IP available) | First Neoverse generation with PCIe Gen5 + CXL IP; CXL 2.0 Type-3 verified on Neoverse N2 reference design platform | [developer.arm.com](https://neoverse-reference-design.docs.arm.com/en/latest/features/cxl.html) |
| Neoverse V2 | 2022 | 3.0 (IP available) | CMN-700 interconnect supports CXL-attached devices; PCIe Gen6 + CXL 3.0 in IP | [arm.com](https://www.arm.com/products/silicon-ip-cpu/neoverse/neoverse-v2) |
| Neoverse N3 | 2024 | 2.0+ (IP available) | Paired with CMN S3 interconnect; scales to 192 cores; CXL I/O available to licensees | [arm.com](https://www.arm.com/products/silicon-ip-cpu/neoverse/neoverse-n3) |
| Neoverse V3 / CSS V3 | 2024 | 2.0+ (IP available) | CSS V3 subsystem: up to 64 cores, 12 DDR5 channels, 64 lanes PCIe Gen5/CXL; highest single-threaded Neoverse performance | [arm.com](https://www.arm.com/products/cloud-datacenter/neoverse-compute-subsystems/css-v3) |

**Real-world Neoverse CXL deployments:** AWS Graviton4 is based on Neoverse V2 but does not publicly expose CXL to workloads. Ampere Altra / AmpereOne are based on Neoverse N1/N2-class architectures; CXL availability depends on each vendor's implementation. As of mid-2026, no major hyperscaler has publicly announced Neoverse-based CXL server availability to customers.

---

### NVIDIA Vera

NVIDIA entered the standalone CPU market with the **Grace CPU** (Arm Neoverse V2-based, 2023) without CXL support, and has followed with **Vera**, a fully custom CPU launched at GTC 2026 with commercial OEM availability expected in H2 2026.

| CPU | Architecture | CXL Version | Key CXL Notes | Availability | Reference |
|---|---|---|---|---|---|
| Grace | Neoverse V2-based, 72 cores | - | - | GA 2023 | [NVIDIA Grace](https://www.nvidia.com/en-us/data-center/grace-cpu/) |
| Vera | Custom Olympus (Armv9.2), 88 cores | **3.1** | PCIe 6.0 + CXL 3.1; 1.2 TB/s LPDDR5X memory bandwidth; NVLink-C2C at 1.8 TB/s for GPU coupling; available as standalone CPU or in Vera Rubin NVL72 superchip rack | OEM availability H2 2026 | [NVIDIA Vera CPU Rack](https://www.nvidia.com/en-us/data-center/products/vera-rack/) <br/><br/> [NVIDIA NVLink-C2C](https://developer.nvidia.com/nvlink-c2c) |

**Key point:** NVIDIA Vera is the first commercially announced server CPU to implement **CXL 3.1**, making it the most CXL-capable CPU available as of this writing, when it ships in H2 2026. This is particularly significant for AI workloads: Vera Rubin racks expose PCIe/CXL connectors at the board edge, enabling external CXL memory pooling appliances (such as those from Liqid or H3 Platform) to attach alongside GPU resources within the same fabric.

Vera is designed primarily to run as a GPU-coupled accelerator CPU (in Vera Rubin NVL72 racks) or as a pure CPU rack (256 liquid-cooled Vera CPUs per rack). OEM server availability in single- and dual-socket configurations is expected from Cisco, Dell, HPE, Lenovo, and Supermicro in H2 2026.

---

## What Changed Since the June 2025 Edition

**New server platforms:**
- **HPE ProLiant DL380 Gen12** and **DL380a Gen12**: Full Xeon 6 refresh with CXL 2.0, up to 36 E3.S bays, up to 8 TB DDR5. Introduced 2025.
- **Lenovo SR850 V4**: 4-socket Xeon 6 P-core platform with CXL 2.0 and up to 16 TB of DDR5 memory. Introduced 2025.
- **Lenovo SR630 V4**: 1U Xeon 6 with CXL 2.0 support. Introduced 2025.
- **Dell PowerEdge R6715 / R6725**: AMD EPYC Turin 1U single- and dual-socket servers with CXL 2.0. GA November 2024.
- **Supermicro X14 4-socket systems**: CXL 2.0 ready 4-socket Intel Xeon 6 P-core systems for large-memory workloads. Shipping July 2025.
- **Intel Xeon 6+ "Clearwater Forest"**: Launched June 1, 2026 at Computex; available through Dell, HPE, Lenovo, and Supermicro. Up to 288 E-cores per socket on Intel 18A process. CXL 2.0 via 96 PCIe Gen5 lanes.

**Deprecated / retired from CXL 2.0 table:**
- The original **Supermicro AS-2125HS-TNR** entry (AMD Genoa / CXL 2.0) has been retained as a reference platform but is superseded by newer H13/H14 systems.

**Notable real-world validation:**
- Microsoft Azure M-series VMs became the **first cloud service CXL deployment** using Astera Labs Leo controllers (November 2025), confirming enterprise-production readiness.
- Intel and Micron demonstrated CXL E3.S expansion modules running on Xeon 6 6900P for HPC and AI workloads in production-class configurations.

**Corrections from June 2025 edition:**
- **AMD Genoa/Bergamo CXL version corrected:** The June 2025 table listed these as "CXL 2.0." Per AMD's own white paper, EPYC 9004 (Genoa/Bergamo) implements **CXL 1.1+** — CXL 1.1 with selected Type 3 memory expansion features from the CXL 2.0 spec. Full CXL 2.0 arrived with EPYC 9005 Turin.

**New CPU section added:**
- A new **CPU Platform CXL Support Reference** section covers Intel Xeon, AMD EPYC, Arm Neoverse, and NVIDIA Vera in detail — including the important nuance that Arm licenses CXL IP to silicon partners who may or may not include it in their final designs.
- **NVIDIA Vera** (announced GTC 2026, OEM availability H2 2026) supports **CXL 3.1** and PCIe 6.0 — the highest CXL version of any commercially announced CPU as of this writing.

---

## Frequently Asked Questions

**Q: Do I need a special CXL switch to use CXL memory on these servers?**
No. Every server in this list can use a CXL memory module (E3.S or AIC) connected directly to a PCIe slot, expanding that server's local memory. A CXL switch is only required if you want to create a pool of memory shared across *multiple* servers.

**Q: Which servers support E3.S CXL modules?**
Most Intel Xeon 6-based platforms include dedicated E3.S bays (typically accessed through front-accessible hot-swap slots) that can be populated with either NVMe SSDs or CXL memory modules. Check the specific server's QVL before ordering.

**Q: What memory latency penalty should I expect with CXL expansion?**
Approximately 70 ns of additional latency versus local DRAM. CXL memory typically appears as an additional NUMA node, so NUMA-aware applications and OS-level memory tiering (e.g., via MemVerge Memory Machine) can place workloads optimally.

**Q: Are AMD EPYC Turin servers fully CXL 2.0 compatible?**
Yes. AMD EPYC Turin (5th Gen, EPYC 9005 series) fully supports CXL 2.0 Type 3 memory expansion via AIC slots. E3.S slot availability varies by OEM chassis design. Earlier Genoa/Bergamo platforms support CXL 1.1+ (a subset of CXL 2.0 Type 3 features) — sufficient for direct-attach memory expansion, but not full multi-host switching/pooling.

**Q: When should I consider CXL 3.x servers?**
CXL 3.x switches are sampling now (Marvell Structera S Apollo 2, Panmnesia PANSWITCH), but the first widely available CXL 3.1 CPU platform is NVIDIA Vera (H2 2026). AMD's upcoming EPYC "Venice" (Zen 6, TSMC 2nm) is also expected in H2 2026 and may introduce CXL 3.x support. For multi-rack pooling and Port-Based Routing, plan accordingly.

**Note** Always check compatability with the vendor before purchasing.