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
# Sybase Binaries on Staging host
ASEBINARIES=$SYBASEPATH
# Staging ASE Details
ASENAME=$SRVNAME
SYBUSER=$USRNAME
SYBPASS=$USRPASSWD
#
#
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
onl=$onl"select 'OK' as STATUS\n"
onl="${onl}go\n"
isql -U$SYBUSER -P$SYBPASS -S$ASENAME -W900 -b --retserverror << ScriptSql
	$(echo -e $onl)
ScriptSql
ChkErr $?
exit 0
# TAR GZ TMP FILES AND DELETE
