---
title: "How to Emulate CXL Persistent Memory Devices with QEMU on Ubuntu 24.04"
meta_title: "A Comprehensive Guide to Emulating CXL PMem with QEMU"
description: "This article provides a step-by-step guide to emulating CXL Persistent Memory (PMem) devices using QEMU on Ubuntu 24.04, including file system setup, QEMU configuration, and guest OS verification."
date: 2025-03-20T00:00:00Z
image: "featured_image.webp"
categories: ["Linux", "CXL", "PMem", "QEMU"]
author: "Steve Scargall"
tags: ["CXL", "PMem", "QEMU", "Ubuntu"]
draft: true
aliases:
---

In this guide, we’ll walk through the steps to emulate a CXL Persistent Memory (PMem) device using QEMU 9.0.2 on Ubuntu 24.04. The setup includes a CXL Type 3 device with a Label Storage Area (LSA), mapped to a file system for persistent storage. This emulation is ideal for testing and development purposes, especially when working with CXL-enabled applications or operating systems.

To streamline the process of setting up a QEMU VM with an emulated CXL Persistent Memory device we will use an Ubuntu 24.04 cloud image. Using a cloud image eliminates the need for manual OS installation and configuration by leveraging cloud-init for automated setup. Feel free to use whatever Guest VM image you like.

## Step 1: Install QEMU and Dependencies

Ensure QEMU and `cloud-image-utils` are installed on your Ubuntu 24.04 host:

```bash
sudo apt update && sudo apt install qemu-system-x86 qemu-utils cloud-image-utils
```

## Step 2: Create Backend Files for the CXL PMem Device

Create the CXL PMem and LSA files on the file system for persistence:

```bash
mkdir -p ~/cxl
fallocate -l 4G ~/cxl/cxl-pmem.raw
fallocate -l 256M ~/cxl/cxl-lsa.raw
```

## Step 3: Download the Ubuntu 24.04 Cloud Image

Download the Ubuntu 24.04 (Noble) server cloud image. A list of available images can be found on the  [Ubuntu Cloud Images](https://cloud-images.ubuntu.com/)  website. You want to download the  `<codename>-server-cloudimg-amd64.img`  file, which is a QEMU QCOW2 image. For this example, we will use the Ubuntu 24.04 server cloud image, but you can use any other version available.

```bash
curl -O https://cloud-images.ubuntu.com/noble/current/noble-server-cloudimg-amd64.img
```

## Step 4: Create a Clone of the Cloud Image

Use qemu-img to create a clone of the downloaded Ubuntu Cloud Image:

```bash
qemu-img create -f qcow2 -b noble-server-cloudimg-amd64.img -F qcow2 cxl-pmem-vm.img
```

Where:

- `-f qcow2`: Specifies the format of the new image (QCOW2).
- `-b noble-server-cloudimg-amd64.img`: Uses the original image as the backing file.
- `cxl-pmem-vm.img`: The name of the cloned image.

Check the current size of the image:

```bash
qemu-img info cxl-pmem-vm.img
```

Look at the 'virtual size'

```bash
$ qemu-img info cxl-pmem-vm.img
image: cxl-pmem-vm.img
file format: qcow2
virtual size: 3.5 GiB (3758096384 bytes). <<<<<<<<<
disk size: 1.05 GiB
...
```

Resize the image to 6GB:

```bash
qemu-img resize cxl-pmem-vm.img 6G
```

Confirm the image has been resized:

```bash
qemu-img info cxl-pmem-vm.img
```

```bash
image: cxl-pmem-vm.img
file format: qcow2
virtual size: 6 GiB (6442450944 bytes). <<<<<<<<
disk size: 1.05 GiB
...
```

## Step 5: Create an SSH Key-Pair for the Guest VM

To acess the Ubuntu OS in the Guest VM, we need to create or use an SSH key-pair. If you haven’t already generated an SSH key pair, you can do so using the ssh-keygen command. Here’s how to generate a new RSA key pair:

```bash
ssh-keygen -t rsa -C "your_email@example.com" -f ./cxl-pmem-key
```bash

When prompted, press enter to leave the passphrase blank.

Example:

```bash
$ ssh-keygen -t rsa -C "your_email@example.com" -f ./cxl-pmem-key
Generating public/private rsa key pair.
Enter passphrase (empty for no passphrase):
Enter same passphrase again:
Your identification has been saved in ./cxl-pmem-key
Your public key has been saved in ./cxl-pmem-key.pub
The key fingerprint is:
SHA256:C4zh+PxxqPnhFbFJrmlStYBMy3Lhz3huegawwSzUzNI your_email@example.com
The key's randomart image is:
+---[RSA 3072]----+
|  = o  |
| o E + |
|.oo O . +  |
|. == B = = |
| ..++ B S  |
|  .o.+ = o |
|  +.X +  |
| Xo= |
|  +++  |
+----[SHA256]-----+
```

This will create a public and private key.

```bash
$ ls -1 cxl-pmem-key*
cxl-pmem-key             // Private Key
cxl-pmem-key.pub         // Public Key
```

## Step 6: Create a Seed Image for Cloud-Init

Create a user-data.yaml file with your desired user configuration. Here is an example of creating a local user called ubuntu with sudo permissions using the SSH key and a password (admin):

```yaml
# user-data.yaml

# Configure the 'ubuntu' user
ssh_pwauth: True
chpasswd:
  expire: false
  users:
  - {name: ubuntu, password: admin, type: text}
users:
  - name: ubuntu
    groups: users, sudo
    shell: /usr/bin/bash
    ssh_authorized_keys:
      - ssh-rsa AAAAB3Nz... # Paste Your SSH Public Key Here

# Grow the root file system
growpart:
  mode: auto
  devices: ['/']
  ignore_growroot_disabled: false
```

Generate the seed image:

```bash
cloud-localds seed.img user-data.yaml
```

## Step 7: Launch the VM with CXL PMem

Start the VM with the following command:

```bash
qemu-system-x86_64 \
  -M q35,cxl=on -m 2G,maxmem=4G,slots=8 -smp 1 \
  -object memory-backend-file,id=cxl-pmem-backend,share=on,mem-path=/home/steve/cxl/cxl-pmem.raw,size=4G \
  -object memory-backend-file,id=cxl-lsa-backend,share=on,mem-path=/home/steve/cxl/cxl-lsa.raw,size=256M \
  -device pxb-cxl,bus_nr=12,bus=pcie.0,id=cxl-host-bridge \
  -device cxl-rp,port=0,bus=cxl-host-bridge,id=root-port,chassis=0,slot=2 \
  -device cxl-type3,bus=root-port,persistent-memdev=cxl-pmem-backend,lsa=cxl-lsa-backend,id=cxl-pmem0 \
  -M cxl-fmw.0.targets.0=cxl-host-bridge,cxl-fmw.0.size=4G \
  -drive file=/home/steve/cxl-pmem-vm.img,format=qcow2 \
  -drive file=/home/steve/seed.img,format=raw \
  -netdev user,id=net0,hostfwd=tcp::2222-:22 \
  -device pcie-root-port,bus=pcie.0,id=pcie-root-port1,chassis=1,slot=3 \
  -device virtio-net-pci,netdev=net0,bus=pcie-root-port1 \
  -nographic
```

Here's a breakdown of the `qemu-system-x86_64` so you can understand the options and arguments, and adjust for your environment.

**Machine and Memory Options**

- `-M q35,cxl=on`: Specifies the machine type (`q35`, a modern Intel chipset) and enables CXL support.
- `-m 2G,maxmem=4G,slots=8`: Allocates 2GB of RAM to the VM, with a maximum expandable memory of 4GB and 8 memory slots for hotplugging.
- `-smp 1`: Configures the VM with 1 virtual CPU.

**Memory Backend Files**

- `-object memory-backend-file,id=cxl-pmem-backend,share=on,mem-path=/home/steve/cxl/cxl-pmem.raw,size=4G`: Creates a memory backend file for the CXL PMem device (4GB size).
- `-object memory-backend-file,id=cxl-lsa-backend,share=on,mem-path=/home/steve/cxl/cxl-lsa.raw,size=256M`: Creates a memory backend file for the Label Storage Area (LSA) (256MB size).

**CXL Device Configuration**

- `-device pxb-cxl,bus_nr=12,bus=pcie.0,id=cxl-host-bridge`: Creates a CXL host bridge on PCI bus 12.
- `-device cxl-rp,port=0,bus=cxl-host-bridge,id=root-port,chassis=0,slot=2`: Adds a CXL root port to the host bridge.
- `-device cxl-type3,bus=root-port,persistent-memdev=cxl-pmem-backend,lsa=cxl-lsa-backend,id=cxl-pmem0`: Attaches a CXL Type 3 PMem device to the root port, linking it to the PMem and LSA backends.
- `-M cxl-fmw.0.targets.0=cxl-host-bridge,cxl-fmw.0.size=4G`**: Configures a CXL Fixed Memory Window (4GB size) targeting the CXL host bridge.

**Disk and Cloud-Init**

- `-drive file=/home/steve/noble-server-cloudimg-amd64.img,format=qcow2`: Attaches the Ubuntu 24.04 cloud image as the primary disk.
- `-drive file=/home/steve/seed.img,format=raw`: Attaches the cloud-init seed image for automated VM configuration.

**Networking**

- `-netdev user,id=net0,hostfwd=tcp::2222-:22`: Configures a user-mode network device with port forwarding (host port 2222 to VM port 22 for SSH).
- `-device pcie-root-port,bus=pcie.0,id=pcie-root-port1,chassis=1,slot=3`: Adds a PCIe root port to the main PCIe bus (`pcie.0`).
- `-device virtio-net-pci,netdev=net0,bus=pcie-root-port1`: Attaches a Virtio network device to the PCIe root port.

**Console Output**

- `-nographic`: Redirects the VM console output to the terminal, allowing you to monitor the boot process and cloud-init logs in real-time.

## Step 8: Access the VM

Once the VM boots, you can SSH into it using the configured SSH key:

```bash
ssh -o "StrictHostKeyChecking no" -i ./cxl-pmem-key ubuntu@localhost -p 2222
```

## Step 9: Verify CXL PMem is seen in the Guest VM

1. **Check CXL Device is Available**:

   You should see a new 'CXL' device in `lspci`

   ```bash
   $ lspci | grep -i cxl 
   0d:00.0 CXL: Intel Corporation Device 0d93 (rev 01)
   ```

2. **Update the Guest VM OS and install the CXL Drivers**

   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

   The Ubuntu Cloud image does not contain the CXL drivers by default. If you used a different image, you may not have the drivers already installed. You can confirm this by checking if the CXL drivers are included or are optional Kernel drivers/modules:

   ```bash
   $ grep CONFIG_CXL /boot/config-$(uname -r)
   CONFIG_CXL_BUS=m
   CONFIG_CXL_PCI=m
   # CONFIG_CXL_MEM_RAW_COMMANDS is not set
   CONFIG_CXL_ACPI=m
   CONFIG_CXL_PMEM=m
   CONFIG_CXL_MEM=m
   CONFIG_CXL_PORT=m
   CONFIG_CXL_SUSPEND=y
   CONFIG_CXL_REGION=y
   # CONFIG_CXL_REGION_INVALIDATION_TEST is not set
   CONFIG_CXL_PMU=m
   ```

   The CXL drviers are optional modules (`=m`). You can confirm if the drivers are loaded or not using:

   ```bash
   $ lsmod | grep -i cxl 
   $
   ```

   If you see no output, then the drivers are not loaded.

   Try to load the drivers. 

   ```bash
   sudo modprobe cxl_pci \
   sudo modprobe cxl_mem \
   sudo modprobe cxl_region 
   ```

   If you see an error somilar to the following, you'll need to install the missing packages

   ```bash
   modprobe: FATAL: Module cxl_pci not found in directory /lib/modules/6.8.0-55-generic
   modprobe: FATAL: Module cxl_mem not found in directory /lib/modules/6.8.0-55-generic
   modprobe: FATAL: Module cxl_region not found in directory /lib/modules/6.8.0-55-generic
   ```

   Install the missing drivers using:

   ```bash
   sudo apt install linux-modules-extra-$(uname -r)
   ```

   Load the drivers, and it should succeed:

   ```bash
   sudo modprobe cxl_pci \
   sudo modprobe cxl_mem \
   sudo modprobe cxl_region 
   ```

   You should now see the drivers are loaded

   ```bash
   lsmod | grep -i cxl
   ```

   Example:

   ```bash
   $ lsmod | grep -i cxl 
   cxl_mem                12288  0
   cxl_port               16384  0
   cxl_pci                28672  0
   cxl_core              299008  4 cxl_port,cxl_mem,cxl_pci
   ```

3. **Install the cxl and ndctl utilities**

   ```bash
   sudo apt install -y cxl ndctl 
   ```

4. **Reboot the Guest VM**

   ```bash
   sudo systemctl reboot
   ```

5. **Manage PMem** using `ndctl` and cxl:

   Confirm the CXL PMem device can be seen

   ```bash
   $ cxl list
   [
     {
        "memdev":"mem0",
        "pmem_size":4294967296,
        "serial":0,
        "host":"0000:0d:00.0"
     }
   ]
   ```

   Show the CXL PMem and Decoder. You should see "pmem_capable:true"

   ```bash
   $ cxl list -D -m mem0
   [
     {
       "decoder":"decoder0.0",
       "size":4294967296,
       "interleave_ways":1,
       "max_available_extent":4294967296,
       "pmem_capable":true,   <<<<
       "volatile_capable":true,
       "accelmem_capable":true,
       "nr_targets":1
     }
   ]
   ```

   ```bash
   ndctl list -CRi
   ndctl create-namespace -m fsdax -r region0
   ```

## Exiting the QEMU Console

Use the following key combination to exit the QEMU console and return the host prompt:

- Press Ctrl + A
- Press x

### Enabling Linux Kernel CXL Debug

If you need to debug issues in the Kernel, add `cxl.debug=1` to the Linux boot command and reboot

Edit `/etc/default/grub` and add `cxl.debug=1` to the `GRUB_CMDLINE_LINUX_DEFAULT` line. For example:

```bash
GRUB_CMDLINE_LINUX="cxl.debug=1"
```

Update Grub

```bash
sudo update-grub
```

Reboot the Guest for the changes to take effect:

```bash
sudo systemctl reboot
```

## Update the Guest VM Kernel to the latest Mainline

To add the PPA, open terminal from system application launcher and run command:

```bash
sudo add-apt-repository ppa:cappelikan/ppa
```

Then check updates and install the tool via commands:

```bash
sudo apt update

sudo apt install mainline pkexec
```

Check for Kernel updates:

```bash
$ mainline check
mainline 1.4.12
Updating Kernels...
Latest update: 6.13.7
Latest point update: 6.8.12
mainline: done
```

Update to the latest mainline Kernel

```bash
sudo mainline install-latest
```

Reboot the Guest VM

```sudo
systemctl reboot
```