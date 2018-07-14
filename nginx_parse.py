#!/usr/bin/python

import argparse
import sys
import operator

parser=argparse.ArgumentParser()
parser.add_argument('--file', action='store', help='Specify the full path to logfile')
args=parser.parse_args()

if len(sys.argv) < 2:
 parser.print_usage()
 sys.exit()

commdict=[]
alterdict={}

##open logfile
a=open(args.file)

##get ip/bytes value from all strings and put them in list of key/values
for i in a.readlines(): commdict.append(dict([(i.split(' ')[0], i.split(' ')[9])]))

##get key/values from common array and set new dict. Group values by keys ip/bytes
for item in commdict:
 if item.keys()[0] != '-':
  alterdict.setdefault(item.keys()[0],[]).append(item.values()[0])

##summarize values. Replace multiple values with sum of them.
try:
 for ip, bytes in alterdict.items():
  alterdict[ip] = sum([int(i) for i in bytes])
except ValueError:
 print 'Value error for key:', ip

##Return 10 items sorted by highest values, desc.
for item in sorted(alterdict.items(), key=operator.itemgetter(1), reverse=True)[0:10]:
 print('Address: {0}\t| Total body_bytes_sent: {1}'.format(item[0], item[1]))
