#!/usr/bin/python

##### Libs
from pyzabbix import ZabbixAPI
import dns
from dns import resolver
from dns import exception
import os
import sys
import socket
import argparse
import ipwhois
from ipwhois import IPWhois
import commands
import time

###Misc
h_qrator=[]
h_nqrator=[]
rs=resolver.Resolver()
rs.nameservers = [socket.gethostbyname('mynameserver.my')]
whois=IPWhois
null=None # With API it works only like that
p_tr_cnt=0
t_tr_cnt=[]
p_tr_ppt=0

###Zabbix access
gca=commands.getoutput('/opt/get-cred zapi')
zapi = ZabbixAPI('http://myzabbix.my/zabbix/')
zapi.login('zapi', gca)

#Read args
parser=argparse.ArgumentParser()
parser.add_argument('--sensor', action='store', help='Choose lookup point')
parser.add_argument('--detail', action='store_true', help='Show details')
parser.add_argument('--count', action='store_true', help='Count number of alerted triggers')
parser.add_argument('--dry', action='store_true', help='Dry run, just print without an action')
parser.add_argument('--setdep', action='store_true', help='Set dependencies')
parser.add_argument('--qrator', action='store_true', help='Only QRATOR hosts')
args=parser.parse_args()

if len(sys.argv) < 2:
 parser.print_usage()
 sys.exit()

if not args.sensor:
 print 'It will not gonna work without a --sensor argument'
 sys.exit()

##Template to find
qr_sys_h=zapi.host.get(filter={'name': '-URL qrator_system'})[0]['hostid']

##get ID of common group
if args.sensor == 'ALIEN_HOST_UFO':
 h_gid=zapi.hostgroup.get(filter={'name': 'ZABBIX - Tezt - URL trigger'})[0]['groupid']
 s_templ='test_deps'
else:
 h_gid=zapi.hostgroup.get(filter={'name': '-URL'})[0]['groupid']
 s_templ='site'

##get hostids
h_hids=[i['hostid'] for i in zapi.usermacro.get(groupids=h_gid, output='extend', selectMacros='yes', with_hosts_and_templates='yes',selectTemplates='yes',filter={'macro': '{$DOMAIN_SITE}'})]
h_hids=[i['hostid'] for i in zapi.host.get(hostids=h_hids, monitored_hosts='yes')]

##get templateid
h_templid=zapi.template.get(hostids=h_hids, ouptput='extend', filter={'name': 'T_URL_' + s_templ})[0]['templateid']

###General functions
##get ASN Identifier
def get_ASN(ipaddr):
 return IPWhois(ipaddr).lookup_rdap()['asn_description'].split(',')[0]

##Functions
##Get sensors triggerids func
def get_SENSORS(arg):
 if args.qrator:
  return zapi.trigger.get(expandDescription='yes',filter={'description': 'Qrator hosts via ' + arg + ' (DEP)'})[0]['triggerid']
 else:
  return zapi.trigger.get(expandDescription='yes',filter={'description': '-URL hosts via ' + arg + ' (DEP)'})[0]['triggerid']

##Get items from triggerids
def get_item(arg):
 return zapi.item.get(triggerids=arg, search={'key': 'w_sensor, checkurl'})

def c_group(i_list):
 global probs
 if i_list == []:
  return 0
 for item in i_list:
  state=''
  p_pts=0
  o_pts=0
  i_ts=int(str(time.time()).split('.')[0]) - 190
  if not int(len([i['value'] for i in zapi.history.get(history='0',itemids=item,time_from=i_ts)])) < '3':
   if args.detail:
    print 'Not enough values to proceed itemid:', item
   continue
  else:
   v_len=int(len([i['value'] for i in zapi.history.get(history='0',itemids=item,time_from=i_ts)]))
   for val in [i['value'] for i in zapi.history.get(history='0',itemids=item,time_from=i_ts)]:
    val=int(float(val))
    limit=int('10')
    if args.detail:
     print val, '>', limit, 'type:', type(val) 
    if val > limit:
     p_pts = p_pts + 1
    if not val > limit:
     o_pts = o_pts + 1
   if p_pts == v_len:
    state='Problem'
   if o_pts == v_len:
    state='OK'
   if (p_pts != v_len and o_pts != v_len):
    state='Not sure'
   if args.detail:
    print 'State of item:', item, 'is:', state 
   if state == 'Not sure' or state == 'Problem':
    probs=probs + 1
  if args.detail:
   print 'History values amount:', v_len, 'type:', type(v_len)
   print 'Problem points:', p_pts, 'type:', type(p_pts)
 return probs

##Get sensors macroames
#s_mname=get_SName(sensor)
w_sensor='{$' + args.sensor + '}'

##Get sensor(muffler) triggerid
s_tid=get_SENSORS(w_sensor)

##Get DEP trigger state
d_state=zapi.trigger.get(triggerids=s_tid)[0]['value']

########
##Find out if depend triggers alerted(Sensor requred) \\ count func Not so easy ==>
#Triggers value refresh does NOT working while dependency triggered, it causes kinda deadlock. SO it's fine to ENABLE DEP trigger, but it will never stand back in OK state. SO let's do Zabbix work for Zabbix. "We do know that you do love Zabbix, that's why we put Zabbix in your Zabbix..." ;)
if args.detail:
 print 'd_state is:', d_state, type(d_state)

if args.count:
#Add percentage
##Check if trigger already activated and:
##If not
 if d_state == '0':
  if args.detail:
   print 'We are at branch 0'
   print 'Stid is:', s_tid
   print 'hids is:', h_hids
   print 't_tr_cnt is:', t_tr_cnt

###Get total number of triggers with deps
  for trigger in zapi.trigger.get(hostids=h_hids, selectDependencies='true', output='extend', active='yes'):
   if (trigger['dependencies'] != [] and s_tid in [i['triggerid'] for i in trigger['dependencies']]):
    t_tr_cnt.append(trigger['triggerid'])

  for trigger in zapi.trigger.get(hostids=h_hids, selectDependencies='true', output='extend', active='yes'):
   if (trigger['dependencies'] != [] and s_tid in [i['triggerid'] for i in trigger['dependencies']]):
#    t_tr_cnt.append(trigger['triggerid'])
    if trigger['value'] == '1':
     p_tr_cnt = p_tr_cnt + 1
  print "%1.f" %(100 - float(len(t_tr_cnt) - p_tr_cnt) / len(t_tr_cnt) * 100)
  if args.detail:
   print 'Count is:', p_tr_cnt
   print 'Total Number is: ', len(t_tr_cnt)
   print 'Percentage is:', "%1.f" %(100 - float(len(t_tr_cnt) - p_tr_cnt) / len(t_tr_cnt) * 100)

######### If yes ############### :)
##Get history records
#Group calculations

 if d_state == '1':
  if args.detail:
   print 'We are at branch 1'
  probs=0
#Get itemids to analyse
  t_items=[] #triggered items
  c_items=[] #not triggered items
  for trigger in zapi.trigger.get(hostids=h_hids, selectDependencies='true', output='extend', active='yes'):
   if (trigger['dependencies'] != [] and s_tid in [i['triggerid'] for i in trigger['dependencies']]):
    if trigger['value'] == '1':
     t_items.append(get_item(trigger['triggerid'])[0]['itemid'])
    if trigger['value'] == '0':
     c_items.append(get_item(trigger['triggerid'])[0]['itemid'])
  res=int(c_group(t_items)) + int(c_group(c_items))
  if args.detail:
   print 'triggered:', t_items, 'Not triggered:', c_items
   print 'Result after calc:', res
  print res
 


########SET DEPENDENCIES

if (args.dry and not args.setdep) or (args.setdep and not args.dry):
 t_set = 0
##Get hosts

 for h_dn in zapi.usermacro.get(groupids=h_gid, templateids=h_templid, output='extend', selectMacros='yes', with_hosts_and_templates='yes',selectTemplates='yes',filter={'macro': '{$DOMAIN_SITE}'}):
  if args.sensor == 'ALIEN_HOST_UFO':
   h_qrator.append(h_dn['hostid'])
  else:
   try:
    for h_ip in rs.query(h_dn['value'].split('/')[0]):
      if get_ASN(h_ip) == 'QRATOR':
       h_qrator.append(h_dn['hostid'])
      else:
       if not get_ASN(h_ip) == 'QRATOR':
        h_nqrator.append(h_dn['hostid'])
   except dns.exception.DNSException:
    if args.detail:
     print 'Error while resolving', h_dn['value'].split('/')[0]

#Get triggerids where dependencies supposed to be
 h_grp=[]
 if args.qrator:
  h_grp=h_qrator
 else:
  h_grp=h_nqrator

 print h_grp

 for p_trigger in zapi.trigger.get(hostids=h_grp, selectDependencies='true', output='extend', selectHosts='true', expandDescription=null, filter={'description': '{$DOMAIN_SITE} via ' + w_sensor}):
  if s_tid not in [i['triggerid'] for i in p_trigger['dependencies']]:
   if not args.dry:
    zapi.trigger.adddependencies(triggerid=p_trigger['triggerid'], dependsOnTriggerid=s_tid)
    t_set = t_set + 1
   if args.dry or args.detail:
    t_set = t_set + 1
    print '| Dependency set for trigger: {0:5} | On host: {1:6} | From Trigger: {2:7} '.format(p_trigger['triggerid'], zapi.host.get(hostids=p_trigger['hosts'][0]['hostid'])[0]['name'], s_tid)
 print 'Total dependencies set:', t_set

 print 'Dependencies set sucessfully.'
