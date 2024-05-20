---
title: "Resolving commands 'Killed' on GCP f1-micro Compute Engine instances"
date: "2021-12-21"
categories: 
  - "linux"
image: "images/pexels-photo-207580.jpeg"
author: Steve Scargall
aliases:
  - /blog/2021/12/21/resolving-commands-killed-on-gcp-f1-micro-compute-engine-instances/
---

When I want to perform a quick task, I generally spin up a Google GCP Compute Engine instance as they're cheap. However, they have limited resources, particularly memory. When refreshing the package repositories, it's quite easy to encounter an Out-of-Memory (OOM) situation which results in the command - yum or dnf - is 'killed'. For example:

```bash
$ sudo dnf update 
CentOS Stream 8 - AppStream                                                                                                  8.3 MB/s |  18 MB     00:02    
CentOS Stream 8 - BaseOS                                                                                                      13 MB/s |  16 MB     00:01    
CentOS Stream 8 - Extras                                                                                                      69 kB/s |  16 kB     00:00    
Google Compute Engine                                                                                                         20 kB/s | 9.4 kB     00:00    
Google Cloud SDK                                                                                                              24 MB/s |  43 MB     00:01    
Killed
```

`dmesg` has a lot of information about the situation, but the key line to confirm dnf caused the OOM event, is:

```bash
[ 1156.249100] Out of memory: Killed process 1538 (dnf) total-vm:638020kB, anon-rss:290432kB, file-rss:0kB, shmem-rss:0kB, UID:0 pgtables:1244kB oom_score_adj:0
```

Many of the OS images provided by GCP and other cloud providers, often do not provide a swap device which is fine for the larger instances but may be required on the smaller memory instances.

To resolve the situation, create a swap device for the instance. The following adds 1GB which is typically enough for the dnf and yum commands.

```bash
sudo fallocate -l 1G /swapfile
sudo mkswap /swapfile
sudo chmod 0600 /swapfile
sudo swapon /swapfile
```

Note: The above is not permanent, so you'll want to add an entry to the /etc/fstab to ensure the swap device is added on each boot, eg:

```bash
/swapfile none                    swap    defaults        0 0
```
