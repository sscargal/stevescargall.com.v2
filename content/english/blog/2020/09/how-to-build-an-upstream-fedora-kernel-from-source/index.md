---
title: "How to build an upstream Fedora Kernel from source"
date: "2020-09-14"
categories: 
  - "how-to"
  - "linux"
tags: 
  - "custom-kernel"
  - "kernel"
image: "images/pexels-photo-97077.jpeg"
author: Steve Scargall
aliases:
  - /blog/2020/09/14/how-to-build-an-upstream-fedora-kernel-from-source/
---

I typically keep my Fedora system current, updating it once every week or two. More recently, I wanted to test the [Idle Page Tracking](https://www.kernel.org/doc/html/latest/admin-guide/mm/idle_page_tracking.html#) feature, but this wasn't enabled in the default kernel provided by Fedora.

```bash
# grep CONFIG_IDLE_PAGE_TRACKING /boot/config-$(uname -r)
# CONFIG_IDLE_PAGE_TRACKING is not set
```

To enable the feature, we need to build a custom kernel with the feature(s) we need. Thankfully, the process isn't too difficult.

For this walk through, I'll be building a customised version of the Fedora 32 kernel version I already have installed (5.8.7-200.fc32.x86\_64), using some of the instructions from [https://fedoraproject.org/wiki/Building\_a\_custom\_kernel](https://fedoraproject.org/wiki/Building_a_custom_kernel).

## Install the dependencies for building kernels

Not all of these will apply to all methods but this provides a good dependency list of items to install

```bash
# sudo dnf install fedpkg fedora-packager rpmdevtools ncurses-devel pesign grubby openssl-devel dwarves
```

if you plan to run 'make xconfig'

```bash
# sudo dnf install qt3-devel libXi-devel gcc-c++
```

Also make sure you add the user doing the build to /etc/pesign/users and run the authorize user script:

```bash
# sudo /usr/libexec/pesign/pesign-authorize
```

It should be noted that pesign pesign-rh-test-certs gets pulled in automatically for some, but not for everyone, it depends on how you installed pesign. It is best to make sure that you have it installed.

## Download the Kernel source

We could clone the github kernel repository, but it's often faster to download the tar.gz or .xz file for the specific kernel version instead.
bash
```
# mkdir ~downloads
# wget https://mirrors.edge.kernel.org/pub/linux/kernel/v$(uname -r | cut -f1 -d'.').x/linux-$(uname -r | cut -f1 -d'-').tar.gz
```

Extract the source and change to the directory

```bash
# tar xf linux-$(uname -r | cut -f1 -d'-').tar.gz
# cd linux-$(uname -r | cut -f1 -d'-')
```

## Applying Patches

If you have any patches to apply, now is the time to do it.

#### The patch method

If you were asked to apply any patches by the developer, this is the stage at which we would do so. These would typically be applied using a command something like..

```bash
$ cat ~/testpatch.diff | patch -p1
```

If you have to try multiple different patches individually, you can unapply the previous one after testing by adding -R on the end of the above command.

#### The git method

Most developers these days generate patches using git and you can use git to help apply patches. You can do:

```bash
$ git am -3 <patch file>
```

This will create a git commit of a single patch in your tree.

## Configure the kernel

For this particular example, we only want to make a modification to the config file to enable CONFIG\_IDLE\_PAGE\_TRACKING. We'll use the default boot/config-5.8.7 file as a starting point, then remove the comment and add the config option.

```bash
# cp /boot/config-$(uname -r) .config
# vi .config

- # CONFIG_IDLE_PAGE_TRACKING is not set
+ CONFIG_IDLE_PAGE_TRACKING=y
```

## Building the kernel

To add some further customization, edit the makefie (`vi Makefile)` and change the EXTRAVERSION line to add something on the end. For example, if it reads "EXTRAVERSION = -rc5" change it to "EXTRAVERSION = -rc5-dave" (what you choose is only relevant for the final part of this procedure)

To use as many vCPUs as possible, use the following command to set the number of CPUs to use during compile time. Otherwise, only a single vCPU is used and it'll take a very long time to compile.

```bash
$ export MAKEFLAGS=-j$(getconf _NPROCESSORS_ONLN)
```

Manage any differences between the old config file and the one in the source. Since we're building the same kernel version, there should be no issues. However, if you're building a newer or older kernel, there may be some differences and dependencies that need to be resolved.

```bash
$ make oldconfig
```

If you want to use the GUI to specify config options, or validate the config file:

```bash
 $ make menuconfig 
```

Build the bzImage file

```bash
$ make bzImage
```

Build the modules (drivers)

```bash
$ make modules
```

Become root and install the modules and kernel

```bash
$ sudo bash
# make modules_install
# make install
```

You have now built and installed a kernel. It will show up in the grub menu next time you reboot. You can check the /boot directory for the new files. I modified the Makefile and set EXTRAVERSION = ipt (Idle Page Tracking). I see the following new files in /boot:

```bash
$ ls -1 /boot/*ipt*
/boot/initramfs-5.8.7ipt.img
/boot/System.map-5.8.7ipt
/boot/vmlinuz-5.8.7ipt
```

I validated the new \*ipt\* kernel option shows up in the Grub menu:

```bash
# grubby --info /boot/vmlinuz-5.8.7ipt
index=0
kernel="/boot/vmlinuz-5.8.7ipt"
args="ro resume=/dev/mapper/fedora_pmemdev1-swap rd.lvm.lv=fedora_pmemdev1/root rd.lvm.lv=fedora_pmemdev1/swap systemd.unified_cgroup_hierarchy=0 $tuned_params"
root="/dev/mapper/fedora_pmemdev1-root"
initrd="/boot/initramfs-5.8.7ipt.img $tuned_initrd"
title="Fedora (5.8.7ipt) 32 (Server Edition)"
id="36835b6e73964bab8640557be534f104-5.8.7ipt"
```

Reboot the host and select the \*ipt\* kernel from the list

```bash
$ sudo systemctl reboot 
```
