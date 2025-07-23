---
title: "Is Your Application Really Using Persistent Memory? Here’s How to Tell."
meta_title: "How to Verify PMEM & CXL Memory Mapping on Linux with FSDAX"
description: "A practical guide on how to verify if your application's memory-mapped files are physically on Persistent Memory (PMEM) or CXL memory. Learn to use a Python script and manual /proc inspection to translate virtual to physical addresses on Linux with FSDAX."
date: 2025-07-23T17:35:00-06:00
image: "featured_image.webp"
categories: ["Linux", "Storage"]
author: "Steve Scargall"
tags: ["PMEM", "Persistent Memory", "CXL", "FSDAX", "DAX", "Linux", "Memory Mapping", "mmap", "pagemap", "procfs", "Virtual Memory", "Physical Address", "Performance Tuning"]
draft: false
---

Persistent memory (PMEM), especially when accessed via technologies like CXL, promises the best of both worlds: DRAM-like speed with the durability of an SSD. When you set up a filesystem like XFS or EXT4 in **FSDAX (File System Direct Access)** mode on a PMEM device, you're paving a superhighway for your applications, allowing them to map files directly into their address space and bypass the kernel's page cache entirely.

But here's the crucial question: after all the setup and configuration, how do you *prove* that your application's data is physically residing on the PMEM device and not just in regular RAM? I've run into this question myself, so I wrote a small Python script to get a definitive answer using SQLite3 as an example application. However, before we proceed with the script, let's examine how you can verify this manually.

## How Virtual-to-Physical Address Mapping Works

Your application doesn't see the computer's actual hardware memory. Instead, it operates in a private *virtual address space* managed by the operating system. When your code accesses a memory address, the CPU's Memory Management Unit (MMU) translates that virtual address into a *physical address*—the real location on the RAM or PMEM chip.

This mapping allows you to determine where your data truly resides. On Linux, you can perform this translation manually for any running application using files in the `/proc` filesystem.

Let's walk through an example. Imagine you have a running process with PID `12345` and you want to inspect a virtual address `0x7f265c63a000` within it. You will need root privileges to complete this task.

**1. Find the Virtual Address Range in `/proc/<PID>/maps`**

First, look at the memory map for your process to confirm what's mapped at that address.

```bash
$ sudo cat /proc/12345/maps | grep my_test_file

# Output might look like this:
7f265c63a000-7f265c64a000 rw-p 00000000 08:01 1234567 /mnt/pmem/my_test_file.db
```

This confirms that the virtual address `0x7f265c63a000` is the start of a memory region mapped to our test file.

**2. Calculate the Pagemap Offset**

The `/proc/12345/pagemap` file contains the translation data. To find the entry for our virtual address, we calculate its offset within that file. Assuming a standard page size of 4096 bytes (0x1000 in hex):

- **Formula**: `offset = (virtual_address / page_size) * 8`
- **Calculation**: `offset = (0x7f265c63a000 / 4096) * 8 = 17501331488`

**3. Read the Pagemap Entry**

Now, use a tool like `dd` to seek to that offset in the pagemap file and read the 8-byte entry.

```bash
$ sudo dd if=/proc/12345/pagemap bs=8 skip=17501331488 count=1 | xxd -g 8

# Output will be the 8-byte entry in hex:
00000000: 86000002058c0100
```

Our 8-byte pagemap entry is `0x86000002058c0100`.

**4. Extract the Page Frame Number (PFN)**

The pagemap entry is a 64-bit value with several fields. The most important for us is the Page Frame Number (PFN), which is stored in bits 0-54.

- **Pagemap Entry**: `0x86000002058c0100`
- **Bit 63 (Present)**: `1` (The page is present in physical RAM/PMEM)
- **Bits 0-54 (PFN)**: To get the PFN, we mask the entry with `0x7FFFFFFFFFFFFF`. The result is `0x2058c01`.

Our Page Frame Number is `0x2058c01`.

**5. Calculate the Physical Address**

The final step is to convert the PFN into a physical address.

- **Formula**: `physical_address = (PFN * page_size) + (virtual_address % page_size)`
- **Calculation**: `physical_address = (0x2058c01 * 4096) + (0x7f265c63a000 % 4096) = 0x2058c01000`

The physical address is `0x2058c01000`.

**6. Compare with `/proc/iomem`**

Finally, check if this physical address falls within a range marked as "Persistent Memory".

```bash
$ cat /proc/iomem | grep "Persistent Memory"

# Output might look like this:
  2050000000-284fffffff : Persistent Memory
```

Our calculated physical address `0x2058c01000` is indeed within the `0x205...` to `0x284...` range. We've manually confirmed the page is on PMEM! As you can see, this is a robust but tedious process, which is why automating it is so helpful.

## Automating the Check with a Python Script

To make this process easy, the script I developed, [sqlite_pmem_test.py](./sqlite_pmem_test.py), automates those exact steps.

1. **Find PMEM Ranges**: First, it parses `/proc/iomem` to identify the physical address ranges that the kernel has reserved for "Persistent Memory". This gives us a map of where PMEM is located in the system's physical address space.
2. **Memory-Map a File**: The script then creates a test file on the desired storage path (e.g., `/mnt/pmem/test.db`) and uses the `mmap` system call to map it into the script's own virtual address space.
3. **Force Mapping**: It "touches" each page of the mapped file to ensure the kernel establishes the virtual-to-physical mapping.
4. **Translate and Verify**: This is the magic step. For each page of the mapped file, the script reads `/proc/self/pagemap` to translate its virtual address into a physical address. It then checks if this physical address falls within the PMEM ranges discovered in the first step.

To run it, you'll need root privileges to access the `pagemap` interface.

## The Results: Seeing is Believing

The script's output makes it immediately apparent whether you're hitting PMEM or not.

### Case 1: The Wrong Path (A Standard SSD)

First, let's run the script on a file located in a user's home directory, which resides on a standard NVMe SSD. The storage is fast, but it's not PMEM and doesn't use DAX.

The data path in this scenario involves an extra step: the kernel reads the data from the SSD into its own memory buffer (the "page cache") and then copies it into your application's memory. The physical address your application sees is in regular DRAM, not on the storage device.

```text
  Application Virtual Memory
  +--------------------------+
  |      mmap'd region       |   <-- Your app sees this
  | [virt: 0x71cffef8e000]   |
  +--------------------------+
              ^
              | Data Copy
              |
  +--------------------------+
  |   Kernel Page Cache      |   <-- Physical address is here
  |     (in DRAM)            |       [phys: 0x7e26ed000]
  +--------------------------+
              ^
              | I/O Read
              |
    +--------------------+
    |   NVMe SSD         |
    +--------------------+
```

The script confirms this indirect path. The physical addresses are in a standard DRAM range, not the PMEM range.

```bash
$ sudo ./testpmem.py $HOME
PMEM ranges: ['0x2050000000-0x284fffffff']
Touching each page to force mapping...

PAGE	[virtual addr]	physical addr	is_PMEM
00	    0x71cffef8e000	0x7e26ed000	    not-pmem
01	    0x71cffef8f000	0x80f441000	    not-pmem
...
15	    0x71cffef9d000	0x6394d7000	    not-pmem
```

### Case 2: The Right Path (An FSDAX-Mounted PMEM Device)

Now, let's run the same script but point it to a path on a filesystem mounted with the `dax` option. With Direct Access, the page cache is bypassed entirely. The application's virtual memory is mapped *directly* to the physical addresses on the PMEM device.

```text
  Application Virtual Memory
  +--------------------------+
  |      mmap'd region       |   <-- Your app sees this
  | [virt: 0x7321bf623000]   |
  +--------------------------+
              |
              | Direct Mapping (No Copy)
              |
  +--------------------------+
  |   Persistent Memory      |   <-- Physical address is here
  |      (PMEM Device)       |       [phys: 0x2058c01000]
  +--------------------------+
```

The difference is night and day. Every single physical address of the memory-mapped file now falls squarely within the system's PMEM range (`0x205...` is between `0x205...` and `0x284...`). This is our proof!

```bash
$ sudo ./testpmem.py /mnt/pmem
PMEM ranges: ['0x2050000000-0x284fffffff']
Touching each page to force mapping...

PAGE	[virtual addr]	physical addr	is_PMEM
00	    0x7321bf623000	0x2058c01000	PMEM
01	    0x7321bf624000	0x2058c02000	PMEM
...
15	    0x7321bf632000	0x2052838000	PMEM
```

## Why Is This Useful?

This simple test is invaluable for a few reasons:

- **Configuration Sanity Check**: It provides undeniable proof that your storage, filesystem, and mount options are configured correctly to enable Direct Access.
- **Performance Debugging**: If a database or other application isn't delivering the performance you expect on a PMEM-enabled system, this is a great first step. If the script reports `not-pmem`, you've found a fundamental configuration flaw.
- **Application Development**: As a developer, you can use this to ensure your application's file I/O patterns are compatible with and correctly leveraging memory-mapped PMEM.

By taking a moment to verify the underlying physical mappings, you can be confident that you are fully harnessing the revolutionary speed of persistent memory.

## Appendix: Script Usage

Download the script [sqlite_pmem_test.py](./sqlite_pmem_test.py).

You can get a complete list of commands by running the script with the `-h` or `--help` flag. Note that the script must be run with `sudo` or as root to access `/proc/self/pagemap`.

### Help Output

```bash
$ ./testpmem.py --help
usage: testpmem.py [-h] [--filesz FILESZ] [--pagesz PAGESZ] [--skip-init] [--show-pmem] [path]

Test PMEM mapping and physical address translation.

positional arguments:
  path                  Directory or file path for the database file. If a directory is given, 'test.db' will be created inside it. Default: /mnt/pmem/test.db

options:
  -h, --help            show this help message and exit
  --filesz FILESZ       Size of the test file in bytes (default: 65536)
  --pagesz PAGESZ       Page size in bytes (default: 4096)
  --skip-init           Skip file initialization if file exists
  --show-pmem           Show PMEM ranges and exit
```

### Command Examples

1. Just show the system's PMEM ranges and exit:

This is useful for a quick check to see what physical address ranges are designated as persistent memory.

```bash
$ sudo ./testpmem.py --show-pmem
PMEM ranges: ['0x2050000000-0x284fffffff']
```

2. Test a specific file path:

Instead of using the default, you can provide a full path to a file you want to test.

```bash
$ sudo ./testpmem.py /var/tmp/mytestfile.db
```

3. Test a directory:

If you provide a directory, the script will create a file named test.db inside it for the test. This is the most common use case.

```bash
# Test a PMEM-mounted directory
$ sudo ./testpmem.py /mnt/pmem

# Test a standard directory on an SSD/HDD
$ sudo ./testpmem.py /home/user/test-location
```

4. Skip file creation:

If the test file already exists and you don't want the script to modify it, use --skip-init.

```bash
$ sudo ./testpmem.py --skip-init /mnt/pmem/test.db
```
