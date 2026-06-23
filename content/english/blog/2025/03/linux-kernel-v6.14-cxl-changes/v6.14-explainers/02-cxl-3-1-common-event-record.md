# Explainer Outline: CXL 3.1 Common Event Record

**Kernel release:** v6.14 (v6.13 → v6.14)  
**Generated:** 2026-06-22

---

## Suggested Title
CXL 3.1 Event Records Explained: How Linux Reads Device Health

## Hook
Imagine your CXL memory device is quietly failing — errors accumulating, performance degrading — but your kernel can't read the warning signs because it's speaking the wrong dialect of the spec. That's exactly the bug these four commits fix, and it matters for every system running CXL hardware today.

## Background
CXL devices report health, error, and informational events through a mailbox command called **Get Event Records**. Every event type — whether it's a DRAM error, a general media fault, or a memory module issue — starts with a shared header called the **Common Event Record**. Think of it as the envelope that all CXL event mail arrives in: before you can read the letter inside, you need to know where the address field ends and the message begins.

The problem: the Linux kernel's struct layout for that envelope was written against an earlier CXL spec revision. CXL 3.1 redefined some of those fields — sizes, offsets, reserved regions — and the kernel hadn't caught up. Reading events from a 3.1-compliant device with an older struct means misinterpreting field boundaries: like reading a CSV with the wrong column count.

CXL itself is a high-speed interconnect (built on PCIe) that lets CPUs access memory on external devices — accelerators, memory expansion modules — with cache-coherent semantics. Event reporting is how those devices say "something happened you should know about."

## Technical Explanation
The Common Event Record is defined in the CXL spec as a fixed binary structure. Each field has a precise byte offset and width. When the spec revises those fields — adding a new flag bit here, resizing a reserved region there — the kernel's C struct must match exactly, because the driver uses pointer arithmetic and `sizeof()` to parse raw bytes from the device mailbox.

**Analogy:** Think of it like a standardized tax form. If the IRS moves "Line 12b: Capital Gains" one row down between editions, and your software still reads row 12b expecting capital gains, you'll silently get the wrong number — no error, just bad data.

The four commits update four structs in sequence:
1. **`struct cxl_event_record_hdr`** — the base Common Event Record, fixing the shared header fields.
2. **`struct cxl_event_mem_module`** — the Memory Module Event, which embeds the common header.
3. **`struct cxl_event_dram`** — the DRAM Event Record.
4. **`struct cxl_event_gen_media`** — the General Media Event Record.

Each downstream struct depends on the common header being correct first — classic layered dependency. Fix the foundation, and everything built on it aligns automatically.

Key code area: `include/linux/cxl-event.h` and `drivers/cxl/core/mbox.c` where events are parsed out of mailbox responses.

## Demo Ideas
- **Side-by-side diff view** of the old vs. new struct in `cxl-event.h` — highlight changed field sizes and offsets with annotations.
- **`pahole` output** before and after: run `pahole` on the struct to show byte layout, demonstrating concretely how field positions shifted.
- **`xxd` hex dump** of a simulated raw event record, then walk through parsing it with both the old and new struct to show how misalignment produces garbage values.
- **`dmesg` output** on a system with a CXL emulator (QEMU + cxl-test) showing events being surfaced correctly post-fix.
- **`git diff` walkthrough** of the four commits — show them as a clean, ordered series.

## Real-World Impact
- **System administrators** running CXL memory expansion shelves get accurate health event data — bad DRAM rows, media errors, and module faults are reported correctly instead of silently garbled.
- **Hardware vendors** shipping CXL 3.1 devices no longer need workarounds for kernels that misparse their event records.
- **Kernel developers** working on RAS (Reliability, Availability, Serviceability) features get a clean, spec-accurate foundation to build correctable/uncorrectable error handling on top of.
- **Data center operators** using CXL for memory tiering get more trustworthy fault telemetry, which feeds into decisions about predictive memory retirement and SLA guarantees.

## Summary & Call to Action
The CXL Common Event Record update is a small patch with outsized consequence: four struct definitions corrected against the 3.1 spec mean every event your CXL device ever reports is now parsed correctly by Linux 6.14+. It's the kind of foundational fix that makes all future CXL reliability work possible.

**Call to action:** If you're working with CXL hardware, check your kernel version — you want 6.14 or later for accurate event reporting. Drop a comment if you'd like a deeper dive into CXL RAS or the Get Event Records mailbox command. Subscribe for more kernel internals breakdowns.

## Key Commits to Reference
- **`cxl/events: Update Common Event Record to CXL spec rev 3.1`** — fixes the base header struct; all other structs depend on this landing first.
- **`cxl/events: Update Memory Module Event Record to CXL spec rev 3.1`** — updates the module-level event that embeds the common header; covers thermal and operational state events.
- **`cxl/events: Update DRAM Event Record to CXL spec rev 3.1`** — fixes parsing of DRAM-specific error events (row, column, bank addresses).
- **`cxl/events: Update General Media Event Record to CXL spec rev 3.1`** — fixes the catch-all media error event type used for physical media faults.

## Estimated Video Length
**6–8 minutes** — 90 seconds for hook/background, 3 minutes on the technical explanation with visuals, 90 seconds on demo, 1 minute on impact and CTA.
