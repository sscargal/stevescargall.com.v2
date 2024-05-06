---
title: "How To Build a custom Linux Kernel to test Data Access Monitor (DAMON)"
date: "2021-12-23"
categories: 
  - "how-to"
  - "linux"
tags: 
  - "active-memory"
  - "working-set-size"
  - "wss"
image: "images/pexels-photo-577585.jpeg"
author: Steve Scargall
---

[DAMON](https://sjp38.github.io/post/damon) is a data access monitoring framework subsystem for the Linux kernel. DAMON (Data Access MONitor) tool monitors memory access patterns specific to user-space processes introduced in Linux kernel 5.15 LTS, such as operation schemes, physical memory monitoring, and proactive memory reclamation. It was designed and implemented by Amazon AWS Labs and [upstreamed into the 5.15 Kernel](https://www.phoronix.com/scan.php?page=news_item&px=DAMON-For-Linux-5.15), but it was not enabled by default.cd /boot

Keen to try this new feature to identify the working set size (Active Memory) of a server or process, this post documents the steps I took to build a custom Kernel with DAMON enabled using Fedora Server 35.

To use this feature, you should first ensure your system is running on a kernel that is built with CONFIG\_DAMON\_RECLAIM=y. To check if your kernel was built with the DAMON feature, run the following:

```
$ grep CONFIG_DAMON /boot/config-$(uname -r)
```

If you see one or more entries, congratulations, your Kernel **does** have the feature and you do not need to continue following this post.  
If no output is returned, your Kernel **does not** have the feature, and you should continue reading.

At the time of writing - 23rd December 2021 - neither the latest stable Fedora Kernel (5.15.10-200.fc35.x86\_64) nor the Linus Torvalds mainline Kernel (5.16.0-0.rc6.20211222git2f47a9a4dfa3.43.vanilla.1.fc35.x86\_64) had the feature enabled. So I needed to build a custom Kernel. If you've never built a Kernel, the process isn't as daunting as one might imagine or used to be. I simply followed some of the instructions on [https://fedoraproject.org/wiki/Building\_a\_custom\_kernel](https://fedoraproject.org/wiki/Building_a_custom_kernel) and [https://sjp38.github.io/post/damon/#install](https://sjp38.github.io/post/damon/#install).

Install the dependencies for building Kernels

```
sudo dnf install fedpkg fedora-packager rpmdevtools ncurses-devel pesign grubby
```

Create a build directory

```
mkdir ~/downloads
cd ~/downloads
```

Clone the Linus Torvalds kernel main branch from kernel.org. This is the bleeding edge release. This will clone the entire upstream tree and may take a while depending on your Internet connection speed.

```
git clone git://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git
- or -
git clone https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git

cd linux
```

If you prefer a stable Kernel release, use:

```
git clone git://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git
- or -
git clone https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git

cd linux
```

Create a Kernel configuration file `.config` in the current directory

```
make oldconfig
```

Add the following DAMON entries to the `.config` file. Open the file for editing and locate the DAMON section which should look something like this:

```
#
# Data Access Monitoring
#
# CONFIG_DAMON is not set
# end of Data Access Monitoring
# end of Memory Management options
```

Add the following entries so your .config file now looks like this:

```
#
# Data Access Monitoring
#
CONFIG_DAMON=y
CONFIG_DAMON_KUNIT_TEST=y
CONFIG_DAMON_VADDR=y
CONFIG_DAMON_PADDR=y
CONFIG_DAMON_PGIDLE=y
CONFIG_DAMON_VADDR_KUNIT_TEST=y
CONFIG_DAMON_DBGFS=y
CONFIG_DAMON_DBGFS_KUNIT_TEST=y
CONFIG_DAMON_RECLAIM=y
# end of Data Access Monitoring
# end of Memory Management options
```

Start the building process using all available CPUs

```
make -j$(nproc)
make bzImage
make modules
```

Assuming no errors were reported during the build phase, install the new Kernel

```
sudo make modules_install
sudo make install
```

Reboot the host. The kernel is unlikely to be the default option in GRUB, so make sure to select the new Kernel when prompted.

Copy the config file to /boot for future reference

```
cp ~/downloads/linux/.config /boot/config-$(uname -r)
```

Once you have tested the Kernel, you may choose to remove the source code to free space on your storage.

```
rm -rf ~/downloads/linux
```

To let sysadmins enable or disable it and tune for the given system, **DAMON**\_RECLAIM utilizes module parameters. That is, you can put `**damon**_reclaim.<parameter>=<value>` on the kernel boot command line or write proper values to `/sys/modules/damon_reclaim/parameters/<parameter>` files.

```
# ls /sys/module/damon_reclaim/parameters/
aggr_interval  max_nr_regions  monitor_region_end    quota_reset_interval_ms  wmarks_high      wmarks_mid
enabled        min_age         monitor_region_start  quota_sz                 wmarks_interval
kdamond_pid    min_nr_regions  quota_ms              sample_interval          wmarks_low
```

A description of each parameter can be found in the [documentation](https://www.kernel.org/doc/html/latest/admin-guide/mm/damon/reclaim.html).

## DAMO - A User-Space Tool

A user-space tool for DAMON, called [DAMO](https://github.com/awslabs/damo) is available. It’s also available at [PyPi](https://pypi.org/project/damo/). You may start using DAMON by following the [Getting Started](https://github.com/awslabs/damo#getting-started) of the tool for start.

To use the latest development release from GitHub, clone the repository:

```
mkdir ~/downloads
cd ~/downloads
git clone https://github.com/awslabs/damo
cd damo
```

Getting help:

```
# ./damo version
1.0.9

# ./damo -h
usage: damo [-h] <command> ...

options:
  -h, --help  show this help message and exit

command:
    record    record data accesses
    schemes   apply operation schemes
    report    report the recorded data accesses in the specified form
    monitor   repeat the recording and the reporting of data accesses
    adjust    adjust the record results with different monitoring attributes
    reclaim   control DAMON_RECLAIM
    features  list supported DAMON features in the kernel
    validate  validate a given record result file
    version   print the version number

# ./damo features
init_regions: Supported
paddr: Supported
record: Unsupported
schemes: Supported
schemes_prioritization: Supported
schemes_quotas: Supported
schemes_speed_limit: Supported
schemes_wmarks: Supported

# ./damo report -h
usage: damo report [-h] <report type> ...

options:
  -h, --help     show this help message and exit

report type:
  <report type>  the type of the report to generate
    raw          human readable raw data
    heats        heats of regions
    wss          working set size
    nr_regions   number of regions


```

## Summary

In this post, I showed how to build a custom Linux Kernel with the DAMON feature enabled.

## References

- [DAMON Project Home Page](https://sjp38.github.io/post/damon/)
- [DAMON: Data Access MONitor](https://www.kernel.org/doc/html/latest/vm/damon/index.html) \[Kernel Docs\]
- [DAMON FAQ](https://www.kernel.org/doc/html/latest/vm/damon/faq.html) \[Kernel Docs\]
- [Amazon's DAMON Landing For Linux 5.15](https://www.phoronix.com/scan.php?page=news_item&px=DAMON-For-Linux-5.15) \[Phoronix\]
- [DAMON Source Code](https://github.com/torvalds/linux/tree/master/mm/damon)
- [Presentation on DAMON](https://linuxplumbersconf.org/event/11/contributions/984/attachments/870/1670/daos_ksummit_2021.pdf)
    - [Demo Code](https://git.kernel.org/pub/scm/linux/kernel/git/sj/linux.git/tree/for_damon_hack/ksummit_2021_demo?h=damon/for_ksummit_2021)
- [DAMO: A userspace tool/command](https://github.com/awslabs/damo)
