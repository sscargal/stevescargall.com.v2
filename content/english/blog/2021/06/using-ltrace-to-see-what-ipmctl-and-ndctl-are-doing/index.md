---
title: "Using ltrace to see what ipmctl and ndctl are doing"
date: "2021-06-23"
categories: 
  - "how-to"
  - "linux"
  - "performance"
  - "troubleshooting"
tags: 
  - "ipmctl"
  - "ndctl"
---

Occasionally, it is necessary to debug commands that are slow. Or you may simply be interested in learning how the tools work. While there are many strategies, here are some simple methods that show code flow and timing information.

To show a high-level view of where the time is being spent within libipmctl, use:

```bash
# ltrace -c -o ltrace_library_count.out -l '*ipmctl*' ipmctl show -memoryresources
```

To show a high-level view of where the time is being spent within libndctl, use:

```bash
# ltrace -c -o ltrace_library_count.out -l '*ndctl*' ipmctl show -memoryresources
```

To show a high-level view of where the time is being spent within libipmctl and libipmctl, use:

```bash
# ltrace -c -o ltrace_library_count.out -l '*ipmctl*' -l '*ndctl*' ipmctl show -memoryresources
```

To trace all libipmctl and libndctl functions, use:

```bash
ltrace -l '*ndctl*' -l '*ipmctl*' ipmctl version
```

To include the time spent within each function, use:

```bash
ltrace -T -l '*ndctl*' -l '*ipmctl*' ipmctl version
```

Flame graphs can be very useful. See [http://www.brendangregg.com/flamegraphs.html](http://www.brendangregg.com/flamegraphs.html).
