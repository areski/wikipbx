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
def extension_url(dest_num, account, modifiers=None):
    sip_url = "%s@%s" % (dest_num, account.domain)
    return sip_dialout_url(sip_url, account, modifiers) 


def sip_dialout_url(sip_url, account, modifiers=None):
    if not modifiers:
        modifiers = {}

    # we must set the domain_name channel variable,
    # or else the cdr processing will look for this
    # and not find it, and not be able to associate
    # the cdr with any account and will reject it
    modifiers['domain_name'] = account.domain
    namevalpairs = ("%s=%s" % item for item in modifiers.iteritems())
    mods_string = ",".join(namevalpairs)
    
    sipprofile_name = get_sip_profile_or_domain(account)

    return "{%s}sofia/%s/%s" % (mods_string, sipprofile_name, sip_url)


def get_sip_profile_or_domain(account):
    # is this account aliased to a sip profile?  if so,
    # then we should use the domain name instead of the
    # sip profile name ..
    return account.domain if account.aliased else account.dialout_profile.name
