# scripts
**get-cred**: Python script that could be useful when you want to use passwords in scripts but don't want them to be compromised.<br />
Supported options are: get, store, update, delete.<br />
I've also included a wrapper for this script in order to be able to import this script as library and call it as a function.<br />
In this case you don't need to care of encoding of your password, it wll happen automatically.<br />

**zabbix**: This directory contains a scripts that performing a communication with Zabbix API in order to set Dependencies on Zabbix proxy triggers.<br />
- **policy_deps.py**: Zabbix core server has a proxy availability trigger and all proxy triggers should have dependencies on that trigger. <br />
Since i had 15 zabbix proxies with about 4000 triggers configured i was need to have some kind of soltion for that, so that's why this script was made.<br />
- **policy_qrator.py**: Was made in order to set complex dependencies on triggers depending on what's going on with perspective of Zabbix availability points. I probably will describe this later.<br />

**flask**: Simple flask app that returns "Hello world". It may be useful if you like to have a docker image with simple app inside.<br />

**nginx_parse.py**: Simple parser of nginx logs. It will show top 10 sources IP that sent most amount of traffic.<br />

**projsync.py**: Simple script that sync Jira project elements between two projects.<br />

 Will be more
