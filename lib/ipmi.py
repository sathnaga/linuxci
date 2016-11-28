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
# Based on the code written by Prudhvi Piapaddy

import pexpect
import time
import sys
import re
import commands


class ipmi:

    def __init__(self, host_name, user_name, password):
        self.host_name = host_name
        if user_name == '':
            self.user_name = ''
        else:
            self.user_name = " -U %s " % user_name
        self.password = password

    def run_cmd(self, cmd, console, timeout=300):
        time.sleep(2)
        console.sendline(cmd)
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
            console.sendcontrol("c")
            print "IPMI Command execution failed"
            print str(e)
            sys.exit(1)

    def bso_auth(self, console, username, password):
        time.sleep(2)
        console.sendline('telnet git.linux.ibm.com')
        time.sleep(5)
        try:
            rc = console.expect(["Username:", "refused", "login:"], timeout=60)
            if rc == 0:
                console.sendline(username)
                rc1 = console.expect(
                    [r"[Pp]assword:", pexpect.TIMEOUT], timeout=120)
                time.sleep(5)
                if rc1 == 0:
                    console.sendline(password)
                    rc2 = console.expect(
                        ["uccess", pexpect.TIMEOUT], timeout=120)
                    if rc2 == 0:
                        print "BSO is passed"
                    else:
                        print "BSO authentication has failed"
                        sys.exit(1)
                else:
                    sys.exit(1)
            elif rc == 1 or rc == 2:
                print "BSO is already passed"
                return
            else:
                print "Problem passing BSO"
                sys.exit(1)
        except pexpect.ExceptionPexpect, e:
            print "IPMI Command execution failed"
            print str(e)
            sys.exit(1)

    def check_kernel_panic(self, console):
        list = [
            "Kernel panic", "Aieee", "soft lockup", "not syncing", "Oops", "Bad trap at PC",
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

    def run_build(self, cmd, console):
        time.sleep(2)
        console.sendline(cmd)
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
                pass
        except:
            print "Time Out exceeded"
            sys.exit(1)

    def run_login(self, console):
        time.sleep(2)
        while True:
            panic = self.check_kernel_panic(console)
            if panic == "panic":
                print "Exiting ..."
                sys.exit(1)
            try:
                rc = console.expect(
                    ["login:", "Report successfully", pexpect.TIMEOUT], timeout=300)
                if rc == 0:
                    res = console.before
                    res = res.splitlines()
                    return "Login"
                elif rc == 1:
                    return "Error"
                else:
                    pass
            except:
                pass

    def activate(self):
        print "running:ipmitool -I lanplus %s -P %s  -H %s sol activate" % (self.user_name, self.password, self.host_name)
        con = pexpect.spawn('ipmitool -I lanplus %s -P %s -H %s sol activate' %
                            (self.user_name, self.password, self.host_name), timeout=60)
        return con

    def deactivate(self):
        print "running:ipmitool -N 1 -R 5 -I lanplus %s -P %s  -H %s sol deactivate" % (self.user_name, self.password, self.host_name)
        pexpect.run('ipmitool -N 1 -R 5 -I lanplus %s -P %s  -H %s sol deactivate' %
                    (self.user_name, self.password, self.host_name), timeout=30)

    def chassisBios(self):
        print "running:ipmitool -N 1 -R 5 -I lanplus %s -P %s  -H %s chassis bootdev bios"
        pexpect.run('ipmitool -N 1 -R 5 -I lanplus %s -P %s  -H %s chassis bootdev bios' %
                    (self.user_name, self.password, self.host_name), timeout=30)

    def chassisOff(self):
        print "running:ipmitool -N 1 -R 5 -I lanplus %s -P %s  -H %s chassis power off" % (self.user_name, self.password, self.host_name)
        pexpect.run('ipmitool -N 1 -R 5 -I lanplus %s -P %s  -H %s chassis power off' %
                    (self.user_name, self.password, self.host_name), timeout=30)

    def chassisOn(self):
        print "running:ipmitool -N 1 -R 5 -I lanplus %s -P %s  -H %s chassis power on" % (self.user_name, self.password, self.host_name)
        pexpect.run('ipmitool -N 1 -R 5 -I lanplus %s -P %s  -H %s chassis power on' %
                    (self.user_name, self.password, self.host_name), timeout=30)

    def getconsole(self):
        self.deactivate()
        con = self.activate()
        time.sleep(5)
        print "Activating"
        time.sleep(5)
        con.logfile = sys.stdout
        con.delaybeforesend = 0.9
        if con.isalive():
            return con
        else:
            print "Problem in getting the console"
            sys.exit(1)

    def status(self):
        con = pexpect.spawn('ipmitool -I lanplus %s -P %s  -H %s chassis status' %
                            (self.user_name, self.password, self.host_name))
        while con.isalive():
            time.sleep(2)
        cmd = ''.join(con.readlines())
        if 'on' in cmd.split("\n")[0]:
            return True
        return False

    def set_unique_prompt(self, console, username, password):
        rc = console.expect_exact(
            "[SOL Session operational.  Use ~? for help]\r\n", timeout=300)
        if rc == 0:
            print "Got ipmi console"
        else:
            sys.exit(1)
        time.sleep(5)
        console.send("\r")
        time.sleep(3)
        try:
            rc = console.expect_exact(["login: "], timeout=60)
            if rc == 0:
                console.sendline(username)
                rc = console.expect(
                    [r"[Pp]assword:", pexpect.TIMEOUT], timeout=120)
                time.sleep(5)
                if rc == 0:
                    console.sendline(password)
                    rc = console.expect(
                        ["Last login", "incorrect"], timeout=60)
                    if rc == 1:
                        print "Wrong Credentials"
                        sys.exit(1)
                else:
                    sys.exit(1)
            else:
                console.expect(pexpect.TIMEOUT, timeout=30)
                print console.before
        except pexpect.ExceptionPexpect, e:
            console.sendcontrol("c")
            console.expect(pexpect.TIMEOUT, timeout=60)
            print console.before
        time.sleep(5)
        console.sendline("PS1=[pexpect]#")
        rc = console.expect_exact("[pexpect]#")
        if rc == 0:
            print "Shell prompt changed"
        else:
            sys.exit(1)

    def get_type(self, console):
        rc = console.expect_exact(
            "[SOL Session operational.  Use ~? for help]\r\n", timeout=300)
        if rc == 0:
            print "Got ipmi console : First run"
        else:
            sys.exit(1)
        time.sleep(5)
        console.send("\r")
        time.sleep(3)
        try:
            rc = console.expect(
                ["\[.+\#", "petitboot", "login:", "(initramfs)"], timeout=400)
            if rc == 0:
                rc_in = console.expect(["login:", pexpect.TIMEOUT],  timeout=120)
                if rc_in == 0:
                    return "login"
                elif rc_in == 1:
                    return "logged"
            elif rc == 1:
                return "petitboot"
            elif rc == 2:
                return "login"
            elif rc == 3:
                return "initramfs"
        except pexpect.ExceptionPexpect, e:
            print "Console connect timedout: chasis reboot"
            console.send('~.')
            time.sleep(10)
            console.close()
            return "timeout"

    def login(self, console, username, password):
        console.sendline(username)
        rc = console.expect(
            [r"[Pp]assword:", pexpect.TIMEOUT], timeout=120)
        time.sleep(5)
        if rc == 0:
            console.sendline(password)
            rc_l = console.expect(
                ["Last login:", "incorrect", pexpect.TIMEOUT], timeout=300)
            if rc_l == 1:
                print "Error in logging.Wrong Credentials"
                sys.exit(1)
        else:
            sys.exit(1)

    def closeconsole(self, console):
        console.send('~.')
        time.sleep(10)
        console.close()
