#!/bin/bash
###We have to use additional wrapper while restoring with barman because we have to copress basebackups in order to save disk space.
##Note that i'm using HOSTNAME as DBNAME in barman configuration.

BACKUPNAME="$1"
DBNAME="$2"
TTIME="$3"
LC_ALL="en_US.UTF-8"
LOGFILE="/var/lib/barman/recover.log"
ARCDIR="/u01/services/barman/archives"
BACKUPDIR="/u01/services/barman/$DBNAME/base/$BACKUPNAME/data"
LASTBACKUP="$(barman list-backup $SERVER | awk '!/FAILED/ {print $2}' | head -n 1)"

###Avoid code duplication
postcheck () {
if [ "$?" == "0" ];
then
        echo "$(date +"%m.%d.%y-%T") OK" | tee -a $LOGFILE
else
        echo "$(date +"%m.%d.%y-%T") FAILED will not continue." | tee -a $LOGFILE
        kill -9 $$
fi
}

###Simple basic checks
#Help key
if [ $1 = "-h" ];
then
	echo -e "\nThis is the wrapper for barman recover command\nIt using destination hostname as backup unit. That can be confusing, but still it's that how it is.\nThis script provides up to 3 argumens. First 2 are vital 3-rd one is optional.\nSyntax is: recover.sh [BACKUPID] [BACKUPUNIT] [TARGETTIME].\nFor 1st argument check barman list-backup prod-db-vip.ahml1.ru for example\nFor 2nd argument check /etc/barman.conf or /etc/barman.d/ dir.\n3rd argument should be acceptable by date -d \"somethinghere\" \"+%Y-%m-%d %H:%M:%S\" command because it's barman recover syntax."
	exit 0
fi

#Check that user is _BARMAN_!
if [ "$(whoami)" != "barman" ];
then
	echo "$(date +"%m.%d.%y-%T") ERROR You should be barman to do that, aborting." | tee -a $LOGFILE
	exit 1
fi

#Check that we passed at least 2 arguments
if [ "$#" -lt 2 ];
then
	echo "$(date +"%m.%d.%y-%T") Illegal number of parameters, that should be at least 2, name of backup and backup unit name that configured in barman." | tee -a $LOGFILE
	echo "Check -h key for this script to get some help."
	exit 1
fi

###Starting
echo -e "$(date +"%m.%d.%y-%T") ==========\nSCRIPT started." | tee -a $LOGFILE

#Check that host avaliable and our ssh port open
if [ ! "echo | nc -v '$DBNAME' 2222 &> /dev/null" ];
then
	if [ ! "ping -c 3 '$DBNAME' &> /dev/null" ]
	then
		echo "$(date +"%m.%d.%y-%T") ERROR Can't ping remote host, aborting." | tee -a $LOGFILE
	else
		echo "$(date +"%m.%d.%y-%T") ERROR SSH port for Barman is not avaliable, termiating." | tee -a $LOGFILE
	fi
	exit 1
fi

#Check that backup name provided and archive exist.
if [ "$BACKUPNAME" != "" ];
then
	if [ ! "$(ls -l $ARCDIR | grep $BACKUPNAME\.tar\.gz)" ];
	then
		echo "$(date +"%m.%d.%y-%T") ERROR Arhcive for given backup name does not exist, aborting." | tee -a $LOGFILE
		kill -9 $$
	else
		echo "$(date +"%m.%d.%y-%T") Found archive for given backup name." | tee -a $LOGFILE
	fi
else
	echo "$(date +"%m.%d.%y-%T") ERROR backup name not specified, aborting" | tee -a $LOGFILE
	exit 1
fi

#Check that correct backup unit specified.
if [ "$DBNAME" != "" ];
then
	if [ ! -d "$BACKUPDIR" ]
	then
		echo "$(date +"%m.%d.%y-%T") ERROR Invalid backup unit specified, aborting." | tee -a $LOGFILE
		kill -9 $$
	else
		echo "$(date +"%m.%d.%y-%T") Found backup unit." | tee -a $LOGFILE
	fi
else
	echo "$(date +"%m.%d.%y-%T") ERROR Backup unit is not specified, aborting." | tee -a $LOGFILE
        exit 1
fi

#Check that target time set correctly
if [ "$TTIME" != "" ];
then
	if [ ! "$(date -d "$TTIME" "+%Y-%m-%d %H:%M:%S")" ];
        then
                echo "$(date +"%m.%d.%y-%T") ERROR invalid --target-time format, it should be ok with \" date -d \"YOURDATE\" +%Y-%m-%d %H:%M:%S\", reffer to manual for details, aborting." | tee -a $LOGFILE
                exit 1
        else
                echo "$(date +"%m.%d.%y-%T") Using target time as: $(date -d "$TTIME" "+%Y-%m-%d %H:%M:%S")." | tee -a $LOGFILE
        fi
else
        echo "$(date +"%m.%d.%y-%T") INFO You've not specified desired target time, will be used basebackup time." | tee -a $LOGFILE
fi

###Now we need to unpack given archive to our directory
#Will unpack only if we do not use latest backup that present unpacked.
if [ "$BACKUPNAME" = "$LASTBACKUP" ];
then
	echo "$(date +"%m.%d.%y-%T") INFO You are going to use latest backup, skipping archive uncompressing." | tee -a $LOGFILE
else
	echo "$(date +"%m.%d.%y-%T") INFO You are not going to use latest backup, will uncompress archive for that backup." | tee -a $LOGFILE
	cd $BACKUPDIR
	echo "$(date +"%m.%d.%y-%T") Uncompressing archive to backup dir..." | tee -a $LOGFILE
	tar --strip-components 7 -xf $ARCDIR/$BACKUPNAME\.tar\.gz
	postcheck
	cd -
fi
###Now assembling recover command for Barman
#Will make up --target-time parameter a bit, because that option kinda tricky. If it not specified it will be not append to command.
if [ "$TTIME" != "" ];
then
	TTIMESTRING="$(date -d "$TTIME" "+%Y-%m-%d %H:%M:%S"+00:00)"
fi

#Prepare remote env
echo "$(date +"%m.%d.%y-%T") Starting recover..." | tee -a $LOGFILE
echo "$(date +"%m.%d.%y-%T") Creating recover dir on remote host." | tee -a $LOGFILE
ssh -p 2222 barman@$DBNAME "mkdir -p /backup/recover/recover_$BACKUPNAME"
postcheck

#Run recovery command
echo "$(date +"%m.%d.%y-%T") Starting recovery procedure." | tee -a $LOGFILE
barman recover $DBNAME $BACKUPNAME /backup/recover/recover_$(date -d "$TTIME" "+%Y-%m-%d%H:%M:%S") --target-time "$TTIMESTRING" --remote-ssh-command="ssh -p 2222 barman@$DBNAME"
postcheck

