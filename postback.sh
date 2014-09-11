#!/bin/bash

## Get mailboxes list
MAILBOX_DIR="/home/vmail/domain/"
MAILBOXES=`ls $MAILBOX_DIR | egrep -v "smth"`
BACKUP_DIR="/var/postback/"
LOCKFILE="/tmp/postback.run"
DATE=`date +%d.%m.%y`
LOGFILE="/home/vmail/backup.log"

##Create lockfile
if [ ! -f "$LOCKFILE" ];
	then touch $LOCKFILE;
	else echo "Lockfile exists! Aborting.";
exit 1;
fi;

echo "Starting..."
##### START WORKING
for i in $MAILBOXES;
do

##Check that backup directory exisits, else create it
	if [ ! -d $BACKUP_DIR${i}/files ];
		then mkdir -p $BACKUP_DIR${i}/files;
	fi;

###Get archives
##Move files, that were acessed more than 10mins ago
find $MAILBOX_DIR${i}/cur/* -mmin \+60 | xargs mv -t $BACKUP_DIR${i}/files/ 2>> /tmp/postback_fails

##Create .tar archive
cd $BACKUP_DIR${i} && tar czf $DATE.tar.gz -C $BACKUP_DIR${i}/files/ . 2>> $LOGFILE

echo "Processing..."

## Check that backup archives were created properly
if [ "$?" != "0" ];
then
echo "`date` Something went wrong!" >> $LOGFILE;
rm $LOCKFILE;
kill -n SIGTERM pid $$;
fi;

##Cleaning up
rm $BACKUP_DIR${i}/files/*

##Refresh maildirsize
rm $MAILBOX_DIR${i}/maildirsize 2>> $LOGFILE

done

echo "Done."

##Remove trash
find $BACKUP_DIR -maxdepth 2 -type f -exec rm -v {} \+
rm $LOCKFILE

echo "Backup sucess at `date`" >> $LOGFILE
