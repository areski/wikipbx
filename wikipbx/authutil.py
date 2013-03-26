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
"""

from wikipbx.wikipbxweb.models import *

def is_root_or_admin(request, account_id=None):
    """
    Check if current logged in user is either the root user, or an admin in the
    given account.
    """
    if not request.user.is_authenticated():
        return False

    if request.user.is_superuser:
        return True

    if account_id:
        account = Account.objects.get(pk=account_id)
    else:
        account = request.user.get_profile().account

    if not account:
        raise Exception("No account_id passed and no account found in request")

    return request.user.get_profile() in account.admins.all()

def is_root(request):
    """
    Check if current logged in user is root.
    """    
    return request.user.is_superuser
