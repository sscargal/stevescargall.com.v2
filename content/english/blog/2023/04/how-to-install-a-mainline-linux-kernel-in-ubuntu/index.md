---
title: How To Install a Mainline Linux Kernel in Ubuntu
date: 2023-04-21T00:20:10Z
draft: false
author: Steve Scargall
tags:
  - ubuntu
  - linux
  - kernel
  - mainline
categories:
  - linux
  - how to
image: "images/_6bd5d195-ab4b-44d7-b628-49ce6aa7ca59-min.jpeg"
author: Steve Scargall
---

By default, Ubuntu systems run with the Ubuntu kernels provided by the Ubuntu repositories. To get unmodified upstream kernels that have new features or to confirm that upstream has fixed a specific issue, we often need to install the mainline Kernel. The mainline kernel is the most recent version of the Linux kernel released by the Linux Kernel Organization. It undergoes several stages of development, including merge windows, release candidates, and final releases. Mainline kernels are designed to offer the latest features and improvements, making them attractive to developers and power users. [Kernel.org](https://www.kernel.org/) lists the available Kernel versions. 

To install the mainline kernel, we need a package called [mainline](https://github.com/bkw777/mainline?ref=learnubuntu.com) available from the cappelikan personal package archive (PPA). To add PPA for the mainline package, use the following command:

```
sudo add-apt-repository ppa:cappelikan/ppa
```

Run the following commands to update the repository and install the mainline utility:

```
sudo apt update
sudo apt install mainline
```

Once installed, we can check the available latest mainline and the point release using the following command:

```
mainline --check
```

For example, the latest stable kernel at the time of writing this article was 6.2.12.

```
$ sudo mainline --check
mainline 1.2.5
Distribution: Ubuntu 22.04.2 LTS
Architecture: amd64
Running kernel: 5.15.0-43-generic
Updating from: 'https://kernel.ubuntu.com/~kernel-ppa/mainline/'
OK
Fetching individual kernel indexes...
Found installed : 5.15.0-43.46
Latest update: 6.2.12
Latest point update: 5.15.108
----------------------------------------------------------------------
```

If you want the very latest unstable mainline, add `--include-unstable` to the command, eg:

```
# mainline --check --include-unstable
mainline 1.2.5
Distribution: Ubuntu 22.04.2 LTS
Architecture: amd64
Running kernel: 5.15.0-43-generic
Updating from: 'https://kernel.ubuntu.com/~kernel-ppa/mainline/'
OK
Fetching individual kernel indexes...
Found installed : 5.15.0-43.46
Latest update: 6.3.0-rc7
Latest point update: 5.15.108
----------------------------------------------------------------------
```

We see Kernel 6.3.0-rc7 is available. 

### Installing the latest mainline kernel

To install the latest stable kernel (6.2.12 in our example), all you have to do is run the following command:
```
$ sudo mainline --install-latest
```

To install the latest point Kernel (5.15.0-43.46), run the following command:
```
$ sudo mainline --install-point
```

To install the latest unstable Kernel (6.3.0-rc7), run the following command:
```
$ sudo mainline --install 6.3.0-rc7
```

For more information and options run `mainline --help`
```
$ mainline --help
mainline 1.2.5
Distribution: Ubuntu 22.04.2 LTS
Architecture: amd64
Running kernel: 5.15.0-43-generic
  
mainline 1.2.5 - Ubuntu Mainline Kernel Installer
  
Syntax: mainline <command> [options]
  
Commands:
  
--check Check for kernel updates
--notify  Check for kernel updates and notify current user
--list  List all available mainline kernels
--list-installed  List installed kernels
--install-latest  Install latest mainline kernel
--install-point Install latest point update for current series
--install <name>  Install specified mainline kernel(1)(3)
--uninstall <name>  Uninstall specified kernel(1)(2)(3)
--uninstall-old Uninstall all but the highest installed version(3)
--download <name> Download specified kernels(2)
--delete-cache  Delete cached info about available kernels
  
Options:
  
--include-unstable  Include unstable and RC releases
--exclude-unstable  Exclude unstable and RC releases
--debug Enable verbose debugging output
--yes Assume Yes for all prompts (non-interactive mode)
  
Notes:
(1) A version string taken from the output of --list
(2) One or more, comma-seperated
(3) The currently running kernel will always be ignored
```

Once the Kernel is installed, reboot

```
$ sudo systemctl reboot
```

When the system boots, verify the new Kernel is loaded

```
$ uname -r
6.3.0-060300rc7-generic
```

Enjoy
