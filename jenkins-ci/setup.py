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
import json
import subprocess
import argparse
import pexpect
import logging
import shutil
sys.path.append(
    os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir))
from lib import common_lib as commonlib


def get_output(cmd):
    commit = subprocess.Popen(
        [cmd], stdout=subprocess.PIPE, shell=True).communicate()[0]
    return commit.replace('\n', '')


def compare_sub_tests(list1, list2):
    list1.sort()
    list2.sort()
    first_list = ''
    second_list = ''
    for test in list1:
        first_list = first_list + test
    for test in list2:
        second_list = second_list + test
    if second_list in first_list:
        print second_list
        print first_list
        return True
    return False


def remove_sid(path, sid):
    file_contents = commonlib.read_json(path + 'subscribers.json')
    shutil.rmtree(path + sid)
    for subscription in file_contents:
        if sid == subscription['SID']:
            file_contents.remove(subscription)
    commonlib.update_json(path + 'subscribers.json', file_contents)


def cleanup(cur_path, tar_name, sid):
    logging.info('CLEAN UP PROCESS')
    if os.path.exists(cur_path + tar_name + '.tar.gz'):
        print cur_path + tar_name + '.tar.gz'
        os.system('rm -rf ' + cur_path + tar_name + '.tar.gz')
    if os.path.exists(cur_path + tar_name):
        os.system('rm -rf ' + cur_path + tar_name)
    if sid:
        if os.path.exists(cur_path + 'hostCopy.tar.gz'):
            os.system('rm -rf ' + cur_path + 'hostCopy.tar.gz')
    if os.path.exists(cur_path + 'hostCopy'):
        os.system('rm -rf ' + cur_path + 'hostCopy')


def complete_json(options):
    complete_json = {}
    complete_json['GIT'] = options.git
    complete_json['BRANCH'] = options.branch
    complete_json['TESTS'] = options.tests

    if options.id:
        logging.info('Adding to completion list in completion.json')
        commonlib.append_json(
            commonlib.base_path + '/completion.json', complete_json)
    else:
        logging.info('Adding to completion list in manual.json')
        commonlib.append_json(
            commonlib.base_path + '/manual.json', complete_json)


def pull_and_tar(cur_path, tar_name):
    print "Common pull and Tar"
    logging.info("Pulling to latest commit")
    os.system('git reset --hard')
    os.system('git clean -df')
    os.system('git config merge.renameLimit 999999')
    os.system('git pull')
    os.chdir(cur_path)
    logging.info('Making a hostcopy')
    os.system('cp -r ' + cur_path + tar_name + ' hostCopy')
    commonlib.tar(cur_path, tar_name)
    os.chdir(cur_path)
    logging.info('Updating tar in Jenkins')
    os.system('cp -f ' + cur_path +
              tar_name + '.tar.gz ' + commonlib.base_path)
    logging.info('Removing git files in host copy')
    os.system('rm -rf hostCopy/.git')
    commonlib.tar(cur_path, 'hostCopy')
    os.chdir(cur_path)


def move_hostCopy(cur_path, sid):
    if sid:
        os.system('mv ' + cur_path + 'hostCopy.tar.gz ' +
                  commonlib.base_path + sid + '/')


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("--id", action="store", dest="id", help="Specify the SID of the run\
                        Usage: --id sid")
    parser.add_argument("--git", action="store", dest="git", help="Specify the git tree \
                        Usage: --git test_name1,test_name2,test_name3")
    parser.add_argument("--branch", action="store", dest="branch", help="Specify the branch\
                        Usage: --branch test_name1,test_name2,test_name3")
    parser.add_argument("--tests", action="store", dest="tests", help="Specify the tests to be performed on the host\
                        Usage: --tests test_name1,test_name2,test_name3")
    parser.add_argument("--host", action="store", dest="host", help="Specify the host details\
                        Usage: --host hostname=hostname,username=username,password=passw0rd")
    parser.add_argument("--next", action="store", dest="next", help="For updation of tar\
                        Usage: --next True")
    parser.add_argument("--buildonly", action="store", dest="buildonly", help="To specify build-only runs\
                        Usage: --buildonly True")

    logging.basicConfig(
        format='\n%(asctime)s %(levelname)s  |  %(message)s', level=logging.DEBUG,  datefmt='%I:%M:%S %p')

    options = parser.parse_args()
    tar_name = commonlib.tar_name(options.git, options.branch)
    host_details = commonlib.get_keyvalue(options.host)
    subscribers_json = commonlib.read_json(
        commonlib.base_path + 'completion.json')
    check_flag = False
    cur_path = get_output('pwd') + '/'

    if not options.id:
        options.id = None

    if options.id:
        if options.next:
            logging.info('Copying tar to current path')
            os.system(
                'cp -f ' + commonlib.base_path + tar_name + '.tar.gz ' + cur_path)
            commonlib.untar(cur_path + tar_name + '.tar.gz')
            logging.info('Checking the commit IDs')
            new_commit = get_output(
                "git ls-remote " + options.git + " " + options.branch + " | head -n1 | awk '{print $1;}'")
            os.chdir(cur_path + tar_name)
            exist_commit = get_output('git log --format="%H" -n 1')
            if exist_commit == new_commit:
                logging.info(
                    "There is no new commit")
                os.chdir(cur_path)
                os.system('mv ' + cur_path + tar_name + ' hostCopy')
                os.system('rm -rf hostCopy/.git/')
                commonlib.tar(cur_path, 'hostCopy')
                move_hostCopy(cur_path, options.id)
                cleanup(cur_path, tar_name, options.id)
                return "repeated_run"
            else:
                pull_and_tar(cur_path, tar_name)
                move_hostCopy(cur_path, options.id)
                logging.info("trigger")
                cleanup(cur_path, tar_name, options.id)
                return "trigger"
        for subscriber in subscribers_json:
            if subscriber['GIT'] == options.git and subscriber['BRANCH'] == options.branch and compare_sub_tests(subscriber['TESTS'].split(','), options.tests.split(',')):
                logging.info("All combo found")
                check_flag = True
                if options.buildonly:
                    logging.info("Subscribing because of Build-only case")
                    check_flag = False
                    break
                logging.info('Copying tar to current path')
                os.system(
                    'cp -f ' + commonlib.base_path + tar_name + '.tar.gz ' + cur_path)
                commonlib.untar(cur_path + tar_name + '.tar.gz')
                logging.info('Checking the commit IDs')
                new_commit = get_output(
                    "git ls-remote " + options.git + " " + options.branch + " | head -n1 | awk '{print $1;}'")
                os.chdir(cur_path + tar_name)
                exist_commit = get_output('git log --format="%H" -n 1')
                if exist_commit == new_commit:
                    logging.info(
                        "This run has already been processed. Please check this Subscription List or manual triggers")
                    logging.info("no_run. Removing the subscription")
                    remove_sid(commonlib.base_path, options.id)

                    cleanup(cur_path, tar_name, options.id)
                    return "no_run"
                else:
                    pull_and_tar(cur_path, tar_name)
                    move_hostCopy(cur_path, options.id)
                    logging.info("trigger")
                    cleanup(cur_path, tar_name, options.id)
                    return "trigger"
    if not check_flag:
        if not options.buildonly:
            logging.info("Combo not found")
        if os.path.exists(commonlib.base_path + tar_name + '.tar.gz'):
            logging.info("Tar found")
            logging.info('Copying tar to current path')
            os.system(
                'cp -f ' + commonlib.base_path + tar_name + '.tar.gz ' + cur_path)
            commonlib.untar(cur_path + tar_name + '.tar.gz')
            new_commit = get_output(
                "git ls-remote " + options.git + " " + options.branch + " | head -n1 | awk '{print $1;}'")
            os.chdir(cur_path + tar_name)
            exist_commit = get_output('git log --format="%H" -n 1')
            logging.info('Comparing the commits')
            if exist_commit == new_commit:
                logging.info(
                    "Performing different tests for same tar and same commit")
                logging.info('Removing git files for the only copy')
                os.chdir(cur_path)
                os.system('mv ' + cur_path + tar_name + ' hostCopy')
                os.system('rm -rf hostCopy/.git/')
                commonlib.tar(cur_path, 'hostCopy')
                move_hostCopy(cur_path, options.id)

                complete_json(options)
                logging.info("trigger")
                cleanup(cur_path, tar_name, options.id)
                return "trigger"
            else:
                pull_and_tar(cur_path, tar_name)
                move_hostCopy(cur_path, options.id)

                complete_json(options)
                logging.info("trigger")
                cleanup(cur_path, tar_name, options.id)
                return "trigger"
        else:
            logging.info("Cloning new tar")
            logging.info(
                "Fetching %s from branch %s", options.git, options.branch)
            os.system('git clone -b ' + options.branch +
                      ' ' + options.git + ' ' + tar_name)
            logging.info('Making a host copy')
            os.system('cp -r ' + cur_path + tar_name + ' hostCopy')
            commonlib.tar(cur_path, tar_name)
            os.chdir(cur_path)
            logging.info('Copying tar to Jenkins path')
            os.system(
                'cp -f ' + cur_path + tar_name + '.tar.gz ' + commonlib.base_path)

            os.system('rm -rf hostCopy/.git')
            commonlib.tar(cur_path, 'hostCopy')
            os.chdir(cur_path)
            move_hostCopy(cur_path, options.id)
            complete_json(options)
            logging.info("trigger")
            cleanup(cur_path, tar_name, options.id)
            return "trigger"

if __name__ == "__main__":
    main()
