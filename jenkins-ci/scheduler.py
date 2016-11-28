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
# Author: Abdul Haleem <abdhalee@linux.vnet.ibm.com>

import os
import sys
import datetime
import json
import fcntl
import errno
import time
sys.path.append(
    os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir))
from lib import common_lib as commonlib
from datetime import date

SID = ''
sidfile = commonlib.base_path + SID + '/' + SID + '.json'
DATENOW = datetime.datetime.now().strftime('%Y_%m_%d')


def form_sid(sid, mailid, git, branch, tests):
    git = git.split('/')[-2]
    mailid = mailid.split('@')[0]
    if tests:
        mean_sid = sid + '-' + mailid + '-' + git + \
            '-' + branch + '-' + tests.replace(',', '-')
    else:
        mean_sid = sid + '-' + mailid + '-' + git + '-' + branch + '-'
    return mean_sid


def check_Qfile():
    '''
    This will check Q file in the path if present print the content
    else create a new q file
    '''
    if os.path.isfile(commonlib.schedQfile):
        print "\nFile Exists !, Current Jobs in Queue....\n"
        print_Q()

    else:
        Qfile = open(commonlib.schedQfile, 'w')
        if os.path.isfile(commonlib.schedQfile):
            print commonlib.schedQfile + ' Job file Created successfully !'
            Qfile.close()


def check_job_inQ(sid, mailid, git, branch, tests):
    '''
    Check if the given job is already in Q file
    else return Flase
    '''
    jobs = []
    while True:
        try:
            with open(commonlib.schedQfile, 'r') as Qfile:
                fcntl.flock(Qfile, fcntl.LOCK_EX | fcntl.LOCK_NB)
                jobs = Qfile.readlines()
                fcntl.flock(Qfile, fcntl.LOCK_UN)
            Qfile.close()
            for job in jobs:
                if form_sid(sid, mailid, git, branch, tests) == job.replace('\n', ''):
                    return True
            print sid + "   Job Not in Queue !!"
            return False
        except IOError as ex:
            if ex.errno != errno.EAGAIN:
                raise "waiting for queue file to unlock"
        else:
            print "waiting for queue file to unlock ... "
            time.sleep(0.1)


def add_job_inQ(sid, mailid, git, branch, tests):
    '''
    Append the new jobs to the Q
    '''
    while True:
        try:
            with open(commonlib.schedQfile, 'a') as Qfile:
                fcntl.flock(Qfile, fcntl.LOCK_EX | fcntl.LOCK_NB)
                Qfile.write(form_sid(sid, mailid, git, branch, tests))
                Qfile.write('\n')
                fcntl.flock(Qfile, fcntl.LOCK_UN)
                Qfile.close()
                return
        except IOError as ex:
            if ex.errno != errno.EAGAIN:
                raise "waiting for queue file to unlock"
        else:
            print "waiting for queue file to unlock ...."
            time.sleep(0.1)


def get_sid_list():
    '''
    Get the list of Subscription ID's from subscription.json
    '''
    sidlist = []
    subfile = commonlib.read_json(commonlib.base_path + 'subscribers.json')
    for sid in subfile:
        sidlist.append(sid['SID'])
    print sidlist
    return sidlist


def get_datafile_info(sid):
    '''
    for the given subscription id get me the data file path and information
    '''
    datafile = {}
    sidfile = commonlib.base_path + sid + '/' + sid + '.json'
    if os.path.isfile(sidfile):
        print sidfile
        datafile = commonlib.read_json(sidfile)
        return datafile
    else:
        print "%s  Error : Datafile not Found !" % sidfile
        return None


def update_datafile(sid, json_data):
    '''
    This will update the value of given key as json_data
    '''
    path = commonlib.base_path + sid + '/' + sid + '.json'
    if os.path.isfile(path):
        commonlib.update_json(path, json_data)


def oneday(cr_date):
    return str((datetime.datetime.strptime(cr_date, '%Y_%m_%d') + datetime.timedelta(days=1)).strftime('%Y_%m_%d'))


def oneweek(cr_date):
    return str((datetime.datetime.strptime(cr_date, '%Y_%m_%d') + datetime.timedelta(days=7)).strftime('%Y_%m_%d'))


def onemonth(cr_date):
    m, y = (cr_date.month + 1) % 12, cr_date.year + \
        ((cr_date.month) + 1 - 1) // 12
    if not m:
        m = 12
    d = min(cr_date.day, [31, 29 if y % 4 == 0 and not y % 400 ==
                          0 else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][m - 1])
    return cr_date.replace(day=d, month=m, year=y).strftime('%Y_%m_%d')


def get_subscrptn_date(sid):
    '''
    return the subscription date for the given sid
    '''
    dicts = {}
    subfile = commonlib.read_json(commonlib.base_path + 'subscribers.json')
    for dicts in subfile:
        if sid in dicts.values():
            subdate = datetime.datetime.now().strftime('%Y_%m_%d')
            if subdate < DATENOW:
                dicts['DATE'] = DATENOW
            return dicts['DATE']
    return None


def print_Q():
    '''
    List the waiting jobs in a Queue
    '''
    task = 0
    jobs = []
    if os.stat(commonlib.schedQfile).st_size != 0:
        while True:
            try:
                with open(commonlib.schedQfile, 'r') as Q:
                    fcntl.flock(Q, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    print " ------------------------------------------------------------"
                    print "| NO. |      SID's                                           |"
                    print " ------------------------------------------------------------"
                    jobs = Q.readlines()
                    fcntl.flock(Q, fcntl.LOCK_UN)
                    Q.close()
                    for job in jobs:
                        task = task + 1
                        print "   %s       %s" % (task, job.replace('\n', ''))
                    print "-------------------------------------------------------------\n"
                    return
            except IOError as ex:
                if ex.errno != errno.EAGAIN:
                    raise
            else:
                print "Waiting for queue file to unlock ..."
                time.sleep(0.1)
    else:
        print "\nQueue File Empty  !!\n"


def main():
    sublist = []
    check_Qfile()
    sublist = get_sid_list()
    for SID in sublist:
        json_data = get_datafile_info(SID)
        LASTRUN = json_data['LASTRUN']
        NEXTRUN = json_data['NEXTRUN']
        BUILDFREQ = json_data['BUILDFREQ']
        DATESUB = get_subscrptn_date(SID)
        MAILID = json_data['MAILID']
        TESTS = json_data['TESTS']
        GIT = json_data['URL']
        BRANCH = json_data['BRANCH']
        datenow = datetime.datetime.strptime(DATENOW, '%Y_%m_%d')
        while not check_job_inQ(SID, MAILID, GIT, BRANCH, TESTS):

            if LASTRUN is None:
                if BUILDFREQ == 'daily':
                    json_data['NEXTRUN'] = oneday(DATESUB)
                if BUILDFREQ == 'weekly':
                    json_data['NEXTRUN'] = oneweek(DATESUB)
                if BUILDFREQ == 'monthly':
                    DATESUB = datetime.datetime.strptime(DATESUB, '%Y_%m_%d')
                    json_data['NEXTRUN'] = onemonth(DATESUB)
                update_datafile(SID, json_data)
                print "always a candidate for Q"
                add_job_inQ(SID, MAILID, GIT, BRANCH, TESTS)
                if check_job_inQ(SID, MAILID, GIT, BRANCH, TESTS):
                    print SID + " Job added to Queue succesfully !"

                # udpate LASTRUN by KORG project, handling here for now
                # json_data['LASTRUN'] = date
                # update_datafile(SID, json_data)

            if LASTRUN is not None:
                if NEXTRUN is not None:
                    nextrun = datetime.datetime.strptime(NEXTRUN, '%Y_%m_%d')
                if nextrun <= datenow:
                    print "It is a candidate add for Q"
                    add_job_inQ(SID, MAILID, GIT, BRANCH, TESTS)
                    if check_job_inQ(SID, MAILID, GIT, BRANCH, TESTS):
                        print SID + " Job added to Queue succesfully !"

                    if BUILDFREQ == 'daily':
                        json_data['NEXTRUN'] = oneday(LASTRUN)
                    if BUILDFREQ == 'weekly':
                        json_data['NEXTRUN'] = oneweek(LASTRUN)
                    if BUILDFREQ == 'monthly':
                        LASTRUN = datetime.datetime.strptime(
                            LASTRUN, '%Y_%m_%d')
                        json_data['NEXTRUN'] = onemonth(LASTRUN)
                    update_datafile(SID, json_data)
                    # Update LAST RUN by korg, updating from here for now
                    # json_data['LASTRUN'] = date
                    # update_datafile(SID, json_data)
            break
    print "\nList all jobs in Queue . . .  \n"
    print_Q()

if __name__ == '__main__':
    main()
