""" 
WikiPBX web GUI front-end for FreeSWITCH <www.freeswitch.org>
Copyright (C) 2007, Branch Cut <www.branchcut.com>

Version: MPL 1.1

The contents of this file are subject to the Mozilla Public License Version
1.1 (the "License"); you may not use this file except in compliance with
the License. You may obtain a copy of the License at
http://www.mozilla.org/MPL/

Software distributed under the License is distributed on an "AS IS" basis,
WITHOUT WARRANTY OF ANY KIND, either express or implied. See the License
for the specific language governing rights and limitations under the
License.

The Original Code is - WikiPBX web GUI front-end for FreeSWITCH

The Initial Developer of the Original Code is
Traun Leyden <tleyden@branchcut.com>
Portions created by the Initial Developer are Copyright (C)
the Initial Developer. All Rights Reserved.

Contributor(s): 
Stas Shtin <antisvin@gmail.com>
"""

import ESL
import random
from django import http
from wikipbx import logger
from wikipbx.wikipbxweb.models import EventSocketConfig, SipProfile


__all__ = 'get_fs_connections', 'get_fs_connection', 'restart_profiles'


def get_fs_connections():
    """
    Get all available ESL connections.
    """
    logger.info("get_fs_connections()")
    sockets = EventSocketConfig.objects.all()
    if sockets:
        logger.info("%s eventsockets" % len(sockets))
    else:
        logger.error("No eventsockets found! Unable to connect to freeswitch.")
        
    for socket in sockets:
        logger.info("creating ESL connection")
        yield ESL.ESLconnection(
            str(socket.listen_ip), str(socket.listen_port),
            str(socket.password))

    logger.info("get_fs_connections() done")

def get_fs_connection():
    """
    Get a single ESL connection. Selected randomly.
    """
    return random.choice(list(get_fs_connections()))

def restart_profiles(success_msg, error_msg, return_url):
    """
    Restart Sofia profiles on freeswitch.
    """
    logger.info("restart_profiles called")

    for connection in get_fs_connections():
        try:                    
            #connection.sendRecv(
            #    ("api sofia profile %s restart" % account.name)
            #    if account else ("api sofia restart profile all"))
            for sipprofile in SipProfile.objects.all():
                connection.sendRecv(
                    (u"api sofia profile %s restart" % sipprofile.name
                     ).encode('utf-8'))
        except Exception, e:
            msg = error_msg + str(e)
        else:
            msg = success_msg
        return http.HttpResponseRedirect("%s?infomsg=%s" % (return_url, msg))

    else:
        msg = ("No EventSocket configured in WikiPBX.  Cannot connect "
               "to freeswitch over event socket")
        return http.HttpResponseRedirect("%s?infomsg=%s" % (return_url, msg))

    logger.info("restart_profiles done")

def sofia_profile_cmd(command):
    """
    Operations on sofia profiles.
    """
    logger.info("sofia_profile_cmd: " + command)

    for connection in get_fs_connections():
        if not connection.connected():
            raise IOError("No connection to FreeSWITCH")
        try:
            connection.sendRecv(command.encode('utf-8'))
        except Exception, e:
            logger.info("sofia_profile_cmd error: " + str(e))
            raise
        logger.info("sofia_profile_cmd done")
        return
    raise ValueError("No EventSocket configured in WikiPBX. "
        "Cannot connect to FreeSWITCH over event socket")
    
def sofia_profile_start(profile_name):
    sofia_profile_cmd(u"bgapi sofia profile %s start" % profile_name)

def sofia_profile_stop(profile_name):
    sofia_profile_cmd(u"bgapi sofia profile %s stop" % profile_name)

def sofia_profile_restart(profile_name):
    sofia_profile_cmd(u"bgapi sofia profile %s restart" % profile_name)

def sofia_profile_rescan(profile_name):
    sofia_profile_cmd(u"bgapi sofia profile %s rescan reloadxml" % profile_name)

def sofia_profile_killgw(profile_name, gateway_name):
    sofia_profile_cmd(u"api sofia profile %s killgw %s" % (profile_name, gateway_name))
