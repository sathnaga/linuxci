#!/usr/bin python

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
import pexpect
import argparse
sys.path.append(
    os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir))
from lib import common_lib as commonlib


def scp_id(sid, host_details):
    if os.path.exists(commonlib.base_path + sid + '/hostCopy.tar.gz'):
        print "Copying tar to host"
        commonlib.scp_to_host(
            commonlib.base_path + sid + '/hostCopy.tar.gz', host_details)
        os.system('rm -rf ' + commonlib.base_path + sid + '/hostCopy.tar.gz')
    sid_json = commonlib.read_json(
        commonlib.base_path + sid + '/' + sid + '.json')
    print type(sid_json)
    print sid_json
    if sid_json['CONFIG'] == '' and sid_json['PATCH'] == '':
        print "NO FILES TO SCP"
        return
    else:
        if sid_json['CONFIG'] == '':
            print "NO CONFIG FILE"
        if sid_json['PATCH'] == '':
            print "NO PATCH FILE"
        commonlib.scp_to_host(
            sid_json['CONFIG'] + ' ' + sid_json['PATCH'], host_details)


def scp_manual(config, patch, host_details):
    if os.path.exists(commonlib.manual_path + '/hostCopy.tar.gz'):
        print "Copying tar to host"
        commonlib.scp_to_host(
            commonlib.manual_path + '/hostCopy.tar.gz', host_details)
        os.system('rm -rf ' + commonlib.manual_path + '/hostCopy.tar.gz')
    if not os.path.exists(commonlib.manual_path + 'configfile') and not os.path.exists(commonlib.manual_path + 'patchfile'):
        print "NO CONFIG FILE AND PATCH FILE"
        return
    else:
        config_path = commonlib.manual_path + config
        patch_path = commonlib.manual_path + patch

        if os.path.exists(commonlib.manual_path + 'configfile'):
            os.system('mv ' + commonlib.manual_path +
                      'configfile ' + commonlib.manual_path + config)
        else:
            config_path = ''
            print "NO CONFIG FILE"
        if os.path.exists(commonlib.manual_path + 'patchfile'):
            os.system('mv ' + commonlib.manual_path +
                      'patchfile ' + commonlib.manual_path + patch)
        else:
            patch_path = ''
            print "NO PATCH FILE"
        commonlib.scp_to_host(config_path + ' ' +
                              patch_path, host_details)


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("--id", action="store", dest="id", help="Specify the SID of the run\
                        Usage: --id sid")
    parser.add_argument("--host", action="store", dest="host", help="Specify the host details of the test\
                        Usage: --host hostname=hostname,username=username,password=passw0rd")
    parser.add_argument("--config", action="store", dest="config", help="Specify the name of config file user uploaded\
                        Usage: --config configfile-name")
    parser.add_argument("--patch", action="store", dest="patch", help="Specify the name of patch file user uploaded\
                        Usage: --id patchfile-name")

    options = parser.parse_args()
    host_details = commonlib.get_keyvalue(options.host)
    if options.id:
        scp_id(options.id, host_details)
    else:
        scp_manual(options.config, options.patch, host_details)
    print "SCP COMPLETE"

if __name__ == "__main__":
    main()
