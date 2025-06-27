---
title: "CXL Device & Fabric Buyer's Guide: A List of GA Components (2025)"
meta_title: "CXL Device & Fabric Buyer's Guide: GA Memory, Switches & Appliances"
description: "The definitive buyer's guide to CXL devices and fabric components. Compare GA CXL memory modules, switches, appliances, and retimers from major industry vendors."
date: 2025-06-27T17:15:01Z
image: "cxl-device-featured-image.webp"
categories: ["Data Center", "Hardware"]
author: "Steve Scargall"
tags: ["CXL", "CXL Devices", "Memory", "Switches", "Retimers", "Samsung", "Micron", "H3 Platform", "Enfabrica", "Buyer's Guide"]
draft: false
---

**Last Updated: June 27, 2025**

This guide provides a curated list of generally available (GA) Compute Express Link (CXL) devices, fabric components, and memory appliances. It is a technical resource for engineers, architects, and hardware specialists looking to identify and compare CXL memory expansion modules, switches, and full system-level appliances from leading vendors. The tables below detail market-ready components, focusing on the specifications required to design and build CXL-enabled infrastructure.

### Introduction

While CXL-enabled servers provide the foundation, the true power of the CXL standard is unlocked by the devices themselves. These components—ranging from memory expanders that break through traditional DIMM capacity limits to the switches and full-blown appliances that form the CXL fabric—are the building blocks of next-generation data centers.

This guide separates the ecosystem into three key categories:
1.  **CXL Memory Expansion Devices:** Modules that add DRAM capacity and bandwidth to a host.
2.  **CXL Switches & Fabric Components:** The hardware that enables memory to be pooled, shared, and connected over distance.
3.  **CXL Memory Appliances:** Complete, integrated systems that provide a turnkey solution for CXL memory pooling.

This is a living document. As the CXL device ecosystem matures, this list will be updated with new GA components.

The CXL Consortium has an [comprehensive list of vendor products](https://computeexpresslink.org/integrators-list/).

### Key Terminology

* **CXL Memory Module (CMM):** A general term for a CXL device that contains DRAM memory, used for capacity or bandwidth expansion.
* **CXL Switch:** A device that enables a CXL fabric, allowing multiple hosts to connect to a pool of multiple CXL devices. Essential for memory pooling (a CXL 2.0 feature).
* **CXL Appliance:** A complete, self-contained system (e.g., a 2U chassis) that includes a CXL switch, device slots, and management, offering a turnkey memory pooling solution.
* **Form Factor:** The physical shape and size of the device. Common form factors include **AIC** (Add-in Card) and **E3.S** (a modern, dense, hot-swappable standard).

---

## CXL Memory Expansion Devices

These Type 3 devices are the most common use case for CXL today, allowing systems to attach vast amounts of memory for data-intensive workloads like in-memory databases and AI.

| Vendor | Product Name/Series | Capacity | Form Factor | CXL Version | DRAM Type | Product Link |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Advantech** | SQR-CX5N | 64GB | E3.S-2T | 2.0 | DDR5 | [Link](https://www.advantech.com/en-us/products/cxl-memory/sub_e40a8a6b-2dc6-4ee3-894d-1b2cbf53aac5) |
| **Astera Labs** | Aurora A-Series | Up to 2TB | AIC (CEM) | 2.0 | DDR5 | [Link](https://www.asteralabs.com/products/leo-cxl-smart-memory-controllers/) |
| **Samsung** | CMM-D | 128GB, 256GB | E3.S | 2.0 | DDR5 | [Link](https://semiconductor.samsung.com/cxl-memory/) |
| **Samsung** | CMM-H | 128GB, 256GB | E3.S | 2.0 | DDR5, NAND | [Link](https://semiconductor.samsung.com/news-events/tech-blog/samsung-cxl-solutions-cmm-h/) |
| **Micron** | CZ120 Series | 128GB, 256GB | E3.S-2T | 2.0 | DDR5 | [Link](https://www.micron.com/products/cxl-memory/cz120) |
| **SK Hynix** | CMM-DDR5 (CMS) | 96GB | E3.S | 2.0 | DDR5 | [Link](https://www.skhynix.com/cxl/) |
| **SMART Modular<br/>Penguin Solutions** | CXA-4F1W | 512GB | AIC (CEM) | 2.0 | DDR5 | [Link](https://www.smartm.com/product/cxl-aic-cxa-4f1w) |
| **SMART Modular<br/>Penguin Solutions** | CXA-8F2W | 1TB | AIC (CEM) | 2.0 | DDR5 | [Link](https://www.smartm.com/product/cxl-aic-cxa-8f2w) |
| **SMART Modular<br/>Penguin Solutions** | CMM-E3S | 64GB, 96GB, 128GB | E3.S-2T | 2.0 | DDR5 | [Link](https://www.smartm.com/product/cmm-cxl-memory-module-e3s) |
| **SMART Modular<br/>Penguin Solutions** | NV-CMM-E3S | 32GB | E3.S-2T | 2.0 | DDR5,NAND | [Link](https://www.smartm.com/product/cxl-memory-module-nv-cmm-e3s) |


---

## CXL Switches & Fabric Components

Switches and retimers are the connective tissue of a CXL fabric. Switches create the logical connections for memory pooling, while retimers ensure signal integrity over physical distances.

| Vendor | Component Type | Product Name/Series | CXL Version | Key Features | Product Link |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Astera Labs**| Smart Memory Controller| Leo P-Series | 2.0 | Enables memory expansion, pooling, & sharing; x16 lanes | [Link](https://www.asteralabs.com/products/leo-cxl-smart-memory-controllers/) |
| **Microchip** | Smart Memory Controller| SMC 2000 Series | 2.0 | Low-latency CXL 2.0 controller for DDR4/DDR5 | [Link](https://www.microchip.com/en-us/products/memory/smart-memory-controllers) |
| **XConn** | Switch ASIC | XC50256 | 2.0 | 256-lane, 2.0Tb/s CXL 2.0 switch | [Link](https://www.xconn-tech.com/products) |
| **Enfabrica** | Switch/Fabric ASIC| RCE (Rapid-Compute Engine)| 2.0 | CXL 2.0 switch with integrated 800GbE networking | [Link](https://www.enfabrica.net/product) |
| **Montage Tech**| Retimer | M88RT51632 | 2.0 | 16-lane PCIe 5.0 / CXL 2.0 Retimer | [Link](https://www.montage-tech.com/PCIe_Retimer) |
| **Montage Tech**| Retimer | M88RT61632 | 3.x | 16-lane PCIe 6.x / CXL 3.x Retimer (Sampling) | [Link](https://www.montage-tech.com/PCIe_Retimer) |

---

## CXL Memory Appliances

Memory appliances are complete, system-in-a-box solutions designed for rapid deployment of CXL memory pooling. They integrate CXL switches, device bays, power, and management into a single chassis.

| Vendor | Model | Form Factor | Max Capacity / Device Support | Host Connectivity | Product Link |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **H3 Platform**| Falcon C5022 | 2U | 22x E3.S CXL Modules | 4x PCIe Gen5 x16 Ports | [Link](https://www.h3platform.com/product-detail/overview/35) |
| **SK Hynix** | Niagara 2.0 | 2U | Scalable Multi-TB | Multi-host fabric connectivity | [Link](https://news.skhynix.com/sk-hynix-to-unveil-next-gen-memory-solutions-at-ocp-global-summit-2023/) |

---

### Frequently Asked Questions (FAQ)

**Q: What is the difference between a CXL memory module and a CXL appliance?**
A: A CXL memory module is a single component (like an AIC or E3.S card) that plugs into a server or appliance. A CXL appliance is a complete, self-contained system with its own chassis, power, and an integrated CXL switch, designed to hold many CXL modules and connect to multiple host servers to create a shared memory pool.

**Q: Can I mix CXL memory from different vendors in an appliance?**
A: Because CXL is an open standard, this is generally possible, but it is always best to consult the appliance vendor's Qualified Vendor List (QVL) to ensure validated interoperability.

**Q: Do I need a CXL switch to use a CXL memory module?**
A: No. You can connect a CXL memory module directly to a CXL-enabled server to expand its local memory. A CXL switch or appliance is only required if you want to create a pool of memory that can be shared between *multiple* servers.