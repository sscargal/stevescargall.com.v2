---
title: "How To Set Linux CPU Scaling Governor to Max Performance"
date: "2020-02-13"
categories: 
  - "how-to"
  - "linux"
tags: 
  - "cpu"
  - "frequency"
  - "governor"
  - "performance"
  - "powersave"
image: "images/pexels-photo-257904.jpeg"
author: Steve Scargall
---

The majority of modern processors are capable of operating in a number of different clock frequency and voltage configurations, often referred to as Operating Performance Points or P-states (in ACPI terminology). As a rule, the higher the clock frequency and the higher the voltage, the more instructions can be retired by the CPU over a unit of time, but also the higher the clock frequency and the higher the voltage, the more energy is consumed over a unit of time (or the more power is drawn) by the CPU in the given P-state. Therefore there is a natural trade-off between the CPU capacity (the number of instructions that can be executed over a unit of time) and the power drawn by the CPU.

The Linux kernel supports CPU performance scaling by means of the `CPUFreq` (CPU Frequency scaling) subsystem that consists of three layers of code: the core, scaling governors and scaling drivers. For benchmarking, we usually want maximum performance and power. By default, most Linux distributions place the system into a 'powersave' mode. The definition for 'powersave' and 'performance' scaling governors are:

**performance**

When attached to a policy object, this governor causes the highest frequency, within the `scaling_max_freq` policy limit, to be requested for that policy.

The request is made once at that time the governor for the policy is set to `performance` and whenever the `scaling_max_freq` or `scaling_min_freq` policy limits change after that.

**powersave**

When attached to a policy object, this governor causes the lowest frequency, within the `scaling_min_freq` policy limit, to be requested for that policy.

The request is made once at that time the governor for the policy is set to `powersave` and whenever the `scaling_max_freq` or `scaling_min_freq` policy limits change after that.

You can read more details about the `CPUFreq` Linux feature and configuration options in the [Kernel Documentation](https://www.kernel.org/doc/html/latest/admin-guide/pm/cpufreq.html).

## Put your CPU's in 'performance' mode

Check the current mode:

```
# cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
powersave
powersave
powersave
powersave
[...snip...]
```

Switch to the 'performance' mode:

```
$ echo "performance" | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
```

Ensure the CPU scaling governor is in performance mode by checking the following; here you will see the setting from each processor (vcpu).

```
# cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
performance
performance
performance
performance
[...snip...]
```

## Summary

In this article we described the `CPUFreq` feature of the Linux Kernel and demonstrated how to switch between CPU scaling governor modes without rebooting the host.

## Bug

In Linux Kernel 5.5.5 I found there's an issue with the default value for `scaling_governor`:

```
# cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
cat: /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor: Invalid argument
cat: /sys/devices/system/cpu/cpu10/cpufreq/scaling_governor: Invalid argument
cat: /sys/devices/system/cpu/cpu11/cpufreq/scaling_governor: Invalid argument
cat: /sys/devices/system/cpu/cpu12/cpufreq/scaling_governor: Invalid argument
cat: /sys/devices/system/cpu/cpu13/cpufreq/scaling_governor: Invalid argument
[...snip...]
```

I found an [ArchLinux Redit discussion](https://www.reddit.com/r/archlinux/comments/f5bqpy/kernel_553_breaks_cpupower/) for the same issue with an associated [bug report](https://bugs.archlinux.org/task/65543). It seems to have been introduced in 5.5.3.

There is a reported change in 5.3.3 - [https://cdn.kernel.org/pub/linux/kernel/v5.x/ChangeLog-5.5.3](https://cdn.kernel.org/pub/linux/kernel/v5.x/ChangeLog-5.5.3)

```
    cpufreq: Avoid creating excessively large stack frames
    
    commit 1e4f63aecb53e48468661e922fc2fa3b83e55722 upstream.
    
    In the process of modifying a cpufreq policy, the cpufreq core makes
    a copy of it including all of the internals which is stored on the
    CPU stack.  Because struct cpufreq_policy is relatively large, this
    may cause the size of the stack frame to exceed the 2 KB limit and
    so the GCC complains when -Wframe-larger-than= is used.
    
    In fact, it is not necessary to copy the entire policy structure
    in order to modify it, however.
    
    First, because cpufreq_set_policy() obtains the min and max policy
    limits from frequency QoS now, it is not necessary to pass the limits
    to it from the callers.  The only things that need to be passed to it
    from there are the new governor pointer or (if there is a built-in
    governor in the driver) the "policy" value representing the governor
    choice.  They both can be passed as individual arguments, though, so
    make cpufreq_set_policy() take them this way and rework its callers
    accordingly.  This avoids making copies of cpufreq policies in the
    callers of cpufreq_set_policy().
    
    Second, cpufreq_set_policy() still needs to pass the new policy
    data to the ->verify() callback of the cpufreq driver whose task
    is to sanitize the min and max policy limits.  It still does not
    need to make a full copy of struct cpufreq_policy for this purpose,
    but it needs to pass a few items from it to the driver in case they
    are needed (different drivers have different needs in that respect
    and all of them have to be covered).  For this reason, introduce
    struct cpufreq_policy_data to hold copies of the members of
    struct cpufreq_policy used by the existing ->verify() driver
    callbacks and pass a pointer to a temporary structure of that
    type to ->verify() (instead of passing a pointer to full struct
    cpufreq_policy to it).
    
    While at it, notice that intel_pstate and longrun don't really need
    to verify the "policy" value in struct cpufreq_policy, so drop those
    check from them to avoid copying "policy" into struct
    cpufreq_policy_data (which allows it to be slightly smaller).
    
    Also while at it fix up white space in a couple of places and make
    cpufreq_set_policy() static (as it can be so).
```

It's unclear (to me) whether this change introduced the problem or if it's unrelated. It's the only change I could find related to cpufreq at the time the issue is seen for the first time.

**Update:** After installing Kernel 5.5.8, the issue is no longer present.
