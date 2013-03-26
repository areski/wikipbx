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

Contributor(s): Riccardo Magliocchetti
"""

import logging
import traceback

"""
Log levels:

    CRITICAL
    ERROR
    WARNING
    INFO
    DEBUG
"""

logobj = logging.getLogger('wikipbx')
logobj.setLevel(logging.DEBUG)
#logobj.setLevel(logging.INFO)

handler = logging.StreamHandler()
logobj.addHandler(handler)

def info(*messages):
    logobj.info(*messages)

def debug(*messages):
    logobj.debug(*messages)

def error(*messages):
    logobj.error(*messages)
    tb = traceback.format_exc()
    logobj.error(tb)

def warn(*messages):
    logobj.warning(*messages)

