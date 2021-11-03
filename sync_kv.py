#!/usr/bin/python

import requests
import json
import os
import sys
import argparse

parser=argparse.ArgumentParser()
parser.add_argument('--secret', action='store')
parser.add_argument('--clientid', action='store')
parser.add_argument('--appid', action='store')
parser.add_argument('--source', action='store')
parser.add_argument('--destination', action='store')
args=parser.parse_args()

#Set vars

workFolder = os.path.abspath(os.getcwd())
srcSecretsKeyList = []
srcSecretsList = []
srcSecretsDict = {}

#Get bearer

payload = {'grant_type': 'client_credentials', 'client_secret': args.secret, 'client_id': args.clientid, 'scope': 'https://vault.azure.net/.default'}
bToken = requests.post('https://login.microsoftonline.com/9247d46b-02d2-4e53-b9c4-ed4ec9aa859b/oauth2/v2.0/token', payload).json()['access_token']

# List & Dump KV secrets names

kvURL = args.source + '/secrets?api-version=7.2'
getHeaders = {'Authorization': 'Bearer ' + bToken }
srcInitSecretsData = requests.get(kvURL, headers=getHeaders).json()

##Dump
for secret in srcInitSecretsData['value']:
 try:
  srcSecretsKeyList.append(secret['id'].split('/')[4])
 except AttributeError:
  print('!AttrError!')
  continue

# Get & Dump KV secrets values

for secret in srcSecretsKeyList:
 secretData = requests.get(args.source + '/secrets/' + secret + '/?api-version=7.2', headers=getHeaders).json()
 secretKey = secretData.get('id').split('/')[4]
 secretValue = secretData.get('value')
 srcSecretsDict[secretKey] = secretValue

## Dump
 with open(workFolder + '/srcKvDump', 'a') as srcDumpFile:
  srcDumpFile.write('%s: %s\n' % (secretKey, secretValue))
 srcDumpFile.close()

print('Secrets successfully exported')

# Create secrets in DST keyvault & Set secrets values

putHeaders = { 'Content-Length': '0', 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + bToken }

for key, value in srcSecretsDict.items():
 secretName = key
 secretPayload = '{\"value\": \"' + value + '\"}'
 response = requests.put(args.destination + 'secrets/' + secretName + '/?api-version=7.2', data=secretPayload, headers=putHeaders)
 print(response.text)

