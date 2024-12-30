---
title: "A Step-by-Step Guide on Using Cloud Images with QEMU 9 on Ubuntu 24.04"
meta_title: "A Step-by-Step Guide on Using Cloud Images with QEMU 9.0.2 on Ubuntu 24.04"
description: "This guide provides detailed steps on how to to install and configure Ubuntu Cloud Images with QEMU."
date: 2024-12-23T00:00:00Z
image: "featured_image.webp"
categories: ["How To", "Linux"]
author: "Steve Scargall"
tags: ["QEMU", "Linux", "Remote Development", "SSH", "Ubuntu"]
draft: false
aliases:
---

## Introduction

Cloud images are pre-configured, optimized templates of operating systems designed specifically for cloud and virtualized environments. Cloud images are essentially vanilla operating system installations, such as Ubuntu, with the addition of the `cloud-init` package. This package enables run-time configuration of the OS through user data, such as text files on an ISO filesystem or cloud provider metadata. Using cloud images significantly reduces the time and effort required to set up a new virtual machine. Unlike ISO images, which require a full installation process, cloud images boot up immediately with the OS pre-installed

This guide will walk you through the process of using Ubuntu cloud images with QEMU 9.0.2, configuring the default network, storage, and users, without the need to manually install and configure OS images from ISOs.

### Prerequisites

- **Ubuntu 24.04 Host**: Ensure you have Ubuntu 24.04 installed on your system.
- **QEMU and Dependencies**: Install QEMU and necessary dependencies.
- **Internet Connection**: Required for downloading cloud images and other resources.
- **Virtualization Support**: Ensure your CPU supports virtualization (VT-x for Intel, AMD-V for AMD).

### Step 1: Install QEMU and Dependencies

If you haven't already installed QEMU and the necessary dependencies, you can do so using the following commands:

```bash
sudo apt update
sudo apt install --yes qemu-system-x86 cloud-image-utils
```

### Step 2: Download the Cloud Image

Download the latest Ubuntu server cloud image. A list of available images can be found on the [Ubuntu Cloud Images](https://cloud-images.ubuntu.com/) website. You want to download the `<codename>-server-cloudimg-amd64.img` file, which is a QEMU QCOW2 image. For this example, we will use the Ubuntu 24.04 server cloud image, but you can use any other version available.

```bash
curl -O https://cloud-images.ubuntu.com/noble/current/noble-server-cloudimg-amd64.img
```

### Step 3: Create a Seed Image for Cloud-Init

To configure the network, storage, and users, you need to create a seed image that contains the necessary cloud-init data.

When instances are launched in a cloud deployment  [cloud-init](https://cloudinit.readthedocs.io/en/latest/)  will search for a datasource to retrieve instance metadata. This data is used to determine what users to create, set a hostname, networking configuration, and many other possible configuration settings. Cloud images will take in two types of data:

- **metadata**: unique configuration data provided by the cloud platform. The values of this data vary depending on the cloud provider. It can include a hostname, networking information, SSH keys, etc.
- **user data**: provided directly by the user to configure the system. This data is simple as a shell script to execute or include  [cloud-config](https://cloudinit.readthedocs.io/en/latest/topics/modules.html)  data that the user can specify settings in a human-friendly format.

In the case of launching a local QEMU image, we need to provide a local datasource for the cloud image to read from. From this datasource, the instance can read both the metadata and/or user data to configure the system.

#### Generate an SSH Key Pair

If you haven't already generated an SSH key pair, you can do so using the `ssh-keygen` command. Here’s how to generate a new RSA key pair:

```bash
ssh-keygen -t rsa -C "your_email@example.com" -f ./my-ssh-key
```

When prompted, press enter to leave the passphrase blank. 

*Example:*

```bash
$ ssh-keygen -t rsa -C "your_email@example.com" -f ./my-ssh-key
Generating public/private rsa key pair.
Enter passphrase (empty for no passphrase):
Enter same passphrase again:
Your identification has been saved in ./my-ssh-key
Your public key has been saved in ./my-ssh-key.pub
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
$ ls -1 my-ssh-key*
my-ssh-key             // Private Key
my-ssh-key.pub         // Public Key
```

#### Create User Data

Create a `user-data.yaml` file with your desired user configuration. Here is an example of creating a local user called `ubuntu` with sudo permissions using the SSH key and a password (`mypassword`):

```bash
cat > user-data.yaml <<EOF
#cloud-config
ssh_pwauth: True
chpasswd:
  expire: false
  users:
  - {name: ubuntu, password: mypassword, type: text}
users:
  - name: ubuntu
    groups: users, sudo
    shell: /usr/bin/bash
    ssh_authorized_keys:
      - ssh-rsa AAAAB3Nz... # Paste Your SSH Public Key Here
EOF
```

Replace the SSH key with the one you generated. Copy and paste the output from `cat my-ssh-key.pub` into the `ssh_authorized_keys:` section of the `user-data.yaml` file.

For the full list of cloud-config options checkout the [cloud-init docs](https://cloudinit.readthedocs.io/en/latest/topics/modules.html).

#### Configure Network Settings (Optional)

By default, cloud-init configures a DHCP client on the instance's `eth0` interface. Here are the key points:

- **DHCP Configuration**: The instance will use DHCP to obtain an IP address, subnet mask, and default gateway for the `eth0` interface
- **No Custom Network Settings**: Without a custom `network-config` section, the network settings will not be overridden, and the default DHCP configuration will be applied.
- **Files Generated**: Cloud-init will generate the necessary network configuration files based on the default settings. For example, on Ubuntu systems using Netplan, the file `/etc/netplan/50-cloud-init.yaml` will be created with the default DHCP configuration

To configure the network settings, you need to create a `network-config.yaml` file.

*Example 1:* Here is an example for a static IP configuration:

```bash
version: 2
ethernets:
  enp1s0:
    dhcp4: no
    addresses: [192.168.122.146/24]
    nameservers:
      addresses: [192.168.122.1]
    routes:
      - to: 0.0.0.0/0
        via: 192.168.122.1
```

*Example 2:* Here is an example for using DHCP and DNS

```bash
version: 2
ethernets:
  eth0:
    dhcp4: true
    dhcp6: true
    nameservers:
      addresses:
        - 8.8.8.8
        - 8.8.4.4
        - 2001:4860:4860::8888
        - 2001:4860:4860::8844
```

#### Create Metadata (Optional)

If you need to specify additional metadata, such as the instance ID or hostname, create a `meta-data.yaml` file:

```bash
echo "instance-id: $(uuidgen || echo i-abcdefg)" > meta-data.yaml
echo "local-hostname: cxl01" >> meta-data.yaml
```

### Step 4: Create the Seed Image

Use the `cloud-localds` command to create the seed image:

```bash
cloud-localds my-seed.img user-data.yaml meta-data.yaml
```

If you created a `network-config.yaml` file, create the seed image using:

```bash
cloud-localds --network-config=network-config.yaml seed.img user-data.yaml
```

### Step 5: Launch the Cloud Image with QEMU

Now, you can launch the cloud image using QEMU with the configured seed image and network settings.

```bash
qemu-system-x86_64 \
  -cpu host \
  -machine type=q35,accel=kvm \
  -m 2048 \
  -nographic \
  -snapshot \
  -netdev id=net00,type=user,hostfwd=tcp::2222-:22 \
  -device virtio-net-pci,netdev=net00 \
  -drive if=virtio,format=qcow2,file=noble-server-cloudimg-amd64.img \
  -drive if=virtio,format=raw,file=my-seed.img
```

### Step 6: Access the Virtual Machine

You can access the virtual machine via the serial console or by SSH. Here is how to SSH into the VM using the SSH keys generated previously:

```bash
ssh -o "StrictHostKeyChecking no" -i ~/my-ssh-key ubuntu@localhost -p 2222
```

### Summary

Congratulation! All being well, you should now have access to your QEMU Guest Virtual Machine. 

QEMU is feature packed. You should take a few minutes to familiarise yourself with the [qemu-system-x86 man page](https://www.qemu.org/docs/master/system/qemu-manpage.html) to understand all the available options and features.
