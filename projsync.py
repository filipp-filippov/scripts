#!/usr/bin/python3

from jira import JIRA
import argparse
import sys
import re

##Credentials
fileName=('/root/.creds')
fileIN = open(fileName, "r")
creds=fileIN.readline().strip('\n').split('%')
username=creds[0]
password=creds[1]
server=creds[2]

##Get arguments.
parser = argparse.ArgumentParser(description='You have to specify 2 arguments that describes source project and destionation peroject.')
parser.add_argument('--source', action='store', help='Source Project')
parser.add_argument('--dest', action='store', help='Destination Project')
args = parser.parse_args()

if not args.source or not args.dest:
 parser.print_help()
 sys.exit()

##Acess Jira and get info.
jira = JIRA(server=server,basic_auth=(username,password))
projSrc = jira.project_components(args.source)
projDst = jira.project_components(args.dest)

###Component match
cMatch=re.compile('^BFB.*')

###Get 'raw' lists (Jira classes are not so handy)
listSrc=[]
listDst=[]

for i in projSrc:
 if cMatch.match(str(i)):
  listSrc.append(str(i))
  
for i in projDst:
 if cMatch.match(str(i)):
  listDst.append(str(i))

###Get absent strings
toAdd=[]

for item in listSrc:
 if item not in listDst:
  toAdd.append(item)

####Add absent strings to project components.
if toAdd != []:
 for item in toAdd:
  print ("Adding absent component:", item)
  jira.create_component(name=item,project=args.dest,description='Business Component',assigneeType='UNASSIGNED')
else:
 print ("Nothing to add.")
