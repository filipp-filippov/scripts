#!/bin/bash

REPSTRING='$1'

#get repo && make dir for arts.
rm -r /opt/build /opt/app
mkdir -p /opt/build /opt/app
yum install -y git
cd /opt/build
git init; git pull $REPSTRING
##
cp * /opt/app

docker run --rm -v /opt/app:/app node:8.1 bash -c "apt-get update && apt-get -y install python g++ make git\
	&& npm install pm2 yarn -g\
	&& cd /tmp; mv /app/* .\
	&& yarn install --production\
	&& mv /tmp/node_modules /app/node_modules"

cp -ra /opt/app /opt/build
