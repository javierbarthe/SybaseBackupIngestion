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
# Backup files
BKPPATH=$BKPPATH
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
RestoreDB(){

        base=$1
        bkploc=$2
        counter=0
        ls ${bkploc}/${base}_s*.*|while read s_dmp
        do
                if [ "$counter" -eq "0" ]; then
                echo "use master" > /tmp/load_${SDBNAME}/load.sql
                echo "go" >> /tmp/load_${SDBNAME}/load.sql
                echo "load database $SDBNAME from '$s_dmp'" >> /tmp/load_${SDBNAME}/load.sql
                counter=1
                else
                echo "stripe on '$s_dmp'" >> /tmp/load_${SDBNAME}/load.sql
                fi
        done
        echo "with listonly=create_sql" >> /tmp/load_${SDBNAME}/load.sql
        echo "go" >> /tmp/load_${SDBNAME}/load.sql
}
# Create a Folder on Tmp to work

if [ ! -d "/tmp/load_${SDBNAME}" ]; then
cd /tmp
mkdir load_$SDBNAME
chmod 777 load_$SDBNAME
cd load_$SDBNAME
else
cd /tmp/load_$SDBNAME
rm -r /tmp/load_$SDBNAME/*
chmod -R 777 /tmp/load_$SDBNAME
fi
#
# Generate Database Load to get Database structure
RestoreDB $STAGEDB $BKPPATH
#loadlist="use master\ngo\nload database $SDBNAME from '$BKPPATH/${SDBNAME}_s0.' \n with listonly=create_sql\n"
#loadlist="${loadlist}go\n"
#echo -e $loadlist > /tmp/load_${SDBNAME}/load.sql
isql -U$SYBUSER -P$SYBPASS -S$ASENAME -W900 -i/tmp/load_${SDBNAME}/load.sql -o/tmp/load_${SDBNAME}/load.out
#
# Begin Process of Generating a new DB now on Delphix
# Change Devices location - CHANGE TO DELPHIX MOUNT PATH / device (sacar todo lo del medio)
sed -i -E "s|., physname = '*\/(.*)\/|        , physname = '${DPXMNTPATH}\/|g" /tmp/load_${SDBNAME}/load.out
# Change Device name
sed -i -E "s|\s* name = '|        name = '$SDBNAME|g" /tmp/load_${SDBNAME}/load.out

# Break load.out into 3 files, one for create database, other for disk inits and the last one for dboptions

INI=`grep -n "CREATE  DATABASE" /tmp/load_${SDBNAME}/load.out | awk -F":" '{print $1}'`
FIN=`wc -l /tmp/load_${SDBNAME}/load.out | awk '{print $1}'`
DESDE=`expr $FIN - $INI + 1`
DBOPT=`grep -n "sp_dboption" /tmp/load_${SDBNAME}/load.out | awk -F":" '{print $1}'`
DBOPT2=`expr $FIN - $DBOPT`
DBOPT3=`expr $DESDE - $DBOPT2 - 1`

#DISK INITS MODIFY
DINIT=`expr $INI - 1`
head -$DINIT /tmp/load_${SDBNAME}/load.out > /tmp/load_${SDBNAME}/diskinits.tmp
sed -i -E "s|go|        , skip_alloc=true\ngo|g" /tmp/load_${SDBNAME}/diskinits.tmp

# CREATE DATABASE MODIFY

tail -$DESDE /tmp/load_${SDBNAME}/load.out | head -$DBOPT3 > /tmp/load_${SDBNAME}/createdb.tmp
sed -i -E "s|go|FOR LOAD\ngo|g" /tmp/load_${SDBNAME}/createdb.tmp
sed -i -E "s|ON |ON $SDBNAME|g" /tmp/load_${SDBNAME}/createdb.tmp
sed -i -E "s|CREATE  DATABASE.*|CREATE  DATABASE $SDBNAME|g" /tmp/load_${SDBNAME}/createdb.tmp
sed -i -E "s|ALTER  DATABASE.*|ALTER  DATABASE $SDBNAME|g" /tmp/load_${SDBNAME}/createdb.tmp
sed -i -E "s|, |        , $SDBNAME|g" /tmp/load_${SDBNAME}/createdb.tmp
#mkdir ${DPXMNTPATH}/$SDBNAME/
#chmod 777 ${DPXMNTPATH}/$SDBNAME/
# Create Staging Database
isql -U$SYBUSER -P$SYBPASS -S$ASENAME -W900 -i/tmp/load_${SDBNAME}/diskinits.tmp -o/tmp/load_${SDBNAME}/diskinits.out
isql -U$SYBUSER -P$SYBPASS -S$ASENAME -W900 -i/tmp/load_${SDBNAME}/createdb.tmp -o/tmp/load_${SDBNAME}/diskinits.out
# Load Staging Database
#loadlist="use master\ngo\nload database $SDBNAME from '$BKPFILE'\n"
#loadlist="${loadlist}go\n"
#echo -e $loadlist > /tmp/load_${SDBNAME}/load_final.sql
sed "/with listonly=create_sql/d" /tmp/load_${SDBNAME}/load.sql > /tmp/load_${SDBNAME}/load_final.sql
isql -U$SYBUSER -P$SYBPASS -S$ASENAME -W900 -i/tmp/load_${SDBNAME}/load_final.sql -o/tmp/load_${SDBNAME}/load_final.out
#
# UNMOUNT STAGE BEFORE SNAPSHOT
#
echo "unmount database ${SDBNAME} to '${DPXMNTPATH}/${SDBNAME}.file'" > /tmp/load_${SDBNAME}/unmount.tmp
echo "go" >> /tmp/load_${SDBNAME}/unmount.tmp
isql -U${SYBUSER} -P${SYBPASS} -S${ASENAME} -i/tmp/load_${SDBNAME}/unmount.tmp -o/tmp/load_${SDBNAME}/unmount.out