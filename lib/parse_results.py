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

import urllib
import datetime
from bs4 import BeautifulSoup
import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--link", action="store", dest="link", help="Specify the link of the HTML to be parsed\
                        Usage: --link http://ltc-jenkins.aus.stglabs.ibm.com/korg/EM/28/testresults/job_report.html")
    parser.add_argument("--file", action="store", dest="files", help="Specify HTML File to be parsed\
                        Usage: --file /home/usrContent/job_report.html")
    parser.add_argument("--table", action="store", dest="table", help="Specify the table to be parsed in HTML\
                        Usage: --table t1")

    options = parser.parse_args()
    if options.link:
        f = urllib.urlopen(options.link)
    elif options.files:
        f = open(options.files,'r')

    myfile = f.read()
    soup = BeautifulSoup(myfile, 'html.parser')
    s = soup.find(id=options.table)
    rows = s.find_all('tr')
    pas = 0
    fail =0
    n = len(rows) - 1
    for row in rows:
        cells = row.find_all("td")
        for cell in cells:
            cell = cell.find_all("div")
            if len(cell) ==1:
                if cell[0].get_text() == "GOOD":
                    pas = pas + 1
    pas_val = (pas * 100)/n
    final_string = str(pas_val) + '__100'
    print final_string
    return final_string

if __name__ == "__main__":
    main()
