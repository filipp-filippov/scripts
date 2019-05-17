#!/usr/bin/python

import sys
import argparse
import base64

parser=argparse.ArgumentParser()
parser.add_argument('--get', action='store', help='Record which value you like to get')
parser.add_argument('--store', action='store', help='Add new Record to store')
parser.add_argument('--update', action='store', help='Record to update')
parser.add_argument('--value', action='store', help='New value of Record. DO NOT put unencrypted data here')
parser.add_argument('--delete', action='store', help='Record to delete')
parser.add_argument('--key', action='store', help='Record metadata')
args=parser.parse_args()

###Check if all arguments were set correctly
for arg_action in args.__dict__:
  if args.__dict__[arg_action] is not None:
    if arg_action in ['get', 'store', 'update', 'delete']:
      action=arg_action
      if action in ['store', 'update'] and (args.__dict__['value'] is None or args.__dict__['key'] is None):
        print 'Can\'t proceed without --value and --key argument\n'
        parser.print_help(sys.stderr)
        sys.exit(1)
      if action in ['get', 'delete'] and args.__dict__['key'] is None:
        print 'Can\'t proceed without --key argument\n'
        parser.print_help(sys.stderr)
        sys.exit(1)
      if args.__dict__['value'] is not None:
        try:
          base64.decodestring(args.__dict__['value'])
        except:
          print "String should be correct"
          sys.exit(1)

###Set filename to parse
secret_file = '/path/to/secret'

###Define actions func

def getpass(username, key):
  global get_pass
  get_pass = None
  s_data = open(secret_file, 'r')
  for secret in s_data.readlines():
    if secret.split(':')[0] == username:
      if secret.split(':')[1] == key:
        get_pass=secret.split(':')[2]
  return get_pass

def storepass(username, key, value):
  s_data = open(secret_file, 'a')
  s_data.write(username + ':' + key + ':' + value + '\n')

def updatepass(username, key, value):
  s_data = open(secret_file, 'r')
    datalines=s_data.readlines()
  newdatalines=[]
  for record in datalines:
    if record.split(':')[0] == username:
      if record.split(':')[1] == key:
        newdatalines.append(record.replace(record.split(':')[2], value + '\n'))
    else:
      newdatalines.append(record)
  s_data = open(secret_file, 'w')
  for line in newdatalines:
    s_data.write(line)
  s_data.close()

def deletepass(username, key):
  s_data = open(secret_file, 'r')
  datalines=s_data.readlines()
  newdatalines=[]
  for record in datalines:
    if record.split(':')[0] != username:
      if record.split(':')[1] != key:
        newdatalines.append(record)
  s_data = open(secret_file, 'w')
  for line in newdatalines:
    s_data.write(line)
  s_data.close()


###Perform actions
if action == 'get':
  try:
    print base64.b64decode(getpass(args.get, args.key)).rstrip().strip('\'')
  except TypeError:
    print 'Password for username/key combination is not found'
    sys.exit(1)
  except IOError:
    print 'Insufficient permissions'
    sys.exit(1)

if action == 'store':
  try:
    getpass(args.store, args.key)
  except IOError:
    print 'Insufficient permissions'
    sys.exit(1)
  if get_pass is not None:
    print 'This resource already exitsts'
    sys.exit(1)
  storepass(args.store, args.key, args.value)

if action == 'update':
  try:
    getpass(args.update, args.key)
  except IOError:
    print 'Insufficient permissions'
    sys.exit(1)
if get_pass is None:
    print 'This resource does not exitsts'
    sys.exit(1)
  updatepass(args.update, args.key, args.value)

if action == 'delete':
  try:
    getpass(args.delete, args.key)
  except IOError:
    print 'Insufficient permissions'
    sys.exit(1)
  if get_pass is None:
    print 'This resource does not exitsts'
    sys.exit(1)
  deletepass(args.delete, args.key)
