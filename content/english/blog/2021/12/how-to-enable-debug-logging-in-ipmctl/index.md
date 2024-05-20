---
title: "How To Enable Debug Logging in ipmctl"
date: "2021-12-05"
categories: 
  - "how-to"
  - "linux"
  - "troubleshooting"
tags: 
  - "debugging"
  - "ipmctl"
  - "nvdimm"
  - "optane"
  - "persistent-memory"
  - "pmem"
image: "images/pexels-photo-577585.jpeg"
author: Steve Scargall
aliases:
  - /blog/2021/12/05/how-to-enable-debug-logging-in-ipmctl/
---

The [ipmctl](https://github.com/intel/ipmctl) utility is used for configuring and managing Intel Optane Persistent Memory modules (DCPMM/PMem). It supports the functionality to:

- Discover Persistent Memory on the server
- Provision the persistent memory configuration
- View and update the firmware on the persistent memory modules
- Configure data-at-rest security
- Track health and performance of the persistent memory modules
- Debug and troubleshoot persistent memory modules

I wrote the [IPMCTL User Guide](https://docs.pmem.io/ipmctl-user-guide/) showing how to use the tool, but what if ipmctl returns an error or something you're not expecting? How do you debug the debugger? On Linux, ipmctl relies on libndctl to help perform communication to the BIOS and persistent memory modules themselves. This is a complicated stack involving multiple kernel drivers and the physical hardware itself. Anything along this path could be causing a problem.

While we could use tools such as strace, ltrace, bpftrace, gdb, etc, ipmctl actually has a nifty feature to record a lot of debug information that can be very helpful to understand where ipmctl is failing. The DBG\_LOG\_LEVEL option defines how much data ipmctl will log. The logs pertain to the operation of the ipmctl command-line tool only and do not reflect any logging functionality of the persistent memory or kernel itself. The available log levels are:

0: Logging is disabled. This is the default.  
1: Log Errors.  
2: Log Warnings, Errors.  
3: Log Informational, Warnings, Errors.  
4: Log Verbose, Informational, Warnings, Errors.

The default log file location on Linux is `/var/log/ipmctl/debug.log` and is defined by DBG\_LOG\_FILE\_NAME.

## Enabling ipmctl debugging

To enable the feature, first check to see what log level is currently in-use. The following shows the default log level is 0 (zero):

```bash
# ipmctl show -preferences

CLI_DEFAULT_DIMM_ID=HANDLE
CLI_DEFAULT_SIZE=GiB
APPDIRECT_SETTINGS=RECOMMENDED
APPDIRECT_GRANULARITY=RECOMMENDED
DBG_LOG_LEVEL=0
```

Set the log level using:

```bash
# ipmctl set -preferences DBG_LOG_LEVEL=4

Set DBG_LOG_LEVEL=4: Success
```

Run an ipmctl command, eg:

```bash
# ipmctl show -dimm

 DimmID | Capacity  | HealthState | ActionRequired | LockState | FWVersion
==============================================================================
 0x0011 | 252.5 GiB | Healthy     | 0              | Disabled  | 01.02.00.5417
 0x0021 | 252.5 GiB | Healthy     | 0              | Disabled  | 01.02.00.5417
 0x0001 | 252.5 GiB | Healthy     | 0              | Disabled  | 01.02.00.5417
 0x0111 | 252.5 GiB | Healthy     | 0              | Disabled  | 01.02.00.5417
 0x0121 | 252.5 GiB | Healthy     | 0              | Disabled  | 01.02.00.5417
 0x0101 | 252.5 GiB | Healthy     | 0              | Disabled  | 01.02.00.5417
 0x1011 | 252.5 GiB | Healthy     | 0              | Disabled  | 01.02.00.5417
 0x1021 | 252.5 GiB | Healthy     | 0              | Disabled  | 01.02.00.5417
 0x1001 | 252.5 GiB | Healthy     | 0              | Disabled  | 01.02.00.5417
 0x1111 | 252.5 GiB | Healthy     | 0              | Disabled  | 01.02.00.5417
 0x1121 | 252.5 GiB | Healthy     | 0              | Disabled  | 01.02.00.5417
 0x1101 | 252.5 GiB | Healthy     | 0              | Disabled  | 01.02.00.5417
```

Check the log file located in `/var/log/ipmctl/debug.log`:

```bash
# head -12 /var/log/ipmctl/debug.log
05/29/2020 21:52:55 	1	Debug	0	>00300020<	NVDIMM-DBG:PbrOs.c::PbrDeserializeCtx:196: PBR MODE from shared memory: 0  
05/29/2020 21:52:55 	2	Debug	0	>00300020<	NVDIMM-DBG:PbrOs.c::PbrDeserializeCtx:204: pbr_ctx.tmp not found, setting to default value  
05/29/2020 21:52:55 	3	Debug	0	>00300020<	NVDIMM-DBG:Pbr.c::PbrInit:858: PbrInit PBR MODE: 0  
05/29/2020 21:52:55 	4	Debug	0	>00300020<	NVDIMM-DBG:Pbr.c::PbrInit:859: PbrInit DONE  
05/29/2020 21:52:55 	5	Debug	0	>00300020<	NvmDimmDriverDriverEntryPoint=0x8342bf00 
05/29/2020 21:52:55 	6	Debug	0	>00300020<	NVDIMM-DBG:NvmDimmDriver.c::NvmDimmDriverDriverEntryPoint:866: Exiting DriverEntryPoint, error = 0x0. 
05/29/2020 21:52:55 	7	Debug	0	>00300020<	NvmDimmCliEntryPoint=0x00007f51833aee90 
05/29/2020 21:52:55 	8	Debug	0	>00300020<	NVDIMM-DBG:Dimm.c::InitializeDimm:4958: Unable to initialize Intel NVM Dimm with custom GUID. Trying NVDIMM control region GUID 
05/29/2020 21:52:55 	9	Debug	0	>00300020<	NVDIMM-DBG:Dimm.c::InitializeDimm:5016: No region found using custom GUID. Trying NVDIMM control region GUID 
05/29/2020 21:52:55 	10	Debug	0	>00300020<	NVDIMM-DBG:Dimm.c::FwCmdIdDimm:1745: Error detected when sending PtIdentifyDimm command (RC = 0x7) 
05/29/2020 21:52:55 	11	Debug	0	>00300020<	NVDIMM-DBG:Dimm.c::InitializeDimm:5068: FW CMD Error: 7 
05/29/2020 21:52:55 	12	Debug	0	>00300020<	NVDIMM-WARN:Dimm.c::InitializeDimmInventory:1269: Unable to initialize NVDIMM 0x28 
```

In ipmctl version 2.x, you can dump the data to the terminal and record it using `tee`, eg:

```bash
ipmctl create -v -goal persistentmemorytype=appdirect | tee -a /var/log/ipmctl/debug.log
```

Now you can review the [ipmctl code](https://github.com/intel/ipmctl) to get an idea for what's going on and where the issue might be.

## Enhancing the Preferences Usability

I filed an enhancement request to improve the user experience. See [https://github.com/intel/ipmctl/issues/105](https://github.com/intel/ipmctl/issues/105) for more information.

## Reproducing ipmctl issues

In ipmctl v2.x, a new playback and record (PBR) feature was added. This is probably only useful to Intel or server OEM/ODM engineering that have access to proprietary information and tools, but it is possible to record the operations issued by ipmctl to the hardware for more in-depth investigations.

The Playback and Record (PBR) is a capability included to enable efficient reproduction and debug of issues a user may encounter. The capability is designed to capture the current state of the platform as it relates to PMem modules, and all interactions with the PMem module firmware. This data can then be stored in a file and sent to the development team for rapid reproduction and debug.

The PBR file contains the following:  
• ACPI tables: NFIT, PCAT and PMTT  
• SMBIOS tables  
• Raw firmware command response data

### Theory of operation: Recording

1. Start a recording session (start -session).
2. Execute all commands to be included in session.
3. Save the recording to a file (dump -session).
4. Stop the recording session (stop -session).
5. Send PBR files to support personnel for analysis.

### Example:

```bash
// Start recording the ipmctl commands
# ipmctl start -session -mode record 
 
// Execute your ipmctl command(s) here>
// Example: ipmctl create -goal MemoryMode=50 

// Save the recording to a file called 'myrecording.pbr' 
# ipmctl dump -destination /tmp/ipmctl_create_goal_appdirect_recording.pbr -session 

// Stop the recording
# ipmctl stop -session 
```

Example:

```bash
# ipmctl start -session -mode record
Setting to record mode.

# ipmctl create -goal PersistentMemoryType=AppDirect
Warning - Executing in recording mode!

The following configuration will be applied:
 SocketID | DimmID | MemorySize | AppDirect1Size | AppDirect2Size
==================================================================
 0x0000   | 0x0001 | 0.000 GiB  | 252.000 GiB    | 0.000 GiB
 0x0000   | 0x0011 | 0.000 GiB  | 252.000 GiB    | 0.000 GiB
 0x0000   | 0x0021 | 0.000 GiB  | 252.000 GiB    | 0.000 GiB
 0x0000   | 0x0101 | 0.000 GiB  | 252.000 GiB    | 0.000 GiB
 0x0000   | 0x0111 | 0.000 GiB  | 252.000 GiB    | 0.000 GiB
 0x0000   | 0x0121 | 0.000 GiB  | 252.000 GiB    | 0.000 GiB
 0x0001   | 0x1001 | 0.000 GiB  | 252.000 GiB    | 0.000 GiB
 0x0001   | 0x1011 | 0.000 GiB  | 252.000 GiB    | 0.000 GiB
 0x0001   | 0x1021 | 0.000 GiB  | 252.000 GiB    | 0.000 GiB
 0x0001   | 0x1101 | 0.000 GiB  | 252.000 GiB    | 0.000 GiB
 0x0001   | 0x1111 | 0.000 GiB  | 252.000 GiB    | 0.000 GiB
 0x0001   | 0x1121 | 0.000 GiB  | 252.000 GiB    | 0.000 GiB
Do you want to continue? [y/n] y
Created following region configuration goal
 SocketID | DimmID | MemorySize | AppDirect1Size | AppDirect2Size
==================================================================
 0x0000   | 0x0001 | 0.000 GiB  | 252.000 GiB    | 0.000 GiB
 0x0000   | 0x0011 | 0.000 GiB  | 252.000 GiB    | 0.000 GiB
 0x0000   | 0x0021 | 0.000 GiB  | 252.000 GiB    | 0.000 GiB
 0x0000   | 0x0101 | 0.000 GiB  | 252.000 GiB    | 0.000 GiB
 0x0000   | 0x0111 | 0.000 GiB  | 252.000 GiB    | 0.000 GiB
 0x0000   | 0x0121 | 0.000 GiB  | 252.000 GiB    | 0.000 GiB
 0x0001   | 0x1001 | 0.000 GiB  | 252.000 GiB    | 0.000 GiB
 0x0001   | 0x1011 | 0.000 GiB  | 252.000 GiB    | 0.000 GiB
 0x0001   | 0x1021 | 0.000 GiB  | 252.000 GiB    | 0.000 GiB
 0x0001   | 0x1101 | 0.000 GiB  | 252.000 GiB    | 0.000 GiB
 0x0001   | 0x1111 | 0.000 GiB  | 252.000 GiB    | 0.000 GiB
 0x0001   | 0x1121 | 0.000 GiB  | 252.000 GiB    | 0.000 GiB
A reboot is required to process new memory allocation goals.

# ipmctl dump -destination /tmp/ipmctl_create_goal_appdirect_recording.pbr -session
Warning - Executing in recording mode!

Successfully dumped 285340 bytes to file.

# ipmctl stop -session
Warning - Executing in recording mode!

Stopping a session will free all recording content.
Do you want to continue? [y/n] y
Stopped PBR session.

# ls -l /tmp/ipmctl_create_goal_appdirect_recording.pbr
-rw-r--r--. 1 root root 285340 Jun  1 08:50 /tmp/ipmctl_create_goal_appdirect_recording.pbr
```
