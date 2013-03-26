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
import datetime
from django.utils.translation import ugettext_lazy as _
from django.db import models
from wikipbx.wikipbxweb.models import Account

__all__ = 'Contact',

class Contact(models.Model):
    """
    A contact database entry that will be stored every time someone is dialed
    out via web dialout.
    """
    first_name = models.CharField(
        _(u"first name"), max_length=150,
        help_text=_(u"First name of the user/owner of this phone."))
    last_name = models.CharField(
        _(u"last name"), max_length=150, null=True, blank=True,
        help_text=_(u"Last name of the user/owner of this phone."))
    title = models.CharField(
        _(u"job title"), max_length=50, null=True, blank=True)
    organization = models.CharField(
        _(u"organization"), max_length=100, null=True, blank=True)
    work = models.CharField(
        _(u"work number"), max_length=25, null=True, blank=True,
        help_text=_(
            u"Acceptable forms are: 14081112222 or "
            "sip:7471122334@proxy01.sipphone.com"))
    home = models.CharField(
        _(u"home number"), max_length=25, null=True, blank=True,
        help_text=_(
            u"Acceptable forms are: 14081112222 or "
            "sip:7471122334@proxy01.sipphone.com"))
    mobile = models.CharField(
        _(u"mobile number"), max_length=25, null=True, blank=True,
        help_text=_(
            u"Acceptable forms are: 14081112222 or "
            "sip:7471122334@proxy01.sipphone.com"))
    notes = models.CharField(
        _(u"notes"), max_length=255, null=True, blank=True,
        default=lambda: _('Created on %s') % datetime.datetime.now())
    is_blacklisted = models.BooleanField(_(u"is blacklisted"), default=False)
    last_saved = models.DateTimeField(auto_now=True, editable=False)

    # Was this number explicitly entered in phonebook or was it just dialed by
    # user at some point in past?    
    is_explicit = models.BooleanField(
        _(u"is explicit"), default=False, editable=False)

    account = models.ForeignKey(Account, verbose_name=_(u"account"))

    def get_vcard_rev(self):
        return self.last_saved.strftime('%Y%m%dT%H%M%SZ')

    @models.permalink
    def get_absolute_url(self):
        return 'contacts:edit', (self.id,), {}

    def __unicode__(self):
        if self.last_name:
            return u"%s, %s" % (self.last_name, self.first_name)
        else:
            return self.first_name

    class Meta:
        verbose_name = _(u"contact")
        verbose_name_plural = _(u"contacts")
        ordering = (
            '-is_explicit', 'last_name', 'first_name', 'work', 'home',
            'mobile')
