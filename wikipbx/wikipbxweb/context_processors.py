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
import django
import sys
import wikipbx
from django.conf import settings


def global_processor(request):
    result = {}

    infomsg = request.REQUEST.get('infomsg', None)
    if infomsg:
        result['infomsg'] = infomsg
        
    urgentmsg = request.REQUEST.get('urgentmsg', None)
    if urgentmsg:
        result['urgentmsg'] = urgentmsg

    # DON'T catch exceptions below - let it be propagated and fixed
    user = request.user
    if (not (user and not user.is_anonymous() and user.is_superuser)
        and (user and not user.is_anonymous() and
             user.is_authenticated())):
        profile = user.get_profile()
        if profile:
            result['account'] = profile.account    

    # Get version of some software.
    for program, version in (('wikipbx', wikipbx.VERSION),
                             ('python', tuple(sys.version_info)),
                             ('django', django.VERSION)):
        result['%s_version' % program] = '%s.%s.%s-%s-%s' % version
    return result
    
def soundclips_media_processor(request):
    return {'SOUNDCLIPS_MEDIA_URL': settings.SOUNDCLIPS_MEDIA_URL}
