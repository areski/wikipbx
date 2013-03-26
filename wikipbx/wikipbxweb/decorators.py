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
Stas Shtin <antisvin@gmail.com>
Portions created by the Initial Developer are Copyright (C)
the Initial Developer. All Rights Reserved.

Contributor(s): 

"""
from django import http
from django.core.urlresolvers import reverse
from wikipbx import authutil
from wikipbx.wikipbxweb.models import EventSocketConfig

__all__ = (
    'require_login', 'require_admin', 'require_root_or_admin', 'require_root')

# _make_check is a higher order function that lets us avoid writing boilerplate
# code for decorators.
def _make_check(
    check, error_dst='wikipbxweb:index',
    error_msg='You are not currently logged in with enough permissions'):
    def _decorator(func):
        return lambda request, *args, **kwargs: (
            func(request, *args, **kwargs) if check(request, *args, **kwargs)
            else http.HttpResponseRedirect(
                reverse(error_dst) + "?urgentmsg=%s" % error_msg))
    return _decorator
    
# User must be logged in.
require_login = _make_check(
    lambda request, *args, **kwargs: request.user.is_authenticated(),
    error_msg="Must be logged in to view this resource")

# User must be logged in as root.
require_admin = _make_check(
    lambda request, *args, **kwargs: (
        request.user.is_authenticated() and
        request.user.get_profile().is_acct_admin()))

# User must be logged in as root or admin.
require_root_or_admin = _make_check(
    lambda request, account_id=None, *args, **kwargs:
    authutil.is_root_or_admin(request, account_id))

# User must be logged in as root.
require_root = _make_check(
    lambda request, *args, **kwargs: authutil.is_root(request))

# Request should come from freeswitch ip address
def fs_address_only(func):
    def decorator(*args, **kwargs):
        host = args[0].get_host().split(":")[0]
        eventsockets = models.EventSocketConfig.objects.all()
        for eventsocket in eventsockets:
            if eventsocket.listen_ip == host:
                return func(*args, **kwargs)
        return http.HttpResponseNotFound("Connections allowed only from FS host")
    return decorator
