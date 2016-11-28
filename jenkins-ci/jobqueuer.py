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

import os
import json
import logging
import fcntl
import sys
import time
import errno
sys.path.append(
    os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir))
from lib import common_lib as commonlib

lines = []
SID = ''


def lock_pop_unlock():
    if os.stat(commonlib.schedQfile).st_size != 0:
        while True:
            try:
                x = open(commonlib.schedQfile, 'rw')
                fcntl.flock(x, fcntl.LOCK_EX | fcntl.LOCK_NB)
                line = x.readline()
                SID = line.replace('\n', '')
                SID = SID.split('-')[0]
                y = open(commonlib.schedQfile, 'w')
                lines = x.readlines()
                for item in lines[0:]:
                    y.write(item)
                fcntl.flock(x, fcntl.LOCK_UN)
                x.close()
                y.close()
                return SID
            except IOError as ex:
                if ex.errno != errno.EAGAIN:
                    raise
            else:
                time.sleep(0.1)
    return None


def get_datafile_params(SID):
    datafile = {}
    sidfile = commonlib.base_path + SID + '/' + SID + '.json'
    if os.path.isfile(sidfile):
        datafile = commonlib.read_json(sidfile)
        return {'kernel_git_repo': datafile['URL'], 'kernel_git_repo_branch': datafile['BRANCH'], 'configfile': datafile['CONFIG'], 'patchfile': datafile['PATCH'], 'tests': datafile['TESTS'], 'buildmachine': datafile['BUILDMACHINE'], 'bootdisk': datafile['BOOTDISK']}
    return None


def main():

    SID = lock_pop_unlock()
    if SID is not None:
        print "SID=" + SID
        DICT = get_datafile_params(SID)
        if DICT is not None:
            for key, val in DICT.items():
                print key + "=" + str(val)
        else:
            return None
    else:
        return None


if __name__ == "__main__":
    main()
