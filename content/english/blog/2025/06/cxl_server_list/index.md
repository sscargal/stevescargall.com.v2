---
title: "CXL Server Buyer's Guide: A Complete List of GA Platforms (Updated 2025)"
meta_title: "CXL Server Buyer's Guide: GA Vendor & Model List (2025)"
description: "Your complete buyer's guide to generally available (GA) CXL servers. Compare models, specs, and CXL features from top vendors like Dell, HPE, Lenovo, and Supermicro."
date: 2025-06-27T16:35:01Z
image: "featured_image.webp"
categories: ["CXL", Servers", "Data Center"]
author: "Steve Scargall"
tags: ["CXL", "Servers", "Buyer's Guide", "Intel", "AMD", "Dell", "HPE", "Lenovo", "Supermicro", "Data Center", "CXL 2.0", "CXL 1.1", "CXL 1.0", "CXL 3.0"]
draft: false
---

**Last Updated: June 27, 2025**

This quick reference guide provides a definitive, up-to-date list of generally available (GA) Compute Express Link (CXL) servers from major OEMs like Dell, HPE, Lenovo, and Supermicro. It is designed for data center architects, engineers, and IT decision-makers who need to identify and compare server platforms that support CXL 1.1 and CXL 2.0 for memory expansion and pooling. The tables below offer a direct comparison of server models, supported CPUs, CXL versions, and compatible CXL device form factors. The goal is to cut through the noise of announcements and roadmaps to provide a clear view of what you can deploy *today*.

[Compute Express Link (CXL)](https://computeexpresslink.org/) is a transformative open-standard interconnect that enables high-speed, low-latency communication between processors and devices, such as accelerators and memory expanders. Its adoption is a critical step toward creating more flexible, efficient, and powerful data center architectures. As this ecosystem matures, however, cutting through marketing announcements to find hardware you can actually deploy today is a significant challenge. This living document serves as that clear, factual resource. I will continuously update it as new CXL server platforms become generally available.

If you know of a GA server that should be included on this list, please let me know.

### Key Terminology

* **CXL (Compute Express Link):** An open standard interconnect built on the PCIe physical layer that allows for coherent memory sharing between a host processor and attached devices.
* **GA (Generally Available):** The product is officially released and can be ordered from the vendor.
* **AIC (Add-In Card):** A CXL device packaged in a standard PCIe card format that can be installed in a server's PCIe slots.
* **E3.S (EDSFF 3" Short):** A newer, compact form factor for devices like SSDs and CXL memory modules, designed for dense, thermally efficient server designs.


### Understanding the Table Columns

- **OEM Vendor**: The original equipment manufacturer of the server.
- **Server Model**: The specific product name or model number.
- **CPU Vendor**: The processor manufacturer (e.g., Intel, AMD). CXL support is tied directly to the CPU generation.
- **Rack Height (U)**: The physical height of the server in standard rack units.
- **GPU Support**: Whether the server chassis and architecture is designed to support GPUs, and if so, how many.
- **CXL Version**: The version of the CXL specification supported by the server's CPU and motherboard.
- **CXL Device Support**: The physical form factors supported for CXL devices, such as E3.S, Add-In Cards (AIC), or other proprietary modules.
- **Product Link**: A direct link to the official vendor product page for more details.
- **Press Release Link**: A direct link to the official vendor product news and announcements for the server product.

## CXL 2.0 Servers

CXL 2.0 introduces switching capabilities, enabling memory pooling and the creation of more flexible, fabric-attached memory solutions. Servers supporting CXL 2.0 are at the forefront of this new architectural paradigm and are backward compatible with CXL 1.1 devices.

| OEM Vendor     | Server Model         | CPU Vendor  | Rack Height (U) | GPU Support                | CXL Version | CXL Device Support | Product Link                                                 |
| -------------- | -------------------- | ----------- | --------------- | -------------------------- | ----------- | ------------------ | ------------------------------------------------------------ |
| **AIC**        | SB201-SU             | Intel       | 2U              | Yes, 2x double-width       | 2.0         | AIC, E3.S          | [Product](https://www.aicpa.com/news/aic-launches-cxl-enabled-storage-server-with-micron-and-intel)<br />[Press Release](https://www.aicipc.com/en/news/6172) |
| **Dell**       | PowerEdge R670       | Intel       | 1U              | Yes, up to 4x single-width | 2.0         | AIC, E3.S          | [Link](https://www.dell.com/en-us/shop/dell-poweredge-servers/poweredge-r670-rack-server/spd/poweredge-r670) |
| **Dell**       | PowerEdge R770       | Intel       | 2U              | Yes, up to 8x double-width | 2.0         | AIC, E3.S          | [Link](https://www.dell.com/en-us/shop/dell-poweredge-servers/poweredge-r770-rack-server/spd/poweredge-r770) |
| **Dell**       | PowerEdge R7715      | AMD         | 2U              | Yes, up to 4x double-width | 2.0         | AIC                | [Link](https://www.dell.com/en-us/shop/dell-poweredge-servers/poweredge-r7715-rack-server/spd/poweredge-r7715) |
| **Dell**       | PowerEdge R7725      | AMD         | 2U              | Yes, up to 8x double-width | 2.0         | AIC                | [Link](https://www.dell.com/en-us/shop/dell-poweredge-servers/poweredge-r7725-rack-server/spd/poweredge-r7725) |
| **KAYTUS**     | KR2280V3             | Intel / AMD | 2U              | Yes                        | 2.0         | E3.S, AIC          | [Link](https://www.kaytus.com/products/servers/rack-servers/kr2280v3) |
| **Lenovo**     | ThinkSystem SR650 V4 | Intel       | 2U              | Yes, up to 8x single-width | 2.0         | E3.S, AIC          | [Product](https://www.lenovo.com/us/en/p/servers-storage/servers/racks/thinksystem-sr650-v4/len102s0061)<br />[Press Release](https://lenovopress.lenovo.com/lp2127-thinksystem-sr650-v4-server) |
| **MSI**        | S2301                | AMD         | 2U              | No                         | 2.0         | E3.S               | [Link](https://www.msi.com/Enterprise-Server/S2301-CXL-Memory-Expansion-Server) |
| **Penguin Solutions**        | Altus XE4318GT-CXL                | AMD         | 4U              | Yes, up to 8x double-width | 2.0         | AIC               | [Link](https://www.penguinsolutions.com/en-us/products/cxl-memory-expansion-servers) |
| **Supermicro** | AS -2125HS-TNR       | AMD         | 2U              | Yes, up to 4x double-width | 2.0         | AIC                | [Link](https://www.supermicro.com/en/products/system/h13/2u/as-2125hs-tnr) |

## CXL 1.1 Servers

CXL 1.1 laid the groundwork, focusing on memory expansion for a single host. These servers are excellent for workloads that require large memory capacity attached directly to a single CPU complex.

| **OEM Vendor** | **Server Model**     | **CPU Vendor** | **Rack Height (U)** | **GPU Support**                         | **CXL Version** | **CXL Device Support** | **Product Link**                                             |
| -------------- | -------------------- | -------------- | ------------------- | --------------------------------------- | --------------- | ---------------------- | ------------------------------------------------------------ |
| **Dell**       | PowerEdge R760       | Intel          | 2U                  | Yes, 2x double-width or 6x single-width | 1.1             | AIC                    | [Link](https://www.dell.com/en-us/shop/dell-poweredge-servers/poweredge-r760-rack-server/spd/poweredge-r760) |
| **HPE**        | ProLiant DL380 Gen11 | Intel          | 2U                  | Yes, up to 4x double-width              | 1.1             | AIC                    | [Link](https://www.hpe.com/us/en/product-catalog/servers/proliant-servers/pip.hpe-proliant-dl380-gen11-server.1014942634.html) |
| **Supermicro** | SYS-221H-TNR         | Intel          | 2U                  | Yes, up to 4x double-width              | 1.1             | AIC                    | [Link](https://www.supermicro.com/en/products/system/hyper/2u/sys-221h-tnr) |

