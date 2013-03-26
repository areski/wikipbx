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
Riccardo Magliocchetti (unbit sas) <riccardo.magliocchetti@gmail.com>
Stas Shtin <antisvin@gmail.com>
"""
from django import forms
from django.utils.translation import ugettext_lazy as _
from wikipbx.contacts import statics
from wikipbx.contacts.models import Contact


class ContactForm(forms.ModelForm):
    class Meta:
        model = Contact
        fields = (
            'first_name', 'last_name', 'work', 'home', 'mobile', 'organization',
            'title', 'is_blacklisted', 'notes')
        widgets = {'notes': forms.Textarea()}

class ExportContactForm(forms.Form):
    export_type = forms.ChoiceField(
        choices=statics.EXPORT_FORMATS.items(),
        label=_(u"Contacts export format"))
