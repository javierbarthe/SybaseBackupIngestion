#!/usr/bin/env bash -xv
#
# PROVISION A VDB SCRIPT
#
# Plugin Reqs
# sa_role user
# toolkit user should be on sybase group
#
# Get Sybase Environment variables
#
# DBNAME
DBNAME=${DB}
# Sybase Binaries on Staging host
ASEBINARIES=$SYBASEPATH
# Staging ASE Details
ASENAME=$SRVNAME
SYBUSER=$USRNAME
SYBPASS=$USRPASSWD
# Delphix Mount Path
#DPXMNTPATH=$DPXPATH
# Load Sybase environment Variables
#
cd ${ASEBINARIES}
source SYBASE.sh
#
# Create a Folder on Tmp to work
if [ ! -d "/tmp/${DBNAME}" ]; then
cd /tmp
mkdir $DBNAME
chmod 777 $DBNAME
cd $DBNAME
else
rm -r /tmp/$DBNAME
cd /tmp
mkdir $DBNAME
chmod 777 $DBNAME
cd $DBNAME
fi
# UNMOUNT VDB
#
echo "unmount database ${DBNAME} to '/tmp/$DBNAME/manifest.file'" > /tmp/${DBNAME}/unmount.tmp
echo "go" >> /tmp/${DBNAME}/unmount.tmp
isql -U${SYBUSER} -P${SYBPASS} -S${ASENAME} -i/tmp/${DBNAME}/unmount.tmp -o/tmp/${DBNAME}/unmount.out
#
# REMOVE VDB FILES
#
#rm -r $DPXMNTPATH/$DBNAME
#
# TAR GZ TMP FILES AND DELETE
