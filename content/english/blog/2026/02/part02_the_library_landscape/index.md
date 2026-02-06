---
title: "The Library Landscape: Why Build Another One?"
meta_title: "The Library Landscape: Why Build Another One?"
date: 2026-02-02T13:05:00-06:00
description: "Evaluating existing 3MF libraries and making the case for a pure Rust implementation"
image: "featured_image.webp"
categories: ["3D Printing"]
author: "Steve Scargall"
tags: ["3D Printing", "Rust", "3MF", "Open Source"]
draft: false
aliases: []
series: "lib3mf-rs"
part: 2
reading_time: 4
---

## Series: Building lib3mf-rs

This post is part of a 5-part series on building a comprehensive 3MF library in Rust:

1. [Part 1: My Journey Building a 3MF Native Rust Library from Scratch](<{{< relref "/blog/2026/02/part01_building_a_3MF_rust_library/index.md" >}}>)
2. [Part 2: The Library Landscape - Why Build Another One?](<{{< relref "/blog/2026/02/part02_the_library_landscape/index.md" >}}>)
3. [Part 3: Into the 3MF Specification Wilderness - Reading 1000+ Pages of Specifications](<{{< relref "/blog/2026/02/part03_into_the_spec_wilderness/index.md" >}}>)
4. [Part 4: Design for Developers - Features, Flags, and the CLI](<{{< relref "/blog/2026/02/part04_design_for_developers/index.md" >}}>)
5. [Part 5: Reflections and What's Next - Lessons from Building lib3mf-rs](<{{< relref "/blog/2026/02/part05_reflections_and_whats_next/index.md" >}}>)

## "Why not just use the existing library?"

It's a fair question. One I asked myself many times during the early days of this project. The 3MF Consortium maintains [lib3MF](https://github.com/3MFConsortium/lib3mf), a comprehensive C++ implementation used by major companies in additive manufacturing. Why build another one?

The answer isn't "because the existing solution is bad." It's more nuanced than that.

## The Official Implementation: lib3MF

The C++ lib3MF is genuinely impressive. It's:

- **Complete**: Implements all specifications thoroughly
- **Battle-tested**: Used in production by major slicer applications
- **Well-maintained**: Active development by the 3MF Consortium
- **Comprehensive**: Includes validation, repair, and extensive functionality

If you're building a C++ application, it's an excellent choice.

But it has characteristics that made it less ideal for what I wanted to build:

### Memory Safety

C++ requires manual memory management. While lib3MF is carefully written, the language itself doesn't prevent:

- Use-after-free bugs
- Double-free errors
- Memory leaks
- Buffer overflows in file parsing

File parsing is a particularly risky domain. You're accepting untrusted input and interpreting it as structured data. One malformed 3MF file could potentially trigger memory corruption.

Rust's borrow checker eliminates entire categories of these bugs at compile time. Not through careful coding—through language-level guarantees.

### Build Complexity

Getting lib3MF integrated into a project requires:

- C++ compiler toolchain
- CMake build system
- Platform-specific configuration
- Managing C++ dependencies (zlib, openssl, etc.)

From Rust, you'd need to:
1. Build C++ library with proper flags
2. Generate or write FFI bindings
3. Wrap unsafe FFI calls
4. Handle C++ exceptions across FFI boundary
5. Manage memory ownership between Rust and C++

It's doable, but it's not pleasant.

### Modern Environment Support

The C++ library predates WebAssembly and async/await patterns. While you could compile it to WASM with Emscripten, it wasn't designed for that environment.

For applications that need:
- Browser-based 3MF validation
- Async I/O for high-throughput systems
- Minimal binary size
- Zero-copy parsing

...the C++ architecture presents challenges.

## The Rust Ecosystem

I surveyed existing Rust crates. Several developers had started implementing 3MF parsers:

- Some focused on the Core specification only
- Others implemented basic geometry reading
- A few included Material extension support

But as I evaluated them against the full specification landscape, none provided complete coverage:

| Specification | Existing Rust Libs |
|--------------|-------------------|
| Core v1.4.0 | ✅ Partial (missing features) |
| Materials v1.2.1 | ⚠️ Basic support |
| Production v1.1.2 | ❌ Not implemented |
| Beam Lattice v1.2.0 | ❌ Not implemented |
| Slice v1.0.2 | ❌ Not implemented |
| Volumetric v0.8.0 | ❌ Not implemented |
| Secure Content v1.0.2 | ❌ Not implemented |
| Boolean Operations v1.1.1 | ❌ Not implemented |
| Displacement v1.0.0 | ❌ Not implemented |

This isn't a criticism of those projects. Building a file format parser is hard work, and implementing the Core specification is valuable on its own.

But modern 3D printing workflows increasingly depend on the extensions:

- **Materials**: Define physical properties, colors, multi-material printing
- **Production**: Track parts, build items, manufacturing metadata
- **Slice**: Store pre-sliced data for faster printing
- **Secure Content**: Digital signatures, encryption, supply chain verification
- **Beam Lattice**: Lightweight structures, optimal material usage

A library that only reads geometry misses the richness of what 3MF enables.

## The Gap in the Ecosystem

I found myself at an intersection:

**What existed:**
- Comprehensive C++ library (with integration complexity)
- Partial Rust implementations (missing critical features)

**What was missing:**
- Memory-safe implementation with complete specification coverage
- Rust-native design that embraces modern patterns
- Minimal dependency footprint for diverse use cases

The gap was real.

## The Decision: Build From Scratch

I decided to build lib3mf-rs with specific design goals:

### 1. Memory Safety as Foundation

Pure Rust implementation, no unsafe code in public APIs. Let the compiler prevent entire bug categories that would require careful review in C++.

This matters because file parsers are attack surfaces. A malicious 3MF file shouldn't be able to corrupt memory, even if it contains carefully crafted malformed data.

### 2. Complete Specification Coverage

All nine specifications. Not "someday" or "if there's demand"—from the start. This meant:

- Reading and understanding 325 features
- Implementing parsing, validation, and generation
- Supporting edge cases and interactions between specifications

### 3. Minimal Dependency Philosophy

I started with a monolithic design and implementation that included all specification features and functionality, but quickly realized this wasn't the correct or 'best' design. Not because it was bad, but not everyone needs cryptography libraries, parallel processing, or needs PNG texture validation. I haven't found a 3MF file in any of the online print file repositories that use these capabilities. I'm not sure the slicers support it. I don't like bloaty code, not that these features were huge. By taking this design decision, it actually caused a signficiant re-write with several days of work to save a few megabytes at best. But I felt it would deliver a better and optimized solution.

lib3mf-rs uses feature flags to make dependencies optional, meaning you, the developer, get to pick what you do and do not want. Here's an example `Config.toml` you can use in your projects to pull in the core, core+crypto, or core+parallel features, while excluding the others.

```toml
# Minimal - just read/write 3MF files
[dependencies]
lib3mf-core = "0.1"

# Add cryptography for digital signatures
[dependencies]
lib3mf-core = { version = "0.1", features = ["crypto"] }

# Add parallel processing for large meshes
[dependencies]
lib3mf-core = { version = "0.1", features = ["parallel"] }
```

The difference is significant:

- **Minimal build** (no features): 154 crates
- **With crypto feature**: ~300 crates
- **Savings**: 48% fewer dependencies for users who don't need security features

This respects developer's choice. Use what you need, don't pay for what you don't.

### 4. Accessibility Beyond Developers

A library is only valuable if people can use it. Not everyone who needs to analyze 3MF files is a Rust developer—or any kind of developer.

This led to a parallel effort: `lib3mf-cli`, a command-line tool that exposes all library capabilities:

```bash
# Install
cargo install lib3mf-cli

# Use immediately
lib3mf-cli stats model.3mf
lib3mf-cli validate project.3mf
lib3mf-cli extract model.3mf "Metadata/thumbnail.png"
```

We'll explore the CLI deeply in Part 4.

## Not Reinventing—Filling a Gap

This wasn't about proving I could build something that already existed. It was about creating what didn't exist: a memory-safe, comprehensive, accessible 3MF implementation for the Rust ecosystem.

The C++ library serves its community well. The existing Rust crates provide value for their use cases. lib3mf-rs aimed to complement, not compete.

## What This Enabled

By building from scratch with clear design principles, we created:

- A library that Rust developers can integrate without FFI complexity
- Complete specification support for modern 3D printing workflows
- Minimal dependencies that respect diverse project requirements
- Tools that non-developers can use immediately
- A foundation for future innovation in 3MF tooling

The next challenge? Actually understanding those nine specifications.
