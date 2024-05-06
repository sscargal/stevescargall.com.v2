---
title: "How To Emulate CXL Devices using KVM and QEMU"
date: "2022-01-20"
categories: 
  - "cxl"
  - "how-to"
  - "linux"
tags: 
  - "featured"
  - "kernel"
  - "kvm"
  - "ndctl"
  - "persistent-memory"
  - "pmem"
  - "qemu"
image: "images/CXL_Logo.jpg"
author: Steve Scargall
---

## What is CXL?

Compute Express Link (CXL) is an open standard for high-speed central processing unit-to-device and CPU-to-memory connections, designed for high-performance data center computers. CXL is built on the PCI Express physical and electrical interface with protocols in three areas: input/output, memory, and cache coherence.

CXL is designed to be an industry open standard interface for high-speed communications, as accelerators are increasingly used to complement CPUs in support of emerging applications such as Artificial Intelligence and Machine Learning.

At the time of writing this blog, CXL 2.0 is the most recent specification. [Download](https://b373eaf2-67af-4a29-b28c-3aae9e644f30.filesusr.com/ugd/0c1418_14c5283e7f3e40f9b2955c7d0f60bebe.pdf) the CXL 2.0 white paper, or [download the CXL 2.0 specification](https://www.computeexpresslink.org/download-the-specification) for all the details. The [computeexpresslink.org](https://www.computeexpresslink.org) website has a lot of excellent articles and videos for you to learn more.

## Who should read this article

Software enablement relies on having a suitable platform when actual hardware isn't available. Developers need to understand how their application(s) will run on the new CXL hardware. System Administrators need to know what a CXL device looks like in the operating system. Hardware, Software, and Solution Architects need to learn how to utilize CXL devices in their environment and solutions. In lieu of access to CXL hardware, this article shows how to emulate CXL devices using KVM/QEMU. This approach is not intended to provide an environment for performance testing since we cannot replicate actual device bandwidth or latencies. The approach outlined in this blog can be used for becoming familiar with CXL devices, using the tools and utilities, creating development environments for adding CXL features to new or existing applications, and performing functional application testing.

## Prerequisites

CXL drivers for Linux were initially upstreamed into the v5.12 Kernel with this pull request. This was mostly plumbing rather than functionality. Since this time, the cxl drivers have received a lot of work and contributions from the CXL consortium. For the purposes of this article, we'll use the latest mainline Kernel (v5.16) so we get the most current features and functionality. This is, at the time of writing, bleeding edge, so the process has more steps than it will in the future once CXL becomes mainstream in Linux distros.

The key requirements are:

- Virtualization is enabled in the BIOS (for KVM acceleration)
- QEMU
- virt-install, libvirt, and libvirt-daemon-kvm
- A recent Linux distro for the host OS - I use Fedora Server 35 on my machine
- A recent Linux distro for the guest OS - I use Fedora Server 35 in this article + the latest 5.16 mainline Kernel
- Git command
- Build Tools (Compiler)

In the future, when all the CXL features are available, you'll only need to install packages. For now, we need to build some of the software stack from source code.

Install the prerequisites for building qemu and ndctl:

```
$ sudo dnf install @development-tools
$ sudo dnf install git gcc gcc-c++ autoconf automake asciidoc asciidoctor xmlto libtool pkg-config glib2 glib2-devel libfabric libfabric-devel doxygen graphviz pandoc ncurses kmod kmod-devel libudev-devel libuuid-devel json-c-devel keyutils-libs-devel iniparser iniparser-devel bash-completion ninja-build sparse pixman pixman-devel
$ sudo dnf install virt-install libvirt libvirt-daemon-kvm qemu-img cloud-init genisoimage
```

## Enable Virtualization

Enabling Virtualization in the BIOS allows us to take advantage of KVM acceleration. Without it, this will still work, but the guest will be considerably slower.

Both Intel and AMD CPU support virtualization technology which allows multiple operating systems to run simultaneously on an x86 server or computer in a safe and efficient manner using hardware virtualization. Intel calls it "Intel VT" and AMD calls theirs "AMD-V"/

In Linux, we can look at `cpuinfo` to determine if virtualization is enabled in the BIOS using:

```
# lscpu | grep Virtualization
Virtualization:                  VT-x
```

- VT-x indicates an Intel CPU has Virtualization enabled
- AMD-V Indicates an AMD CPU has virtualization enabled

## Install QEMU

At the time of writing, the latest release of QEMU (6.2.0) does not have CXL support, so we'll use the cxl-2.0v4 development branch from Ben Widawsky (Intel), which is based on QEMU 6.0.50.

Create a working directory to download QEMU:

```
$ mkdir ~/downloads
$ cd ~/downloads
```

Clone Ben's QEMU branch and confirm the default branch is the one we want (cxl-2.0v4):

```
$ git clone https://gitlab.com/bwidawsk/qemu
$ cd qemu
$ git branch 
* cxl-2.0v4
```

Build QEMU:

```
mkdir build
cd build
../configure --prefix=/opt/qemu-cxl
make -j all
make install
```

Note 1 - In contrast to autoconf scripts, QEMU’s configure is expected to be silent while it is checking for features. It will only display output when an error occurs, or to show the final feature enablement summary on completion. The configure operation can take many minutes, so be patient.  
  
Note 2 - Since this is a development branch of QEMU, I want to install it under /opt/qemu-cxl so it doesn't interfere with any existing or future QEMU installation. Alternatively, don't run 'make install' and source the binaries and libraries from the 'build' directory.

## Configure the Host Networking

Confirm IP forwarding is enabled for IPv4 and/or IPv6 on the host (0=Disabled, 1=Enabled):

```
$ sudo cat /proc/sys/net/ipv4/ip_forward
1
$ sudo cat /proc/sys/net/ipv6/conf/default/forwarding
1
```

If necessary, activate forwarding temporarily until the next reboot:

```
$ sudo echo 1 > /proc/sys/net/ipv4/ip_forward
$ sudo echo 1 > /proc/sys/net/ipv6/conf/all/forwarding
```

For a permanent setup create the following file:

```
$ sudo vim /etc/sysctl.d/50-enable-forwarding.conf
# local customizations
#
# enable forwarding for dual stack
net.ipv4.ip_forwarding=1
net.ipv6.conf.all.forwarding=1
```

## Download a Guest Operating System

There are two approaches to take:

1. Download the ISO for the operating system and go through the installation process on first boot
2. Use Cloud Images. A cloud image is a ready to use (virtual) system disk image that a virtual machine can use. Some simple configuration is required.

We'll use the Cloud Image for this article.

The location of the downloaded images can be any location you choose. By default, the libvirt default location for images to install from is `/var/lib/libvirt/boot`. If this doesn't exist, verify you installed the prerequisite libvirt\* packages shown earlier.

```
// Confirm the OS base directory exists
$  ls -ld /var/lib/libvirt/boot
drwx--x--x. 2 root root 4096 Dec 16 11:01 /var/lib/libvirt/boot

// Download the disk image
$ sudo wget https://mirror.genesisadaptive.com/fedora/linux/releases/35/Cloud/x86_64/images/Fedora-Cloud-Base-35-1.2.x86_64.qcow2 -O /var/lib/libvirt/boot/Fedora-Cloud-Base-35-1.2.x86_64.qcow2

// Download the disk image checksum
$ sudo wget https://mirror.genesisadaptive.com/fedora/linux/releases/35/Cloud/x86_64/images/Fedora-Cloud-35-1.2-x86_64-CHECKSUM -O /var/lib/libvirt/boot/Fedora-Cloud-35-1.2-x86_64-CHECKSUM

// Perform checksum validation to confirm the image is okay
// Because the *CHECKSUM file contains the values for all cloud images, we ignore the missing and  WARNING message.
$ cd /var/lib/libvirt/boot
$ sudo sha256sum --ignore-missing -c *-CHECKSUM
Fedora-Cloud-Base-35-1.2.x86_64.qcow2: OK
sha256sum: WARNING: 19 lines are improperly formatted
```

Create a new disk image from the cloud image for our new guest VM called "CXL-Test":

```
$ sudo cp  /var/lib/libvirt/boot/Fedora-Cloud-Base-35-1.2.x86_64.qcow2 /var/lib/libvirt/images/CXL-Test.qcow2

// Grow the disk image by 15GiB
$ sudo qemu-img resize /var/lib/libvirt/images/CXL-Test.qcow2 +15G
Image resized.

// Review the image information 
$ sudo qemu-img info /var/lib/libvirt/images/CXL-Test.qcow2
image: /var/lib/libvirt/images/CXL-Test.qcow2
file format: qcow2
virtual size: 20 GiB (21474836480 bytes)
disk size: 359 MiB
cluster_size: 65536
Format specific information:
    compat: 0.10
    compression type: zlib
    refcount bits: 16
```

An alternative approach is to use the downloaded cloud image as a backing file and create a new image from it:

```
qemu-img create -f qcow2 \
-b /var/lib/libvirt/boot/Fedora-Cloud-Base-35-1.2.x86_64.qcow2 \
-f qcow2 \
-F qcow2 \
/var/lib/libvirt/images/CXL-Test.qcow2 \
20G
```

## Configure the Cloud Image

There are several common approaches to configuring the guest OS:

1. Use `virt-install` with the `--cloud-init` option to create a random password for first time boot. [Go Here](#configure-the-guest-os-using-virsh-install).
2. Build a bootstrap ISO image with the necessary configuration information and boot the guest using the `qemu-system-x86_64` command. [Go Here](#configure-the-guest-os-using-a-cloud-init-boot-strap-image).

I'll cover both approaches here. You should spend time correctly configuring your host. These options do not result in a secure environment, which is fine for experimenting, but not production.

### Configure the Guest OS using virsh-install

The virsh command used to manage virsh guest domains. At the time of writing, it doesn't natively support nvdimm (PMem) or CXL devices. One solution is to manually edit the XML to add the devices, which is outside the scope of this article. Instead, we can use virst-install to initially provision and configure the guest OS, then use qemu-system-x86\_64 to launch the guest with the required PMem and CXL devices.

```
$ sudo virt-install --connect qemu:///system \
--name CXL-Test \
--memory 4096 \
--cpu host --vcpus 4 \
--os-type linux \
--os-variant fedora35 \
--import \
--graphics none \
--disk /var/lib/libvirt/images/CXL-Test.qcow2,format=qcow2,bus=virtio \
--network direct,source=enpXsY,source_mode=route, model=virtio \
--network bridge=virbr0,model=virtio \
--cloud-init
```

The temporary root password is displayed in the first few seconds. You need to make a note of this one-time password! It should be similar to the following (where \* is your actual password):  
  
Starting install…  
Password for first root login is: \*\*\*\*\*\*\*\*\*\*\*\*\*\*\*\*  
Installation will continue in 10 seconds (press Enter to skip)…

Here is a description of the options we used:

<table><tbody><tr><td>--name VM_NAME</td><td>Unique name of the VM to install as shown e.g.in VM list</td></tr><tr><td>--memory 4096</td><td>Amount of memory to allocate</td></tr><tr><td>--cpu host --vcpus 4</td><td>same cpu type as host, adjust numbers as appropriate</td></tr><tr><td>--os-type linux</td><td>Fix here, used by virt-install to determine defaults</td></tr><tr><td>--os-variant fedora35</td><td>Adjust distribution and version as needed</td></tr><tr><td>--import</td><td>Fixed, skips installation procedure and boots from the first (virtual) disk as specified by the first ‐-disk parameter.</td></tr><tr><td>--graphics none</td><td>Fixed, enforces a redirect of the VM login prompt to the host terminal window for immediate access.</td></tr><tr><td>--disk /var/lib/libvirt/images/VM_NAME.qcow2, format=qcow2,bus=virtio</td><td>disk image file, adjust VM_NAME</td></tr><tr><td>--network direct,source=enpXsY,source_mode=route, model=virtio</td><td>specify&nbsp;<em>external</em>&nbsp;network (macvlan)&nbsp;<em>first</em>, it will get the name eth0 as usual. Adjust interface name as appropriate.</td></tr><tr><td>--network bridge=virbr0,model=virtio</td><td>specify the&nbsp;<em>internal</em>&nbsp;network (libvirt generated bridge)&nbsp;<em>second</em>. It will get the name eth1 as usual.</td></tr><tr><td>--cloud-init</td><td>new with version 3 to handle nocloud configuration</td></tr></tbody></table>

Once the guest OS boots, you should be presented with the "fedora login:" prompt. Use the username of "root" and the one-time password shown when we launched the installation process. You'll be required to change the password:

```
fedora login: root
Password:
You are required to change your password immediately (administrator enforced).
Current password:
New password:
Retype new password:
#
```

Continue to [Update the Kernel](#update-the-kernel).

### Configure the Guest OS using a cloud-init boot strap image

The cloud image that we’re using requires `cloud-init` to perform some first-time setup. I’m trying to use only the bare minimum configuration to bring up a virtual machine here, but curious readers should head over to the [cloud-init documentation](https://cloudinit.readthedocs.io/en/latest/) if you want to learn other ways that it can be used to customize their virtual machine.

Cloud-init uses two configuration files, `user-data` and `meta-data`. The meta-data file describes the instance information (hostname, etc), while the user-data describes OS and user configuration information.

Create the meta-data file, specifying the instance and hostname:

```
$ cat > /var/lib/libvirt/boot/meta-data << EOF
instance-id: cxl-test
local-hostname: cxl-test
EOF
```

Next, we’re going to create the user-data file and ask ccloud-init to create a new user called 'cxldemo' using an SSH public key (no local login via the console):

```
$ cat > /var/lib/libvirt/boot/user-data << EOF
#cloud-config

# Add a 'cxltest' user to the system with a password
users:
  - default
  - name: cxltest
    gecos: CXL Test User
    primary_group: wheel
    groups: users
    sudo: ALL=(ALL) NOPASSWD:ALL
    lock_passwd: false
    ssh-authorized-keys:
      - ssh-rsa AAAAB3NzaC1yc2EAAAADAQ[...snip...]Ife0E0JCiBFAL3C5SIZjjfQ4w== 
    shell: /usr/bin/bash

# Grow the root file system
growpart:
  mode: auto
  devices: ['/']
  ignore_growroot_disabled: false
EOF
```

The 'ssh-authorized-keys' should exists in `.ssh/id_rsa/id_rsa.pub`. If you do not have a private and public key created, generate one using:

```
$ ssh-keygen -b 4096
```

If you do not want to allow or configure ssh into the guest VM, you can create local logins by replacing the above user-data file with this one:

```
$ cat > /var/lib/libvirt/boot/user-data << EOF
#cloud-config

# Add a 'cxltest' user to the system with a password
users:
  - default
  - name: cxltest
    gecos: CXL Test User
    primary_group: wheel
    groups: users
    sudo: ALL=(ALL) NOPASSWD:ALL
    lock_passwd: false 
    shell: /usr/bin/bash

# Set local logins
chpasswd:
  list: |
    root:password
    cxltest:password
  expire: False

# Grow the root file system
growpart:
  mode: auto
  devices: ['/']
  ignore_growroot_disabled: false
EOF
```

Create an ISO image of the user-data and meta-data files that we'll use for the first boot.

```
$ sudo genisoimage -output /var/lib/libvirt/boot/Fedora-Cloud-CXL-test-cloud-init.iso \
-volid cidata -joliet -rock \
/var/lib/libvirt/boot/user-data \
/var/lib/libvirt/boot/meta-data
```

Start the guest. The following options use the Cloud disk image, the Cloud-Init ISO, assign 4GB of RAM, 4 vCPUs, and configure the host to boot on the console (STDOUT). This is sufficient to boot the host and perform the initial configuration. You should configure the guest with options appropriate to your environment.

```
$ sudo /opt/qemu-cxl/bin/qemu-system-x86_64 -drive file=/var/lib/libvirt/images/CXL-Test.qcow2,format=qcow2,index=0,media=disk,id=hd \
-cdrom /var/lib/libvirt/boot/Fedora-Cloud-CXL-test-cloud-init.iso \
-m 4G,slots=8,maxmem=8G \
-smp 4 \
-machine type=q35,accel=kvm,nvdimm=on,cxl=on \
-enable-kvm \
-nographic \
-net nic \
-net user,hostfwd=tcp::2222-:22
```

To exit the console press Ctrl-A, then type 'x' to exit, or run `sudo poweroff` within the guest.

To login via ssh use the following from the host:

```
$ ssh cxldemo@localhost -p 2222
```

Now you can proceed to configure the guest as you see fit, eg: setup proxies, update the OS, install packages, etc. This can all be done from the user-data cloud-init file.

## Update the Kernel

The Fedora 35 Server Cloud Image comes with Kernel 5.14.10-300. I want to use Kernel 5.16. By the time you read this, 5.16 may be available, in which can you simply need to run `$ sudo dnf update`. At the time of writing this article, 5.15.14-200 was the most recent, so we'll install the latest mainline Kernel following the instructions for [Fedora Kernel Vanilla Repositories](https://fedoraproject.org/wiki/Kernel_Vanilla_Repositories).

The 5.16 Mainline Kernel doesn't have full CXL support. You can build a custom 5.16 Kernel with more CXL features from [https://git.kernel.org/pub/scm/linux/kernel/git/cxl/cxl.git](https://git.kernel.org/pub/scm/linux/kernel/git/cxl/cxl.git) using the tagged "cxl-for-5.16".

Download the definitions for the Kernel vanilla repositories:

```
$ curl -s https://repos.fedorapeople.org/repos/thl/kernel-vanilla.repo | sudo tee /etc/yum.repos.d/kernel-vanilla.repo
```

Run this to install the latest stable mainline kernel:

```
$ sudo dnf --enablerepo=kernel-vanilla-stable update
$ sudo systemctl reboot
```

## Configure CXL

The following configured two CXL devices in the guest.

```
$ sudo /opt/qemu-cxl/bin/qemu-system-x86_64 -drive file=/var/lib/libvirt/images/CXL-Test.qcow2,format=qcow2,index=0,media=disk,id=hd \
-m 4G,slots=8,maxmem=8G \
-smp 4 \
-machine type=q35,accel=kvm,nvdimm=on,cxl=on \
-enable-kvm \
-nographic \
-net nic \
-net user,hostfwd=tcp::2222-:22 \
-object memory-backend-ram,size=4G,id=mem0 \
-numa node,nodeid=0,cpus=0-3,memdev=mem0 \
-object memory-backend-file,id=cxl-mem1,share=on,mem-path=cxl-window1,size=512M \
-object memory-backend-file,id=cxl-label1,share=on,mem-path=cxl-label1,size=1K \
-object memory-backend-file,id=cxl-label2,share=on,mem-path=cxl-label2,size=1K \
-device pxb-cxl,id=cxl.0,bus=pcie.0,bus_nr=52,uid=0,len-window-base=1,window-base[0]=0x4c00000000,memdev[0]=cxl-mem1 \
-device cxl-rp,id=rp0,bus=cxl.0,addr=0.0,chassis=0,slot=0,port=0 \
-device cxl-rp,id=rp1,bus=cxl.0,addr=1.0,chassis=0,slot=1,port=1 \
-device cxl-type3,bus=rp0,memdev=cxl-mem1,id=cxl-pmem0,size=256M,lsa=cxl-label1 \
-device cxl-type3,bus=rp1,memdev=cxl-mem1,id=cxl-pmem1,size=256M,lsa=cxl-label2 \
-daemonize
```

Once the host boots, you can verify there are two 'mem' devices under /dev/cxl:

```
$ ls -1 /dev/cxl
mem0
mem1

$ cxl list -M
[
  {
    "memdev":"mem0",
    "pmem_size":268435456,
    "ram_size":0
  },
  {
    "memdev":"mem1",
    "pmem_size":268435456,
    "ram_size":0
  }
]
```

This is as far as we can go with the mainline Kernel for now. If you built the custom 5.16 Kernel, you'll see the devices appear in `ndctl list`, but you won't be able to create namespaces yet. Patches for kernel 5.17 are under review that should bring more functionality along with ndctl/cxl version73 once they are available.
