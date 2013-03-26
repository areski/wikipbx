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

from wikipbx.wikipbxweb.models import *
from wikipbx.wikipbxweb.models import SipProfile
from django.conf import settings
import random
import os

def get_temp_ext(vardict, action, tempname, account):
    """
    Create a temporary extension in the database.
    started out as a workaround for calling python scripts
    with arguments (eg, the extension sets channel variables).

    @vardict - will all be set as channel variables
    @action - the last line of the extension, basically an ivr
    @tempname - to help prevent collision, eg, 'soundclip'
    @account - the account this extension will belong to

    Example extension action xml:

    <action application="set" data="foo=bar"/>
    <action application="python" data="wikipbx.ivr.test.main"/>
    """

    # create a dest_num
    counter = 0
    while counter < 1000:
        number2try = random.randint(1000000,9999999)
        dest_num = "%s-%s" % (tempname, number2try)            
        dest_num_dialplan = "^%s$" % dest_num
        matches = Extension.objects.filter(account=account,
                                           dest_num=dest_num)
        if matches:
            # drats, already used ..
            counter += 1
            continue
        else:
            break
    
    # generate the actions_xml statements that set variables
    actions_xml = ""
    for channelvar_name, channelvar_val in vardict.items():
        line = '<action application="set" data="%s=%s"/>\n' % (
            channelvar_name, channelvar_val)
        actions_xml += line
    actions_xml += "%s\n" % action

    # create extension
    priority = new_ext_priority_position(account)    
    ext = Extension.objects.create(
        account=account, dest_num=dest_num, actions_xml=actions_xml,
        priority_position=priority, is_temporary=True)

    return dest_num

def new_ext_priority_position(account):
    """
    When creating a new extension, get the next available
    priority position at end of list
    """
    # find the greatest priority position so far
    exts = Extension.objects.filter(
        account=account).order_by("-priority_position")
    if not exts:
        return 0
    greatest_pp = exts[0].priority_position
    return greatest_pp + 1

def reset_priority_position(account, extension, direction):
    """
    Set given extension as top extension (position priority 0)
    """
    exts = Extension.objects.filter(account=account)
    exts = exts.order_by("is_temporary", "priority_position")
    if not exts or len(exts) <= 1:
        return
    extlist = list(exts)
    extlist.remove(extension)
    if direction == "highest":
        extlist.insert(0, extension)
    elif direction == "lowest":
        extlist.append(extension)        
    else:
        raise Exception("Unknown direction: %s" % direction)    

    counter = 0
    for ext in extlist:
        ext.priority_position = counter
        ext.save()
        counter += 1

def bump_priority_position(account, extension, direction):
    exts = Extension.objects.filter(
        account=account).order_by("is_temporary","priority_position")
    if not exts or len(exts) <= 1:
        return
    extlist = list(exts)
    curindex = extlist.index(extension)
    extlist.remove(extension)
    if direction == "raise":
        newindex = curindex - 1
    elif direction == "lower":
        newindex = curindex + 1
    else:
        raise Exception("Unknown direction: %s" % direction)
    extlist.insert(newindex, extension)
    counter = 0
    for ext in extlist:
        ext.priority_position = counter
        ext.save()
        counter += 1
