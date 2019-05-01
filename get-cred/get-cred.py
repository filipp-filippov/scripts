#!/usr/bin/python

import sys
import argparse
import base64

parser=argparse.ArgumentParser()
parser.add_argument('--get', action='store', help='Key which value you like to get')
parser.add_argument('--store', action='store', help='Add new key-value to store')
parser.add_argument('--update', action='store', help='Key to update')
parser.add_argument('--value', action='store', help='New value of key. DO NOT put unencrypted data here')
parser.add_argument('--delete', action='store', help='Key to delete')
args=parser.parse_args()

###Check if all arguments were set correctly
for arg_action in args.__dict__:
  if args.__dict__[arg_action] is not None:
    action=arg_action
    if action in ['store', 'update'] and args.__dict__['value'] is None:
      print 'Can\'t proceed without --value argument\n'
      parser.print_help(sys.stderr)
      sys.exit(1)
    if args.__dict__['value'] is not None:
      try:
        base64.decodestring(args.__dict__['value'])
      except:
        print "String should be correct"
        sys.exit(1)

###Set filename to parse
secret_file = '/tmp/secret'

###Define actions func

def getpass(resource):
  global get_pass
  get_pass = None
  s_data = open(secret_file, 'r')
  for secret in s_data.readlines():
    if secret.split(':')[0] == resource:
      get_pass=secret.split(':')[1]
  return get_pass

def storepass(key, value):
  s_data = open(secret_file, 'a')
  s_data.write(key + ':' + ' ' + value + '\n')

def updatepass(key, value):
  s_data = open(secret_file, 'r')
  datalines=s_data.readlines()
  newdatalines=[]
  for record in datalines:
    if record.split(':')[0] == key:
      newdatalines.append(record.replace(record.split(':')[1], '\ ' + value + '\n'))
    else:
      newdatalines.append(record)
  s_data = open(secret_file, 'w')
  for line in newdatalines:
    s_data.write(line)
  s_data.close()

def deletepass(key):
  s_data = open(secret_file, 'r')
  datalines=s_data.readlines()
  newdatalines=[]
  for record in datalines:
    if record.split(':')[0] != key:
      newdatalines.append(record)
  s_data = open(secret_file, 'w')
  for line in newdatalines:
    s_data.write(line)
  s_data.close()


###Perform actions
if action == 'get':
  try:
    print base64.b64decode(getpass(args.get)).rstrip().strip('\'')
  except TypeError:
    print 'Key not found'
    sys.exit(1)
  except IOError:
    print 'Insufficient permissions'
    sys.exit(1)

if action == 'store':
  try:
    getpass(args.store)
  except IOError:
    print 'Insufficient permissions'
    sys.exit(1)
  if get_pass is not None:
    print 'This resource already exitsts'
    sys.exit(1)
  storepass(args.store, args.value)

if action == 'update':
  try:
    getpass(args.update)
  except IOError:
    print 'Insufficient permissions'
    sys.exit(1)
  if get_pass is None:
    print 'This resource does not exitsts'
    sys.exit(1)
  updatepass(args.update, args.value)

if action == 'delete':
  try:
    getpass(args.delete)
  except IOError:
    print 'Insufficient permissions'
    sys.exit(1)
  if get_pass is None:
    print 'This resource does not exitsts'
    sys.exit(1)
  deletepass(args.delete)