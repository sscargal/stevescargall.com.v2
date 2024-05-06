+++
# Post Title - Auto-generated from the file name
title = "Programming Persistent Memory: A Comprehensive Guide for Developers"

# Post creation date
date = 2023-01-25T19:54:35Z

# Post is a Draft = True|False
draft = false

# Authors. Comma separated list, e.g. `["Bob Smith", "David Jones"]`.
authors = ["Steve Scargall"]

# Tags and categories
# For example, use `tags = []` for no tags, or the form `tags = ["A Tag", "Another Tag"]` for one or more tags.
tags = ["Persistent Memory","PMem"]
categories = ["Books"]

# Featured Image
image = 'programming_persistent_memory_book_cover.png'
+++


## Description

This is a comprehensive guide to persistent memory programming, is targeted towards experienced programmers. You will understand how persistent memory brings together several new software/hardware requirements, and offers great promise for better performance and faster application startup times—a huge leap forward in byte-addressable capacity compared with current DRAM offerings.

This revolutionary new technology gives applications significant performance and capacity improvements over existing technologies. It requires a new way of thinking and development, which makes this highly disruptive to the IT/computing industry. The full spectrum of industry sectors that will benefit from this technology include, but are not limited to, in-memory and traditional databases, AI, analytics, HPC, virtualization, and big data.

Programming Persistent Memory describes the technology and why it is exciting in the industry. It covers the operating system and hardware requirements as well as how to create development environments using emulated or real persistent memory hardware. The book explains fundamental concepts, provides an introduction to persistent memory programming APIs for C, C++, Javascript, and other languages, discusses RMDA with persistent memory, reviews security features, and presents many examples. Source code and examples that you can run on your own systems are included.

## Table of Contents

**Chapter 1.** Introduction to Persistent Memory - Introduces persistent memory and dips our toes in the water with a simple persistent key-value store example using libpmemkv.

**Chapter 2.** Persistent Memory Architecture - Describes the persistent memory architecture and focuses on the hardware requirements developers should know.

**Chapter 3.** Operating System Support for Persistent Memory - Provides information relating to operating system changes and features and how persistent memory is seen by the OS.

**Chapter 4.** Fundamental Concepts of Persistent Memory Programming - Builds on the first three chapters and describes the fundamental concepts of persistent memory programming.

**Chapter 5.** Introducing the Persistent Memory Development Kit (PMDK) - Introduces the Persistent Memory Development Kit (PMDK), a suite of libraries to assist software developers.

**Chapter 6.** libpmem: Low-Level Persistent Memory Support - Describes and shows how to use libpmem from the PMDK, a low-level library providing persistent memory support.

**Chapter 7.** libpmemobj: A Native Transactional Object Store - Provides information and examples using libpmemobj, a C native object store library from the PMDK.

**Chapter 8.** libpmemobj++: The Adaptable Language - C++ and Persistent memory - Shows the C++ libpmemobj++ store from the PMDK, similar to libpmemobj.

**Chapter 9.** pmemkv: A Persistent In-Memory Key-Value Store - Expands upon the introduction to libpmemkv from Chapter 1 with a more in-depth discussion using examples.

**Chapter 10.** Volatile Use of Persistent Memory - Is for those who want to take advantage of persistent memory, but do not require data to be stored persistently. libmemkind is a user-extensible heap manager built on top of jemalloc which enables control of memory characteristics and partitioning of the heap between kinds of memory, including persistent memory. libvmemcache is an embeddable and lightweight in-memory caching solution. It's designed to fully take advantage of large-capacity memory, such as Persistent Memory with DAX, through memory mapping in an efficient and scalable way.

**Chapter 11.** Designing Data Structures for Persistent Memory - Provides a wealth of information for designing data structures for persistent memory.

**Chapter 12.** Debugging Persistent Memory Applications - Introduces tools and walks through several examples of how software developers can debug persistent memory enabled applications.

**Chapter 13.** Enabling Persistence in a Real World Application - Discusses how a real world application was modified to enable persistent memory features.

**Chapter 14.** Concurrency and Persistent Memory - Describes how concurrency in applications should be implemented for use with persistent memory.

**Chapter 15.** Profiling and Performance - Teaches performance concepts and demonstrates how to use the Intel® VTune suite of tools to profile systems and applications before and after code changes are made.

**Chapter 16.** PMDK Internals: Algorithms and Data Structures Underpinning PMDK - Takes us on a deep dive through some of the PMDK internals.

**Chapter 17.** Reliability, Availability, and Serviceability (RAS) - Describes the implementation of Reliability, Availability, and Serviceability (RAS) with the hardware and operating system layers.

**hapter 18.** Remote Persistent Memory - Discusses how applications can scale-out across multiple systems using local and remote persistent memory.

**Chapter 19.** Advanced Topics - Describes things such as NUMA considerations, using volume managers, and more on CPU machine instructions.

## Translations

The book has been translated into Simplified Chinese and Korean.

## Buy or Download

You can buy a printed copy in English from Amazon, or Chinese from jd.com, or download a free copy in PDF or ePUB formats using these buttons:

{{< button label="Download PDF [Free]" link="https://link.springer.com/content/pdf/10.1007/978-1-4842-4932-1.pdf" rel="nofollow noreferrer" >}}
{{< button label="Download ePUB [Free]" link="https://link.springer.com/download/epub/10.1007/978-1-4842-4932-1.epub" rel="nofollow noreferrer" >}}
{{< button label="Buy on Amazon.com [$]" link="https://amzn.to/2V7FqRz" rel="nofollow noreferrer" >}}
{{< button label="Buy Chinese Version [¥]" link="https://item.m.jd.com/product/13201774.html#summary" rel="nofollow noreferrer" >}}
