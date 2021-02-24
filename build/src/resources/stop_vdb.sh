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
# VDB NAME
VDBNAME=${VDB}
# Sybase Binaries on Staging host
ASEBINARIES=$SYBASEPATH
# Staging ASE Details
ASENAME=$SRVNAME
SYBUSER=$USRNAME
SYBPASS=$USRPASSWD
# Delphix Mount Path
DPXMNTPATH=$DPXPATH
# Load Sybase environment Variables
#
cd ${ASEBINARIES}
source SYBASE.sh
#
# Create a Folder on Tmp to work
if [ ! -d "/tmp/${VDBNAME}" ]; then
cd /tmp
mkdir $VDBNAME
chmod 777 $VDBNAME
cd $VDBNAME
else
rm -r /tmp/$VDBNAME
cd /tmp
mkdir $VDBNAME
chmod 777 $VDBNAME
cd $VDBNAME
fi
# UNMOUNT VDB
#
echo "unmount database ${VDBNAME} to '/tmp/$VDBNAME/manifest.file'" > /tmp/${VDBNAME}/unmount.tmp
echo "go" >> /tmp/${VDBNAME}/unmount.tmp
isql -U${SYBUSER} -P${SYBPASS} -S${ASENAME} -i/tmp/${VDBNAME}/unmount.tmp -o/tmp/${VDBNAME}/unmount.out
#
# TAR GZ TMP FILES AND DELETE
