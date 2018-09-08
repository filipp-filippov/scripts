#!/bin/sh
###Postgres backup script
###It's all about unix timstamps fun, enjoy.

ARCDIR='/u01/services/barman/archives'
LOGFILE='/var/lib/barman/basebackup.log'
TIMESTAMP=$(date +"%m.%d.%y-%T")
GLOBMOSTAMP=""
GZIP="-6"

###Cleanup stage
#We need to find and purge old backups.
#Backup policy is 6 mothly Full backups, 4 weekly Full backups,
#wal logs for last week (binded to last weekly backup)

###Check files age. When the month changes, then it's the begin of month, skip this and remove everything after that file, till the next month.

for i in $(ls -tr $ARCDIR/* | head -n -4); do
CURMOSTAMP="$(date -d "$(stat $i | awk '/Modify/ {print $2,$3}')" +%B)"
FLINODE="$(stat $i | awk '/Inode/ {print $4}')"
if [ "$GLOBMOSTAMP" != "$CURMOSTAMP" ];
then
	echo "$TIMESTAMP Skipping $i because it's first file of the month."  >> $LOGFILE
	echo "$TIMESTAMP File timestamp is: $(stat $i | awk '/Modify/ {print $2,$3}')"  >> $LOGFILE
	GLOBMOSTAMP=$CURMOSTAMP
else
	echo "$TIMESTAMP We will remove $i because time has come." >> $LOGFILE
	echo "$TIMESTAMP Inode is $FLINODE"  >> $LOGFILE
	echo "$TIMESTAMP File timestamp is: $(stat $i | awk '/Modify/ {print $2,$3}')"  >> $LOGFILE
	find $ARCDIR -type f -inum $FLINODE | xargs rm
fi
done

###Cleanup complete
##Now it's time to make basebackup and archive it by gzip. compression level=6
echo "$(date +"%m.%d.%y-%T") Starting backup process..." > $LOGFILE
barman backup prod-db-vip.ahml1.ru 
if [ "$?" == "0" ];
then
	echo "$(date +"%m.%d.%y-%T") Backup was success, compressing..." >> $LOGFILE
	BACKUPSTAMP=$(barman list-backup prod-db-vip.ahml1.ru | head -1 | cut -d ' ' -f 2)
	cd $ARCDIR\
	&& tar czf $BACKUPSTAMP\.tar\.gz /u01/services/barman/prod-db-vip.ahml1.ru/base/$BACKUPSTAMP/data\
	&& echo "$(date +"%m.%d.%y-%T") Compression was success." >> $LOGFILE\
	&& rm -rf /u01/services/barman/prod-db-vip.ahml1.ru/base/$BACKUPSTAMP/data/*
	cd -
else
	echo "$(date +"%m.%d.%y-%T") ERROR Backup was not successful" >> $LOGFILE
fi	

