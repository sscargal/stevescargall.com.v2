---
title: "CXL Device & Fabric Buyer's Guide: A List of GA Components"
meta_title: "CXL Device & Fabric Buyer's Guide: GA Memory, Switches & Appliances"
description: "The definitive buyer's guide to CXL devices and fabric components. Compare GA CXL memory modules, switches, appliances, and retimers from major industry vendors."
date: 2025-06-27T17:15:01Z
image: "featured_image.webp"
categories: ["Data Center", "Hardware"]
author: "Steve Scargall"
tags: ["CXL", "CXL Devices", "Memory", "Switches", "Retimers", "Samsung", "Micron", "H3 Platform", "Enfabrica", "Buyer's Guide"]
draft: false
---

**Last Updated: June 2, 2026**

This guide provides a curated list of generally available (GA) Compute Express Link (CXL) devices, fabric components, and memory appliances. It is a technical resource for engineers, architects, and hardware specialists looking to identify and compare CXL memory expansion modules, switches, and full system-level appliances from leading vendors. The tables below detail market-ready components, focusing on the specifications required to design and build CXL-enabled infrastructure.

## Introduction

While CXL-enabled servers provide the foundation, the true power of the CXL standard is unlocked by the devices themselves. These components—ranging from memory expanders that break through traditional DIMM capacity limits to the switches and full-blown appliances that form the CXL fabric—are the building blocks of next-generation data centers. The CXL ecosystem has reached an important inflection point: what was a technology preview in 2023 is now a production-grade option in 2026, with hyperscale cloud deployments (notably Microsoft Azure M-series VMs) validating the architecture at scale.

This guide separates the ecosystem into three key categories:

1. **CXL Memory Expansion Devices:** Modules that add DRAM capacity and bandwidth to a host.
2. **CXL Switches & Fabric Components:** The hardware that enables memory to be pooled, shared, and connected over distance.
3. **CXL Memory Appliances:** Complete, integrated systems that provide a turnkey solution for CXL memory pooling.

> **Note:** This is a living document. As the CXL device ecosystem matures, this list will be updated with new GA components. The CXL Consortium maintains a [comprehensive list of vendor products](https://computeexpresslink.org/integrators-list/).

---

## Key Terminology

| Term | Definition |
|---|---|
| **CXL Memory Module (CMM)** | A general term for a CXL device that contains DRAM memory, used for capacity or bandwidth expansion. |
| **CXL Switch** | Enables a CXL fabric, allowing multiple hosts to connect to a pool of CXL devices. Essential for memory pooling (a CXL 2.0 feature). |
| **CXL Appliance** | A complete, self-contained system (e.g., a 2U chassis) with an integrated CXL switch, device slots, and management. |
| **AIC (Add-In Card)** | A CXL device in a standard PCIe card format, installed in a server's PCIe slots. |
| **E3.S (EDSFF 3" Short)** | A compact, hot-swappable form factor for CXL memory modules and SSDs, designed for dense server designs. |
| **Type 3 Device** | A CXL classification for memory expansion devices that respond to CPU memory read/write operations. |
| **GA (Generally Available)** | The product is officially released and can be ordered from the vendor. |
| **Sampling** | Pre-production silicon available to qualified customers for evaluation; not yet GA. |

---

## CXL Memory Expansion Devices

Type 3 devices are the most common CXL use case today, allowing systems to attach vast amounts of memory for data-intensive workloads like in-memory databases, AI inference (KV cache), and analytics. CXL 2.0 modules offer approximately 70ns of added latency versus direct-attached DRAM—still 20–50× faster than NVMe storage.

| Vendor | Product Name | Capacity | Form Factor | CXL Version | DRAM Type | Year Introduced | Product Link |
|---|---|---|---|---|---|---|---|
| **Advantech** | SQR-CX5N | 64 GB | E3.S-2T | 2.0 | DDR5 | 2024 | [Link](https://www.advantech.com/en-us/products/cxl-memory/sub_e40a8a6b-2dc6-4ee3-894d-1b2cbf53aac5) |
| **Astera Labs** | Leo A-Series | Up to 2 TB | AIC (CEM) | 2.0 | DDR5 | 2023 | [Link](https://www.asteralabs.com/products/leo-cxl-smart-memory-controllers/) |
| **Micron** | CZ120 | 128 GB, 256 GB | E3.S-2T | 2.0 | DDR4/DDR5 | 2023 | [Link](https://www.micron.com/products/memory/cxl-memory) |
| **Micron** | CZ122 | Up to 256 GB | E3.S-2T | 2.0 | DDR5 | 2024 | [Link](https://www.micron.com/about/blog/applications/data-center/introducing-micron-cz122-and-red-hat-certification-of-memory-expansion-portfolio) |
| **Samsung** | CMM-D (Gen 1) | 128 GB, 256 GB, 512 GB | E3.S | 2.0 | DDR5 | 2022 | [Link](https://semiconductor.samsung.com/us/consumer-storage/internal-ssd/cxl/) |
| **Samsung** | CMM-D 2.0 | 128 GB, 256 GB | E3.S | 2.0 | DDR5 | 2025 | [Link](https://semiconductor.samsung.com/news-events/tech-blog/worlds-first-cmm-d-technology-leading-the-ai-era/) |
| **Samsung** | CMM-H | 128 GB, 256 GB | E3.S | 2.0 | DDR5 + NAND | 2023 | [Link](https://semiconductor.samsung.com/news-events/tech-blog/samsung-cxl-solutions-cmm-h/) |
| **SK Hynix** | CMM-DDR5 (CMS) | 96 GB | E3.S | 2.0 | DDR5 | 2023 | [Link](https://news.skhynix.com/sk-hynix-completes-customer-validation-of-cxl-based-ddr5/) |
| **SK Hynix** | CMM-Ax | TBA | E3.S / AIC | 2.0+ | DDR5 | 2025 (sampling) | [Link](https://news.skhynix.com/sk-hynix-showcases-advanced-ai-memory-at-sc25/) |
| **SMART Modular / Penguin Solutions** | CXA-4F1W | 512 GB | AIC (CEM) | 2.0 | DDR5 | 2023 | [Link](https://www.smartm.com/product/cxl-aic-cxa-4f1w) |
| **SMART Modular / Penguin Solutions** | CXA-8F2W | 1 TB | AIC (CEM) | 2.0 | DDR5 | 2023 | [Link](https://www.smartm.com/product/cxl-aic-cxa-8f2w) |
| **SMART Modular / Penguin Solutions** | CMM-E3S | 64 GB, 96 GB, 128 GB | E3.S-2T | 2.0 | DDR5 | 2023 | [Link](https://www.smartm.com/product/cmm-cxl-memory-module-e3s) |
| **SMART Modular / Penguin Solutions** | NV-CMM-E3S | 32 GB | E3.S-2T | 2.0 | DDR5 + NAND | 2023 | [Link](https://www.smartm.com/product/cxl-memory-module-nv-cmm-e3s) |

### What Changed Since 2025

- **Micron CZ122:** A second-generation module with improved RAS features, hardware-based heterogeneous interleaving, and Red Hat RHEL 9.3 certification. Supersedes the CZ120 for new designs.
- **Samsung CMM-D 2.0:** Refreshed DDR5-native CMM-D with CXL 3.1 variants targeted for H1 2026. Customer samples available since late 2025.
- **SK Hynix CMM-DDR5:** Completed formal customer validation in October 2025, moving from sampling to production-ready status.
- **SK Hynix CMM-Ax:** A next-generation compute-capable CXL module integrating processing-in-memory functionality alongside memory expansion. Demonstrated at SC25 and CES 2026; sampling underway.
- **Astera Labs Leo / Azure:** The Leo A-Series achieved the industry's first hyperscale cloud CXL deployment in Microsoft Azure M-series VMs (November 2025), validating production-grade CXL memory expansion.

---

## CXL Switches & Fabric Components

Switches and retimers are the connective tissue of a CXL fabric. Switches create the logical connections for memory pooling across multiple hosts; retimers ensure signal integrity over the physical distances required in rack-scale deployments.

> **Ecosystem note:** XConn Technologies—creator of the industry's first CXL 2.0 switch ASIC—was acquired by Marvell Technology in early 2026 for ~$540M. The XConn product line continues as Marvell's Structera S CXL switch family.

| Vendor | Component Type | Product Name/Series | CXL Version | Key Features | Year Introduced | Product Link |
|---|---|---|---|---|---|---|
| **Astera Labs** | Smart Memory Controller | Leo P-Series | 2.0 | Memory expansion, pooling & sharing; up to 2 TB per controller; x16 lanes | 2022 | [Link](https://www.asteralabs.com/products/leo-cxl-smart-memory-controllers/) |
| **Marvell (via XConn)** | Switch ASIC | Structera S 20256 (Apollo) | 2.0 | 256-lane, CXL 2.0 switch; PCIe Gen5; in production | 2024 | [Link](https://www.marvell.com/company/newsroom/marvell-next-gen-cxl-switch-enabling-memory-pooling-breaks-ai-memory-wall.html) |
| **Marvell (via XConn)** | Switch ASIC | Structera S 30260 (Apollo 2) | 3.1 | 260-lane hybrid CXL 3.1 + PCIe Gen 6.2; sampling Q3 2026 | 2025 | [Link](https://www.marvell.com/company/newsroom/marvell-next-gen-cxl-switch-enabling-memory-pooling-breaks-ai-memory-wall.html) |
| **Microchip** | Smart Memory Controller | SMC 2000 Series | 2.0 | Low-latency CXL 2.0 controller for DDR4/DDR5 | 2022 | [Link](https://www.microchip.com/en-us/products/memory/smart-memory-controllers) |
| **Montage Technology** | Retimer | M88RT51632 | 2.0 | 16-lane PCIe 5.0 / CXL 2.0 Retimer; in mass production | 2023 | [Link](https://www.montage-tech.com/PCIe_Retimer) |
| **Montage Technology** | Retimer | M88RT61632 | 3.x | 16-lane PCIe 6.x / CXL 3.x Retimer; 64 GT/s PAM4; sampling Jan 2025 | 2025 | [Link](https://www.montage-tech.com/PCIe_Retimer/M88RT61632) |
| **Panmnesia** | Switch ASIC | PANSWITCH H1SW06245ACFAA | 3.2 | PCIe 6.4 / CXL 3.2 hybrid; Port-Based Routing (PBR); first CXL 3.2-compliant switch silicon; sampling Nov 2025; mass production planned 2026 | 2025 | [Link](https://panmnesia.com/news/en/2025-11-13-switch-sample/) |
| **Enfabrica** | Switch/Fabric ASIC | RCE (Rapid-Compute Engine) | 2.0 | CXL 2.0 switch with integrated 800 GbE networking | 2023 | [Link](https://www.enfabrica.net/product) |

### What Changed Since 2025

- **XConn → Marvell Structera S:** XConn's Apollo (CXL 2.0, in production) and Apollo 2 (CXL 3.1, sampling) are now marketed as the Marvell Structera S family following the Q1 2026 acquisition. Product capabilities are unchanged; future roadmap integrates with Marvell's UALink and connectivity portfolio.
- **Panmnesia PANSWITCH:** The first commercially available silicon fully implementing CXL 3.2, including Port-Based Routing. Enables multi-rack CXL fabrics with thousands of devices. Mass production announced April 2026.
- **Montage M88RT61632:** CXL 3.x retimer sampling since January 2025, addressing the signal integrity challenges of PCIe Gen 6 deployments.
- **CXL 4.0 specification:** Released November 2025, doubling bandwidth to 128 GT/s via PCIe 7.0 integration. No silicon products yet, but relevant for 2027+ roadmaps.

---

## CXL Memory Appliances

Memory appliances are complete, system-in-a-box solutions designed for rapid deployment of CXL memory pooling. They integrate CXL switches, device bays, power, and management into a single chassis, removing the need to source and integrate components separately.

| Vendor | Model | Form Factor | Max Capacity / Device Support | Host Connectivity | Year Introduced | Product Link |
|---|---|---|---|---|---|---|
| **H3 Platform** | Falcon C5022 | 2U | 22× E3.S CXL Modules | 4× PCIe Gen5 x16 Ports | 2023 | [Link](https://www.h3platform.com/product-detail/overview/35) | 
| **Liqid** | EX-5410C CXL | 4U | 10x CXL Gen 5.0 x16 FHFL Double Wide Modules | 4 x Liqid HX-5160C-1C is a CXL 2.0 Gen 5 x16 Host Bus Adapter (HBA) | 2024 | [Link](https://www.liqid.com/products/composable-memory-solutions) |
| **Samsung** | CMM-B (CXL Memory Module-Box) | 2U | Up to 24× E3.S CMM-D Modules; up to ~5.5 TB pooled | Multi-host CXL fabric; co-designed with Supermicro | 2023 | [Link](https://semiconductor.samsung.com/us/consumer-storage/internal-ssd/cxl/) |
| **SK Hynix** | Niagara 2.0 | 2U | Scalable Multi-TB | Multi-host fabric connectivity | 2023 | [Link](https://news.skhynix.com/sk-hynix-to-unveil-next-gen-memory-solutions-at-ocp-global-summit-2023/) |

> **Samsung CMM-B note:** Samsung's CMM-B appliance page was retired July 31, 2025. The underlying technology (Pangea v2 system with 22× CMM-D modules, 5.5 TB pooled, 10.2× data transfer improvement over RDMA) has been demonstrated publicly. Contact Samsung directly for current appliance availability.

### What Changed Since 2025

- **Samsung Pangea v2:** Publicly demonstrated in 2025/2026, connecting 22 CMM-D modules into a 5.5 TB shared pool. Samsung has announced **Pangea v3** based on CXL 3.2, planned for 2026.
- **Commercial CXL pools:** Production CXL memory pools reaching 100 TiB became available in 2025, from Liqid, with larger deployments planned through 2026.

---

## Frequently Asked Questions

**Q: What is the difference between a CXL memory module and a CXL appliance?**
A CXL memory module is a single component (like an AIC or E3.S card) that plugs into a server or appliance. A CXL appliance is a complete, self-contained system with its own chassis, power, and an integrated CXL switch, designed to hold many CXL modules and connect to multiple host servers to create a shared memory pool.

**Q: Can I mix CXL memory from different vendors in an appliance?**
Because CXL is an open standard, this is generally possible. However, always consult the appliance vendor's Qualified Vendor List (QVL) to ensure validated interoperability before deploying in production.

**Q: Do I need a CXL switch to use a CXL memory module?**
No. You can connect a CXL memory module directly to a CXL-enabled server to expand its local memory. A CXL switch or appliance is only required if you want to create a pool of memory that can be shared between *multiple* servers.

**Q: How much latency does CXL memory add compared to local DRAM?**
CXL 2.0 memory expansion adds approximately 70 ns of latency compared to directly attached DRAM. This is still 20–50× faster than NVMe storage, making CXL suitable for AI KV cache, in-memory databases, and analytics workloads that can tolerate slightly higher memory latency.

**Q: What is the difference between CXL 1.1, 2.0, and 3.x?**
CXL 1.1 enables memory expansion from a single host. CXL 2.0 adds switching capabilities, enabling memory pooling and sharing across multiple hosts. CXL 3.x (3.0, 3.1, 3.2) extends this further with enhanced coherency, multi-level switching, Port-Based Routing, and doubled bandwidth (64 GT/s via PCIe Gen6).

**Q: Is CXL 4.0 relevant for purchasing decisions today?**
Not immediately. CXL 4.0 was published in November 2025 and doubles bandwidth to 128 GT/s via PCIe 7.0. No silicon products exist yet. Plan for CXL 4.0 as a 2027+ consideration.
