---
title: "How to Confirm Virtual to Physical Memory Mappings for PMem and FSDAX Files"
meta_title: "Linux: Confirm Persistent Memory (PMem) Virtual to Physical Mappings"
description: "Learn how to verify, at the page level, whether your files are physically mapped to Persistent Memory (PMem) or DRAM on Linux. This guide includes both Python and C scripts to test and visualize memory mappings on DAX/FSDAX and non-DAX storage."
date: 2025-07-19T00:00:00-06:00
image: "featured_image.webp"
categories: ["Linux", "Persistent Memory"]
author: "Steve Scargall"
tags: ["Persistent Memory", "PMem", "DAX", "FSDAX", "Linux", "Python", "C", "mmap", "pagemap", "Virtual Memory", "Physical Memory", "Sysadmin", "Performance Tuning"]
draft: false
aliases:
---

Are you curious whether your application’s memory-mapped files are really using Intel Optane Persistent Memory (PMem), Compute Express Link (CXL) Non-Volatile Memory Modules (NV-CMM), or another DAX-enabled persistent memory device? Want to understand how virtual memory maps onto physical, non-volatile regions? Let's use easily adaptable scripts in both Python and C to confirm this on your Linux system, definitively.

## Why Does This Matter?

With the advent of **persistent memory and DAX (Direct Access) filesystems**, applications can memory-map files directly onto PMem, bypassing the traditional DRAM page cache. This promises significant performance and durability improvements for data-intensive workloads and databases, such as SQLite, Redis, and others.

But how can you *prove* that a process is actually using PMem and not just DRAM? Enter `/proc/self/pagemap`, a kernel interface that lets you see how your virtual memory is mapped to physical memory at the page level.

## The Python Test Script

This Python script:

- **Creates/opens a file** on your PMem/DAX filesystem.
- **Initializes the file** with a known pattern.
- **Memory-maps** the file (`mmap`) and touches each page to ensure it's resident in memory.
- **Uses `/proc/self/pagemap`** to fetch the physical address backing each virtual memory page.
- **Reads `/proc/iomem`** to find all persistent memory regions.
- **Prints a mapping table**, showing for each page the virtual and physical addresses, and whether it resides on persistent memory.

## Python Script

```python
#!/usr/bin/env python3
import mmap
import os
import struct
import sys
import re

FILENAME = "/mnt/pmem/testfile"
FILESZ = 4096 * 16  # 16 pages, 4 KiB per page
PAGESZ = 4096

def get_pmem_ranges():
    pmem = []
    with open('/proc/iomem', 'r') as f:
        for line in f:
            if re.search(r"Persistent Memory", line):
                m = re.match(r'\s*([0-9a-f]+)-([0-9a-f]+)', line)
                if m:
                    start = int(m.group(1), 16)
                    end = int(m.group(2), 16)
                    if not any(r[0]==start and r[1]==end for r in pmem):
                        pmem.append((start, end))
    return pmem

def virt2phys(vaddr):
    pagemap_entry_offset = (vaddr // PAGESZ) * 8
    with open("/proc/self/pagemap", "rb") as f:
        f.seek(pagemap_entry_offset)
        entry = f.read(8)
        if len(entry) != 8:
            return None
        val = struct.unpack("Q", entry)[0]
        present = (val >> 63) & 1
        pfn = val & ((1 << 55) - 1)
        if present and pfn != 0:
            return pfn * PAGESZ
        else:
            return None

def phys_in_pmem(phys, pmem_ranges):
    for lo, hi in pmem_ranges:
        if lo <= phys <= hi:
            return True
    return False

def main():
    if not os.path.exists(FILENAME) or os.path.getsize(FILENAME) < FILESZ:
        with open(FILENAME, "wb") as f:
            f.truncate(FILESZ)
            for off in range(0, FILESZ, PAGESZ):
                f.seek(off)
                f.write(struct.pack("<I", off // PAGESZ) * (PAGESZ // 4))
        print(f"File {FILENAME} created and initialized.")

    pmem_ranges = get_pmem_ranges()
    print(f"PMEM ranges: {[f'0x{x[0]:x}-0x{x[1]:x}' for x in pmem_ranges]}")

    with open(FILENAME, "r+b") as f:
        mm = mmap.mmap(f.fileno(), FILESZ, access=mmap.ACCESS_WRITE)
        print(f"Touching each page to force mapping...")
        # Find our testfile mapping from /proc/self/maps
        mapstart, mapend = None, None
        with open("/proc/self/maps") as fd_selfmaps:
            for l in fd_selfmaps:
                if FILENAME in l:
                    tokens = l.split()
                    addrrange = tokens[0].split('-')
                    mapstart, mapend = int(addrrange[0], 16), int(addrrange[1], 16)
                    break
        if mapstart is None:
            print("[Error] Could not find mapping of testfile in /proc/self/maps")
            sys.exit(1)
        print(f"\nPAGE\t[virtual addr]\tphysical addr\t(PMEM?)")
        for i in range(0, FILESZ, PAGESZ):
            mm[i]  # Touch page
            vaddr = mapstart + i
            phys = virt2phys(vaddr)
            isinpmem = phys_in_pmem(phys, pmem_ranges) if phys is not None else False
            print(f"{i//PAGESZ:02d}\t0x{vaddr:x}\t{('0x%x'%(phys) if phys else '--')}\t{'(PMEM)' if isinpmem else ''}")
        mm.close()

if __name__ == "__main__":
    if os.geteuid() != 0:
        print("Run as root for pagemap access")
        sys.exit(1)
    main()
```

## The C Version

Want real, low-level control? Here’s a minimal C program with exactly the same logic:

- Creates/fills a file
- Memory-maps it
- Touches each page
- Reads `/proc/self/pagemap` to find the physical address
- Shows if that address is within a PMem region

## C Script

```c
// pmem_testcase.c
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>
#include <string.h>
#include <errno.h>

#define FILENAME "/mnt/pmem/testfile"
#define FILESZ (4096 * 16)
#define PAGESZ 4096

typedef struct { uint64_t start, end; } pmem_range_t;

int get_pmem_ranges(pmem_range_t* pmem, int max) {
    FILE *f = fopen("/proc/iomem", "r");
    char line[256];
    int n = 0;
    while (fgets(line, sizeof(line), f)) {
        if (strstr(line, "Persistent Memory")) {
            unsigned long long s, e;
            if (sscanf(line, " %llx-%llx", &s, &e) == 2) {
                if (n == 0 || (pmem[n-1].start != s || pmem[n-1].end != e))
                    pmem[n].start = s, pmem[n++].end = e;
                if (n >= max) break;
            }
        }
    }
    fclose(f);
    return n;
}

uint64_t virt2phys(uint64_t vaddr) {
    uint64_t value = 0;
    off_t offset = (vaddr / PAGESZ) * 8;
    FILE *pf = fopen("/proc/self/pagemap", "rb");
    if (!pf) return 0;
    if (fseeko(pf, offset, SEEK_SET) != 0) { fclose(pf); return 0; }
    if (fread(&value, 8, 1, pf) != 1)   { fclose(pf); return 0; }
    fclose(pf);
    if (!(value & (1ULL<<63))) return 0;
    uint64_t pfn = value & ((1ULL<<55)-1);
    return pfn ? (pfn * PAGESZ) : 0;
}

int phys_in_pmem(uint64_t phys, pmem_range_t* pmem, int n) {
    for (int i = 0; i < n; ++i)
        if (phys >= pmem[i].start && phys <= pmem[i].end) return 1;
    return 0;
}

int main() {
    int fd = open(FILENAME, O_RDWR | O_CREAT, 0666);
    if (fd < 0) { perror("open"); return 1; }
    if (ftruncate(fd, FILESZ) != 0) { perror("ftruncate"); close(fd); return 1; }

    // Initialize file with a pattern
    uint8_t buf[PAGESZ];
    for (int i = 0; i < 16; ++i) {
        memset(buf, i, PAGESZ);
        if (write(fd, buf, PAGESZ) != PAGESZ) { perror("write"); close(fd); return 1; }
    }
    lseek(fd, 0, SEEK_SET);

    void *addr = mmap(NULL, FILESZ, PROT_READ|PROT_WRITE, MAP_SHARED, fd, 0);
    if (addr == MAP_FAILED) { perror("mmap"); close(fd); return 1; }

    pmem_range_t pmem[16];
    int n_pmem = get_pmem_ranges(pmem, 16);
    printf("PMEM ranges:\n");
    for (int i=0; i<n_pmem; ++i)
        printf("  0x%lx-0x%lx\n", pmem[i].start, pmem[i].end);

    printf("Touching pages and checking mappings...\n\n");
    printf("%-4s %-16s %-16s %s\n", "PAGE", "[virtual addr]", "[physical addr]", "PMEM?");
    for (int i = 0; i < FILESZ/PAGESZ; ++i) {
        uint64_t vaddr = (uint64_t)addr + (i*PAGESZ);
        volatile uint8_t b = *((volatile uint8_t*) (vaddr)); // Force touch
        (void)b;
        uint64_t paddr = virt2phys(vaddr);
        printf("%02d   0x%012lx   ", i, vaddr);
        if (paddr)
            printf("0x%012lx   %s\n", paddr, phys_in_pmem(paddr, pmem, n_pmem) ? "(PMEM)" : "");
        else
            printf("--\n");
    }
    munmap(addr, FILESZ);
    close(fd);
    return 0;
}
```

## How to Build and Run the C Version

```bash
gcc -O2 -o pmem_testcase pmem_testcase.c
sudo ./pmem_testcase
```

## Example Output

```text
PMEM ranges:
  0x2050000000-0x284fffffff
Touching pages and checking mappings...

PAGE [virtual addr]   [physical addr]  PMEM?
00   0x7feed5b0e000   0x21dab2a000     (PMEM)
01   0x7feed5b0f000   0x21dab2b000     (PMEM)
...
15   0x7feed5b1d000   0x21dab39000     (PMEM)
```

## What This Confirms

- Your file is actively mapped into your process address space.
- When you touch each page, Linux assigns a physical page from the DAX region to the corresponding real PMem.
- `/proc/self/pagemap` reveals the correspondence, allowing you to prove that your application is truly using persistent memory.

## What Happens with a Regular NVMe or Non-PMem Filesystem?

To understand the difference, let’s repeat our test using a file on the root NVMe drive (`/testfile`) instead of the pmem DAX filesystem.

## Example Output (Non-PMem Filesystem on NVMe)

```text
$ sudo ./testpmem.py 
File /testfile created and initialized.
PMEM ranges: ['0x2050000000-0x284fffffff']
Touching each page to force mapping...
  (Python does not expose the actual VMA for mmap regions; recommend using C for true VMA)

PAGE [virtual addr] physical addr (PMEM?)
00 0x7523397a6000 0x542dc3000
01 0x7523397a7000 0x35e52e000
02 0x7523397a8000 0x35e52f000
03 0x7523397a9000 0x2dfa86000
04 0x7523397aa000 0x2dfa87000
05 0x7523397ab000 0x2c77a4000
...
14 0x7523397b4000 0x2d042d000
15 0x7523397b5000 0x276596000
```

Notice a key difference: **None of the physical addresses are marked `(PMEM)`**.

## What Does This Tell Us?

- The script still creates, fills, and touches each page of the mapped file, and reports real virtual→physical mappings.
- However, none of the physical page addresses fall within your system’s DAX/PMem region (`0x2050000000-0x284fffffff` in this example).
- This is because the file is located on a regular NVMe drive, managed by the traditional block device subsystem, not DAX/PMem.
- As a result, the memory mapping is backed by DRAM, handled by the kernel’s page cache. The actual file contents physically reside on the SSD, but what you see in `/proc/self/pagemap` are physical frames in DRAM, not persistent memory.

## Why is This Important?

When benchmarking or deploying databases, you want strong, low-level proof that your memory-mapped data is using true persistent memory - and not just ordinary (volatile) DRAM! This test provides that confirmation.

## Summary: What To Expect

- **On a PMem + DAX/FSDAX mount**:
   Physical addresses show up in the known PMem range, and you’ll see the `(PMEM)` tag.
- **On a regular NVMe or xfs/ext4 drive**:
   Physical addresses are *not* in the PMem range—pages are backed by DRAM, via the traditional page cache.

This comparison ensures that you truly understand where your data resides and can confidently determine whether your application is utilizing persistent memory as intended.

This experiment helps you verify (with real, low-level evidence) that your optimized code and fast storage truly do what you designed. Happy building!

## Final Thoughts

This is a powerful tool for systems programmers, database architects, and performance engineers who want to *prove* their application is genuinely running on persistent memory and not just using DRAM cache. Whether you’re experimenting in Python or C, this approach gives you low-level confidence in your DAX/PMem setup.

You can adapt these techniques to watch any application’s memory mappings - just change the mapping and page access logic to suit your needs.
