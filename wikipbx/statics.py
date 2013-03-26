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

from pytz import timezone

# following must correspond to what is in settings.py
DEFAULT_TZ_NAME="UTC"
DEFAULT_TZ = timezone("UTC")


not_found = ('<?xml version="1.0"?>\n'
             '<document type="freeswitch/xml">'
             '<section name="result">'
             '<result status="not found" />'
             '</section>'
             '</document>')

# Action variable types and their description
AV_TYPE_SELECTION = 0
AV_TYPE_PROMPT = 1
AV_TYPE_TEXT = 2

AV_TYPE_CHOICES = {
    AV_TYPE_SELECTION: 'Selection',
    AV_TYPE_PROMPT: 'Prompt',
    AV_TYPE_TEXT: 'Text',
    }

# Kinds of Action variables and their description
AV_KIND_AUDIO_FILE = 0
AV_KIND_EXTENSION = 1
AV_KIND_GATEWAY = 2
AV_KIND_IVR_SCRIPT = 3
AV_KIND_LOCAL_ENDPOINT = 4
AV_KIND_VOICE_TYPE = 5
AV_KIND_IVR_MENU = 6

AV_KIND_CHOICES = { 
    AV_KIND_AUDIO_FILE: 'Audio file', 
    AV_KIND_EXTENSION: 'Extensions', 
    AV_KIND_GATEWAY: 'Gateway',
    AV_KIND_IVR_MENU: 'IVR menu',
    AV_KIND_IVR_SCRIPT: 'IVR script',
    AV_KIND_LOCAL_ENDPOINT: 'Local endpoint',
    AV_KIND_VOICE_TYPE: 'Voice type',
    }                     

# Dialplan context prefixes
CONTEXT_PREFIX = '__account_'
SIP_PROFILE_CONTEXT_PREFIX = '__sip_profile_'
