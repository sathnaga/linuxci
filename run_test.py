#!/usr/bin/env python

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
#
# See LICENSE for more details.
#
# Copyright: 2016 IBM
# Author: Abdul Haleem <abdhalee@linux.vnet.ibm.com>
#       : Harish <harisrir@linux.vnet.ibm.com>

import pexpect
import os
import time
import sys
import argparse
import re
import datetime
import commands
import logging
from lib import ipmi
from lib import hmc
from lib import bso_authenticator
from lib import common_lib as commonlib
from lib import scp_to_host as scplib

# basic required pkgs, without this the run fails
basepkg = ['git', 'telnet', 'rpm', 'python']
file_path = os.path.dirname(__file__)


def tear_down(obj, console):
    '''
    Clean host
    TODO: clear following
    1. hostCopy.tar.gz
    2. autotest
    3. avocado-fvt-wrapper
    4. patches
    '''
    logging.info('Cleaning Host')
    clean_list = ['hostCopy.tar.gz', 'autotest', 'avocado-fvt-wrapper',
                  'autotest-client-tests.patch', 'autotest.patch']
    for folder in clean_list:
        logging.info('Removing ' + folder)
        obj.run_cmd('rm -rf /root/' + folder, console)


def check_ls(obj, console, val):
    '''
    Checks if dirctory is created with ls
    '''
    flag = False
    contents = obj.run_cmd('ls', console)
    for line in contents:
        for folder in line.split():
            if folder == val:
                flag = True
                break
    return flag


def run_function(obj, console, host_details, git, tests, bso_details, sid, components, hmc=False):
    '''
    In PowerKVM or Power NV, Check for bso auth
    1. Clone the git.
    2. Do a kernel-build test
    3. Wait for login & Login
    4. Run --continue
    5. Return path of the html generated.
    '''
    # Check repository is set and check and install basic packages
    logging.info('\nCheck for package repository and install basic pkgs\n')
    release = commonlib.detect_distro(obj, console)
    logging.info(release)
    if 'None' in release:
        logging.info('\nERROR: Unsupported OS !!!')

    if any(re.findall(r'Red Hat|CentOS|Fedora', str(release))):
        status = obj.run_cmd(
            'yum repolist all > /dev/null 2>&1;echo $?', console)
        if status[-1] != '0':
            logging.info('\nERROR: Please set Package repository !!!')
            sys.exit(0)
        basepkg.append('openssh-clients')
        tool = 'yum install -y '

    elif 'Ubuntu' in release:
        status = obj.run_cmd(
            'apt-get update > /dev/null 2>&1;echo $?', console)
        if status[-1] != '0':
            logging.info('\nERROR: Please set Package repository !!!')
            sys.exit(0)
        basepkg.append('openssh-client')
        tool = 'apt-get install -y '

    elif 'SUSE' in release:
        status = obj.run_cmd('zypper repos > /dev/null 2>&1;echo $?', console)
        if status[-1] != '0':
            logging.info('\nERROR: Please set Package repository !!!')
            sys.exit(0)
        basepkg.append('openssh')
        tool = 'zypper install '

    for pkg in basepkg:
        if 'openssh' in pkg:
            cmd = 'which scp;echo $?'
        else:
            cmd = 'which %s;echo $?' % (pkg)
        status = obj.run_cmd(cmd, console)
        if status[-1] != '0':
            cmd = tool + pkg + ' > /dev/null 2>&1;echo $?'
            status = obj.run_cmd(cmd, console)
            if status[-1] != '0':
                logging.info('\nERROR: package %s could not install !!!')
                sys.exit(0)

    obj.bso_auth(console, bso_details['username'], bso_details['password'])
    result_path = None
    dummy_1 = obj.run_cmd('uname -r', console)
    dummy_2 = obj.run_cmd('cd', console)
    if check_ls(obj, console, 'avocado-fvt-wrapper'):
        deleted_folder = obj.run_cmd(
            'rm -rf avocado-fvt-wrapper', console)
    repo_result = obj.run_cmd(commonlib.avocado_repo, console)

    if not check_ls(obj, console, 'avocado-fvt-wrapper'):
        logging.error("\nProblem in cloning avocado repo")
        sys.exit(1)
    move_in = obj.run_cmd('cd avocado-fvt-wrapper', console)
    clean = obj.run_cmd(commonlib.avocado_clean, console)
    move_out = obj.run_cmd('cd /root/', console)

    logging.info('\nCloning autotest')
    if check_ls(obj, console, 'autotest'):
        deleted_folder = obj.run_cmd(
            'rm -rf autotest', console)
    result = obj.run_cmd(commonlib.clone_cmd, console)
    cur_path = obj.run_cmd('pwd', console)
    base_path = os.path.join(cur_path[-1], 'autotest')

    if not check_ls(obj, console, 'autotest'):
        logging.error("\nProblem in cloning autotest repo")
        tear_down(obj, console)
        sys.exit(1)
    else:
        obj.run_cmd('cd autotest; git apply /root/autotest.patch', console)
        obj.run_cmd(
            'cd client/tests; git apply /root/autotest-client-tests.patch', console)
        obj.run_cmd('cd', console)

    content_src = obj.run_cmd('ls /home/', console)
    for val in content_src:
        if 'linux_src' in val:
            deleted_src = obj.run_cmd('rm -rf /home/linux_src/', console)

    if sid:
        config_name = git['kernel_config'].rsplit('/', 1)[-1]
        git['kernel_config'] = config_name

    if tests:
        tests = "'" + tests + "'"
        build_cmd = './autotest/client/autotest-local ./autotest/client/tests/kernelorg/kernel-build.py --args "host_kernel=' + \
            git['host_kernel_git'] + ' host_kernel_branch=' + git['host_kernel_branch'] + \
            ' config_dir=' + git['kernel_config'] + ' patches=' + \
            git['patches'] + ' tests=' + tests + '"'
    else:
        build_cmd = './autotest/client/autotest-local ./autotest/client/tests/kernelorg/kernel-build.py --args "host_kernel=' + \
            git['host_kernel_git'] + ' host_kernel_branch=' + git['host_kernel_branch'] + \
            ' config_dir=' + git['kernel_config'] + \
            ' patches=' + git['patches'] + '"'

    build_result = obj.run_build(build_cmd, console)
    time.sleep(10)
    try:
        if build_result == 'build':
            return (None, None)
        elif build_result == 'kexec':
            login_result = obj.run_login(console)
            if login_result == 'Login':
                console.sendline(host_details['username'])
                if hmc:
                    console.send('\r')
                rc = console.expect(
                    [r'[Pp]assword:', pexpect.TIMEOUT], timeout=120)
                time.sleep(5)
                if rc == 0:
                    console.sendline(host_details['password'])
                    if hmc:
                        console.send('\r')
                else:
                    tear_down(obj, console)
                    sys.exit(1)
            elif login_result == 'Error':
                logging.error('Error before kexec...')
                tear_down(obj, console)
                sys.exit(1)
            else:
                console.expect(pexpect.TIMEOUT, timeout=30)
                logging.error('Error before logging in..')
                tear_down(obj, console)
                sys.exit(1)
        elif build_result == 'report':
            logging.error(' Error in kernel building')
            tear_down(obj, console)
            sys.exit(1)
        else:
            logging.error('Error before kexec')
            tear_down(obj, console)
            sys.exit(1)
    except pexpect.ExceptionPexpect, e:
        console.sendcontrol("c")
        console.expect(pexpect.TIMEOUT, timeout=60)
        logging.info("%s", console.before)

    rc = console.expect(['Last login:', 'incorrect'], timeout=300)
    time.sleep(5)
    if rc == 0:
        console.sendline('PS1=[pexpect]#')
        if hmc:
            console.send('\r')
        rc = console.expect_exact('[pexpect]#')
        if rc == 0:
            logging.info(' Shell prompt changed')
        else:
            tear_down(obj, console)
            sys.exit(1)
        logging.info("Enable kernel ftrace:")
        result = obj.run_cmd('sysctl -w kernel.ftrace_dump_on_oops=1', console)
        continue_result = obj.run_cmd(
            commonlib.continue_cmd, console, timeout=7200)
        if 'Report successfully' in continue_result[-1]:
            result_path = os.path.join(base_path, 'client/results/default')
        else:
            logging.error(' Error Creating HTML')

        if components:
            create_folder = obj.run_cmd(
                'mkdir -p /root/avocado-korg/', console)
            remove_results = obj.run_cmd(
                'rm -rf /root/avocado-korg/*', console)
            move_in = obj.run_cmd('cd avocado-fvt-wrapper', console)

            # TODO: parallel_run for each_component
            for component in components.split(','):
                obj.run_cmd('mkdir -p /root/avocado-korg/' +
                            component, console)
                test_result = obj.run_cmd(commonlib.avocado_test_run % (
                    component, component), console, timeout=1000)
        else:
            logging.info("No avocado opeartion")

    elif rc == 1:
        logging.error("Error in host credentials")
        tear_down(obj, console)
        sys.exit(1)

    if result_path:
        return (result_path, commonlib.avocado_result)
    else:
        return (None, commonlib.avocado_result)


def check_ipmi_details(details):
    if details['ip'] and details['password']:
        return True
    return False


def check_hmc_details(details):
    if details['ip'] and details['username'] and details['password'] and details['server'] and details['lpar']:
        return True
    return False


def check_host_details(details):
    if details['hostname'] and details['username'] and details['password']:
        return True
    return False


def scp_from_host(host_details, src_dir, dest_dir, files='*'):
    logging.info("SCPing the files")
    logging.info('scp -l 8192 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -r ' + host_details[
                 'username'] + '@' + host_details['hostname'] + ':' + src_dir + '/' + files + ' ' + dest_dir + '/')
    scp = pexpect.spawn('scp -l 8192 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -r ' + host_details['username'] + '@' + host_details[
                        'hostname'] + ':' + src_dir + '/' + files + ' ' + dest_dir + '/')
    res = scp.expect([r'[Pp]assword:', pexpect.EOF])
    if res == 0:
        scp.sendline(host_details['password'])
        logging.info("Copying the results")
        scp.logfile = sys.stdout
        wait = scp.expect([pexpect.EOF], timeout=500)
        if wait == 0:
            logging.info('Files successfully copied')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ipmi", action="store", dest="ipmi", help="Specify the FSP/BMC ip,username and password\
                        Usage: --ipmi 'ip=fsp_ip,username=,password=password'")
    parser.add_argument("--hmc", action="store", dest="hmc", help="Specify the HMC ip, username, password, server_name in HMC, lpar_name in HMC\
                        Usage: --hmc 'ip=hmc_ip,username=hmc_username,password=hmc_password,server=server_name,lpar=lpar'")
    parser.add_argument("--host", action="store", dest="host", help="Specify the machine ip, linux username and linux password\
                        Usage: --host 'hostname=hostname,username=username,password=password'")
    parser.add_argument("--args", action="store", dest="args",
                        help="Specify the kernel git tree and kernel git branch Usage: --args 'host_kernel_git=git_link,host_kernel_branch=branch'")
    parser.add_argument("--tests", action="store", dest="tests", help="Specify the tests to perform\
                        Usage: --tests 'test_name1,test_name2,test_name3'")
    parser.add_argument("--list", action="store", dest="list", help="lists the tests available to run\
                        Usage: --list autotest or --list avocado")
    parser.add_argument("--disk", action="store", dest="disk", help="Specify the boot partition disk by-id\
                        Usage: --disk scsi-35000039348114000-part2")
    parser.add_argument("--bso", action="store", dest="bso", help="Specify the bso auth and password\
                        Usage: --bso username=user1@x.abc.com,password=password")
    parser.add_argument("--id", action="store", dest="id", help="[Optional] Specify the SIDfor CI run\
                        Usage: --id sid")
    parser.add_argument("--config", action="store", dest="config", help="[Optional] Specify the path of config file or config\
                        option like 'make pseries_le_deconfig' or if no config specifed the default base config will be used\
                        Usage: --config '/pathto/configfile-name' or --config 'make pseries_le_deconfig'")
    parser.add_argument("--patch", action="store", dest="patch", help="[Optional] Specify the path to patch file\
                        Usage: --patch '/pathto/patchfile-name'")
    parser.add_argument("--avtest", action="store", dest="avtest", help="[Optional] Specify the tests to perform in avocado\
                        Usage: --tests cpu,generic,io")

    options = parser.parse_args()
    machine_type = None
    host_details = None
    git = None
    tests = None
    disk = None
    sid = None
    logging.basicConfig(
        format='\n%(asctime)s %(levelname)s  |  %(message)s', level=logging.DEBUG,  datefmt='%I:%M:%S %p')

    if options.list:
        list = options.list
        if 'autotest' in list:
            testfile = 'lib/tests.autotest'
        elif 'avocado' in list:
            testfile = 'lib/tests.avocado'
        try:
            with open(testfile, 'r') as tests:
                testlist = tests.readlines()
                for test in testlist:
                    print test.replace('\n', '')
        finally:
            print "\nUsage: python run_test.py --list autotest\nUsage:   --tests ltp \n\t --tests 'ltp,fio,dbench,fsfuzzer'"
            tests.close()
            sys.exit(0)

    if options.avtest:
        print "ERROR:  No avocado support!!!"
        print "\nUsage: python run_test.py --list autotest\n"
        sys.exit(0)

    if options.host:
        logging.info('%s', options.host)
        host_details = commonlib.get_keyvalue(options.host)
        if not check_host_details(host_details):
            logging.error('Provide necessary host details')
            sys.exit(1)
    else:
        logging.error('Provide host details')
        sys.exit(1)
    if options.bso:
        bso_details = commonlib.get_keyvalue(options.bso)
    else:
        logging.error('Specify bso details')
        sys.exit(1)

    if options.ipmi and options.hmc:
        logging.error('Specify only one type of arguement')
        sys.exit(1)
    elif options.ipmi:
        machine_type = 'Power KVM/NV'
        logging.error('Passing BSO for %s', host_details['hostname'])
        bso_authenticator.pass_bso(host_details['hostname'], user=bso_details[
                                   'username'], password=bso_details['password'])
    elif options.hmc:
        machine_type = 'Power VM'
    else:
        logging.error('Specify atleast one type of arguement')
        sys.exit(1)

    if options.disk:
        disk = options.disk
    else:
        logging.error("Disk not specified. Please specify a disk")
        sys.exit(1)

    if options.args:
        git = commonlib.get_keyvalue(options.args)
    else:
        logging.error("Provide git tree, branch")
        sys.exit(1)

    if options.tests:
        tests = options.tests
    else:
        logging.warning("Tests not specified. Performing kernel build only")

    if not options.avtest:
        logging.info("No avocado tests to perform")

    if not options.config:
        options.config = ''

    if not options.patch:
        options.patch = ''

    if options.id:
        sid = options.id
    base_path = os.path.dirname(os.path.abspath('__file__'))

    if machine_type == 'Power KVM/NV':
        # 1. Get ipmi console
        # 2. run function with IPMI object,console
        # 3. copy the results the consoles
        # 4. Close the console

        details = commonlib.get_keyvalue(options.ipmi)
        is_up = os.system('ping -c 1 ' + details['ip'])
        if not is_up == 0:
            logging.error('System is down !')
        else:
            if check_ipmi_details(details):
                if not details['username']:
                    details['username'] = ''
                ipmi_reb = ipmi.ipmi(
                    details['ip'], details['username'], details['password'])
                logging.info("REBOOTING THE MACHINE")
                console = ipmi_reb.getconsole()
                console_type = ipmi_reb.get_type(console)

                if console_type == 'timeout':
                    logging.info(
                        "Do a chassis power of-on to get system to normal state")
                    if ipmi_reb.status():
                        ipmi_reb.chassisOff()
                        while ipmi_reb.status():
                            logging.info("waiting for chassis OFF ...")
                            time.sleep(1)
                        time.sleep(60)
                        ipmi_reb.chassisOn()
                        time.sleep(60)
                        while not ipmi_reb.status():
                            logging.info("waiting for chassis ON ...")
                            time.sleep(1)
                        if not ipmi_reb.status():
                            sys.exit(0)
                    else:
                        ipmi_reb.chassisOn()
                        time.sleep(60)
                        while not ipmi_reb.status():
                            logging.info("waiting for chassis ON ...")
                            time.sleep(1)
                        if not ipmi_reb.status():
                            sys.exit(0)

                    time.sleep(10)
                    console = ipmi_reb.getconsole()
                    time.sleep(15)
                    console_type = ipmi_reb.get_type(console)

                if console_type == 'initramfs':
                    logging.info("Initramfs Shell")
                    console.sendline('reboot')
                    rc = console.expect(["Exit to shell"], timeout=1500)
                    if rc == 0:
                        logging.info('Exiting Shell')
                        console.sendline("\r")
                        rc1 = console.expect(
                            ["Exiting petitboot", "login:"], timeout=200)
                        if rc1 == 0:
                            logging.info("Continuing")
                        if rc1 == 1:
                            logging.info("Logging-in after initramfs")
                            ipmi_reb.login(console, host_details[
                                'username'], host_details['password'])
                    else:
                        logging.info("Console did not reach Petitboot")
                elif console_type == 'login':
                    logging.info("Logging into system")
                    ipmi_reb.login(console, host_details[
                                   'username'], host_details['password'])
                elif console_type == 'logged' or console_type == 'petitboot':
                    # Find the partition of installation on top of the disk
                    logging.info("System Logged in/Petitboot state")
                console.sendline("PS1=[pexpect]#")
                rc = console.expect_exact("[pexpect]#")
                if rc == 0:
                    logging.info("Shell prompt changed")
                else:
                    sys.exit(1)
                dummy_1 = ipmi_reb.run_cmd('cd', console)
                dummy_2 = ipmi_reb.run_cmd('cd', console)
                uuid_result = ipmi_reb.run_cmd(
                    'blkid /dev/disk/by-id/' + disk + '\r', console)
                if uuid_result[1] == '[pexpect]#':
                    logging.error(
                        "Disk ID not found. OS may not be installed in disk")
                    sys.exit(1)
                for uid in uuid_result:
                    UUID_match = re.search('UUID=(.*)', uid)
                    if UUID_match:
                        break
                if not UUID_match:
                    logging.error(
                        "UUID cannot be found of the boot partition")
                    sys.exit(1)
                UUID = UUID_match.group(1)
                UUID_list = re.findall('"([^"]*)"', UUID)
                logging.info('%s', UUID_list[0])
                console.sendline(
                    'nvram --update-config petitboot,bootdev=uuid:' + str(UUID_list[0]))
                console.sendline('nvram --update-config auto-boot?=true\r')
                time.sleep(5)
                console.sendline('reboot')
                pet_result = console.expect(
                    ['Petitboot', pexpect.TIMEOUT], timeout=3600)
                if pet_result == 1:
                    logging.error("System took more than 1 hour.. Exiting")
                    sys.exit(1)
                rc_reb = console.expect('login:', timeout=1500)
                if rc_reb == 0:
                    logging.info("Reboot successful.")
                ipmi_reb.closeconsole(console)

                logging.info("REBOOT COMPLETE")
                time.sleep(10)
                if options.id:
                    scplib.scp_id(options.id, host_details)
                else:
                    scplib.scp_manual(
                        options.config, options.patch, host_details)
                logging.info('Copying git patches')
                commonlib.scp_to_host('' + os.path.join(file_path, 'patches/autotest.patch') + ' ' + os.path.join(
                    file_path, 'patches/autotest-client-tests.patch'), host_details)
                logging.info("SCP COMPLETE")
                ipmi_obj = ipmi.ipmi(
                    details['ip'], details['username'], details['password'])
                con = ipmi_obj.getconsole()
                ipmi_obj.set_unique_prompt(
                    con, host_details['username'], host_details['password'])
                dummy_1 = ipmi_obj.run_cmd(' uname -r', con)
                home_dir = ipmi_obj.run_cmd('cd', con)
                result_dir, avocado_dir = run_function(
                    ipmi_obj, con, host_details, git, tests, bso_details, sid, options.avtest)
                if result_dir:
                    dest_dir = None
                    result_path = os.path.join(file_path, 'results')
                    if not os.path.exists(result_path):
                        os.makedirs(result_path)
                    dest_dir = os.path.join(
                        result_path, 'kernelOrg_' + datetime.datetime.now().strftime('%Y_%m_%d_%H_%M_%S'))
                    os.makedirs(dest_dir)
                    # Copying autotest results
                    scp_from_host(host_details, result_dir, dest_dir)
                    # Copying avocado results
                    if options.avtest:
                        dest_av = os.path.join(
                            result_path, 'kernelOrg_' + datetime.datetime.now().strftime('%Y_%m_%d_%H_%M_%S') + '_avocado')
                        os.makedirs(dest_av)
                        scp_from_host(host_details, avocado_dir, dest_av)
                        clean = ipmi_obj.run_cmd(commonlib.avocado_clean, con)
                    tear_down(mk, con)
                elif result_dir is None and avocado_dir is None:
                    logging.info(
                        'Kernel Building Complete. No Kernel Boot and Tests')
                    tear_down(ipmi_obj, con)
                elif result_dir is None:
                    logging.info('Exit ! Tests took more than 2 hours')
                    tear_down(ipmi_obj, con)
                else:
                    logging.error('Error with result generation')
                    tear_down(ipmi_obj, con)
                ipmi_obj.closeconsole(con)
            else:
                logging.error('Specify necessary details of IPMI')
    elif machine_type == 'Power VM':
        # 1. Get HMC console
        # 2. Get LPAR console
        # 3. Run function with HMC object, console
        # 4. Copy the results back
        # 5. Close the consoles

        details = commonlib.get_keyvalue(options.hmc)
        if not details['username']:
            details['username'] = ''

        reboot_obj = hmc.hmc(
            details['ip'], details['username'], details['password'])
        reboot_obj.login()
        logging.info(" REBOOTING MACHINE")
        reb_result = reboot_obj.reboot_step(
            disk, details['server'], details['lpar'])
        if reb_result == "Login":
            logging.info("SYSTEM REBOOTED")
            time.sleep(10)

        if options.id:
            scplib.scp_id(options.id, host_details)
        else:
            scplib.scp_manual(options.config, options.patch, host_details)
        logging.info('Copying git patches')
        commonlib.scp_to_host('' + os.path.join(file_path, 'patches/autotest.patch') + ' ' + os.path.join(
            file_path, 'patches/autotest-client-tests.patch'), host_details)
        logging.info("SCP COMPLETE")

        logging.info("Passing BSO for %s", host_details['hostname'])
        bso_authenticator.pass_bso(host_details['hostname'], user=bso_details[
                                   'username'], password=bso_details['password'])

        mk = hmc.hmc(details['ip'], details['username'], details['password'])
        is_up = os.system('ping -c 1 ' + details['ip'])
        if not is_up == 0:
            logging.info('System is down !')
        else:
            if check_hmc_details(details):
                logging.info('System is up !')
                mk.login()
                console = mk.get_lpar_console(details['username'], details['password'], details[
                                              'server'], details['lpar'], host_details['username'], host_details['password'])
                mk.set_unique_prompt(console)
                dummy_1 = mk.run_cmd(' uname -r', console)
                home_dir = mk.run_cmd('cd', console)

                result_dir, avocado_dir = run_function(
                    mk, console, host_details, git, tests, bso_details, sid, options.avtest, hmc=True)
                if result_dir:
                    dest_dir = None
                    result_path = os.path.join(file_path, 'results')
                    if not os.path.exists(result_path):
                        os.makedirs(result_path)
                    dest_dir = os.path.join(
                        result_path, 'kernelOrg_' + datetime.datetime.now().strftime('%Y_%m_%d_%H_%M_%S'))
                    os.makedirs(dest_dir)
                    # Copying autotest results
                    scp_from_host(host_details, result_dir, dest_dir)
                    # Copying avocado results
                    if options.avtest:
                        dest_av = os.path.join(
                            result_path, 'kernelOrg_' + datetime.datetime.now().strftime('%Y_%m_%d_%H_%M_%S') + '_avocado')
                        os.makedirs(dest_av)
                        scp_from_host(host_details, avocado_dir, dest_av)
                        clean = mk.run_cmd(commonlib.avocado_clean, console)
                    tear_down(mk, console)
                elif result_dir is None and avocado_dir is None:
                    logging.info(
                        'Kernel Building Complete. No Kernel Boot and Tests')
                    tear_down(mk, console)
                elif result_dir is None:
                    logging.info('Exit ! Tests took more than 2 hours')
                    tear_down(mk, console)
                else:
                    logging.error('Error with result generation')
                    tear_down(mk, console)
                mk.close_console(console)
            else:
                logging.error('Specify necessary HMC details')

if __name__ == '__main__':
    main()
