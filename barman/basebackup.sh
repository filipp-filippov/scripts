#!/bin/sh
###Barman backup wrapper
###Maintainer: Filipp Filippov

SERVER=$1
MANUAL=$2
ARCDIR='/u01/services/barman/archives'
LOGFILE='/var/lib/barman/basebackup.log'
GLOBMOSTAMP=""
LOCKFILE='/var/lib/barman/backup.lock'
GZIP="-6"
WEEK="604800" #In seconds

###Cleanup stage
#Added switch from manual run if this argument not passed this script will not run manually.
#We need to find and purge old backups.
#Backup policy is 6 mothly Full backups, 4 weekly Full backups,
#wal logs for last week (binded to last weekly backup)
#We need to archive everything except latest backup if we want to recover fast in case of emergency. So we will have uncompressed latest basebackup and duplicate it with archive.

###TRAP ctrl-c
function droplock() {
	rm $LOCKFILE
	echo "$(date +"%m.%d.%y-%T") Lockfile removed." | tee -a $LOGFILE
}
trap droplock SIGINT

#Check that server specified it's vital
if [ "$SERVER" = "" ];
then
	echo "$(date +"%m.%d.%y-%T") You should specify server as an argument, aborting"  | tee -a $LOGFILE
	exit 1
else
	BACKUPDIR="/u01/services/barman/$SERVER/base"
	ALLBACKUPS="$(barman list-backup $SERVER | awk '!/FAILED/ {print $2}')"
	LASTBACKUP="$(barman list-backup $SERVER | awk '!/FAILED/ {print $2}' | head -n 1)"
fi

#Check that time has come if not, do not run this script
#Compare present time with time of modification of backup directory. If more than 1 week passed it's time to make backup.
TIMEDIFF="$[$(date +%s) - $(date -d "$(stat $BACKUPDIR/$LASTBACKUP | awk '/Modify/ {print $2,$3}')" +%s)]"
if [ "$WEEK" -lt "$TIMEDIFF" ];
then
	echo "$(date +"%m.%d.%y-%T") It's time to make backup, starting." | tee -a $LOGFILE
else
	if [ "$MANUAL" = "run" ];
	then
		echo "$(date +"%m.%d.%y-%T") Manual start triggered." | tee -a $LOGFILE
	else
		echo "$(date +"%m.%d.%y-%T") Latest backup is younger than 1 week, exiting." | tee -a $LOGFILE
		exit 0
	fi
fi

#Check if backup process not running already
if [ -f /var/lib/barman/backup.lock ];
then
	echo "$(date +"%m.%d.%y-%T") Backup already running." | tee -a $LOGFILE
	exit 1
else
	touch /var/lib/barman/backup.lock
	echo "$(date +"%m.%d.%y-%T") Lockfile created." | tee -a $LOGFILE
fi

###Check files age. When the month changes, then it's the begin of month, skip this and remove everything after that file, till the next month.

echo "$(date +"%m.%d.%y-%T") Removing archives that older than 26 weeks from now."  >> $LOGFILE
find $ARCDIR -type f -mtime +168 -print -exec rm {} +

for i in $(ls -tr $ARCDIR/* | head -n -5); do
CURMOSTAMP="$(date -d "$(stat $i | awk '/Modify/ {print $2,$3}')" +%B)"
FLINODE="$(stat $i | awk '/Inode/ {print $4}')"
if [ "$GLOBMOSTAMP" != "$CURMOSTAMP" ];
then
	echo "$(date +"%m.%d.%y-%T") Skipping $i because it's first file of the month."  >> $LOGFILE
	echo "$(date +"%m.%d.%y-%T") File timestamp is: $(stat $i | awk '/Modify/ {print $2,$3}')"  >> $LOGFILE
	GLOBMOSTAMP=$CURMOSTAMP
else
	echo "$(date +"%m.%d.%y-%T") We will remove $i because time has come." >> $LOGFILE
	echo "$(date +"%m.%d.%y-%T") Inode is $FLINODE"  >> $LOGFILE
	echo "$(date +"%m.%d.%y-%T") File timestamp is: $(stat $i | awk '/Modify/ {print $2,$3}')"  >> $LOGFILE
	find $ARCDIR -type f -inum $FLINODE -print -exec rm {} +
fi
done

###Cleanup complete
##Now it's time to make basebackup and archive it by gzip. compression level=6
##Careful in this section. You should run backup command or will suffer.
echo "$(date +"%m.%d.%y-%T") Starting backup process..." >> $LOGFILE
barman backup $SERVER 
if [ "$?" == "0" ];
then
	echo "$(date +"%m.%d.%y-%T") Backup was success, compressing..." >> $LOGFILE
	BACKUPSTAMP=$(barman list-backup $SERVER | head -1 | cut -d ' ' -f 2)
	cd $ARCDIR\
	&& tar czf $BACKUPSTAMP\.tar\.gz $BACKUPDIR/$BACKUPSTAMP/data\
	&& echo "$(date +"%m.%d.%y-%T") Compression was success." >> $LOGFILE
	cd -
else
	echo "$(date +"%m.%d.%y-%T") ERROR Backup was not successful" >> $LOGFILE
fi	

###Cleanup everything from basebackup dir except latest backup
#Get latest sucessful backup
for BD in $ALLBACKUPS;
do
if [ "$BD" != "$LASTBACKUP" ];
then
#Check that archive for backup exists
	if [ "ls $ARCDIR | grep -q $BD" ];
	then
		echo "$(date +"%m.%d.%y-%T") Found archive for backup $BD, can continue." >> $LOGFILE
	else
		echo "$(date +"%m.%d.%y-%T") Archive for backup $BD, not found. Will archive that data before continue." >> $LOGFILE
		cd $ARCDIR\
		&& tar czf $BD\.tar\.gz $BACKUPDIR/$BD/data\
		&& echo "$(date +"%m.%d.%y-%T") Compression for backup $BD was success." >> $LOGFILE
		cd -
	fi
	echo "$(date +"%m.%d.%y-%T") Wiping out outdated directory $BD, actual backup stored in $LASTBACKUP" >> $LOGFILE
	rm -rf $BACKUPDIR/$BD/data/*
else
	echo "$(date +"%m.%d.%y-%T") Found latest backup directory $BD, skipping." >> $LOGFILE
fi
done

#Rm lockfile
droplock
