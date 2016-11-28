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
# Author: Harish <harisrir@linux.vnet.ibm.com>

import os
import sys
import datetime
import re
import argparse
import json
import subprocess
sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir))
from lib import common_lib as commonlib


def get_subid(path, mailid):
    mailid = mailid.split("@")
    if os.path.exists(path):
        subfile = commonlib.read_json(path)
        sub_id = subfile[len(subfile) - 1]['SID']
        su_id = sub_id.split('#')
        subscribe_id = int(su_id[len(su_id) - 1]) + 1
        subscribe_id = "KORG#" + str(subscribe_id)
    else:
        subscribe_id = "KORG#1"
    return subscribe_id


def create_sidfile(json_details, sid_file):

    unique_git = commonlib.tar_name(
        json_details['git'], json_details['branch'])
    sid_json = {}
    sid_json['GITDIR'] = commonlib.base_path + unique_git + '.tar.gz'
    sid_json['URL'] = json_details['git']
    sid_json['BRANCH'] = json_details['branch']
    sid_json['COMMITID'] = None
    sid_json['LASTRUN'] = None
    sid_json['NEXTRUN'] = None
    sid_json['BUILDFREQ'] = json_details['build_freq']
    sid_json['TESTS'] = json_details['tests']
    sid_json['BUILDMACHINE'] = json_details['buildmachine']
    sid_json['BOOTDISK'] = json_details['bootdisk']
    sid_json['MAILID'] = json_details['mailid']

    config_name = json_details['configfile'].rsplit('/', 1)[-1]
    file_pathc = json_details['configfile'].replace(config_name, '')
    file_name = json_details['patchfile'].rsplit('/', 1)[-1]
    file_pathp = json_details['patchfile'].replace(file_name, '')

    os.makedirs(commonlib.base_path + sid_file + '/')
    # with sid_file = open(base_path + json_details['sid'] +'.json', 'w') load
    # the sid_json
    if os.path.exists(file_pathc + 'configfile'):
        os.system('mv ' + file_pathc + 'configfile ' +
                  commonlib.base_path + sid_file + '/' + config_name)
        sid_json['CONFIG'] = commonlib.base_path + sid_file + '/' + config_name
    elif 'make' in json_details['configfile']:
        sid_json['CONFIG'] = json_details['configfile']
    else:
        sid_json['CONFIG'] = ''
    if os.path.exists(file_pathp + 'patchfile'):
        os.system('mv ' + file_pathp + 'patchfile ' +
                  commonlib.base_path + sid_file + '/' + file_name)
        sid_json['PATCH'] = commonlib.base_path + sid_file + '/' + file_name
    else:
        sid_json['PATCH'] = ''
    commonlib.update_json(
        commonlib.base_path + sid_file + '/' + sid_file + '.json', sid_json)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--args", action="store", dest="args", help="Specify the git, branch, frequency config and patch files\
                        Usage: --args mailid=mailid,git=git_link,branch=branch,build_freq=breq,config=path-to-file,patches=path-to-patch")
    parser.add_argument("--tests", action="store", dest="tests", help="Specify the tests to be performed on the host\
                        Usage: --tests test_name1,test_name2,test_name3")
    parser.add_argument("--buildmachine", action="store", dest="bm", help="Specify the host to run\
                        Usage: --host host-ip")
    parser.add_argument("--bootdisk", action="store", dest="bdisk", help="Specify the boot disk of the host to run\
                        Usage: --disk disk")

    options = parser.parse_args()
    time = datetime.datetime.now().strftime('%Y_%m_%d')
    json_details = {}
    if options.args:
        options.args = options.args + ",date=" + str(time)
        details = commonlib.get_keyvalue(options.args)
        json_details = commonlib.get_keyvalue(options.args)

    if options.tests:
        json_details['tests'] = options.tests
    else:
        json_details['tests'] = None

    if options.bm:
        json_details['buildmachine'] = options.bm
    if options.bdisk:
        json_details['bootdisk'] = options.bdisk

    subscribers_json = {}
    subscribers_json['SID'] = get_subid(
        commonlib.base_path + '/subscribers.json', json_details['mailid'])
    subscribers_json['MAILID'] = json_details['mailid']
    subscribers_json['DATE'] = json_details['date']
    subscribers_json['DATAFILE'] = subscribers_json['SID'] + '.json'
    subscribers_json['STATUS'] = None
    subscribers_json['GIT'] = json_details['git']
    subscribers_json['BRANCH'] = json_details['branch']
    subscribers_json['TESTS'] = json_details['tests']

    commonlib.append_json(commonlib.base_path + '/subscribers.json', subscribers_json)

    create_sidfile(json_details, subscribers_json['SID'])
    print subscribers_json['SID']

if __name__ == '__main__':
    main()
