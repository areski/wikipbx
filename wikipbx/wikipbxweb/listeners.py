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

import os


def pre_delete_endpoint(sender, **kwargs):
    """
    Delete endpoint extensions.
    """
    dest_num = "^%s$" % kwargs['instance'].userid
    endpoint_extensions = kwargs['instance'].account.extension_set.filter(
        dest_num=dest_num)
    for extension in endpoint_extensions:
        extension.delete()

def pre_delete_soundclip(sender, **kwargs):
    """
    Delete soundclip file.
    """
    script_path = kwargs['instance'].get_path()
    if os.path.exists(script_path):
        os.remove(script_path)

def pre_delete_ivr(sender, **kwargs):
    """
    Delete IVR file.
    """
    script_path = kwargs['instance'].get_script_path()
    if os.path.exists(script_path):
        os.remove(script_path)
