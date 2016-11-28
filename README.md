1. OVERVIEW
-----------

    This repository contains scripts and API's for the Linux contineous integration
    framework for build, boot, and testing of linux git tree, the script takes any linux
    kernel git tree, perform a build, boot to the new kernel and run the tests.

2. OPERATING SYSTEM SUPPORT
---------------------------

    *Running this scripts against unsupported Host may result in multiple test failures -
        proceed at your own risk.

    The repository can be cloned on machine installed with linux operating system such as:
        - Fedora
        - Ubuntu
        - Centos

3. PREREQUISITES
----------------

    * Target build machine should be installed with any of the following operating system
        - Fedora
        - Ubuntu
        - Centos
    * Basic packages like, git, telnet, rpm should be installed
    * software package repositories should be set properly.


4. "run_test.py" Main Script:
----------------------------

    This is a main wrapper for triggering build kernel testing. It prepares the system, start kernel compile,
    build and boot the specified kernel and gets back the results of the tests specified in the system.

    usage:
        run_test.py [-h] [--ipmi IPMI] [--hmc HMC] [--host HOST] [--args ARGS]
                    [--tests TESTS] [--list LIST] [--disk DISK] [--bso BSO] [--id ID]
                    [--config CONFIG] [--patch PATCH] [--avtest AVTEST]

    optional arguments:
        -h, --help       show this help message and exit

        --ipmi IPMI      Specify the FSP/BMC ip,username and password Usage:
                         --ipmi 'ip=fsp_ip,username=,password=password'

        --hmc HMC        Specify the HMC ip, username, password, server_name in HMC, lpar_name in HMC Usage: 
                         --hmc 'ip=hmc_ip,username=hmc_username,password=hmc_password,server=server_name,lpar=lpar'

        --host HOST      Specify the machine ip, linux username and linux password Usage:
                         --host  'hostname=hostname,username=username,password=password'

        --args ARGS      Specify the kernel git tree and kernel git branch Usage:
                         --args 'host_kernel_git=git_link,host_kernel_branch=branch

        --tests TESTS    Specify the tests to perform in Usage:
                         --tests 'test_name1,test_name2,test_name3'

        --list LIST      lists the tests available to run Usage:
                         --list autotest or --list avocado

        --disk DISK      Specify the boot partition disk by-id Usage:
                         --disk scsi-35000039348114000-part2

        --bso BSO        [OPTIONAL] Specify the bso auth and password Usage:
                         --bso 'username=abc@xx.xxx.com,password=password'

        --id ID          [OPTIONAL] Specify the SID for CI run Usage:
                         Usage: --id sid

        --config CONFIG  [OPTIONAL] Specify the path of config file or config option like 
                         'make pseries_le_deconfig' or if no config specifed the default base config will be used  Usage:
                         --config '/pathto/configfile-name' OR --config 'make pseries_le_deconfig'

        --patch PATCH    [OPTIONAL] Specify the path to patch file Usage:
                         --patch  '/pathto/patchfile-name'

        --avtest AVTEST  [OPTIONAL] Specify the tests to perform in avocado Usage:
                         --tests cpu, generic, io

5. How to Run ?
---------------
- Clone the linuxci repository $ git clone https://github.com/linuxci/linuxci.git

- cd linuxci

- Run the command line tool run_test.py

FSP/BMC managed system [Power Baremetal]
---------------------------------------
python run_test.py
	--ipmi 'ip=FSP/BMC_IP,username=FSP/BMC_username,password=FSP/BMC_password'
	--host 'hostname=host_ip,username=root,password=password'
	--args 'host_kernel_git="git://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git",host_kernel_branch=master'
        --tests 'em_performance,em_cpuidle,ltp -f fs,sanity_em,rcutorture,dbench'
	--disk scsi-1IBM_IPR-0_6DC7570000000020-part2
	--bso 'username=abc@in.x.com,password=password'
        --config 'linuxci/config-3.19.0-12-generic'
        --patch 'linuxci/xyz.patch'


HMC managed systen [PowerVM LPAR]
---------------------------------
python run_test.py
	--hmc 'ip=9.xx.xx.xxx,username=hmc_username,password=hmcpassword,server=server_name_in_hmc,lpar=lparname_in_hmc'
        --host 'hostname=host_ip,username=root,password=password'
	--args 'host_kernel_git=git://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git,host_kernel_branch=master'
	--tests 'sleeptest,ltp -f mm,dbench'
	--disk U8286.42A.1069B3T-V3-C12-T1-L8100000000000000
	--bso 'username=xyz@in.x.com,password=password'
	--config 'linuxci/configfilename'
	--patch 'linuxci/abc.patch'

6. RESULTS
----------

The results are copied to a folder 'linuxci/results/kernelOrg_timestamp'

7. ISSUES & CONTRIBUITIONS
--------------------------

To make any changes to the code, please follow normal Open source guidlines. however:

If you want to contribute to the framework, please open a new issue including
the below information to help make it as useful as possible.

    Label the issue as a "Enhancement/Documentation"
    Feature Description
    functionality affected
    Workaround(if any)

If you find an issue while using the framework, please open a new issue including
the below information to help make it as useful as possible. We will help with
certain sections as the issue gets investigated and resolved:

    Label the issue as a "bug"
    Issue / Limitation Description
    Reason / Root Cause for Failure(if known)
    functionality affected
    Workaround(if any)

Once a "bug" issue is resolved or is classified as a limitation, we will provide
the following new or updated information where possible:

    Reason / Root Cause for Failure
    Workaround(if any)
    Resolution action

If you have a question to help clarify the use of the CI framework, please open a
new issue including the below information to help make it as useful as possible:

    Label the issue as a "question"
    State your question
    Provide any supporting links, code sections / references, etc.
    possible to help explain your question.
