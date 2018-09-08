#!/bin/sh

WALSTATUS=$(barman check prod-db-vip.ahml1.ru | awk -F '\:' '/replication\ slot/ {print $2}'| xargs)
PSQLSTATUS=$(barman check prod-db-vip.ahml1.ru | awk -F '\:' '/PostgreSQL\:/ {print $2}'| xargs)
LOGFILE='/var/lib/barman/flow.log'
TIMESTAMP=$(date +"%m.%d.%y-%T")

if [ "$WALSTATUS" = "OK" ];
then
	echo "$TIMESTAMP WAL streaming OK" >> $LOGFILE
else
	echo "$TIMESTAMP ERROR WAL straming error occured, see \"barman check prod-db-vip.ahml1.ru\" for details." >> $LOGFILE
	echo "$TIMESPAMP Will try to create replication slot for barman" >> $LOGFILE
	barman receive-wal --create-slot prod-db-vip.ahml1.ru
fi

if [ "$PSQLSTATUS" = "OK" ];
then
	echo "$TIMESTAMP Connection to PostgreSQL OK" >> $LOGFILE
else
	echo "$TIMESTAMP ERROR Can't establish connection to PostgreSQL" >> $LOGFILE
fi
