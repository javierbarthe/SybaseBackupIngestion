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
exit 1
fi
#
# MOUNT VDB AGAIN
#
echo "mount database ${VDBNAME} from '/tmp/$VDBNAME/manifest.file'" > /tmp/${VDBNAME}/vdb.tmp
echo "go" >> /tmp/${VDBNAME}/vdb.tmp
isql -U${SYBUSER} -P${SYBPASS} -S${ASENAME} -i/tmp/${VDBNAME}/vdb.tmp -o/tmp/${VDBNAME}/mount_vdb.out
# ONLINE VDB
onl="use master\ngo\nonline database $VDBNAME\n"
onl="${onl}go\n"
echo -e ${onl} > /tmp/${VDBNAME}/online.sql
isql -U$SYBUSER -P$SYBPASS -S$ASENAME -W900 -i/tmp/${VDBNAME}/online.sql -o/tmp/${VDBNAME}/online.out
# TAR GZ TMP FILES AND DELETE
