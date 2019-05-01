#!/usr/bin/python

##### IMPORTS

from getpass import getpass
from pyzabbix import ZabbixAPI
import os
import sys
import argparse
import random
import commands
import psycopg2

###Misc
charrange=['\\','`','*','_','{','}','[',']','(',')','>','#','+','-','!','$','\'']

###Zabbix access
gca=commands.getoutput('/opt/get-cred zapi')
zapi = ZabbixAPI('http://myzabbix.my/zabbix/')
zapi.login('zapi', gca)


###Setting up command line
parser=argparse.ArgumentParser()
parser.add_argument('--host', action='store', help='Operations only for given host')
parser.add_argument('--detail', action='store_true', help='Show details')
parser.add_argument('--debug', action='store_true', help='Turn on debug output')
parser.add_argument('--execute', action='store_true', help='Switch this flag to execute operations')
parser.add_argument('--proxy', action='store', help='Relative proxy')
parser.add_argument('--short', action='store_true', help='Any errors?')
parser.add_argument('--fixall', action='store_true', help='Fix all dependecies on all proxies')
args=parser.parse_args()

###Check that user provided some args
if len(sys.argv) < 2:
 parser.print_usage()
 exit()

###DICTIONARY FOR PROXIES

####Setting up dictionary for proxies
proxyHostId = [str(i['hostid']) for i in zapi.host.get(output=['extend','name'], search={ 'name': 'observer-' })]
proxyDict = []
#NativeDepTriggers 1st cloumn
for z in zapi.trigger.get(hostids=proxyHostId, output=['triggerid'], expandData='true', search={ 'description' : ' DEP' }):
 for a in zapi.host.get(triggerids=z, selectTriggers='true', output=['hostid','triggers','name']):
  for b in zapi.proxy.get(output=['host']):
   for c in zapi.host.get(templateids='3815', expandData='true', selectMacros=['macro','value'],filter={'macro': '{$PX_NAME}'}):
    for d in c['macros']:
     if d['value'] == b['host']:
      if c['hostid'] == a['hostid']:
       proxyDict.append(dict([('triggerid', str(z['triggerid'])), ('hostid', str(a['hostid'])), ('proxyid', str(b['proxyid'])), ('hostname', str(a['name'])),('proxyname', str(b['host']))]))
 
##Triggerids of proxies
proxyTriggerIds = []
for px in proxyDict: proxyTriggerIds.append(str(px['triggerid']))

#####GetData functions
###Uniq
def uniq(vals):
 return dict.fromkeys(vals).keys()

###All proxy triggerids
proxyIds = [proxy['proxyid'] for proxy in proxyDict]

###Al hosts that belong to one of proxy
global proxyHosts
proxyHosts = []
for host in zapi.host.get(proxyids=proxyIds):
 proxyHosts.append(host['hostid'])

###Get all triggers with dependencies
global allDepTrs
conn=psycopg2.connect("dbname='zabbix' user='zabbix'")
cur = conn.cursor()
cur.execute("""SELECT triggerid_down FROM trigger_depends""")
allDepTrs = str(cur.fetchall()).replace('\'', '').replace('(', '').replace(')', '').replace(',', '').replace('L', '').replace(']', '').replace('[', '').split()

###All hosts with deps
global allDepHosts
allDepHosts = []
for trigger in zapi.trigger.get(triggerids=allDepTrs, output=['extend','hosts','flags'], selectHosts='yes', selectDependencies='true', expandData='true'):
 allDepHosts.append(trigger['hosts'][0]['hostid'])
 allDepHosts = uniq(allDepHosts)

### Hosts with dependencies and not monitored by proxy
global hostsWithoutProxy
hostsWithoutProxy = (list(set(allDepHosts) - set(proxyHosts)))

###Get any proxy value using any another proxy value
def getProxyItem(findVal, item):
 for proxy in proxyDict:
  for pxVal in proxy.values():
   if findVal == pxVal:
    return proxy[item]
    
###GetDetailed info about trigger's attributes
def TrsDetail(hid):
 return zapi.trigger.get(triggerids=hid, selectDependencies='true', expandData='true', expandDescription='true', output='extend')

def proxyGetHosts(proxy, key):
 global proxy_proxyId
 global proxy_belongHosts
 proxyId = getProxyItem(proxy, 'proxyid')
 proxy_belongHosts = []
 for host in zapi.host.get(proxyids=proxyId, expandData='true', output=['extend','name','hostid']):
  proxy_belongHosts.append(host[key])
 return proxy_belongHosts

def getHostObjects(host):
 global host_hostname
 global host_data
 global host_hostId
 global host_hostProxyId
 global host_hostTriggerIds
 global host_hostProxyName
 global host_hostProxyTriggerId
 global host_hostDepTrs
 global host_hostIndepTrs
 global host_hostDepTrsWrong
 global host_hostTrsDetail
 global host_hostWrongProxyTrs
 global trigger_deplist
 global host_wrongTrProxy
 host_hostDepTrs = []
 trigger_deplist = []
 host_hostIndepTrs = []
 host_hostDepTrsWrong = []
 host_data = zapi.host.get(search={'name': host}, output=['extend','triggers','hostid','proxy_hostid'], expandData='true', selectTriggers='true') #with_triggers='true'
 host_hostId = host_data[0]['hostid']
 host_hostTriggerIds = [str(trigger['triggerid']) for trigger in host_data[0]['triggers']]
 host_hostProxyId = host_data[0]['proxy_hostid']
 host_hostProxyName = getProxyItem(host_hostProxyId, 'proxyname')
 host_hostProxyTriggerId = getProxyItem(host_hostProxyId, 'triggerid')
 host_hostTrsDetail = TrsDetail(host_hostTriggerIds)
 host_hostWrongProxyTrs = [trid for trid in proxyTriggerIds if trid != host_hostProxyTriggerId]
 for trigger in host_hostTrsDetail:
  if (trigger['dependencies'] != [] and trigger['flags'] != '4'): #try it
   for dep in trigger['dependencies']:
    if dep['triggerid'] == host_hostProxyTriggerId and [dep['triggerid'] for dep in trigger['dependencies'] if dep['triggerid'] in host_hostWrongProxyTrs] == [] and trigger['flags'] != '4':
     host_hostDepTrs.append(str(trigger['triggerid']))
    elif dep['triggerid'] in host_hostWrongProxyTrs:
     host_hostDepTrsWrong.append(str(trigger['triggerid']))
  if (trigger['dependencies'] == [] or [dep['triggerid'] for dep in trigger['dependencies'] if dep['triggerid'] in proxyTriggerIds] == []) and trigger['flags'] != '4':
   host_hostIndepTrs.append(str(trigger['triggerid']))
 for trigger in TrsDetail(host_hostDepTrsWrong):
  for dep in trigger['dependencies']:
   getProxyItem(dep['triggerid'], 'proxyname')
   if getProxyItem(dep['triggerid'], 'proxyname'):
    host_wrongTrProxy = getProxyItem(dep['triggerid'], 'proxyname')

def hostHealthCheck(host):
 print host
 if host_hostProxyName:
  print 'Host monitored by proxy:', host_hostProxyName 
 else:
  print 'Host not monitored by any proxy.'
 print 'Total number of host triggers:', len(host_hostTriggerIds)
 if len(host_hostDepTrs) == '0' and len(host_hostIndepTrs) == 0 and len(host_hostDepTrsWrong) == 0:
  print 'Host don\'t have any dependencies'
 if len(host_hostDepTrs) != '0':
  print 'Number of triggers with correct dependencies:', len(host_hostDepTrs)
  if args.detail:
   for trigger in TrsDetail(host_hostDepTrs):
    for dep in trigger['dependencies']:
     if dep['triggerid'] == host_hostProxyTriggerId and dep['triggerid'] not in host_hostWrongProxyTrs:
      print '| {0:5} | {1:55} | Depends on proxy: {2:11} | Hostname: {3} |'.format(trigger['triggerid'], trigger['description'], host_hostProxyName, trigger['hostname'])
 else: 
  print '(!) All triggers dependencies are incorrect'
 if len(uniq(host_hostDepTrsWrong)):
  print 'Number of triggers with incorrect dependencies:', len(uniq(host_hostDepTrsWrong))
  if args.detail:
   for trigger in TrsDetail(uniq(host_hostDepTrsWrong)):
    print '| {0:5} | {1:55} | Dependes on proxy: {2:11}| Hostname: {3} |'.format(trigger['triggerid'], trigger['description'], host_wrongTrProxy, trigger['hostname'])
 if len(host_hostIndepTrs) != 0:
  print 'Number of triggers that haven\'t dependencies:', len(host_hostIndepTrs)
  if args.detail:
   for trigger in TrsDetail(host_hostIndepTrs):
    print '| {0:5} | {1:55} | Hostname: {2} |'.format(trigger['triggerid'], trigger['description'], trigger['hostname'])
 if (args.execute and not args.short) or args.debug:
  print '#####\tFixing\t#####'

###Fix indep
 for trigger in host_hostIndepTrs:
  if args.debug or (args.execute and not args.short):
   print '| ADD DEP | {0:5} <- {1:6} | Proxy: {2:9} |'.format(trigger, host_hostProxyTriggerId, host_hostProxyName)
  if args.execute:
   if args.debug:
    print trigger
    print host_hostProxyTriggerId
   zapi.trigger.adddependencies(triggerid=trigger, dependsOnTriggerid=host_hostProxyTriggerId)
 if len(host_hostIndepTrs) != '0':
  print 'Total:', len(host_hostIndepTrs)

###Fix dep
 if args.debug or (args.execute and not args.short):
  if len(TrsDetail(uniq(host_hostDepTrsWrong))) != 0:
   for trigger in uniq(host_hostDepTrsWrong):
    print '| DEL DEP | {0:5} -> {1:6} | Proxy: {2:9} |'.format(trigger, getProxyItem(host_wrongTrProxy, 'triggerid') ,host_wrongTrProxy)
    print '| ADD DEP | {0:5} <- {1:6} | Proxy: {2:9} |'.format(trigger, host_hostProxyTriggerId, host_hostProxyName)
  if args.execute:
   if args.debug:
    print host_hostDepTrsWrong
   for trigger in TrsDetail(uniq(host_hostDepTrsWrong)):
    trigger_deplist = []
    if args.debug:
     print 'Trigger deplist (should be empty)', trigger_deplist
     print 'Operation trigger:', trigger['triggerid'], trigger['description']
    for dep in trigger['dependencies']:
     if args.debug:
      print 'Dep to append to new deplist:', dep['triggerid']
     trigger_deplist.append(dep['triggerid'])
     if args.debug:
      print 'New deplist after append dep:', trigger_deplist
    zapi.trigger.deletedependencies(triggerid=trigger['triggerid'])
    if args.debug:
     print 'Deps deleted, zeroed triggerid', trigger['triggerid']
     print trigger_deplist
     print 'Operate wrong Trigger:', trigger['description']
    for trigger_wrong in host_hostWrongProxyTrs: ###1
     if args.debug:
      print 'Trigger_WRONG', trigger_wrong
      print 'Trigger deplist:', trigger_deplist, 'Trigger:', trigger['description']
     if trigger_wrong in trigger_deplist:
      trigger_deplist.remove(trigger_wrong)
      if args.debug:
       print 'Nwe deplist after delete wrong trigger:', trigger_deplist, 'Wrong trigger:', trigger_wrong
     if host_hostProxyTriggerId not in trigger_deplist: #or trigger_deplist != []:
      if args.debug:
       print 'Trigger new deplist before append dependencies (Should be empty)', trigger_deplist
      trigger_deplist.append(host_hostProxyTriggerId)
      if args.debug:
       print 'Trigger deplist after append dependency:', trigger_deplist
     zapi.trigger.deletedependencies(triggerid=trigger['triggerid'])
    for trigger_dep in (uniq(trigger_deplist)):
     if args.debug:
      print 'triggers to add', (uniq(trigger_deplist))
      print 'triggerid from start', trigger['triggerid']
      print 'triggerid from deps', trigger_dep
     zapi.trigger.adddependencies(triggerid=trigger['triggerid'], dependsOnTriggerid=trigger_dep)
     if args.debug:
      print 'Dependency added:', trigger_dep
   print 'Total fixes:', len(host_hostDepTrsWrong)
 
def checkProxyTriggers(proxy):
 global wrongProxyDeps
 wrongProxyDeps = []
 for trigger in zapi.trigger.get(hostids=hostsWithoutProxy, output='extend', expandData='true', selectDependencies='true'):
  for dep in trigger['dependencies']:
   if dep['triggerid'] == getProxyItem(proxy, 'triggerid'):
    wrongProxyDeps.append(trigger['triggerid'])
    wrongProxyDeps = uniq(wrongProxyDeps)
 return wrongProxyDeps
    

def fixproxy(proxy):
 global proxy_ProbsNum
 global totalProxyProbsNum
 proxy_ProbsNum = 0
 if args.debug:
  print "Starting fixproxy procedure..."
 proxyGetHosts(proxy, 'name')
 proxy_hostsTriggers=[]
 proxy_hostsWrongTriggers=[]
 proxy_hostsDepTriggers=[]
 proxy_hostsIndepTriggers=[]
 checkProxyTriggers(args.proxy)
 for host in proxy_belongHosts:
  getHostObjects(host)
  for trigger in host_hostTriggerIds:
   proxy_hostsTriggers.append(trigger)
  for trigger in  host_hostDepTrsWrong:
   proxy_hostsWrongTriggers.append(trigger)
  for trigger in host_hostDepTrs:
   proxy_hostsDepTriggers.append(trigger)
  for trigger in host_hostIndepTrs:
   proxy_hostsIndepTriggers.append(trigger)
  if args.debug and not args.short or (args.execute and not args.short) and not args.short:
   print 'Hostname: {0}'.format(host)
   hostHealthCheck(host)
 if (args.proxy and args.short):
  totalProxyProbsNum = 0
  proxy_ProbsNum = len(wrongProxyDeps) + len(proxy_hostsIndepTriggers) + len(proxy_hostsWrongTriggers)
  totalProxyProbsNum = totalProxyProbsNum + proxy_ProbsNum
  print totalProxyProbsNum
  sys.exit()
 if args.debug or args.proxy: 
  if wrongProxyDeps != []:
   print 'Hosts that not montored by proxy, but have relations with proxy:', checkProxyTriggers(proxy)
   print 'Total hosts monitored by {0} : {1}'.format(proxy, len(proxy_belongHosts))
   print 'Total triggers of proxy hosts:', len(proxy_hostsTriggers)
   print 'Total triggers with correct dependencies:', len(proxy_hostsDepTriggers)
   print 'Total triggers without dependencies:', len(proxy_hostsIndepTriggers)
   print 'Total triggers with incorrect dependencies:', len(proxy_hostsWrongTriggers)
 elif args.fixall:
  if args.short:
   proxy_ProbsNum = len(wrongProxyDeps) + len(proxy_hostsIndepTriggers) + len(proxy_hostsWrongTriggers)
   totalProxyProbsNum = totalProxyProbsNum + proxy_ProbsNum
  if args.debug or args.detail:
   proxy_ProbsNum = len(wrongProxyDeps) + len(proxy_hostsIndepTriggers) + len(proxy_hostsWrongTriggers)
   totalProxyProbsNum = totalProxyProbsNum + proxy_ProbsNum
   print "Proxy is:", proxy
   print len(wrongProxyDeps), len(proxy_hostsIndepTriggers), len(proxy_hostsWrongTriggers)
   print 'WrongDeps : {0} NoDeps : {1} WrongTrs : {2}'.format(wrongProxyDeps, proxy_hostsIndepTriggers, proxy_hostsWrongTriggers)

def main():
 global totalProxyProbsNum
 if args.host:
  getHostObjects(args.host)
  hostHealthCheck(args.host)

 if args.proxy:
  fixproxy(args.proxy)

 if args.fixall:
  avaliableProxies = [item['proxyname'] for item in proxyDict]
  for proxy in avaliableProxies:
   if args.debug or args.execute or args.detail:
    fixproxy(proxy)
   else:
    totalProxyProbsNum = totalProxyProbsNum + proxy_ProbsNum
    print totalProxyProbsNum

main()

