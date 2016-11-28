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
# Author: Harish <harisrir@linux.vnet.ibm.com>

import os
import sys
import argparse
import logging
import datetime
import subprocess
sys.path.append(
    os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir))
from lib import common_lib as commonlib


def get_output(cmd):
    commit = subprocess.Popen(
        [cmd], stdout=subprocess.PIPE, shell=True).communicate()[0]
    return commit.replace('\n', '')


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("--id", action="store", dest="id", help="Specify the SID of the run\
                        Usage: --id sid")
    parser.add_argument("--git", action="store", dest="git", help="Specify the git tree\
                        Usage: --git test_name1,test_name2,test_name3")
    parser.add_argument("--branch", action="store", dest="branch", help="Specify the branch\
                        Usage: --branch test_name1,test_name2,test_name3")
    parser.add_argument("--tests", action="store", dest="tests", help="Specify the tests to be performed on the host\
                        Usage: --tests test_name1,test_name2,test_name3")
    parser.add_argument("--result", action="store", dest="result", help="Specify the result of the tests on the host\
                        Usage: --result PASS")

    logging.basicConfig(
        format='\n%(asctime)s %(levelname)s  |  %(message)s', level=logging.DEBUG,  datefmt='%I:%M:%S %p')

    options = parser.parse_args()
    if options.id:
        logging.info("UPDATING DATAFILE OF SUBSCRIPTION")
        old_json = commonlib.read_json(
            commonlib.base_path + options.id + '/' + options.id + '.json')
        print old_json['NEXTRUN']
        old_json['LASTRUN'] = datetime.datetime.now().strftime('%Y_%m_%d')
        old_json['COMMITID'] = get_output(
            "git ls-remote " + options.git + " " + options.branch + " | head -n1 | awk '{print $1;}'")
        commonlib.update_json(
            commonlib.base_path + options.id + '/' + options.id + '.json', old_json)
        sub_json = commonlib.read_json(
            commonlib.base_path + 'subscribers.json')
        for sub in sub_json:
            if sub['SID'] == options.id:
                sub['STATUS'] = options.result
        commonlib.update_json(
            commonlib.base_path + 'subscribers.json', sub_json)
    else:
        logging.info("UPDATING DATAFILE OF USER TRIGGERS")
        new_json = {}
        new_json['GIT'] = options.git
        new_json['BRANCH'] = options.branch
        new_json['TESTS'] = options.tests
        new_json['COMMITID'] = get_output(
            "git ls-remote " + options.git + " " + options.branch + " | head -n1 | awk '{print $1;}'")
        new_json['RUNTIME'] = datetime.datetime.now().strftime('%Y_%m_%d')
        new_json['RESULT'] = options.result
        commonlib.append_json(
            commonlib.base_path + 'user_triggers.json', new_json)

if __name__ == "__main__":
    main()
