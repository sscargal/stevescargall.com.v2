---
title: "My Journey Building a 3MF Native Rust Library from Scratch"
meta_title: "My Journey Building a 3MF Native Rust Library from Scratch"
description: "How adding a travel distance feature to OrcaSlicer sparked a journey into building a comprehensive 3MF library in Rust"
date: 2026-02-01T13:05:00-06:00
image: "featured_image.webp"
categories: ["3D Printing"]
author: "Steve Scargall"
tags: ["3D Printing", "Rust", "3MF", "Open Source"]
draft: false
aliases: []
series: "lib3mf-rs"
part: 1
reading_time: 4
---

For the past few years, I've been getting more and more into 3D printing as a hobbyist. Like everyone, I started with one, a Bambu Lab X1 Carbon, which has now grown to three printers. I find the hobby fascinating as it entangles software, firmware, hardware, physics, and materials science.

As a software engineer, I'm naturally drawn to the software side of things (Slicer and Firmware). But what interests me most, is how the software interacts with the hardware and the materials. How the slicer translates the 3D model into instructions for the printer (G-Code). How the printer executes those instructions. How the materials behave under the printer's control.

About three months ago (Oct'25), I had successfully submitted a [travel distance feature to OrcaSlicer](https://stevescargall.com/blog/2025/10/i-added-a-feature-to-orcaslicer-to-show-travel-distance-and-moves/). It was my first contribution to a major 3D printing project, and I was thrilled to see how it would be accepted and used by others.

Most modern slicers use 3MF files to store the 3D model and its associated data. This format is everywhere in the 3D printing world. Yet I realized I only understood the surface of what these files contained. I wanted to understand 3MF deeply, not just use it.

## Series: Building lib3mf-rs

This post is part of a 5-part series on building a comprehensive 3MF library in Rust:

1. [Part 1: My Journey Building a 3MF Native Rust Library from Scratch](<{{< relref "/blog/2026/02/part01_building_a_3MF_rust_library/index.md" >}}>)
2. [Part 2: The Library Landscape - Why Build Another One?](<{{< relref "/blog/2026/02/part02_the_library_landscape/index.md" >}}>)
3. [Part 3: Into the 3MF Specification Wilderness - Reading 1000+ Pages of Specifications](<{{< relref "/blog/2026/02/part03_into_the_spec_wilderness/index.md" >}}>)
4. [Part 4: Design for Developers - Features, Flags, and the CLI](<{{< relref "/blog/2026/02/part04_design_for_developers/index.md" >}}>)
5. [Part 5: Reflections and What's Next - Lessons from Building lib3mf-rs](<{{< relref "/blog/2026/02/part05_reflections_and_whats_next/index.md" >}}>)

## The Curiosity That Started Everything

The travel distance feature required me to analyze toolpath G-Code data stored in 3MF files. I found myself asking questions:

- How does the slicer embed this information?
- What else is packed into these files that I don't see?
- Why do some 3MF files work seamlessly while others cause errors?

I started reading the [3MF specification](https://3mf.io/spec/). Then I discovered there wasn't just *one* specification—there were nine. The Core specification, plus eight extensions covering materials, production workflows, beam lattices, slicing data, volumetric properties, security, boolean operations, and displacement mapping.

I was fascinated. This wasn't just a simple mesh container—3MF is a sophisticated format designed for the entire additive manufacturing workflow, from design through production.

## Why Rust?

I wanted a project to deepen my Rust knowledge. Something substantial. Something that would force me to understand both a complex domain (3MF) and a powerful language (Rust) at the same time. Coming from a systems, file system, and kernel programming background, Rust's promise of memory safety without garbage collection intrigued me. The borrow checker was challenging, but I appreciated what it enforced: safety by design, not by careful coding.

The pieces started coming together: What if I built a comprehensive 3MF library in Rust?

## The Library Landscape

My first step was research. Surely someone had already solved this problem?

The official library exists: [lib3MF](https://github.com/3MFConsortium/lib3mf) from the 3MF Consortium. Written in C++, it's comprehensive and widely used in industry. But it has characteristics that made it less appealing for my goals:

- **Complex build system** - Dependencies on C++ toolchains, careful platform-specific configuration
- **Memory management** - Manual memory management with all its associated risks
- **Integration challenges** - Difficult to use from Rust without unsafe FFI bindings
- **Not designed for modern environments** - No first-class WebAssembly or async support

I also surveyed existing Rust implementations. [Several crates on crates.io](https://crates.io/search?q=3mf) implemented parts of the 3MF specification. But as I evaluated them, a pattern emerged:

- Most implemented only the Core specification
- Material definitions were missing or incomplete
- Production extensions? Not implemented
- Secure Content? Not there
- Beam lattices, volumetric data, boolean operations? Not found

None implemented all nine specifications extensively.

## The Decision

I could have:
1. Used the C++ library through FFI bindings
2. Contributed to an existing Rust crate
3. Built something from scratch

I chose option three.

Not because I wanted to reinvent the wheel, but because I saw an opportunity to build something the ecosystem needed:

- **Memory safe by design** - Pure Rust implementation, leveraging the type system and borrow checker
- **Complete specification coverage** - All nine specifications, not just Core
- **Minimal dependencies** - Don't force users to pull in cryptography libraries if they just want to read mesh data
- **Modern architecture** - Async-ready, WASM-capable, designed for current and future use cases
- **Developer-friendly** - Clear APIs, comprehensive documentation, real-world examples

## What I Built

Over the next few months, I used my limited spare time to immerse myself in specifications, Rust patterns, and 3D printing workflows. The result is [lib3mf-rs](https://github.com/sscargal/lib3mf-rs):

- **Complete specification coverage**: All 9 specifications, all features
- **Pure Rust**: Memory safe with zero unsafe code in the public API
- **Flexible architecture**: Feature flags let you use only what you need
- **CLI for everyone**: A command-line tool so anyone can use the library, even without writing code
- **Production-ready**: Comprehensive test coverage, fuzzing infrastructure, real-world validation

But more than the code, this project became a journey of deep learning:

- Understanding complex specifications
- Designing APIs that balance safety and ergonomics
- Building for diverse use cases (from hobbyists to industrial workflows)
- Creating tools that empower both developers and non-developers

## Why This Matters

3MF is central to modern 3D printing. Bambu Lab, Prusa, Ultimaker, and other leading manufacturers have adopted it. The format carries not just geometry, but materials, print settings, slicing data, and production metadata.

When a file format becomes infrastructure, its implementation quality matters. Memory safety matters. Correctness matters. Accessibility matters.

This is why lib3mf-rs exists.

## The Journey Ahead

Over this blog series, I'll share:

- Why building from scratch made sense (and what I learned from existing solutions)
- The two weeks I spent just reading specifications
- Design decisions that shaped the architecture
- How the CLI makes these capabilities accessible to everyone
- Lessons learned and what surprised me along the way

This is the story of going from "I want to understand this" to "I built the infrastructure for others to build on."

From curiosity to contribution.

---

**Next in this series**: [Part 2: The Library Landscape - Why Build Another One?]({{< relref "../part02_the_library_landscape/index.md" >}})

**Resources**:
- [lib3mf-rs on GitHub](https://github.com/sscargal/lib3mf-rs)
- [lib3mf-rs documentation](https://sscargal.github.io/lib3mf-rs)
- [Install the CLI](https://crates.io/crates/lib3mf-cli): `cargo install lib3mf-cli`
