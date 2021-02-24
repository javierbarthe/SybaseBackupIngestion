#!/usr/bin/env bash -xv
#
# MONITOR DB STATUS - 0 OK, 2 OK if STAGEDB, 3 ERROR
#
# Get Sybase Environment variables
#
# VDB NAME
DBNAME=${DB}
# Sybase Binaries on Staging host
ASEBINARIES=$SYBASEPATH
# Staging ASE Details
ASENAME=$SRVNAME
SYBUSER=$USRNAME
SYBPASS=$USRPASSWD
# Create a Folder on Tmp to work
if [ ! -d "/tmp/${DBNAME}" ]; then
cd /tmp
mkdir $DBNAME
chmod 777 $DBNAME
fi
cd /tmp/$DBNAME/
# CHECK ERROR FUNCTION
ChkErr(){ if [ $1 != 0 ] ; then exit $1 ; fi }
#
# Load Sybase environment Variables
#
cd ${ASEBINARIES}
source SYBASE.sh
#
# CHECK DBMS STATUS
#
onl="set nocount on\ngo\n"
onl=$onl"select isnull(status2,-1) AS STATUS from master..sysdatabases where name ='"${DBNAME}"'\n"
onl="${onl}go"
echo -e $onl > /tmp/${DBNAME}/check.sql
isql -U$SYBUSER -P$SYBPASS -S$ASENAME -W900 -b -i/tmp/${DBNAME}/check.sql -o/tmp/${DBNAME}/check.out
ChkErr $?
CMDOUT=`cat /tmp/${DBNAME}/check.out | awk '{print $1}'`
if [ -z "$CMDOUT" ]
then
	exit 1
else
	echo $CMDOUT
	exit 0
fi
# TAR GZ TMP FILES AND DELETE