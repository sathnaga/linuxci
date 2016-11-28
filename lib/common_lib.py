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
import json
import re
import logging
import pexpect
import sys
import ConfigParser

config_details = ConfigParser.ConfigParser()
config_details.read(os.path.join(os.path.dirname(__file__), 'details.ini'))
clone_cmd = config_details.get('Details', 'clone_cmd')
continue_cmd = config_details.get('Details', 'continue_cmd')
avocado_repo = config_details.get('Details', 'avocado_repo')
avocado_result = config_details.get('Details', 'avocado_result')
avocado_clean = config_details.get('Details', 'avocado_clean')
avocado_test_run = config_details.get('Details', 'avocado_test_run')
base_path = config_details.get('Details', 'base_path')
schedQfile = config_details.get('Details', 'schedQfile')
# same as schedQfile: build_notifier_loc
subscribersfile = config_details.get('Details', 'subscribersfile')
manual_path = config_details.get('Details', 'manual_path')


def detect_distro(obj, console):
    release = [
        {'name': 'redhat-release', 'key': 'Red Hat'}, {
            'name': 'SuSE-release', 'key': 'SUSE'},
        {'name': 'os-release', 'key': 'Ubuntu'}, {'name': 'centos-release', 'key': 'CentOS'}, {'name': 'fedora-release', 'key': 'Fedora'}]
    for distro in release:
        cmd = 'if [ -f /etc/%s ] ;then echo Yes;else echo No;fi' % (
            distro['name'])
        status = obj.run_cmd(cmd, console)
        if status[-1] == 'Yes':
            cmd = 'grep -w "%s" /etc/%s > /dev/null 2>&1;echo $?' % (
                distro['key'], distro['name'])
            status = obj.run_cmd(cmd, console)
            if status[-1] == '0':
                return distro['key']
    return None


def read_json(path):
    if os.path.isfile(path):
        subfile = open(path, 'r')
        json_data = json.load(subfile)
        file_contents = json_data['data']
        return file_contents
    else:
        return []


def scp_to_host(file_path, host_details):
    scp = pexpect.spawn('scp -l 8192 -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -r ' +
                        file_path + ' ' + host_details['username'] + '@' + host_details['hostname'] + ':/root/')
    res = scp.expect([r'[Pp]assword:', pexpect.EOF])
    if res == 0:
        scp.sendline(host_details['password'])
        logging.info("Copying files to host")
        scp.logfile = sys.stdout
        wait = scp.expect([pexpect.EOF], timeout=500)
        if wait == 0:
            logging.info('Files successfully copied')


def append_json(path, json_details):
    file_contents = read_json(path)
    json_data = {}
    with open(path, mode='w') as file_json:
        file_contents.append(json_details)
        json_data['data'] = file_contents
        json.dump(json_data, file_json)


def update_json(path, json_details):
    json_data = {}
    with open(path, mode='w') as file_json:
        json_data['data'] = json_details
        json.dump(json_data, file_json)


def tar_name(git, branch):
    git = re.split(".org|.com", git, 1)[1][1:]
    git = git.replace('/', '_')
    return git + '_' + branch


def tar(folder, tar_folder):
    os.chdir(folder)
    if os.path.isdir(tar_folder):  # Handling with proper git name
        print "Tarring " + tar_folder
        os.system('tar -czf ' + tar_folder +
                  '.tar.gz ' + tar_folder)


def untar(tar_file):
    if os.path.exists(tar_file):
        print "Untarring " + tar_file
        os.system('tar -xzf ' + tar_file)


def get_keyvalue(values):
    details = {}
    values = values.split(',')
    for value in values:
        n = re.findall('(.*?)=.*', value)[0]
        x, v = value.split('%s=' % n)
        details[n] = v
    return details
