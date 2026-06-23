# Explainer Outline: CXL 3.1 Component Identifier

**Kernel release:** v6.14 (v6.13 → v6.14)  
**Generated:** 2026-06-22

---

## Suggested Title
CXL 3.1 Component Identifier: Tracing Events Across Devices in Linux

## Hook (first 15 seconds — grab the viewer)
Imagine your CXL memory device throws an error — but you can't tell if it's isolated to one chip or cascading across an entire memory pool. Before CXL 3.1, the kernel had no standard way to correlate events across components. That changes now. Let's look at how a single new field in the Linux kernel unlocks multi-device event tracing.

## Background (what problem existed before / what is CXL in this context)
- Brief intro to CXL (Compute Express Link): a high-speed interconnect standard for attaching memory, accelerators, and storage to CPUs with cache-coherent, low-latency access.
- CXL devices emit *event records* — structured telemetry about errors, health, and state changes — which Linux reads and exposes to user space via the kernel's CXL event subsystem.
- Before CXL 3.1: event records had no vendor-defined correlation handle. If a platform had multiple CXL components (e.g., a switch upstream of several memory expanders), there was no standard field to say "these three events all came from the same physical fault domain."
- The spec gap: system administrators and RAS (Reliability, Availability, Serviceability) tools were left to correlate events manually, by timestamp or heuristic — error-prone in large memory-pool deployments.

## Technical Explanation (the key concept, how the code/feature works — use analogies)
**Analogy:** Think of the Component Identifier like a tracking number on a package. Every package (event record) from the same shipment (fault chain) carries the same number, so the warehouse management system (RAS software) can instantly group them.

- **What the spec adds:** CXL 3.1 introduces a Component Identifier field — a vendor-defined, opaque byte sequence — that a device stamps onto event records. Devices in the same component hierarchy can use the same identifier, enabling correlation without out-of-band metadata.
- **What the kernel patch does:**
  - Extends the in-kernel CXL event record structure to hold the Component Identifier field.
  - Adds formatting support so the identifier is correctly serialized and presented when events are read from kernel space (via `tracepoints` and `cxl_mem` ABI).
  - "Formatting support" means the kernel knows how to decode the raw bytes into a human-readable (or tool-parseable) representation, rather than discarding or truncating the field.
- **Where it lives in the stack:** `drivers/cxl/core/events.c` — the central event-processing layer that sits between the hardware mailbox and user-space consumers like `rasdaemon`.

## Demo Ideas (concrete things to show on screen or in a terminal)
1. **Kernel source walkthrough** — show the struct change adding the Component Identifier field and the formatting function alongside existing fields (e.g., `dpa`, `hpa`, `flags`).
2. **Trace event output** — use `trace-cmd` or `perf` to capture a CXL event trace; highlight the new `component_id` field in the formatted output.
3. **rasdaemon log** — show a before/after of a CXL event log entry: without the field (field missing or raw hex), then with the patch applied and the identifier printed cleanly.
4. **Correlation scenario diagram** — a slide or ASCII diagram showing a CXL switch + two memory expanders, with arrows showing events from both expanders carrying the same Component Identifier, then being grouped by a RAS tool.
5. **Kernel config / module** — briefly show that no new Kconfig option is needed; it's part of the existing `CONFIG_CXL_MEM`.

## Real-World Impact (who benefits and how)
- **Data center operators** running CXL memory pools (e.g., tiered memory for AI/ML workloads): can now pinpoint whether an error event is isolated or part of a wider component failure — critical for deciding between a live migration vs. a full rack pull.
- **RAS/observability tooling authors** (`rasdaemon`, OpenBMC, vendor IPMI stacks): the kernel now surfaces a stable, spec-defined correlation handle they can index on, without custom heuristics.
- **Platform vendors** implementing CXL 3.1 devices: their Component Identifier stamps are now honored end-to-end in the Linux RAS pipeline, making the field useful rather than silently discarded.
- **Why it matters now:** CXL 3.x memory expanders are entering production deployments. Getting the telemetry pipeline right in v6.14 means operators have the correlation primitives before large-scale rollouts, not after.

## Summary & Call to Action
- Recap: CXL 3.1 introduces the Component Identifier to tag event records with a vendor-defined correlation handle; this Linux v6.14 patch teaches the kernel to format and expose it correctly.
- The patch is small — one commit — but it closes a real gap in the CXL event telemetry pipeline.
- **Call to action:** If you're building or evaluating CXL platforms, test your device's Component Identifier output with `trace-cmd` after updating to v6.14+. Links to the commit and CXL spec section in the description. Subscribe for more deep-dives into CXL kernel development every release cycle.

## Key Commits to Reference
| Commit | Note |
|---|---|
| `cxl/events: Add Component Identifier formatting for CXL spec rev 3.1` | Core patch — extends the event record struct and adds the formatting path for the new CXL 3.1 field. |

## Estimated Video Length
**6–8 minutes** — the concept is self-contained and the code surface is small (one commit, one struct field), so a tight walkthrough with a diagram and a live `trace-cmd` demo fits comfortably in this range without padding.
