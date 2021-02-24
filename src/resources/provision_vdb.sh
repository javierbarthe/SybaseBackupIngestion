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
# Delphix Mount Path
DPXMNTPATH=$DBPATH
# Staging DB Name
cd ${DPXMNTPATH}
SDBNAME=`ls -ltr *.file | awk '{print $9}'| awk -F "." '{print $1}'`
#echo ${SDBNAME} >> /tmp/dlpx_edsi.log
# VDB NAME
VDBNAME=${VDB}
# Sybase Binaries on Staging host
ASEBINARIES=$SYBASEPATH
# Staging ASE Details
ASENAME=$SRVNAME
SYBUSER=$USRNAME
SYBPASS=$USRPASSWD
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
fi
# UNMOUNT STAGE AND MOUNT AGAIN, AFTER THAT MOUNT WITH NEW NAME VDB
#
#echo "unmount database "${SDBNAME}" to '/tmp/$VDBNAME/manifest.file'" > /tmp/${VDBNAME}/unmount.tmp
#echo "go" >> /tmp/${VDBNAME}/unmount.tmp
#isql -U${SYBUSER} -P${SYBPASS} -S${ASENAME} -i/tmp/${VDBNAME}/unmount.tmp -o/tmp/${VDBNAME}/unmount.out
#
# COPY FILES FOR GENERATE A NEW VDB
#
#if [ ! -d "${DPXMNTPATH}/${VDBNAME}" ]; then
#mkdir $DPXMNTPATH/$VDBNAME
#cp $DPXMNTPATH/$SDBNAME/* $DPXMNTPATH/$VDBNAME/
#chmod -R 777 $DPXMNTPATH/$VDBNAME
#fi
#
# LIST DATABASE AND DEVICES TO MOUNT
#
echo "mount database ${SDBNAME} from '${DPXMNTPATH}/${SDBNAME}.file' with listonly" > /tmp/${VDBNAME}/stgdb.tmp
echo "go" >> /tmp/${VDBNAME}/stgdb.tmp
isql -U${SYBUSER} -P${SYBPASS} -S${ASENAME} -i/tmp/${VDBNAME}/stgdb.tmp -o/tmp/${VDBNAME}/mount_list.out
#
# MOUNT STAGING AGAIN
#
#echo "mount database ${SDBNAME} from '/tmp/$VDBNAME/manifest.file'" > /tmp/${VDBNAME}/stgdb.tmp
#echo "go" >> /tmp/${VDBNAME}/stgdb.tmp
#isql -U${SYBUSER} -P${SYBPASS} -S${ASENAME} -i/tmp/${VDBNAME}/stgdb.tmp -o/tmp/${VDBNAME}/mount_stg.out
#
# GENERATE MOUNT COMMAND TO NEW VDB
#
sed -i '1d' /tmp/${VDBNAME}/mount_list.out
sed -i -E 's|\[device\]$|using|g' /tmp/${VDBNAME}/mount_list.out
sed -i -E "s|.'*\/(.*)\/|'${DPXMNTPATH}/|g" /tmp/${VDBNAME}/mount_list.out
sed -i -E "s|'$|',|g" /tmp/${VDBNAME}/mount_list.out
sed -i '$s/,$/\ngo/' /tmp/${VDBNAME}/mount_list.out
sed -i -E "s|${SDBNAME}$|mount database ${SDBNAME} as ${VDBNAME} from '${DPXMNTPATH}/${SDBNAME}.file'|g" /tmp/${VDBNAME}/mount_list.out
isql -U${SYBUSER} -P${SYBPASS} -S${ASENAME} -i/tmp/${VDBNAME}/mount_list.out -o/tmp/${VDBNAME}/mount_list.outt
# ONLINE VDB
onl="use master\ngo\nonline database $VDBNAME\n"
onl="${onl}go\n"
echo -e ${onl} > /tmp/${VDBNAME}/online.sql
isql -U$SYBUSER -P$SYBPASS -S$ASENAME -W900 -i/tmp/${VDBNAME}/online.sql -o/tmp/${VDBNAME}/online.out

# TAR GZ TMP FILES AND DELETE
