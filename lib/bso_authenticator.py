#!/usr/bin/python

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
# Author:  Satheesh Rajendran <sathnaga@linux.vent.ibm.com>

import telnetlib
import argparse


def pass_bso(host, user='ltctest@in.ibm.com', password='test@ltc16'):
    """
    Pass BSO Authentication
    TODO: Handle failures cases more refined
    """
    try:
        telnet = telnetlib.Telnet(host)
    except Exception:
        print "Bso for host:", host, "is already passed"
        return
    telnet.read_until("Username:")
    telnet.write(user + "\n")
    telnet.read_until("Password:")
    telnet.write(password + "\n")
    telnet.read_all()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--hostnames",
                        dest="hostnames",
                        default='git.linux.ibm.com',
                        help="Give hostnames to pass bso comma separated")
    parser.add_argument("--password",
                        dest="password",
                        default='test@ltc16',
                        help="password for given username")
    parser.add_argument("--user",
                        dest="user",
                        default='ltctest@in.ibm.com',
                        help="username to pass bso")

    args = parser.parse_args()
    hostnames = args.hostnames.split(',')
    for hostname in hostnames:
        pass_bso(hostname, args.user, args.password)
