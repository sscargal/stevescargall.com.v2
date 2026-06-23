---
title: "Linux 7.2 Seeds \"Blackwell-Next\": A Deep Dive into the nvgrace-gpu VFIO CXL DVSEC Change"
meta_title: "NVIDIA Blackwell-Next VFIO CXL DVSEC: Linux 7.2 Kernel Deep Dive"
description: "Linux 7.2's VFIO pull adds CXL DVSEC-based GPU readiness to the nvgrace-gpu driver for Blackwell-Next. A code-level walkthrough from a kernel developer and CXL architect's perspective."
date: 2026-06-23T00:00:00Z
image: "featured_image.webp"
categories: ["CXL", "Linux"]
author: "Steve Scargall"
tags: ["CXL", "Linux", "Kernel", "NVIDIA", "VFIO", "GPU", "Virtualization", "Blackwell"]
draft: false
aliases:
---

Linux 7.2's VFIO pull request quietly dropped a commit with a codename I hadn't seen before: **Blackwell-Next**. If you only read the Phoronix headline, it looks like a minor prep patch. It is — but it's also a clean window into where NVIDIA is taking its CPU-coherent GPU stack, how CXL is quietly becoming the standard signaling interface for next-generation accelerators, and what that means if you're building infrastructure or tooling on top of these platforms.

Let me walk through what actually changed, verified against the live kernel source.

## Background: The nvgrace-gpu VFIO Driver

The `nvgrace-gpu` driver (`drivers/vfio/pci/nvgrace-gpu/main.c`) is a VFIO PCI variant driver for NVIDIA's Grace-based superchips — the GH200 Grace Hopper and GB200/GB300 Grace Blackwell. These are not discrete add-in cards. They're CPU+GPU superchips where a Grace (or Vera) ARM CPU and one or more NVIDIA GPUs share a chip-to-chip cache-coherent interconnect (NVLink-C2C), with the GPU's HBM accessible from the CPU as coherent memory.

What this driver does is expose that GPU device memory to KVM/QEMU VMs via VFIO — direct passthrough of coherent GPU RAM to a virtual machine, no host driver interposing on every access. The memory appears to the guest as two 64-bit BARs:

| BAR | Region | Type | Purpose |
|-----|--------|------|---------|
| BAR4/5 | `usemem` | Cacheable (NORMAL) | Workload GPU memory, GPUDirect RDMA-capable |
| BAR2/3 | `resmem` | Non-cacheable (NORMAL_NC) | MIG feature support (GH200 only) |

The split exists because GH200 has a hardware bug: MIG requires a non-cached region, so the driver carves 1GB off the end of device memory and maps it differently. GB200 and later have the bug fixed — no partition needed, the entire device memory is exposed as one cacheable BAR4/5 region.

Memory sizing doesn't come from the PCI BARs themselves. It comes from ACPI Device-Specific Data (DSD) properties that firmware sets:

```c
device_property_read_u64(&pdev->dev, "nvidia,gpu-mem-base-pa", pmemphys);
device_property_read_u64(&pdev->dev, "nvidia,gpu-mem-size",    pmemlength);
```

Current supported hardware:

| Device | PCI ID | Readiness path |
|--------|--------|----------------|
| GH200 120GB | 0x2342 | Legacy BAR0 |
| GH200 480GB | 0x2345 | Legacy BAR0 |
| GH200 SKU   | 0x2348 | Legacy BAR0 |
| GB200 SKU   | 0x2941 | Legacy BAR0 |
| GB300 SKU   | 0x31C2 | **CXL DVSEC** (Blackwell-Next) |

That last row is where Linux 7.2 comes in.

## What "Blackwell-Next" Actually Changed

The Phoronix article was published 2026-06-21. The commit landed three weeks earlier on 2026-06-02 as **`682ecb14e8`**, authored by Ankit Agrawal (NVIDIA), suggested by VFIO maintainer Alex Williamson, and reviewed by Kevin Tian (Intel). It touches exactly two files: `+163/-12` lines in `main.c` and `+1` line in `include/uapi/linux/pci_regs.h`.

Worth noting: GB300 (0x31C2) was **not** added by this commit. That happened 9 months earlier in a separate commit by Tushar Dave (`407aa63018`, 2025-09-25). The Blackwell-Next patch doesn't touch the device ID table at all. What it adds is the CXL DVSEC *readiness path* that GB300 needs — the device was already registered, it just didn't have the right probe logic.

### The Core Problem This Solves

On GH200 and GB200, the driver checks whether the GPU is ready to accept memory access by polling two BAR0 registers: one for HBM training completion and one for C2C link status. Both need to read `0xFF` before the driver allows VM memory mappings to proceed:

```c
#define C2C_LINK_BAR0_OFFSET     0x1498
#define HBM_TRAINING_BAR0_OFFSET 0x200BC
#define STATUS_READY             0xFF
#define POLL_TIMEOUT_MS          (30 * 1000)  /* 30 seconds */

do {
    if ((ioread32(io + C2C_LINK_BAR0_OFFSET) == STATUS_READY) &&
        (ioread32(io + HBM_TRAINING_BAR0_OFFSET) == STATUS_READY))
        return 0;
    if (schedule_timeout_killable(msecs_to_jiffies(POLL_QUANTUM_MS)))
        return -EINTR;
} while (!time_after(jiffies, timeout));
```

This requires BAR0 to be mapped during probe: `pci_enable_device()` → `pci_request_selected_regions()` → `pci_iomap()`. It's proprietary — those register offsets are not standardized anywhere.

On **Blackwell-Next (GB300)**, the hardware doesn't use BAR0 registers for readiness signaling. Instead, it exposes the CXL Device DVSEC capability in PCIe config space. The kernel comment says it directly (line 1277):

> "On Blackwell-Next systems, memory readiness is determined via the CXL Device DVSEC in PCI config space and does not require BAR0."

### The CXL DVSEC Path

At probe time, the driver now calls `pci_find_dvsec_capability()` looking for the standard CXL Device DVSEC (vendor ID `PCI_VENDOR_ID_CXL`, capability ID `PCI_DVSEC_CXL_DEVICE = 0`):

```c
nvdev->cxl_dvsec = pci_find_dvsec_capability(pdev, PCI_VENDOR_ID_CXL,
                                              PCI_DVSEC_CXL_DEVICE);
```

If this returns zero — capability not present — the device uses the legacy BAR0 path. Non-zero means GB300 or later: use CXL DVSEC. Every subsequent branch in the driver checks `nvdev->cxl_dvsec` to pick the right path.

The CXL readiness check reads the `RANGE_SIZE_LOW(0)` register from the CXL Device DVSEC in config space (offset `0x1C` from the DVSEC base). Two bits matter:

- `PCI_DVSEC_CXL_MEM_INFO_VALID` (bit 0): device memory information is valid
- `PCI_DVSEC_CXL_MEM_ACTIVE` (bit 1): device memory is active and accessible

This is straight from **CXL spec r4.0 section 8.1.3.8.2**, which defines a two-phase readiness sequence:

1. `MEM_INFO_VALID` must be set within **1 second** of reset/power-on
2. `MEM_ACTIVE` must be set within `Memory_Active_Timeout` after `MEM_INFO_VALID`

That timeout field is three bits at positions [15:13] of the same register. The encoding is exponential — each step is 4×:

```c
static inline unsigned long cxl_mem_active_timeout_ms(u8 timeout)
{
    return MSEC_PER_SEC << (2 * min_t(u8, timeout, 4));
    /* 000b=1s, 001b=4s, 010b=16s, 011b=64s, 100b+=256s */
}
```

The worst case is **256 seconds** — roughly 8.5× longer than the legacy 30-second BAR0 poll. That's a meaningful probe-time difference.

### The Locking Challenge

A 256-second wait can't happen under `memory_lock` — it would block every VM memory access for the entire duration. The legacy 30-second wait was manageable inside the lock; 256 seconds is not.

The solution is an explicit lockless fast path for CXL devices. In the huge fault handler:

```c
/* Run locklessly before acquiring memory_lock */
if (nvdev->cxl_dvsec && READ_ONCE(nvdev->reset_done) &&
    nvgrace_gpu_wait_device_ready_cxl(nvdev))
    return VM_FAULT_SIGBUS;

scoped_guard(rwsem_read, &vdev->memory_lock) {
    /* Quick re-check under lock to catch reset races */
    rc = nvgrace_gpu_check_device_ready(nvdev);
    if (rc == -EAGAIN)
        goto retry;   /* reset raced the lockless wait — retry, not SIGBUS */
    ...
}
```

If a device reset races in between the lockless CXL wait and the in-lock recheck, the recheck returns `-EAGAIN` and the fault handler loops back to the CXL wait rather than returning a spurious `VM_FAULT_SIGBUS` to the VM. The same pattern is applied in `nvgrace_gpu_read_mem()` and `nvgrace_gpu_write_mem()`.

The kernel also calls this out explicitly (line 1289):

> "Note that the worst-case wait here is ~256s (vs ~30s on the legacy path) and may block device unbind/sysfs for the duration."

If you're scripting around this driver and wondering why an unbind is hanging, there's your answer.

### Signal Handling Fix (Both Paths)

The patch also fixed an existing issue on the legacy path. The original `msleep()` loop was not interruptible — a stuck 30-second probe could not be killed. The patch switches both paths to `schedule_timeout_killable()`, which returns `-EINTR` on a fatal signal. No more hung-task kernel panics while waiting on a slow device.

## Is This Driver Actually Useful Today?

Yes. This is not a placeholder or an early stub. The `nvgrace-gpu` driver has been production-grade since GH200 launched in 2023-2024. The "Supported" status is in the Linux MAINTAINERS file, copyright 2024 NVIDIA. GH200 systems are deployed at scale in AI data centers and research labs. GB200 is shipping to enterprises and hyperscalers now.

The GB300 (0x31C2) device ID has been in the table since September 2025. This Blackwell-Next patch completes the picture by giving GB300 the readiness path its firmware actually uses. Without it, GB300 would fall through to the legacy BAR0 path on a device that doesn't use BAR0 for readiness — which would likely timeout or produce unpredictable results.

Standard KVM/QEMU needs no modifications. The VFIO character device interface is unchanged. No new sysfs attributes. No new devdax nodes. The VM guest sees the same BAR layout it always has. The only behavioral change from the VM operator's perspective is that GB300 probe might take longer (up to 256s) and is now interruptible.

## What the P2P TODO Tells Us

There's a commented-out block in `nvgrace_get_dmabuf_phys()` that's worth reading:

```c
/*
 * if (nvdev->resmem.memlength && region_index == RESMEM_REGION_INDEX) {
 *     The P2P properties of the non-BAR memory is the same as the
 *     BAR memory, so just use the provider for index 0. Someday
 *     when CXL gets P2P support we could create CXLish providers
 *     for the non-BAR memory.
 * }
 */
```

Device-to-device DMA (GPUDirect RDMA) works today via the BAR0 P2P provider for both regions. The comment is noting that once the CXL subsystem gains native P2P DMA support, the non-BAR memory could have CXL-specific providers instead. That's a future optimization, not a missing feature. The driver does P2P today.

## For CXL Software Architects

Linux 7.1 landed the CXL Type 2 accelerator infrastructure — exporting internal structs so external drivers can bind Type 2 devices (accelerators with attached memory) into the CXL stack:

```c
/* 7.1: cxl: export internal structs for external Type2 drivers */
/* 7.1: cxl: support Type2 when initializing cxl_dev_state */
```

Linux 7.2 (this patch) moves GPU readiness signaling onto the standardized CXL DVSEC mechanism. These two releases together are not coincidental — they represent NVIDIA progressively aligning the Grace GPU stack with CXL protocol semantics.

If you're building accelerator management tooling on top of `nvgrace-gpu`, the `cxl_dvsec` field is now the detection signal for device generation. Zero means legacy (GH200/GB200); non-zero means Blackwell-Next (GB300) or later. The `nvgrace_gpu_wait_device_ready_cxl()` function implements the spec-defined state machine directly against `pci_regs.h` constants — no vendor-specific register knowledge required.

## Speculating on Vera Rubin

This is where I shift from "what the code says" to "what I think it means," so take it accordingly.

NVIDIA's Grace CPU (paired with Hopper and Blackwell GPUs) supports PCIe Gen5. The Vera CPU — paired with Rubin GPUs in the next-generation superchip arriving H2 2026 — explicitly supports **PCIe Gen6 and CXL 3.1**. That's the first time NVIDIA has listed CXL on a CPU specification. NVLink-C2C Gen2 doubles coherent bandwidth from 900 GB/s to 1.8 TB/s and ties Vera to two Rubin GPUs per superchip, with up to 288GB HBM4 per GPU.

The pattern the Blackwell-Next patch establishes is significant: `pci_find_dvsec_capability(pdev, PCI_VENDOR_ID_CXL, PCI_DVSEC_CXL_DEVICE)` at probe time, then a clean branch to the CXL DVSEC readiness state machine. A future Vera+Rubin VFIO variant driver (`nvvera-gpu` or whatever they name it) would almost certainly use the same pattern — except there would be no legacy BAR0 fallback. The CXL path would be the *only* path.

The P2P TODO comment becomes interesting here too. CXL 3.1 includes a peer-to-peer DMA fabric specification. Once that lands in the kernel's CXL subsystem, those commented-out CXL P2P providers in `nvgrace_get_dmabuf_phys()` become implementable. With Vera supporting CXL 3.1 natively, the motivation to do that work goes up substantially.

The CXL DVSEC `Memory_Active_Timeout` encoding — supporting up to 256 seconds — also makes more sense in the context of Vera Rubin's 288GB HBM4 per GPU. HBM4 training at that density takes time. A 30-second hard cap was already pushing it for GB200 HBM3e; 256 seconds is the CXL spec's answer to "how long does a really large HBM stack need?"

My read: "Blackwell-Next" is NVIDIA's internal label for the GB300 architecture class, where CXL DVSEC became the GPU memory readiness interface. GB300 is the bridge hardware. Vera Rubin drops the bridge — it's CXL-native from the start, and the kernel work to support that is already underway in the pattern this commit establishes.

## What to Watch For

- A `nvvera-gpu` or similar VFIO variant driver appearing in the Linux 7.3–8.0 timeframe as Vera Rubin hardware samples reach kernel developers
- CXL P2P patches in the CXL subsystem — if and when these land, the commented-out provider code in `nvgrace_get_dmabuf_phys()` becomes the model for how to use it
- ACPI DSD property evolution — Vera's CXL 3.1 fabric-level addressing might require different firmware properties than `nvidia,gpu-mem-base-pa` / `nvidia,gpu-mem-size`
- Other VFIO variant drivers adopting the same `pci_find_dvsec_capability()` + CXL DVSEC detection pattern for their own next-generation hardware

The commit itself is 175 lines. The implications are longer.

---

**Links:**
- Commit `682ecb14e8`: [vfio/nvgrace-gpu: Add Blackwell-Next GPU readiness check via CXL DVSEC](https://github.com/torvalds/linux/commit/682ecb14e83840e87ea36c6d7c16c5111ce18784)
- Prior commit `407aa63018`: [vfio/nvgrace-gpu: Add GB300 SKU to the devid table](https://github.com/torvalds/linux/commit/407aa63018d15c35a34938633868e61174d2ef6e) (Tushar Dave, 2025-09-25)
- Driver source: [drivers/vfio/pci/nvgrace-gpu/main.c](https://github.com/torvalds/linux/blob/master/drivers/vfio/pci/nvgrace-gpu/main.c)
- VFIO pull request for Linux 7.2: [lore.kernel.org](https://lore.kernel.org/lkml/20260615163849.5b6ac84c@shazbot.org/)
- CXL spec reference: CXL r4.0 sec 8.1.3.8.2 (Memory_Active_Timeout encoding)
- NVIDIA Vera CPU: [PCIe Gen6 / CXL 3.1 specifications](https://www.nvidia.com/en-us/data-center/vera-cpu/)
- NVIDIA Vera Rubin platform technical overview: [Inside the NVIDIA Vera Rubin Platform](https://developer.nvidia.com/blog/inside-the-nvidia-rubin-platform-six-new-chips-one-ai-supercomputer/)
