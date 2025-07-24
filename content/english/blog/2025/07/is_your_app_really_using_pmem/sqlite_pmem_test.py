#!/usr/bin/env python3
import mmap
import os
import struct
import sys
import re
import argparse

FILESZ = 4096 * 16  # 16 pages, 4 KiB per page
PAGESZ = 4096

def phys_in_pmem(phys, pmem_ranges):
    for lo, hi in pmem_ranges:
        if lo <= phys <= hi:
            return True
    return False

def get_pmem_ranges():
    pmem = []
    with open('/proc/iomem', 'r') as f:
        for line in f:
            if re.search(r"Persistent Memory", line):
                m = re.match(r' *([0-9a-f]+)-([0-9a-f]+)', line)
                if m:
                    start = int(m.group(1), 16)
                    end = int(m.group(2), 16)
                    if not any(r[0]==start and r[1]==end for r in pmem):
                        pmem.append((start, end))
    return pmem

def virt2phys(vaddr, pagesz):
    # Translate virtual address to physical using /proc/self/pagemap
    pagemap_entry_offset = (vaddr // pagesz) * 8
    with open("/proc/self/pagemap", "rb") as f:
        f.seek(pagemap_entry_offset)
        entry = f.read(8)
        if len(entry) != 8:
            return None
        val = struct.unpack("Q", entry)[0]
        present = (val >> 63) & 1
        pfn = val & ((1 << 55) - 1)
        if present and pfn != 0:
            return pfn * pagesz
        else:
            return None
def main(args):
    # Determine FILENAME from path argument
    if os.path.isdir(args.path):
        filename = os.path.join(args.path, 'test.db')
    else:
        filename = args.path
    filesz = args.filesz
    pagesz = args.pagesz

    if args.show_pmem:
        pmem_ranges = get_pmem_ranges()
        print(f"PMEM ranges: {[f'0x{x[0]:x}-0x{x[1]:x}' for x in pmem_ranges]}")
        sys.exit(0)

    if (not os.path.exists(filename) or os.path.getsize(filename) < filesz) and not args.skip_init:
        with open(filename, "wb") as f:
            f.truncate(filesz)
            for off in range(0, filesz, pagesz):
                f.seek(off)
                f.write(struct.pack("<I", off // pagesz) * (pagesz // 4))
        print(f"File {filename} created and initialized.")
    elif args.skip_init:
        print(f"Skipping file initialization for {filename}.")

    pmem_ranges = get_pmem_ranges()
    print(f"PMEM ranges: {[f'0x{x[0]:x}-0x{x[1]:x}' for x in pmem_ranges]}")

    with open(filename, "r+b") as f:
        mm = mmap.mmap(f.fileno(), filesz, access=mmap.ACCESS_WRITE)
        vbase = id(mm) # Python doesn't give the true mapping, see note below.
        print(f"Touching each page to force mapping...")
        vaddrs = []
        for i in range(0, filesz, pagesz):
            x = mm[i]  # Touch
            vaddr = mmap.mmap.mmap.__dict__['__init__'].__self__.__array_interface__['data'][0] + i if hasattr(mm, '__array_interface__') else None
            # However, Python mmap doesn't expose the real mapping address. For truly precise addresses, use C.
            vaddrs.append(None)
        # print("  (Python does not expose the actual VMA for mmap regions; recommend using C for true VMA)")
        print(f"\nPAGE\t[virtual addr]\tphysical addr\tis_PMEM")
        fd_selfmaps = open("/proc/self/maps")
        maps_lines = fd_selfmaps.readlines()
        fd_selfmaps.close()
        # Find our testfile mapping
        mapstart, mapend = None, None
        for l in maps_lines:
            if filename in l:
                tokens = l.split()
                addrrange = tokens[0].split('-')
                mapstart, mapend = int(addrrange[0], 16), int(addrrange[1], 16)
                break
        if mapstart is None:
            print("[Error] Could not find mapping of testfile in /proc/self/maps")
            sys.exit(1)
        for i in range(0, filesz, pagesz):
            vaddr = mapstart + i
            phys = virt2phys(vaddr, pagesz)
            if phys is None:
                pmem_status = '--'
            else:
                pmem_status = 'PMEM' if phys_in_pmem(phys, pmem_ranges) else 'not-pmem'
            print(f"{i//pagesz:02d}\t0x{vaddr:x}\t{('0x%x'%(phys) if phys is not None else '--')}\t{pmem_status}")
        mm.close()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Test PMEM mapping and physical address translation.")
    parser.add_argument('path', nargs='?', default='/mnt/pmem/test.db',
                        help="Directory or file path for the database file. If a directory is given, 'test.db' will be created inside it. Default: /mnt/pmem/test.db")
    parser.add_argument('--filesz', type=int, default=FILESZ, help="Size of the test file in bytes (default: 65536)")
    parser.add_argument('--pagesz', type=int, default=PAGESZ, help="Page size in bytes (default: 4096)")
    parser.add_argument('--skip-init', action='store_true', help="Skip file initialization if file exists")
    parser.add_argument('--show-pmem', action='store_true', help="Show PMEM ranges and exit")
    # Only parse args here, don't run main logic
    if '--help' in sys.argv or '-h' in sys.argv:
        parser.parse_args()
        sys.exit(0)
    args = parser.parse_args()
    if os.geteuid() != 0:
        print("Run as root for pagemap access")
        sys.exit(1)
    main(args)


