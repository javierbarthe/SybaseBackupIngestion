#!/usr/bin/env bash -xv
# Plugin Reqs
# sa_role user
# toolkit user should be on sybase group
#
# Get Sybase Environment variables
#
# Staging DB Name
SDBNAME=${STAGEDB}dpx
# Sybase Binaries on Staging host
ASEBINARIES=$SYBASEPATH
# Staging ASE Details
ASENAME=$SRVNAME
SYBUSER=$USRNAME
SYBPASS=$USRPASSWD
# Delphix Mount Path
DPXMNTPATH=$DPXPATH
#
# Load Sybase environment Variables
#
cd ${ASEBINARIES}
source SYBASE.sh
#
#
# MOUNT STAGE AFTER SNAPSHOT
#
echo "mount database ${SDBNAME} from '${DPXMNTPATH}/${SDBNAME}.file'" > /tmp/load_${SDBNAME}/mount.tmp
echo "go" >> /tmp/load_${SDBNAME}/mount.tmp
isql -U${SYBUSER} -P${SYBPASS} -S${ASENAME} -i/tmp/load_${SDBNAME}/mount.tmp -o/tmp/load_${SDBNAME}/mount.out
#
# TAR GZ TMP FILES AND DELETE

