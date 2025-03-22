---
title: "Building NDCTL Utilities from Source: A Comprehensive Guide"
meta_title: "How to Compile and Install NDCTL Tools on Linux"
description: "This article provides a step-by-step guide on how to build NDCTL utilities from source code, including prerequisites, compilation, and installation on Linux systems."
date: 2025-03-22T12:28:00Z
image: "featured_image.webp"
categories: ["Linux", "CXL", "PMEM"]
author: "Steve Scargall"
tags: ["NDCTL", "DAXCTL", "CXL", "Persistent Memory"]
draft: false
aliases:
---

**Building NDCTL with Meson on Ubuntu 24.04**  

The [NDCTL](https://github.com/pmem/ndctl) package includes the `cxl`, `daxctl`, and `ndctl` utilities. It uses the Meson build system for streamlined compilation. This guide reflects the modern build process for managing NVDIMMs, CXL, and PMEM on Ubuntu 24.04.

If you do not install a more recent Kernel than the one provided by the distro, then it is not recommended to compile these utilities from source code. If you have installed a mainline Kernel, then you will likely require a newer version of these utilities that are compatible with your Kernel. See the [NDCTL Releases](https://github.com/pmem/ndctl/releases) as the Kernel support information is provided there.

Here is the support matrix as of ndctl Version 81 and Kernel 6.14:

| NDCTL Version | Linux Kernel Version |
| :-- | :-- |
| v81 | 6.14 |
| v80 | 6.11 |
| v79 | 6.9 |
| v78 | 6.5 |
| v77 | 6.3 |
| v76.1 | 6.2 |
| v76 | 6.2 |
| v75 | 6.1 |
| v74.1 | 6.0 |
| v73 | 5.19 |
| v72.1 | 5.17 |

## **Prerequisites**

Use the following steps to install the prerequisite packages before we start the build and compile phase.

1. **System Update**:

    ```bash
    sudo  apt update && sudo apt upgrade -y
    ```

2. **Core Build Tools**:

    ```bash
    sudo  apt install -y git meson ninja-build pkg-config automake autoconf
    ```

3. **Libraries and Tools**:

    ```bash
    sudo  apt install -y  asciidoc asciidoctor ruby-asciidoctor xmlto libtool  libkmod-dev libsystemd-dev libudev0 libudev-dev uuid-dev libjson-c-dev libkeyutils-dev libinih-dev bash-completion keyutils libkeyutils-dev libiniparser-dev libtraceevent-dev libtracefs-dev
    ```

## **Step 1: Clone the Repository**

```bash
git clone https://github.com/pmem/ndctl.git && cd ndctl
```

## **Step 2: Configure with Meson**

Create a build directory and configure:

```bash
meson setup build
```

## **Step 3: Compile the Code**

Build using Ninja (Meson's backend):

```bash
meson compile -C build
```

## **Step 4: Install Binaries (Optional)**

```bash
sudo meson install -C build
```

If you choose not to install the binaries, the individual commands can be found in the `ndctl/build/<cmd>` directory, ie:

- **cxl**: ~/ndctl/build/cxl/cxl
- **ndctl**: ~/ndctl/build/ndctl/ndctl
- **daxctl**: ~/ndctl/build/daxctl/daxctl

## **Step 5: Verify Installation**

```bash
cxl --version
```

## **Troubleshooting**
  
**Build Errors**:

Should you encounter any issues during the configure or build processes, you clean and rebuild using `rm -rf build && meson setup build`.
