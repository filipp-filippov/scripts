#!/usr/bin/python

import requests
import json
import os
import sys
import argparse

parser=argparse.ArgumentParser()
parser.add_argument('--srcTenantId', action='store')
parser.add_argument('--srcSecret', action='store')
parser.add_argument('--srcClientId', action='store')
parser.add_argument('--srcKv', action='store')
parser.add_argument('--dstTenantId', action='store')
parser.add_argument('--dstSecret', action='store')
parser.add_argument('--dstClientId', action='store')
parser.add_argument('--dstKv', action='store')
args = parser.parse_args()

# Set vars

workFolder = os.path.abspath(os.getcwd())
srcSecretsKeyList = []
srcSecretsList = []
srcSecretsDict = {}

# Get bearer


def get_bearer(clientsecret, clientid, tenantid):
    payload = {'grant_type': 'client_credentials', 'client_secret': clientsecret, 'client_id': clientid, 'scope': 'https://vault.azure.net/.default'}
    beartoken = requests.post('https://login.microsoftonline.com/' + tenantid + '/oauth2/v2.0/token', payload).json()['access_token']
    return beartoken

# List & Dump KV secrets names


srcBearToken = get_bearer(args.srcSecret, args.srcClientId, args.srcTenantId)
print(srcBearToken)
kvURL = args.srcKv + '/secrets?api-version=7.2'
getHeaders = {'Authorization': 'Bearer ' + srcBearToken}
srcInitSecretsData = requests.get(kvURL, headers=getHeaders).json()

## Dump
for secret in srcInitSecretsData['value']:
    try:
        srcSecretsKeyList.append(secret['id'].split('/')[4])
    except AttributeError:
        print('!AttrError!')
        continue

# Get & Dump KV secrets values

for secret in srcSecretsKeyList:
    secretData = requests.get(args.srcKv + '/secrets/' + secret + '/?api-version=7.2', headers=getHeaders).json()
    secretKey = secretData.get('id').split('/')[4]
    secretValue = secretData.get('value')
    srcSecretsDict[secretKey] = secretValue

    ## Dump
    with open(workFolder + '/srcKvDump', 'a') as srcDumpFile:
        srcDumpFile.write('%s: %s\n' % (secretKey, secretValue))
    srcDumpFile.close()

print('Secrets successfully exported')

# Create secrets in DST keyvault & Set secrets values

dstBearToken = get_bearer(args.dstSecret, args.dstClientId, args.dstTenantId)
print(dstBearToken)
putHeaders = {'Content-Length': '0', 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + dstBearToken}

for key, value in srcSecretsDict.items():
    secretName = key
    secretPayload = '{\"value\": \"' + value + '\"}'
    response = requests.put(args.dstKv + 'secrets/' + secretName + '/?api-version=7.2', data=secretPayload, headers=putHeaders)
    print(response.text)
