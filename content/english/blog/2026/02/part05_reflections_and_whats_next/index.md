---
title: "Reflections and What's Next: Lessons from Building lib3mf-rs"
meta_title: "Reflections and What's Next: Lessons from Building lib3mf-rs"
date: 2026-02-05T13:05:00-06:00
description: "What we learned building a comprehensive 3MF library, and an invitation to join the journey"
image: "featured_image.webp"
categories: ["3D Printing"]
author: "Steve Scargall"
tags: ["3D Printing", "Rust", "3MF", "Open Source"]
series: "lib3mf-rs"
part: 5
reading_time: 4
draft: false

---

## Series: Building lib3mf-rs

This post is part of a 5-part series on building a comprehensive 3MF library in Rust:

1. [Part 1: My Journey Building a 3MF Native Rust Library from Scratch](<{{< relref "/blog/2026/02/part01_building_a_3MF_rust_library/index.md" >}}>)
2. [Part 2: The Library Landscape - Why Build Another One?](<{{< relref "/blog/2026/02/part02_the_library_landscape/index.md" >}}>)
3. [Part 3: Into the 3MF Specification Wilderness - Reading 1000+ Pages of Specifications](<{{< relref "/blog/2026/02/part03_into_the_spec_wilderness/index.md" >}}>)
4. [Part 4: Design for Developers - Features, Flags, and the CLI](<{{< relref "/blog/2026/02/part04_design_for_developers/index.md" >}}>)
5. [Part 5: Reflections and What's Next - Lessons from Building lib3mf-rs](<{{< relref "/blog/2026/02/part05_reflections_and_whats_next/index.md" >}}>)

On February 4th, 2026, lib3mf-rs is a published open-source project with complete specification coverage, available for anyone to use.

- **Github**: [https://github.com/sscargal/lib3mf-rs](https://github.com/sscargal/lib3mf-rs)
- **Crates.io**: 
  - [lib3mf-core](https://crates.io/crates/lib3mf-core)
  - [lib3mf-cli](https://crates.io/crates/lib3mf-cli)
  - [lib3mf-async](https://crates.io/crates/lib3mf-async)
  - [lib3mf-converters](https://crates.io/crates/lib3mf-converters)
- **Documentation** [lib3mf-rs Documentation](https://sscargal.github.io/lib3mf-rs/stable/book/)"

## What Surprised Me

### Surprise 1: Specification Quality Varies

Some specifications were beautifully written with clear examples and edge cases documented. Others required reading between the lines to understand intended behavior. AI was invaluable in helping me understand the specifications and identify edge cases.

The Core specification is excellent—detailed, with diagrams and examples. The Displacement extension felt more like a reference than a guide.

This taught me to validate assumptions through experimentation. When the spec was ambiguous, I implemented what made logical sense, then tested against real-world files.

### Surprise 2: Edge Cases Are Everywhere

Every assumption I made had an edge case:

- "Meshes are always oriented consistently" → Nope, some files have mixed winding orders
- "Materials always have names" → Nope, names are optional
- "Build items don't overlap" → Nope, multiple items can occupy same space
- "Units are always specified" → Nope, defaults exist but aren't always applied correctly

The path from "works on test files" to "works on real-world files" was longer than expected.

### Surprise 3: Memory Safety Catches Real Bugs

I expected Rust's borrow checker to prevent theoretical problems. What surprised me was how often it caught actual bugs during development:
```rust
// This won't compile - borrow checker catches the issue:
let mesh = model.object_mut(0)?;
let triangle = mesh.triangle(0)?; // Immutable borrow
mesh.add_triangle(v0, v1, v2)?;   // ❌ Can't mutate while borrowed
```

In C++, this would compile and might work... until the `triangle` reference became invalid after vector reallocation. Rust prevented the bug at compile time.

The safety wasn't theoretical—it was practical and immediate.

### Surprise 4: The CLI Became the Showcase

I built the CLI as an afterthought: "Let's make the library accessible to non-developers."

It became the most visible part of the project. People who would never write Rust code could immediately:
- Validate their 3MF files
- Extract thumbnails
- Understand why slicers rejected files
- Compare model versions

The CLI democratized access to functionality that previously required writing code.

### Surprise 5: Documentation is Never Done

I wrote comprehensive docs: API documentation, architecture guides, examples, feature matrices.

People still had questions. Good questions. Questions that revealed assumptions I didn't document:

- "Does it support encrypted 3MF files?" (Yes, with crypto feature)
- "Can I use this in WASM?" (Yes, but needs async support)
- "What about really large files?" (Streaming mode handles them)

Documentation is continuous. Each question improves clarity. If you find something unclear in the documentation, please open a [GitHub issue](https://github.com/sscargal/lib3mf-rs/issues) or submit a PR to improve it.

## Lessons Learned

### Lesson 1: Read Specifications First

Spending two weeks reading before coding felt slow. It saved months of rewrites.

Understanding the full landscape before designing architecture meant I built the right abstractions. If I'd started coding after just reading Core, I would have built interfaces that didn't generalize to Materials, Production, or Secure Content.

**Takeaway**: For complex domains, invest in understanding before building.

### Lesson 2: Feature Flags Are Powerful

Making cryptography optional via feature flags meant:
- Faster compile times for most users
- Smaller dependency trees
- Easier debugging
- Clearer separation of concerns

But it added complexity: Testing every feature combination, maintaining compatibility, documenting what's available when.

**Takeaway**: Feature flags are worth the complexity for libraries with diverse use cases.

### Lesson 3: Traits Enable Composition

Rust's trait system enabled elegant designs:
```rust
// Any archive reader that implements this trait works:
pub trait ArchiveReader {
    fn read_entry(&mut self, path: &str) -> Result<Vec<u8>>;
    fn list_entries(&self) -> Result<Vec<String>>;
}

// ZIP implementation:
impl ArchiveReader for ZipReader { /* ... */ }

// Testing implementation (in-memory):
impl ArchiveReader for MockArchive { /* ... */ }

// Future: Could add .tar.gz support without changing core
impl ArchiveReader for TarGzReader { /* ... */ }
```

Traits enabled testability, extensibility, and clear contracts.

**Takeaway**: Design with traits from the start, even if you only have one implementation initially.

### Lesson 4: Examples Are Documentation

The best documentation was working examples:

- [`create_cube.rs`](https://github.com/sscargal/lib3mf-rs/blob/main/lib3mf-core/examples/create_cube.rs) - Creating models programmatically
- [`read_model.rs`](https://github.com/sscargal/lib3mf-rs/blob/main/lib3mf-core/examples/read_model.rs) - Parsing and inspecting models
- [`validate.rs`](https://github.com/sscargal/lib3mf-rs/blob/main/lib3mf-core/examples/validate.rs) - Validation workflows

People learn by doing. Runnable examples beat prose explanations.

**Takeaway**: Write examples that demonstrate real use cases, not toy problems.

### Lesson 5: Open Source Is About People

Publishing to crates.io was exciting. But the real reward was people using it:

- Issues filed with thoughtful bug reports
- Questions that showed people understood the library
- Feedback on API ergonomics
- Interest from unexpected domains (not just 3D printing)

Open source isn't just about code—it's about enabling others to build things you never imagined.

**Takeaway**: Optimize for user empowerment, not just technical excellence.

## What This Journey Meant

I started wanting to understand 3MF deeply. I achieved that—but gained more:

**Technical Growth:**
- Deep Rust expertise (trait systems, zero-cost abstractions, memory model)
- Systems programming skills (file parsing, memory management, performance optimization)
- Specification interpretation (reading standards documents, validating implementations)

**Domain Knowledge:**
- 3MF format internals
- Additive manufacturing workflows
- Digital signatures and cryptography in manufacturing

**Perspective:**
- Building comprehensive solutions takes time
- Documentation multiplies impact
- Accessibility matters more than cleverness

From curiosity to contribution. From user to architect.

## An Invitation to Contribute

lib3mf-rs is open source: [github.com/sscargal/lib3mf-rs](https://github.com/sscargal/lib3mf-rs)

Areas where contributions would be valuable:

**Testing & Validation:**
- Test against diverse real-world 3MF files
- Report edge cases and corner cases
- Add fuzzing corpus examples

**Documentation:**
- Improve API documentation clarity
- Write tutorials for specific use cases
- Create video walkthroughs

**Examples:**
- Format converters (STL, OBJ, PLY to 3MF)
- 3MF model generators for specific domains
- Integration examples (CI/CD, automation)

**Performance:**
- Benchmark against real workloads
- Profile and optimize hot paths
- Parallel processing improvements

**Features:**
- Language bindings (Python, JavaScript, others)
- WASM optimization
- Additional CLI commands

Whether you're a Rust expert or just curious about 3MF, there's room to contribute.

## Try It Today

**Install the CLI:**
```bash
cargo install lib3mf-cli
```

**Use the library:**
```toml
[dependencies]
lib3mf-core = "0.1"
```

**Read the docs:**
- [Documentation site](https://sscargal.github.io/lib3mf-rs)
- [GitHub repository](https://github.com/sscargal/lib3mf-rs)
- [Crates.io: lib3mf-core](https://crates.io/crates/lib3mf-core)
- [Crates.io: lib3mf-cli](https://crates.io/crates/lib3mf-cli)

## Final Thoughts

Building lib3mf-rs taught me that deep understanding comes from building, not just reading. The specifications made sense intellectually, but implementing them revealed subtle complexities documentation couldn't capture.

The 3D printing ecosystem needs tools that are:
- Memory safe (files from untrusted sources shouldn't crash software)
- Comprehensive (modern workflows use the full specification)
- Accessible (not everyone is a developer)
- Open (manufacturing benefits from open standards and tools)

lib3mf-rs is a step toward that vision.

If you work with 3MF files—whether you're a hobbyist, professional, or developer—I hope this library serves you well. If you find bugs, have questions, or want to contribute, the door is open.

Thank you for following this journey.
