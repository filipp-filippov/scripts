#!/usr/bin/python
import os
import sys
import time
import string
import smtplib
import subprocess
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

now = (time.strftime("%d-%m-%Y"))
### This script has crated for analisyng disk space usage and prevent fileserver overflow.

def statfunc():
## Creating file 
	now = (time.strftime("%d-%m-%Y"))
	f = open('/home/admin/fs/' +(now) +'.stat', 'w')
	f2 = open('/home/admin/diff/' +(now) +'.stat', 'w')
## Defining command
	du = "/usr/bin/du"
	du_arg = "-lshb"
	du_arg2 = "-lsh"
	dpath = "/mnt/fileserver/files/"
	dlist = os.walk(os.path.join(dpath)).next()[1]
## Preparing command
	for i in dlist:
	   curDir = os.path.join(dpath, i)
	   cmd = [du, du_arg, curDir]
## Executing command and intercept shell stdout
	   process = subprocess.Popen(cmd, stdout=subprocess.PIPE)
	   out = process.stdout.read()
## Writing result to file
	   f.write(out)
	f.close()
###FIXME Duplicate function
	for i in dlist:
           curDir = os.path.join(dpath, i)
           cmd = [du, du_arg2, curDir]
## Executing command and intercept shell stdout
           process = subprocess.Popen(cmd, stdout=subprocess.PIPE)
           out = process.stdout.read()
## Writing result to file
           f2.write(out)
        f2.close()

### Result comparsion

def difffunc():
## Select filenames to compare
    array=[]
    path = "/home/admin/fs/"
    flist = os.listdir(path)
    first = 0
    second = 0
    for i in flist:
	    ftime = os.stat((path) + (i))[8]
	    sftime = str(ftime)
	    out = (sftime + ' ' + i)
	    array.append(out)
    iarray = array
    for i in array:
	    challenger = i.split(' ')[0]
	    if first < challenger:
	    	first = challenger
	    	first_str = i
	    first_file = first_str.split(' ')[1]
    array.remove(first_str)
    for i in array:
	    challenger = i.split(' ')[0]
	    if second < challenger:
	    	second = challenger
	    	second_str = i
	    second_file = second_str.split(' ')[1]
## Diff Time !
    now = (time.strftime("%d-%m-%Y"))
    tool = "/usr/bin/diff"
    arg1 = "--side-by-side"
    arg2 = "--suppress-common-lines" # Don't show equal strings
    f = file('/home/admin/diff/' +(now) +'.diff', 'w')
    f1 = os.path.join(path, first_file)
    f2 = os.path.join(path, second_file)
    cmd = [tool, arg1, arg2, f1, f2]
    drum = []
## Executing and gathering STDOUT
    diff = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    iexit = diff.stdout.read()
## Operating STDOUT 
    d = iexit.split()
    v = [i.strip('|').strip('\t').strip('\n').strip('\'\'').strip(',') for i in d]
    vn = str(v).strip('\'\'').strip('\"').replace('\"', '').replace('\'\'', '').replace(',', '')
    useful = vn.strip('\[').strip('\]').split()
## Comparsion & getting result
    path = useful[1::2]
    values = useful[0::2]
    upath = path[0::2]
    av = values[0::2]
    bv = values[1::2]
    av = [int(i.strip('\"').strip('\'')) for i in av]
    bv = [int(i.strip('\"').strip('\'')) for i in bv]
## Unification data containers
    for a, b, c in zip(av, bv, upath):
	diff = (a-b)/1048576
## Ok, we got output, and then we need to fromat it !
	outstr = str(c).split('/')[4].strip('\'').ljust(20)+'folder has changed: '.ljust(15)+str(diff).rjust(7)+'MBytes'.rjust(7)
	f.write((outstr) + '\n')
    f.close()

## Simple df

def simple():

    fl = open('/home/admin/diff/simple', 'w')
    cbin = '/bin/df'
    arg = '-h'
    cmd = [cbin, arg]
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    pout = process.stdout.read()
    fl.write(pout)
    fl.close()

## Send Mail
def mailfunc():

    msg = MIMEMultipart()
    cur_stat = open('/home/admin/diff/' +(now) +'.stat', 'rb')
    stat_file = open('/home/admin/diff/' +(now) +'.diff', 'rb')
    simple_stat = open('/home/admin/diff/simple', 'rb')
    part1 = MIMEText(stat_file.read().encode("utf-8"), 'plain', 'utf-8')
    part2 = MIMEText(cur_stat.read().encode("utf-8"), 'plain', 'utf-8')
    part3 = MIMEText(simple_stat.read().decode("utf-8"), 'plain', 'utf-8')
    stat_file.close()
    cur_stat.close()
    simple_stat.close()

    msg['Subject'] = 'Cron report'
    msg['From'] = 'Cron'
    msg.attach(part1)
    msg.attach(part2)
    msg.attach(part3)
    print msg
    m = smtplib.SMTP()
    m.connect("mail.domain.ru", 25)
    m.sendmail("cron@domain.ru", "admin@domain.ru", msg.as_string())
    m.quit()

def main():
	statfunc()
	difffunc()
	simple()
	mailfunc()
main()
