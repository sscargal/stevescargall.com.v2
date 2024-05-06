---
title: "How to Create a Bootable Windows USB in Fedora Linux"
date: "2019-05-21"
categories: 
  - "how-to"
tags: 
  - "bootable-usb"
  - "fedora"
  - "kvm"
  - "qemu"
  - "server"
  - "window"
image: "images/Windows-Linux-USB.png"
---

In this tutorial, I am going to show you how to create a Windows Server 2019 bootable USB in Linux, though any Windows version will work. I am using Fedora 30 for this tutorial but the steps should be valid for other Linux distributions as well.

Here’s what you need:

- Windows Server 2019 ISO (or Windows 10 ISO)

- WoeUSB Application

- A USB key (pen drive or stick) with at least 6 Gb of space

## Step 1: Download Windows 10 ISO

Go to the Microsoft website and download the Windows ISO from the links provided:

- Windows 7 - [https://www.microsoft.com/en-us/software-download/windows7](https://www.microsoft.com/en-us/software-download/windows7)

- Windows 8.1 - [https://www.microsoft.com/en-us/software-download/windows8](https://www.microsoft.com/en-us/software-download/windows8)

- Windows 10 - [https://www.microsoft.com/en-us/software-download/windows10](https://www.microsoft.com/en-us/software-download/windows10)

- Windows Server 2019 (Evaluation) - [https://www.microsoft.com/en-us/evalcenter/evaluate-windows-server-2019](https://www.microsoft.com/en-us/evalcenter/evaluate-windows-server-2019)

- Windows Server 2019 Essentials - [https://www.microsoft.com/en-us/evalcenter/evaluate-windows-server-2019-essentials](https://www.microsoft.com/en-us/evalcenter/evaluate-windows-server-2019-essentials)

- Windows Server 2019 Hyper-V - [https://www.microsoft.com/en-us/evalcenter/evaluate-hyper-v-server-2019](https://www.microsoft.com/en-us/evalcenter/evaluate-hyper-v-server-2019)

## Step 2: Install WoeUSB

[WoeUSB](https://github.com/slacka/WoeUSB) is a free and open source application for creating Windows 10 bootable USB. This package contains two programs:

- **woeusb**: A command-line utility that enables you to create your own bootable Windows installation USB storage device from an existing Windows Installation disc or disk image

- **woeusbgui**: A GUI wrapper of woeusb based on WxWidgets

Install WoeUSB using the Fedora package repository:

```
$ sudo dnf install WoeUSB
```

## Step 3: Using WoeUSB to create bootable Windows USB device

I'll use the `woeusb` command line rather than the `woeusbgui` since I'm using a remote linux server without the desktop. Since the size of the ISO is larger than the default FAT32 can handle, we need to specify NTFS file systems. Additionally, we will erase and use the entire capacity of the USB key (/dev/sde), then write the contents of the ISO (17763.379.190312-0539.rs5\_release\_svc\_refresh\_SERVER\_EVAL\_x64FRE\_en-us.iso) to it.

> WARNING! All data on the USB key will be erased

```
$ sudo woeusb --target-filesystem NTFS --device 17763.379.190312-0539.rs5_release_svc_refresh_SERVER_EVAL_x64FRE_en-us.iso /dev/sde
```

Output:

```
WoeUSB v3.2.12
==============================
Mounting source filesystem...
Wiping all existing partition table and filesystem signatures in /dev/sde...
/dev/sde: 2 bytes were erased at offset 0x000001fe (dos): 55 aa
/dev/sde: calling ioctl to re-read partition table: Success
Ensure that /dev/sde is really wiped...
Creating new partition table on /dev/sde...
Creating target partition...
Making system realize that partition table has changed...
Wait 3 seconds for block device nodes to populate...
Cluster size has been automatically set to 4096 bytes.
Creating NTFS volume structures.
mkntfs completed successfully. Have a nice day.
--2019-05-20 13:59:11-- https://github.com/pbatard/rufus/raw/master/res/uefi/uefi-ntfs.img
Location: https://raw.githubusercontent.com/pbatard/rufus/master/res/uefi/uefi-ntfs.img [following]
--2019-05-20 13:59:12-- https://raw.githubusercontent.com/pbatard/rufus/master/res/uefi/uefi-ntfs.img
Length: 524288 (512K) [application/octet-stream]
Saving to: ‘/tmp/WoeUSB.Huv3Ym.tempdir/uefi-ntfs.img’

uefi-ntfs.img                    100%[========================================================>] 512.00K  1.48MB/s    in 0.3s

2019-05-20 13:59:12 (1.48 MB/s) - ‘/tmp/WoeUSB.Huv3Ym.tempdir/uefi-ntfs.img’ saved [524288/524288]

1024+0 records in
1024+0 records out
524288 bytes (524 kB, 512 KiB) copied, 0.0333775 s, 15.7 MB/s
Mounting target filesystem...
Applying workaround to prevent 64-bit systems with big primary memory from being unresponsive during copying files.
Copying files from source media...
Installing GRUB bootloader for legacy PC booting support...
Installing for i386-pc platform.
Installation finished. No error reported.
Installing custom GRUB config for legacy PC booting...
Resetting workaround to prevent 64-bit systems with big primary memory from being unresponsive during copying files.
Unmounting and removing "/media/woeusb_source_1558382344_4486"...
Unmounting and removing "/media/woeusb_target_1558382344_4486"...
You may now safely detach the target device
Done :)
The target device should be bootable now
```

## Step 4: \[Optional\] Verify the USB drive

It is a good idea to verify the USB drive is bootable before you reboot and find out so you don't loose that time.

We can test the USB device using QEMU. If you don't have QEMU/KVM installed, you can install the package group using:

```
$ sudo dnf install @virtualization
```

Now we can create a new temporary Guest Virtual Machine without network and disks. We simply provide the USB device as the boot device and supply some Memory. The following uses our USB device (/dev/sde):

```
$ qemu-system-x86_64 -hda /dev/sde -m 4G -machine pc,accel=kvm -enable-kvm -vnc :0 -daemonize
```

> **Note:** If you are connecting remotely to the Linux system, you may need to open the firewall to allow the remote VNC port(s). The default port for VNC is 5900 + the `-vnc :<port>`. In our example, we ask QEMU to use VNC port `:0` which maps to port 5900. VNC port `:1` maps to 5901, etc. The following opens a range of ports to allow you to connect up to 11 running VM Guests. Ideally, you should only open as many ports as you need.
> 
> $ sudo firewall-cmd --list-ports  
> $ sudo firewall-cmd --get-default-zone  
> FedoraServer  
> $ sudo firewall-cmd --state  
> running  
> $ sudo firewall-cmd --zone=FedoraServer --add-port=5900-5910/tcp --permanent  
> success  
> $ sudo firewall-cmd --reload  
> success  
> $ sudo systemctl restart firewalld

If the QEMU guest VM starts successfully, ie, you get no error from the `qemu-system-x86_64` command, you can connect to it using a local VNC Client on your desktop. Linux and Windows have several VNC clients to choose from. I use [VNC Viewer](https://www.realvnc.com/en/connect/download/viewer/) from [RealVNC](https://www.realvnc.com).

You should see the initial loading screen, then Windows Server 2019 will display the first installation window as shown below:

![Windows Server 2019 booted using QEMU/KVM](https://stevescargall.com/wp-content/uploads/2019/05/windows_server_2019_via_vncviewer_and_qemu-kvm-1.png?w=1016)

Windows Server 2019 booted using QEMU/KVM

## Step 5: Using the Windows bootable USB

Once the bootable USB is ready, restart your system. At boot time, press F6 to enter the boot manager. Select the USB device from the list.

Once you're through the initial loading screen, you’ll see that Windows gives you the option to install or repair your system. You know what to do now from here.
