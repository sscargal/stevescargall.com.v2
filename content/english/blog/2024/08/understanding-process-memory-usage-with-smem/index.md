---
title: "Understanding Memory Usage with `smem`"
meta_title: "Analyzing Linux Memory Usage with smem: Deep Dive into RSS, USS, and More"
description: "Discover how to use the smem Linux utility to analyze process memory usage in detail, focusing on key metrics like Resident Set Size (RSS) and Unique Set Size (USS). Learn advanced tips, comparisons to top and htop, and practical examples for optimizing your system's memory performance."
date: 2024-08-20T00:00:00Z
image: "featured_image.webp"
categories: ["How To", "Linux"]
author: "Steve Scargall"
tags: ["Performance", "Memory Management"]
draft: false
aliases:
---

Memory management is crucial for Linux administrators and developers, especially when optimizing performance for resource-intensive applications. While tools like `top` and `htop` are commonly used to monitor system performance, they often don't provide enough detail regarding memory usage breakdown. This is where `smem` comes into play.

### What is `smem`?

`smem` is a command-line tool that reports memory usage per process and provides better insight into shared memory than most traditional tools, taking shared memory pages into account. Unlike `top` or `htop`, which primarily display RSS (Resident Set Size), `smem` can also show USS (Unique Set Size), which is a better metric for understanding how much memory would be freed if a particular process were terminated. This blog will guide you through using `smem`, explaining these critical memory metrics and providing comparisons to more familiar tools.

### Understanding Memory Metrics: RSS vs. USS

Before diving into `smem` usage, it's important to understand two key memory metrics:

- **Resident Set Size (RSS):** RSS represents the portion of a process's memory that is held in RAM. This includes memory shared with other processes (e.g., shared libraries). Tools like `top` or `htop` display RSS, which gives a general sense of how much memory a process is using, but it doesn't differentiate between shared and exclusive memory.
- **Unique Set Size (USS):** USS measures the amount of memory that is used exclusively by a process, without considering shared memory. This is important because USS indicates how much memory would actually be released if the process were terminated. It provides a more accurate reflection of a process's individual memory footprint.
- **Proportional Set Size(PSS):** The unshared memory (USS) plus a process's proportion of shared memory is reported as the PSS (Proportional Set Size).  The USS and PSS only include physical memory usage.  They do not include memory that has been swapped out to disk.

### Installing `smem`

To install `smem` on Debian, Ubuntu, and Mint, you can use the following command:

```bash
sudo apt install smem
```

Once installed, you are ready to start analyzing memory usage.

### Basic Usage of `smem`

The simplest way to use `smem` is to run it without any options. This provides an overview of the memory usage by all processes, displaying important metrics such as PID (Process ID), User, Command, RSS, PSS (Proportional Set Size), and USS.

```bash
smem
```

Output example:
```bash
  PID User     Command                         Swap     USS      PSS      RSS
  726 root     /usr/libexec/upowerd               0   11984    13736    25312
 1432 user     /usr/libexec/tracker-miner         0   10840    12934    23764
```

In the output:
- **USS (Unique Set Size):** Shows the unique memory used by the process.
- **PSS (Proportional Set Size):** An estimate of how much memory the process is using, considering shared memory divided proportionally across processes.
- **RSS (Resident Set Size):** Shows how much memory the process has in RAM.

### Viewing USS for All Processes

You can sort the output by USS to see which processes are using the most unique memory:

```bash
smem -s uss
```

Output example:
```bash
$ smem -s uss
    PID User    Command                          Swap     USS      PSS      RSS 
   1882 user    -bash                              0     2044     2501     5304 
   1783 user    /lib/systemd/systemd --user        0     3052     4359     9644 
1575618 user    /usr/bin/python3 /usr/bin/s        0     8684     9822    14128 
```

This command will display the processes sorted by USS, allowing you to easily identify memory hogs.

### Viewing Memory Usage as Percentages

Sometimes, it's helpful to view memory usage as a percentage of total system memory. To do this, use the `-p` flag:

```bash
smem -p
```

Output example:
```bash
$ smem -p
    PID User    Command                         Swap      USS      PSS      RSS 
   1882 user    -bash                          0.00%    0.03%    0.03%    0.07% 
   1783 user    /lib/systemd/systemd --user    0.00%    0.04%    0.05%    0.12% 
1732035 user    /usr/bin/python3 /usr/bin/s    0.00%    0.11%    0.12%    0.17% 
```

This will include percentage columns for USS, PSS, and RSS, making it easier to understand how much of your system's memory is being consumed by individual processes.

### Viewing USS for a Specific Process

If you want to drill down into the memory usage of a specific process, use the `-P` flag with a process ID (PID). This allows you to view USS, PSS, and RSS for that particular process.

```bash
smem -P <PID>
```

Example:
```bash
$ smem -P 1732035
    PID User     Command                         Swap      USS      PSS      RSS 
1944111 user     /usr/bin/python3 /usr/bin/s        0     8032     9120    13328 
```

This will show detailed memory information for the process with PID 1432.

### Advanced Options

`smem` comes with several advanced options that allow further customization of the output:

- **Show Totals:** You can use the `-t` flag to show the total memory usage for all processes.
```bash
  smem -t
```

  Output example:
```bash
  $ smem -t
    PID User     Command                         Swap      USS      PSS      RSS 
   1882 user    -bash                              0     2044     2497     5304 
   1783 user    /lib/systemd/systemd --user        0     3052     4360     9644 
2025476 user    /usr/bin/python3 /usr/bin/s        0     8556     9675    13900 
-------------------------------------------------------------------------------
      3 1                                           0    13652    16532    28848 
```

- **Filter by User:** To filter memory usage by a specific user, use the `-U` option followed by the username:
```bash
  smem -U user
```

- **Graphs:** For a visual representation of memory usage, `smem` also supports pie charts and bar graphs. For instance:
```bash
  smem --pie uss
  smem --bar uss
```

  Supported options to generate the charts are:

  command  process command line
  maps     total number of mappings
  name     name of process
  pid      process ID
  pss      proportional set size (including sharing)
  rss      resident set size (ignoring sharing)
  swap     amount of swap space consumed (ignoring sharing)
  user     owner of process
  uss      unique set size
  vss      virtual set size (total virtual memory mapped)

### Comparing `smem` to Other Tools

While tools like `top`, `htop`, and `ps` provide a good overview of system performance and memory usage, they lack the ability to distinguish between shared and unique memory effectively. 

- **`top` and `htop`:** These tools display RSS but don't differentiate between memory that is shared across processes and memory that is uniquely used by a process. This makes them less precise for detailed memory analysis, especially in environments where shared libraries are prevalent.
  
- **`ps`:** The `ps` command can display RSS but, similar to `top`, lacks insight into how memory is shared or unique to processes.

### Conclusion

For Linux administrators and developers, understanding how memory is being used by individual processes is crucial, especially when optimizing applications or troubleshooting memory leaks. Tools like `smem` provide a deeper level of insight than more common utilities like `top` or `htop`. By focusing on USS, administrators can make more informed decisions about memory optimization, knowing exactly how much memory would be freed when terminating a process.

Whether you are investigating an application’s memory usage or trying to pinpoint inefficiencies in your system, `smem` gives you the detail you need to make data-driven decisions.