""" 
WikiPBX web GUI front-end for FreeSWITCH <www.freeswitch.org>
Copyright (C) 2010, Branch Cut <www.branchcut.com>

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


import re
from django import forms
from django.utils.translation import ugettext_lazy as _
from wikipbx.wikipbxweb import widgets

__all__ = ('FreeswitchAddressField', 'RepeatedPasswordField')

address_re = re.compile(
    "^(stun\:|host\:)?\w+(?:[A-Z0-9-]+\.)+[A-Z]{2,6}"
    "|(autonat\:)?(25[0-5]|2[0-4]\d|[0-1]?\d?\d)"
    "(\.(25[0-5]|2[0-4]\d|[0-1]?\d?\d)){3}"
    "|(auto|auto-nat)$", re.IGNORECASE)


class FreeswitchAddressField(forms.CharField):
    def __init__(self, max_length=100, initial='auto', *args, **kwargs):
        super(FreeswitchAddressField, self).__init__(
            max_length=max_length, initial=initial, *args, **kwargs)
        
    def clean(self, value):
        if address_re.match(value):
            return value
        else:
            raise forms.ValidationError(_(
                "This field must be set to a value like: "
                "\"<IP address>\", \"autonat:<IP address>\", "
                "\"stun:<Host Name>\", \"host:<Host Name>\", \"auto\" or "
                "\"auto-nat\""))
        

class RepeatedPasswordField(forms.MultiValueField):
    """
    Password field with two entries.
    """
    default_error_messages = {
        'unmatching': _(u'Entered values don\'t match')}
    widget = widgets.RepeatedPasswordWidget

    def __init__(self, max_length=None, *args, **kwargs):
        fields = (
            forms.CharField(max_length=max_length, widget=forms.PasswordInput()),
            forms.CharField(max_length=max_length, widget=forms.PasswordInput()))
        super(RepeatedPasswordField, self).__init__(fields, *args, **kwargs)

    def compress(self, data_list):
        """
        Make sure that both values match. Return just one of them.
        """
        if not data_list[0] == data_list[1]:
            raise forms.ValidationError(self.error_messages['unmatching'])
        return data_list[0]
