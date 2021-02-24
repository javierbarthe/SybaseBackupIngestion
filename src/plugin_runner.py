import pkgutil
import logging
import sys
from dlpx.virtualization import libs
from dlpx.virtualization.libs import PlatformHandler
from dlpx.virtualization.platform.exceptions import UserError
from dlpx.virtualization.platform import Status
from generated.definitions import RepositoryDefinition, SnapshotDefinition, SourceConfigDefinition
from dlpx.virtualization.platform import Mount, MountSpecification, Plugin
from generated.definitions import (
    RepositoryDefinition,
    SourceConfigDefinition,
    SnapshotDefinition,
)

plugin = Plugin()
def _setup_logger():
    # This will log the time, level, filename, line number, and log message.
    log_message_format = '[%(asctime)s] [%(levelname)s] [%(filename)s:%(lineno)d] %(message)s'
    log_message_date_format = '%Y-%m-%d %H:%M:%S'
    # Create a custom formatter. This will help with diagnosability.
    formatter = logging.Formatter(log_message_format, datefmt= log_message_date_format)
    platform_handler = libs.PlatformHandler()
    platform_handler.setFormatter(formatter)
    logger = logging.getLogger()
    logger.addHandler(platform_handler)
    # By default the root logger's level is logging.WARNING.
    logger.setLevel(logging.DEBUG)

# Setup the logger.
_setup_logger()
logger = logging.getLogger(__name__)


#
# Below is an example of the repository discovery operation.
#
# NOTE: The decorators are defined on the 'plugin' object created above.
#
# Mark the function below as the operation that does repository discovery.
@plugin.discovery.repository()
def repository_discovery(source_connection):
    #
    # This is an object generated from the repositoryDefinition schema.
    # In order to use it locally you must run the 'build -g' command provided
    # by the SDK tools from the plugin's root directory.
    #
    repository = RepositoryDefinition()
    repository.name= "SAP ASE Backup Ingestion"
    log_msg = "Running discovery process:" + repository.name
    logger.info(log_msg)
    dlphx_srv_log = "echo `date` - '" + log_msg + "' >> /tmp/dlpx_edsi.log"
    dlphx_srv_log_exc = libs.run_bash(source_connection, dlphx_srv_log)
    return [repository]
#    return [RepositoryDefinition(name='40ba781d-a70a-4197-ae1a-8753ea401c93')]


@plugin.discovery.source_config()
def source_config_discovery(source_connection, repository):
    #
    # To have automatic discovery of source configs, return a list of
    # SourceConfigDefinitions similar to the list of
    # RepositoryDefinitions above.
    #

    return []

@plugin.linked.pre_snapshot()
def restore_staging(staged_source, repository, source_config, optional_snapshot_parameters):
    stage_mount_path = staged_source.mount.mount_path
    sybbin = staged_source.parameters.binarypath
    dsource_name = source_config.name
    backloc = source_config.sybbkploc
    asename = staged_source.parameters.asename
    aseuser = staged_source.parameters.aseuser
    asepass = staged_source.parameters.asepass
    log_msg = "Running script to generate staging (Ingestion Phase)"
    logger.info(log_msg)
    dlphx_srv_log = "echo `date` - '" + log_msg + "' >> /tmp/dlpx_edsi.log"
    dlphx_srv_log_exc = libs.run_bash(staged_source.staged_connection, dlphx_srv_log)
    # Create staging DB and Load backup to staging 
    variables={"SYBASEPATH": sybbin, "STAGEDB": dsource_name, "BKPPATH": backloc, "SRVNAME": asename, "USRNAME": aseuser, "USRPASSWD": asepass, "DPXPATH": stage_mount_path}
    link_script = pkgutil.get_data('resources', 'link_pre_snap.sh')
    # Execute script on remote host
    getlinkdetails = libs.run_bash(staged_source.staged_connection, link_script,variables,check=True)
    # Fail operation
    if getlinkdetails.exit_code != 0:
        raise RuntimeError('Failed to run script to link SAP ASE Backup', ' ' , ' ')
    log_msg = "Link Pre Snap Msg from Source server" + getlinkdetails.stdout
    logger.info(log_msg)
    dlphx_srv_log = "echo `date` - '" + log_msg + "' >> /tmp/dlpx_edsi.log"
    dlphx_srv_log_exc = libs.run_bash(staged_source.staged_connection, dlphx_srv_log)
    return Status.ACTIVE

@plugin.linked.mount_specification()
def linked_mount_specification(staged_source, repository):
    mount_location = staged_source.parameters.mount_location
    mount = Mount(staged_source.staged_connection.environment, mount_location)
    log_msg = "Setting up mount on Staging Server at " + mount_location
    logger.info(log_msg)
    #
    dlphx_srv_log = "echo `date` - '" + log_msg + "' >> /tmp/dlpx_edsi.log"
    dlphx_srv_log_exc = libs.run_bash(staged_source.staged_connection, dlphx_srv_log)
    return MountSpecification([mount])

@plugin.linked.stop_staging()
def dsource_stop_staging(staged_source, repository, source_config):
    stage_mount_path = staged_source.mount.mount_path
    sybbin = staged_source.parameters.binarypath
    dsource_name = source_config.name
    asename = staged_source.parameters.asename
    aseuser = staged_source.parameters.aseuser
    asepass = staged_source.parameters.asepass
    log_msg = "Running script to delete (or Stop) staging"
    logger.info(log_msg)
    dlphx_srv_log = "echo `date` - '" + log_msg + "' >> /tmp/dlpx_edsi.log"
    dlphx_srv_log_exc = libs.run_bash(staged_source.staged_connection, dlphx_srv_log)
    variables={"SYBASEPATH": sybbin, "SRVNAME": asename, "USRNAME": aseuser, "USRPASSWD": asepass}
    getsrvstatus = pkgutil.get_data('resources', 'check_syb_status.sh')
    srvstatus = libs.run_bash(staged_source.staged_connection, getsrvstatus,variables,check=False)
    log_msg = "Check status of Staging Server: " + asename + ' ' + srvstatus.stdout
    logger.info(log_msg)
    dlphx_srv_log = "echo `date` - '" + log_msg + "' >> /tmp/dlpx_edsi.log"
    dlphx_srv_log_exc = libs.run_bash(staged_source.staged_connection, dlphx_srv_log)
    if srvstatus.exit_code != 0:
        return Status.INACTIVE
    else:
        variables={"SYBASEPATH": sybbin, "DB": dsource_name+'dpx', "SRVNAME": asename, "USRNAME": aseuser, "USRPASSWD": asepass}
        link_script = pkgutil.get_data('resources', 'delete_db.sh')
        getlinkdetails = libs.run_bash(staged_source.staged_connection, link_script,variables,check=True)
        # Fail operation
        if getlinkdetails.exit_code != 0:
            raise RuntimeError('Failed to run script to delete SAP ASE DB', ' ' , ' ')
        log_msg = "Link Post Delete Msg from Source server" + getlinkdetails.stdout
        logger.info(log_msg)
        dlphx_srv_log = "echo `date` - '" + log_msg + "' >> /tmp/dlpx_edsi.log"
        dlphx_srv_log_exc = libs.run_bash(staged_source.staged_connection, dlphx_srv_log)

@plugin.linked.start_staging()
def dsource_start_staging(staged_source, repository, source_config):
    stage_mount_path = staged_source.mount.mount_path
    sybbin = staged_source.parameters.binarypath
    dsource_name = source_config.name
    asename = staged_source.parameters.asename
    aseuser = staged_source.parameters.aseuser
    asepass = staged_source.parameters.asepass
    log_msg = "Running script to Start staging"
    logger.info(log_msg)
    dlphx_srv_log = "echo `date` - '" + log_msg + "' >> /tmp/dlpx_edsi.log"
    dlphx_srv_log_exc = libs.run_bash(staged_source.staged_connection, dlphx_srv_log)
    variables={"SYBASEPATH": sybbin, "SRVNAME": asename, "USRNAME": aseuser, "USRPASSWD": asepass}
    getsrvstatus = pkgutil.get_data('resources', 'check_syb_status.sh')
    srvstatus = libs.run_bash(staged_source.staged_connection, getsrvstatus,variables,check=False)
    log_msg = "Check status of Staging Server: " + asename + ' ' + srvstatus.stdout
    logger.info(log_msg)
    dlphx_srv_log = "echo `date` - '" + log_msg + "' >> /tmp/dlpx_edsi.log"
    dlphx_srv_log_exc = libs.run_bash(staged_source.staged_connection, dlphx_srv_log)
    if srvstatus.exit_code != 0:
        return Status.INACTIVE
    else: 
        # Create staging DB and Load backup to staging 
        variables={"SYBASEPATH": sybbin, "DPXPATH": stage_mount_path, "VDB":dsource_name+'dpx', "SRVNAME":asename, "USRNAME":aseuser, "USRPASSWD":asepass}
        link_script = pkgutil.get_data('resources', 'start_staging.sh')
        # Execute script on remote host
        getlinkdetails = libs.run_bash(staged_source.staged_connection, link_script,variables,check=True)
        # Fail operation
        if getlinkdetails.exit_code != 0:
            raise RuntimeError('Failed to run script to Start SAP ASE DB', ' ' , ' ')
        log_msg = "Start Staging Msg from Source server" + getlinkdetails.stdout
        logger.info(log_msg)
        dlphx_srv_log = "echo `date` - '" + log_msg + "' >> /tmp/dlpx_edsi.log"
        dlphx_srv_log_exc = libs.run_bash(staged_source.staged_connection, dlphx_srv_log)

@plugin.linked.post_snapshot()
def linked_post_snapshot(staged_source,repository,source_config,optional_snapshot_parameters):
    stage_mount_path = staged_source.mount.mount_path
    sybbin = staged_source.parameters.binarypath
    dsource_name = source_config.name
    asename = staged_source.parameters.asename
    aseuser = staged_source.parameters.aseuser
    asepass = staged_source.parameters.asepass
    log_msg = "Running post snapshot mount: "
    logger.info(log_msg)
    # Create staging DB and Load backup to staging 
    variables={"SYBASEPATH": sybbin, "STAGEDB": dsource_name, "SRVNAME": asename, "USRNAME": aseuser, "USRPASSWD": asepass, "DPXPATH": stage_mount_path}
    link_script = pkgutil.get_data('resources', 'link_post_snap.sh')
    # Execute script on remote host
    getlinkdetails = libs.run_bash(staged_source.staged_connection, link_script,variables,check=True)
    # Fail operation
    if getlinkdetails.exit_code != 0:
        raise RuntimeError('Failed to run script to mount staging database', ' ' , ' ')
    log_msg = "Link Post Snap Msg from Source server" + getlinkdetails.stdout
    logger.info(log_msg)
    #
    dlphx_srv_log = "echo `date` - '" + log_msg + "' >> /tmp/dlpx_edsi.log"
    dlphx_srv_log_exc = libs.run_bash(staged_source.staged_connection, dlphx_srv_log)
    return SnapshotDefinition()

@plugin.virtual.configure()
def configure_new_vdb(virtual_source, snapshot, repository):
    mount_location = virtual_source.parameters.mount_location
    name = "VDB mounted at {}".format(mount_location)
    sybbin = virtual_source.parameters.binarytgt
    sybvdbname = virtual_source.parameters.vdbname
    vdbusername = virtual_source.parameters.vdbusername
    vdbpassword = virtual_source.parameters.vdbpassword
    sybsrvname = virtual_source.parameters.asename
    variables={"SYBASEPATH": sybbin, "DBPATH":mount_location, "VDB":sybvdbname, "SRVNAME":sybsrvname, "USRNAME":vdbusername, "USRPASSWD":vdbpassword}
    startvdb = pkgutil.get_data('resources', 'provision_vdb.sh')
    response = libs.run_bash(virtual_source.connection, startvdb,variables,check=True)
    log_msg = "Configure vDB in Target server " + response.stdout
    logger.info(log_msg)
    #
    dlphx_srv_log = "echo `date` - '" + log_msg + "' >> /tmp/dlpx_edsi.log"
    dlphx_srv_log_exc = libs.run_bash(virtual_source.connection, dlphx_srv_log)
    # Fail operation if the timestamp couldn't be retrieved
    if response.exit_code != 0:
        raise RuntimeError('Failed to run script to start SAP ASE vDB in Target server', ' ' , ' ')
    #return Status.ACTIVE
    return SourceConfigDefinition(name=sybvdbname,sybbkploc='')

@plugin.virtual.reconfigure()
def reconfigure_vdb(virtual_source, repository, source_config, snapshot):
    mount_location = virtual_source.parameters.mount_location
    name = "VDB mounted at {}".format(mount_location)
    sybbin = virtual_source.parameters.binarytgt
    sybvdbname = virtual_source.parameters.vdbname
    vdbusername = virtual_source.parameters.vdbusername
    vdbpassword = virtual_source.parameters.vdbpassword
    sybsrvname = virtual_source.parameters.asename
    variables={"SYBASEPATH": sybbin, "SRVNAME": sybsrvname, "USRNAME": vdbusername, "USRPASSWD": vdbpassword}
    getsrvstatus = pkgutil.get_data('resources', 'check_syb_status.sh')
    srvstatus = libs.run_bash(virtual_source.connection, getsrvstatus,variables,check=False)
    log_msg = "Check status of Target Server: " + sybsrvname + ' ' + srvstatus.stdout
    logger.info(log_msg)
    dlphx_srv_log = "echo `date` - '" + log_msg + "' >> /tmp/dlpx_edsi.log"
    dlphx_srv_log_exc = libs.run_bash(virtual_source.connection, dlphx_srv_log)
    if srvstatus.exit_code != 0:
        return Status.INACTIVE
    else:   
        variables={"SYBASEPATH": sybbin, "DBPATH":mount_location, "VDB":sybvdbname, "SRVNAME":sybsrvname, "USRNAME":vdbusername, "USRPASSWD":vdbpassword}
        startvdb = pkgutil.get_data('resources', 'provision_vdb.sh')
        response = libs.run_bash(virtual_source.connection, startvdb,variables,check=True)
        log_msg = "Configure vDB in Target server " + response.stdout
        logger.info(log_msg)
        dlphx_srv_log = "echo `date` - '" + log_msg + "' >> /tmp/dlpx_edsi.log"
        dlphx_srv_log_exc = libs.run_bash(virtual_source.connection, dlphx_srv_log)
        # Fail operation if the timestamp couldn't be retrieved
        if response.exit_code != 0:
            raise RuntimeError('Failed to run script to start SAP ASE vDB in Target server', ' ' , ' ')
        return SourceConfigDefinition(name=sybvdbname,sybbkploc='')

@plugin.virtual.post_snapshot()
def virtual_post_snapshot(virtual_source, repository, source_config):
    return SnapshotDefinition()

@plugin.virtual.mount_specification()
def vdb_mount_spec(virtual_source, repository):
    mount_location = virtual_source.parameters.mount_location
    mount = Mount(virtual_source.connection.environment, mount_location)
    log_msg = "Mounting NFS to Target server " + mount_location
    logger.info(log_msg)
    #
    dlphx_srv_log = "echo `date` - '" + log_msg + "' >> /tmp/dlpx_edsi.log"
    dlphx_srv_log_exc = libs.run_bash(virtual_source.connection, dlphx_srv_log)
    return MountSpecification([mount])

@plugin.linked.status()
def linked_status(staged_source, repository, source_config):
    stage_mount_path = staged_source.mount.mount_path
    sybbin = staged_source.parameters.binarypath
    dsource_name = source_config.name
    asename = staged_source.parameters.asename
    aseuser = staged_source.parameters.aseuser
    asepass = staged_source.parameters.asepass
    variables={"SYBASEPATH": sybbin, "SRVNAME": asename, "USRNAME": aseuser, "USRPASSWD": asepass}
    getsrvstatus = pkgutil.get_data('resources', 'check_syb_status.sh')
    srvstatus = libs.run_bash(staged_source.staged_connection, getsrvstatus,variables,check=False)
    log_msg = "Check status of Staging Server: " + dsource_name+'dpx' + ' ' + srvstatus.stdout
    logger.info(log_msg)
    dlphx_srv_log = "echo `date` - '" + log_msg + "' >> /tmp/dlpx_edsi.log"
    dlphx_srv_log_exc = libs.run_bash(staged_source.staged_connection, dlphx_srv_log)
    if  srvstatus.exit_code != 0:
        return Status.INACTIVE
    else: 
        variables={"SYBASEPATH": sybbin, "DB": dsource_name+'dpx', "SRVNAME": asename, "USRNAME": aseuser, "USRPASSWD": asepass}
        getdbstatus = pkgutil.get_data('resources', 'check_db_status.sh')
        dbstatus = libs.run_bash(staged_source.staged_connection, getdbstatus,variables,check=True)
        log_msg = "Check status of Staging DB " + dsource_name+'dpx' + ' ' + dbstatus.stdout
        logger.info(log_msg)
        dlphx_srv_log = "echo `date` - '" + log_msg + "' >> /tmp/dlpx_edsi.log"
        dlphx_srv_log_exc = libs.run_bash(staged_source.staged_connection, dlphx_srv_log)
        if dbstatus.exit_code != 0:
            raise RuntimeError('Failed to run script to check SAP ASE Staging DB status in Staging server', ' ' , ' ')
        if '16' in dbstatus.stdout:
            return Status.ACTIVE
        elif '0' in dbstatus.stdout:
            return Status.ACTIVE
        elif '48' in dbstatus.stdout:
            return Status.ACTIVE    
        else:
            return Status.INACTIVE

@plugin.virtual.status()
def virtual_status(virtual_source, repository, source_config):
    sybbin = virtual_source.parameters.binarytgt
    sybvdbname = virtual_source.parameters.vdbname
    vdbusername = virtual_source.parameters.vdbusername
    vdbpassword = virtual_source.parameters.vdbpassword
    sybsrvname = virtual_source.parameters.asename
    variables={"SYBASEPATH": sybbin, "SRVNAME": sybsrvname, "USRNAME": vdbusername, "USRPASSWD": vdbpassword}
    getsrvstatus = pkgutil.get_data('resources', 'check_syb_status.sh')
    srvstatus = libs.run_bash(virtual_source.connection, getsrvstatus,variables,check=False)
    log_msg = "Check status of Target Server: " + sybsrvname + ' ' + srvstatus.stdout
    logger.info(log_msg)
    dlphx_srv_log = "echo `date` - '" + log_msg + "' >> /tmp/dlpx_edsi.log"
    dlphx_srv_log_exc = libs.run_bash(virtual_source.connection, dlphx_srv_log)
    if srvstatus.exit_code != 0:
        return Status.INACTIVE
    else:    
        variables={"SYBASEPATH": sybbin, "DB": sybvdbname, "SRVNAME": sybsrvname, "USRNAME": vdbusername, "USRPASSWD": vdbpassword}
        getdbstatus = pkgutil.get_data('resources', 'check_db_status.sh')
        dbstatus = libs.run_bash(virtual_source.connection, getdbstatus,variables,check=True)
        log_msg = "Check status of  vDB " + sybvdbname + ' ' + dbstatus.stdout
        logger.info(log_msg)
        dlphx_srv_log = "echo `date` - '" + log_msg + "' >> /tmp/dlpx_edsi.log"
        dlphx_srv_log_exc = libs.run_bash(virtual_source.connection, dlphx_srv_log)
        # Fail operation if the timestamp couldn't be retrieved
        if dbstatus.exit_code != 0:
            raise RuntimeError('Failed to run script to check SAP ASE Virtual DB status in Staging server', ' ' , ' ')
        if '0' in dbstatus.stdout:
            return Status.ACTIVE
        else:
            return Status.INACTIVE

@plugin.virtual.unconfigure()
def unconfigure(virtual_source, repository, source_config):
    sybbin = virtual_source.parameters.binarytgt
    sybvdbname = virtual_source.parameters.vdbname
    vdbusername = virtual_source.parameters.vdbusername
    vdbpassword = virtual_source.parameters.vdbpassword
    sybsrvname = virtual_source.parameters.asename
    variables={"SYBASEPATH": sybbin, "SRVNAME": sybsrvname, "USRNAME": vdbusername, "USRPASSWD": vdbpassword}
    getsrvstatus = pkgutil.get_data('resources', 'check_syb_status.sh')
    srvstatus = libs.run_bash(virtual_source.connection, getsrvstatus,variables,check=False)
    log_msg = "Check status of Target Server: " + sybsrvname + ' ' + srvstatus.stdout
    logger.info(log_msg)
    dlphx_srv_log = "echo `date` - '" + log_msg + "' >> /tmp/dlpx_edsi.log"
    dlphx_srv_log_exc = libs.run_bash(virtual_source.connection, dlphx_srv_log)
    if srvstatus.exit_code != 0:
        return Status.INACTIVE
    else:    
        variables={"SYBASEPATH": sybbin, "DB":sybvdbname, "SRVNAME":sybsrvname, "USRNAME":vdbusername, "USRPASSWD":vdbpassword}
        deletevdb = pkgutil.get_data('resources', 'delete_db.sh')
        response = libs.run_bash(virtual_source.connection, deletevdb,variables,check=True)
        log_msg = "Delete vDB in Target server " + response.stdout
        logger.info(log_msg)
        #
        dlphx_srv_log = "echo `date` - '" + log_msg + "' >> /tmp/dlpx_edsi.log"
        dlphx_srv_log_exc = libs.run_bash(virtual_source.connection, dlphx_srv_log)
        # Fail operation if the timestamp couldn't be retrieved
        if response.exit_code != 0:
            raise RuntimeError('Failed to run script to Delete SAP ASE vDB in Target server', ' ' , ' ')

@plugin.virtual.stop()
def stop(virtual_source, repository, source_config):
    mount_location = virtual_source.parameters.mount_location
    name = "VDB mounted at {}".format(mount_location)
    sybbin = virtual_source.parameters.binarytgt
    sybvdbname = virtual_source.parameters.vdbname
    vdbusername = virtual_source.parameters.vdbusername
    vdbpassword = virtual_source.parameters.vdbpassword
    sybsrvname = virtual_source.parameters.asename
    variables={"SYBASEPATH": sybbin, "DPXPATH": mount_location, "VDB":sybvdbname, "SRVNAME":sybsrvname, "USRNAME":vdbusername, "USRPASSWD":vdbpassword}
    deletevdb = pkgutil.get_data('resources', 'stop_vdb.sh')
    response = libs.run_bash(virtual_source.connection, deletevdb,variables,check=True)
    log_msg = "Stop vDB in Target server " + response.stdout
    logger.info(log_msg)
    #
    dlphx_srv_log = "echo `date` - '" + log_msg + "' >> /tmp/dlpx_edsi.log"
    dlphx_srv_log_exc = libs.run_bash(virtual_source.connection, dlphx_srv_log)
    # Fail operation if the timestamp couldn't be retrieved
    if response.exit_code != 0:
        raise RuntimeError('Failed to run script to Stop SAP ASE vDB in Target server', ' ' , ' ')

@plugin.virtual.start()
def start(virtual_source, repository, source_config):
    mount_location = virtual_source.parameters.mount_location
    name = "VDB mounted at {}".format(mount_location)
    sybbin = virtual_source.parameters.binarytgt
    sybvdbname = virtual_source.parameters.vdbname
    vdbusername = virtual_source.parameters.vdbusername
    vdbpassword = virtual_source.parameters.vdbpassword
    sybsrvname = virtual_source.parameters.asename
    variables={"SYBASEPATH": sybbin, "DPXPATH": mount_location, "VDB":sybvdbname, "SRVNAME":sybsrvname, "USRNAME":vdbusername, "USRPASSWD":vdbpassword}
    deletevdb = pkgutil.get_data('resources', 'start_vdb.sh')
    response = libs.run_bash(virtual_source.connection, deletevdb,variables,check=True)
    log_msg = "Stop vDB in Target server " + response.stdout
    logger.info(log_msg)
    #
    dlphx_srv_log = "echo `date` - '" + log_msg + "' >> /tmp/dlpx_edsi.log"
    dlphx_srv_log_exc = libs.run_bash(virtual_source.connection, dlphx_srv_log)
    # Fail operation if the timestamp couldn't be retrieved
    if response.exit_code != 0:
        raise RuntimeError('Failed to run script to Start SAP ASE vDB in Target server', ' ' , ' ')