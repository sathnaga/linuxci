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

import os
import sys
import time
import pexpect
from pexpect import pxssh


class hmc:

    '''

    This class contains the modules to perform various HMC operations on an LPAR.
    The Host IP, username and password of HMC have to be passed to the class intially
    while creating the object for the class.

    '''

    def __init__(self, host_ip, user_name, password):
        #self.host_name = host_name
        self.host_ip = host_ip
        self.user_name = user_name
        self.password = password

    def login(self):
        '''
        To log in to the HMC Console

        This module uses pxssh to log in to the HMC console and helps to maintain the session
        using the ip address, username and password that are passed to the class.

        '''
        try:
            self.s = pxssh.pxssh()
            self.s.login(self.host_ip, self.user_name, self.password)
        except pxssh.ExceptionPxssh, e:
            print "Try Again", str(e)
            sys.exit(1)

    def run_command(self, command):
        try:
            self.s.sendline(command)
            self.s.prompt(timeout=30)
            time.sleep(0.5)
            res = self.s.before
            self.s.sendline("echo $?")
            self.s.prompt(timeout=30)
            time.sleep(0.5)
            self.check = self.s.before
            if("0" in self.check):
                print "\n Running command...\n"
                #print res
                return res
            else:
                print "Command not executed successfully"
        except Exception, info:
            print info
            sys.exit(1)

    def check_kernel_panic(self, console):
        list = ["Kernel panic", "Aieee", "soft lockup", "not syncing", "Oops", "Bad trap at PC",
                "Unable to handle kernel NULL pointer", "Unable to mount root device", "grub>", "grub rescue", pexpect.TIMEOUT]
        try:
            rc = console.expect(list, timeout=120)
            if rc in [0, 1, 2, 3, 4, 5, 6, 7]:
                print "system got " + list[rc] + ", exiting"
                return "panic"
            else:
                pass
        except:
            pass

    def run_login(self, console):
        time.sleep(2)
        time.sleep(5)
        while True:
            panic = self.check_kernel_panic(console)
            if panic == "panic":
                print "Exiting Console"
                sys.exit(1)
            try:
                rc = console.expect(["login:", pexpect.TIMEOUT], timeout=600)
                if rc == 0:
                    res = console.before
                    res = res.splitlines()
                    return "Login"
                else:
                    pass
            except:
                pass

    def run_build(self, cmd, console):
        time.sleep(2)
        console.sendline(cmd)
        console.send('\r')
        time.sleep(5)
        try:
            rc = console.expect(
                ["Kernel Building Complete", "TEST: installing and booting the kernel", "Report successfully", pexpect.TIMEOUT], timeout=7200)
            if rc == 0:
                return "build"
            elif rc == 1:
                res = console.before
                res = res.splitlines()
                return "kexec"
            elif rc == 2:
                return "report"
            else:
                res = console.before
                res = res.split(cmd)
                return res[-1].splitlines()
        except:
            print "Time out Exceeded"
            sys.exit(1)

    def bso_auth(self, console, username, password):
        time.sleep(2)
        console.sendline('telnet git.linux.ibm.com')
        console.send("\r")
        time.sleep(5)
        try:
            rc = console.expect(["Username:", "refused", "login:"], timeout=60)
            if rc == 0:
                console.sendline(username)
                console.send("\r")
                rc1 = console.expect(
                    [r"[Pp]assword:", pexpect.TIMEOUT], timeout=120)
                time.sleep(5)
                if rc1 == 0:
                    console.sendline(password)
                    console.send("\r")
                    rc2 = console.expect(
                        ["BSO Authentication Successful", pexpect.TIMEOUT], timeout=120)
                    if rc2 == 0:
                        print "BSO is passed"
                        return
                    else:
                        print "BSO authentication has failed"
                        sys.exit(1)
            elif rc == 1 or rc == 2:
                print "BSO is already passed"
                return
            else:
                print "Problem in BSO authentication"
                sys.exit(1)
        except pexpect.ExceptionPexpect, e:
            print "IPMI Command execution failed"
            print str(e)
            sys.exit(1)

    def run_cmd(self, cmd, console, timeout=300):
        time.sleep(2)
        console.sendline(cmd)
        console.send('\r')
        time.sleep(5)
        try:
            rc = console.expect(
                [r"\[pexpect\]#$", pexpect.TIMEOUT], timeout)
            if rc == 0:
                res = console.before
                res = res.splitlines()
                return res
            else:
                res = console.before
                res = res.split(cmd)
                return res[-1].splitlines()
        except pexpect.ExceptionPexpect, e:
            print "LPAR Command execution failed"
            print str(e)
            sys.exit(1)

    def set_unique_prompt(self, console):
        time.sleep(5)
        console.sendline("PS1=[pexpect]#")
        console.send('\r')
        rc = console.expect_exact("[pexpect]#")
        if rc == 0:
            print "\nShell prompt changed"
        else:
            sys.exit(1)

    def get_lpar_proc_mode(self, server_name):
        res = self.run_command("lssyscfg -r sys -F lpar_proc_compat_modes -m "+ server_name)
        return res

    def get_lpar_console(self, hmc_username, hmc_password, server_name, lpar_name, login_id, passwd):
        print "De-activating the console"
        self.run_command("rmvterm -m " + server_name + " -p " + lpar_name)
        self.s.send('\r')
        # print self.s.before
        con = pexpect.spawn("ssh " + hmc_username + "@" + self.host_ip)
        h = con.expect(["[Pp]assword:", pexpect.TIMEOUT], timeout=60)
        if h == 0:
            con.sendline(hmc_password)
            # con.interact()
        else:
            sys.exit(1)
        # user name and pswd of HMC
        try:
            print "Opening the LPAR console"
            con.sendline("mkvterm -m " + server_name + " -p " + lpar_name)
            con.send('\r')
            i = con.expect(["Open Completed.", pexpect.TIMEOUT], timeout=30)
            con.send('\r')
            con.logfile = sys.stdout
            con.delaybeforesend = 0.9
            if i == 0:
                i = con.expect(["login:", "#", pexpect.TIMEOUT], timeout=60)
                # print i, con.before
                if i == 0:
                    con.sendline(login_id)
                    con.send('\r')
                    i = con.expect(
                        ["Password:", pexpect.TIMEOUT], timeout=60)
                    if i == 0:
                        con.sendline(passwd)
                        con.send('\r')
                        i = con.expect(
                            ["Last login", "incorrect", pexpect.TIMEOUT], timeout=60)
                        if i == 1:
                            print "Wrong Credentials for host"
                            sys.exit(1)
                    return con
                elif i == 1:
                    return con
                else:
                    print "Console in different state"
                    sys.exit(1)
        except Exception, info:
            print info
            sys.exit(1)

    def reboot_step(self, disk, server_name, lpar_name):
        # 1. shuttdown
        # 2. boot to smsmenu
        # 3. mkvterm
        # 4. send 1     to boot options
        # 5. send 5  to list boot devices
        # 6. grep for scsi device which we want
        # 7. than fetch the corresponding option in same screen
        # 8. send the no. and
        # 9. send 2  for normal boot
        # 10. send 1  to say Yes
        print "Shutting down LPAR"
        self.run_command(
            'chsysstate -r lpar -o shutdown --immed -m ' + server_name + ' -n ' + lpar_name)
        self.s.prompt(timeout=10)
        print "Booting LPAR to SMS menu"
        self.run_command(
            'chsysstate -r lpar -b sms -o on -m ' + server_name + ' -n ' + lpar_name)
        self.s.send('\r')
        con = pexpect.spawn("ssh " + self.user_name + "@" + self.host_ip)
        con.logfile = sys.stdout
        con.delaybeforesend = 0.9
        h = con.expect(["[Pp]assword:", pexpect.TIMEOUT], timeout=60)
        # print h
        if h == 0:
            con.sendline(self.password)
        else:
            sys.exit(1)
        try:
            print "\nDeactivating Console"
            con.sendline("rmvterm -m " + server_name + " -p " + lpar_name)
            print "\nActivating Console"
            con.sendline("mkvterm -m " + server_name + " -p " + lpar_name)
            con.send('\r')
            con.send('\r')
            time.sleep(5)
            i = con.expect(["Main Menu", pexpect.TIMEOUT], timeout=30)
            if i == 0:
                i = con.expect(["key:", pexpect.TIMEOUT], timeout=30)
                if i == 0:
                    con.send('5')
                    con.send('\r')
                    time.sleep(5)
                    i = con.expect(["Multiboot", pexpect.TIMEOUT], timeout=30)
                    if i == 0:
                        i = con.expect(["key:", pexpect.TIMEOUT], timeout=30)
                        if i == 0:
                            con.send('1')
                            con.send('\r')
                            time.sleep(5)
                            i = con.expect(
                                ["Select Device Type", pexpect.TIMEOUT], timeout=30)
                            if i == 0:
                                i = con.expect(
                                    ["key:", pexpect.TIMEOUT], timeout=30)
                                if i == 0:
                                    lines = con.before.split("\n")
                                    flag = False
                                    for index, line in enumerate(lines):
                                        if 'List all Devices' in line:
                                            flag = True
                                            con.send(lines[index][1])
                                            con.send('\r')
                                            time.sleep(5)
                                    i = con.expect(
                                        ["Navigation keys", pexpect.TIMEOUT], timeout=30)
                                    if i == 0:
                                        lines = con.before.split("\n")
                                        flag = False
                                        for index, line in enumerate(lines):
                                            if disk in line:
                                                flag = True
                                                con.send(lines[index - 1][1])
                                                con.send('\r')
                                                time.sleep(5)
                                                i = con.expect(
                                                    ["Normal Mode", pexpect.TIMEOUT], timeout=30)
                                                if i == 0:
                                                    i = con.expect(
                                                        ["key:", pexpect.TIMEOUT], timeout=30)
                                                    if i == 0:
                                                        con.send('2')
                                                        con.send('\r')
                                                        time.sleep(5)
                                                        i = con.expect(
                                                            ["Are you sure", pexpect.TIMEOUT], timeout=30)
                                                        if i == 0:
                                                            i = con.expect(
                                                                ["key:", pexpect.TIMEOUT], timeout=30)
                                                            if i == 0:
                                                                con.send('1')
                                                                con.send('\r')
                                                                log_in = con.expect(
                                                                    ["login:", pexpect.TIMEOUT], timeout=300)
                                                                if log_in == 0:
                                                                    return "Login"
                                        if flag == False:
                                            print "\nError !OS not installed in disk"
                                            sys.exit(1)
        except Exception, e:
            print "Something wrong in SMS menu"
            print e
            sys.exit(1)

    def close_console(self, console):
        console.send('~.')
        time.sleep(5)
        console.close()
