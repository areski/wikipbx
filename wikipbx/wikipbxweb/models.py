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

import os
import re
from django.db import models
from django.db.models.signals import pre_delete
from django.contrib.auth.models import User as DjangoUser
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from wikipbx import sofiautil, statics
from wikipbx.wikipbxweb import listeners
from xml.dom import minidom

__all__ = (
    'ServerLog', 'UserProfile', 'Account', 'EmailConfig', 'Endpoint', 'Ivr',
    'Soundclip', 'Extension', 'CompletedCall', 'SipProfile', 'SofiaGateway',
    'EventSocketConfig', 'ActionTemplate', 'ActionVariable', 'Action',
    'ActionData', 'ExtensionAction', 'IvrMenu', 'IvrMenuDestination')

    
class UserProfile(DjangoUser):
    """
    Each 'web user', including admins, is an extension of Django user profile.
    The root user does NOT have a userprofile associated with it.

    The superuser is just a User/Userprofile with the is_super
    flag set to True.  Nothing in the db design ensures the
    rule above, it is enforced by the code.
    """
    user = models.OneToOneField(
        DjangoUser, verbose_name=_(u"user"), primary_key=True)
    account = models.ForeignKey(
        "Account", verbose_name=_(u"account"), related_name="account")

    def is_acct_admin(self):
        return (self in self.account.admins.all())

    def short_email(self):
        """
        Get a shortened version of email.
        """
        numchars = 10
        if len(self.user.email) <= numchars:
            return self.user.email
        else:
            return "%s.." % self.user.email[:8]

    @models.permalink
    def get_absolute_url(self):
        return 'wikipbxweb:user-edit', (self.account_id, self.pk), {}
            
    def __unicode__(self):
        return self.user.email

    class Meta:
        verbose_name = _(u'user profile')
        verbose_name_plural = _(u'user profiles')
        ordering = ['user']


class SipProfile(models.Model):
    """
    Sip profile is a sip user agent.
    """
    MANAGE_PRESENCE_CHOICES = (
        ("false", _(u"False")), ("passive", _(u"Passive")),
        ("true", _(u"True")))
    MULTIPLE_REGISTRATIONS_CHOICES = (    
        ("call-id", _(u"Call-id")), ("contact", _(u"Contact")), 
        ("false", _(u"False")), ("true", _(u"True")))

    name = models.CharField(_(u"SIP profile name"), max_length=50,
        help_text=_(u"E.g.: external, internal, etc..."))
    ext_rtp_ip = models.CharField(
        _(u"external RTP IP"), max_length=100, default="auto",
        help_text=_(
            u"External/public IP address to bind to for RTP."))
    ext_sip_ip = models.CharField(
        _(u"external SIP IP"), max_length=100, default="auto",
        help_text=_(
            u"External/public IP address to bind to for SIP."))
    rtp_ip = models.CharField(
        _(u"RTP IP"), max_length=100, default="auto",
        help_text=_(u"Internal IP address to bind to for RTP."))
    sip_ip = models.CharField(
        _(u"SIP IP"), max_length=100, default="auto",
        help_text=_(u"Internal IP address to bind to for SIP."))
    sip_port = models.PositiveIntegerField(_(u"SIP port"), default=5060)
    accept_blind_reg = models.BooleanField(
        _(u"accept blind registration"), default=False,
       help_text=_(
           u"If true, anyone can register to server and will "
           "not be challenged for username/password information."))
    auth_calls = models.BooleanField(
        _(u"authenticate calls"), default=True,
        help_text=_(
            u"If true, FreeeSWITCH will authorize all calls "
            "on this profile, i.e. challenge the other side for "
            "username/password information."))
    manage_presence = models.CharField(
        _(u"manage presence"), max_length=100, default="false",
        choices=MANAGE_PRESENCE_CHOICES,
        help_text=_(
            u"Set to 'true' to enable presence. Required for MWI."))
    log_auth_failures = models.BooleanField(
        _(u"log auth failures"), default=False,
        help_text=_(
            u"It true, log authentication failures. Required for Fail2ban."))
    multiple_registrations = models.CharField(
        _(u"multiple registrations"), max_length=100, default="false",
        choices=MULTIPLE_REGISTRATIONS_CHOICES,
        help_text=_(
            u"Used to allow to call one extension and ring several phones."))

    # Dialplan context used for calls passing through this profile.
    @property
    def context(self):
        return ''.join((statics.SIP_PROFILE_CONTEXT_PREFIX, str(self.id)))    

    def __unicode__(self):
        return "%s (%s:%s)" % (self.name, self.sip_ip, self.sip_port)

    def accept_blind_reg_str(self):
        if self.accept_blind_reg:
            return "True"
        else:
            return "False"

    def get_gateways(self):
        """
        Get all gateways in the system assigned to this sip profile.
        """
        retval = []
        accounts = Account.objects.filter(enabled=True)
        for account in accounts:
            for gateway in account.sofiagateway_set.all():
                if gateway.sip_profile.id == self.id:
                    retval.append(gateway)
        return retval

    def get_aliased_domains(self):
        """
        Get all accounts that are aliased to this profile.
        """
        accounts = Account.objects.filter(
            enabled=True, dialout_profile=self, aliased=True)
        return accounts

    def form_dict(self):
        retval = {}
        retval['name'] = self.name
        retval['ext_rtp_ip'] = self.ext_rtp_ip
        retval['ext_sip_ip'] = self.ext_sip_ip
        retval['rtp_ip'] = self.rtp_ip
        retval['sip_ip'] = self.sip_ip
        retval['sip_port'] = self.sip_port
        retval['accept_blind_reg'] = self.accept_blind_reg
        retval['auth_calls'] = self.auth_calls
        return retval

    @models.permalink
    def get_absolute_url(self):
        return 'wikipbxweb:profile-edit', (self.pk,), {}

    class Meta:
        verbose_name = _("SIP profile")
        verbose_name_plural = _("SIP profiles")
        ordering = ['name']
        unique_together = (('sip_ip', 'sip_port'),)
        
    
class Account(models.Model):
    """
    On a dedicated appliance, there will only be one account
    for the people who bought the appliance.  In other situations
    there might be more than one account, eg, a hosted version
    (wikipbx.com selling hosted accts to the masses).

    Each Account has one or more account admins.  The account
    admin is also an enduser, but just has more privilages.    
    """
    name = models.CharField(_(u"name"), max_length=50)    
    admins = models.ManyToManyField(
        'UserProfile', verbose_name=_(u"admins"), related_name="admins")
    enabled = models.BooleanField(_(u"enabled"), default=True)

    # will be returned with directory xml: <domain name="$${domain}">
    # for all endpoints that belong to this account.
    # all sip endpoints for this account MUST use this domain when
    # connecting to the switch.  when endpoints are dialed,
    # this domain is used: eg, sofia/foo/100%foo.com.  perhaps
    # this field should be merged with domain.
    # if left blank, the system falls back to ext_sip_ip.
    domain = models.CharField(_(u"domain"), max_length=50, unique=True)

    # the profile to use when generating dialstrings for this
    # account.  note that this does not restrict this account
    # to this profile, quite the contrary, since the account will
    # be active (eg, dialplan seved) on all profiles.
    dialout_profile = models.ForeignKey(
        'SipProfile', verbose_name=_(u"dialout profile"))

    # if this is true, the domain associated with this account
    # will be "aliased" to the default dialout profile, so in other
    # words the domain can be used as a synonym for that profile
    # and instead of dialstring: sofia/external/123@att.com you
    # can use sofia/yourcompany.com/123@att.com and freeswitch
    # will dial out of the external profile (assuming the external
    # profile is the default dialout profile for this account)
    aliased = models.BooleanField(_(u"alias for domain"), default=True)

    # Dialplan context
    @property
    def context(self):
        return ''.join((statics.CONTEXT_PREFIX, str(self.id)))

    # Get Account Id from context string
    @staticmethod
    def context_account(context):
        if context.startswith(statics.CONTEXT_PREFIX):
            return context[len(statics.CONTEXT_PREFIX):]
        return None

    def short_name(self):
        numchars = 10
        if len(self.name) <= numchars:
            return self.name
        else:
            return "%s.." % self.name[:8]

    def form_dict(self):
        retval = {}
        retval['name'] = self.name
        retval['enabled'] = self.enabled
        retval['domain'] = self.domain
        retval['dialout_profile'] = self.dialout_profile.id
        retval['aliased'] = self.aliased
        retval['context'] = self.context
        return retval
     
    def is_admin(self, userprofile):
        return userprofile in self.admins.all()

    def get_gateway_choices(self):
        """
        Get all gateways that can be used by this account.
        """
        return [
            (gw['id'], gw['name'])
            for gw in SofiaGateway.objects.filter(
                models.Q(account=self) | models.Q(accessible_all_accts=True)
                ).values('id', 'name')]

    @models.permalink
    def get_absolute_url(self):
        return 'wikipbxweb:account-edit', (self.pk,), {}

    def __unicode__(self):
        return self.name

    class Meta:
        verbose_name = _(u"account")
        verbose_name_plural = _(u"accounts")
        ordering = ['name']


class ActionTemplate(models.Model):
    name = models.CharField(_("name"), max_length=100)
    description =  models.TextField(_("description"), blank=True)
    xml_template = models.TextField(_("xml template"))

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ['name']


class ActionVariable(models.Model):
    template = models.ForeignKey("ActionTemplate")
    name = models.CharField(_("name"), max_length=100, blank=True)
    variable_type = models.IntegerField(
        choices=statics.AV_TYPE_CHOICES.items())
    kind = models.IntegerField(
        choices=statics.AV_KIND_CHOICES.items(), blank=True, null=True)
    default = models.CharField(_("default value"), max_length=255, 
                               blank=True, null=True)
    tag = models.CharField(_("template tag"), max_length=100)

    def dialplan_value(self, value):
        if self.variable_type == statics.AV_TYPE_SELECTION:
            if self.kind == statics.AV_KIND_AUDIO_FILE:
                # Audiofile
                try:
                    # If it's an id, we'll load soundclip from DB
                    int(value)
                    audiofile = Soundclip.objects.get(pk=value)
                except ValueError:
                    # String - system audio clips
                    audiofile = Soundclip(name=value)
                val = audiofile.get_path()
            elif self.kind == statics.AV_KIND_EXTENSION:
                # Extension
                ext = Extension.objects.get(pk=value)
                val = ext.dest_num
            elif self.kind == statics.AV_KIND_GATEWAY:
                # Gateway
                gw = SofiaGateway.objects.get(pk=value)
                val = gw.name
            elif self.kind == statics.AV_KIND_IVR_MENU:
                # IVR
                ivr_menu = IvrMenu.objects.get(pk=value)
                val = ivr_menu.ivr.name
            elif self.kind == statics.AV_KIND_IVR_SCRIPT:
                # IVR
                ivr = Ivr.objects.get(pk=value)
                val = ivr.get_module_path()
            elif self.kind == statics.AV_KIND_LOCAL_ENDPOINT:
                # Endpoint
                ep = Endpoint.objects.get(pk=value)
                val = ep.userid
            else:
                val = value
        else:
            val = value
        return val
    
    def __unicode__(self):
        return "%s.%s" % (self.template, self.name)

    class Meta:
        unique_together = (('template', 'name'), ('template', 'tag'),)


class Action(models.Model):
    template = models.ForeignKey("ActionTemplate")
    def __unicode__(self):
        return "%s (%d)" % (self.template, self.id)

    @staticmethod
    def create_actions(action_object, num_actions=1, new_order=1):
        """
        Create specified number of Action objects.
        Action templates list limited by filter.
        """
        actions = []

        # Load templates depending from action objcet type
        if action_object == IvrMenuDestination:
            templates = ActionTemplate.objects.filter(
                name__startswith='IVR destination')
        else:
            templates = ActionTemplate.objects.exclude(
                name__startswith='IVR destination')

        if templates:
            for i in range(new_order, new_order+num_actions):
                action = Action(template=templates[0])
                actions.append(action_object(order=i, action=action))

        return actions

class ActionData(models.Model):
    action = models.ForeignKey("Action")
    variable = models.ForeignKey("ActionVariable")
    value = models.TextField()

    def dialplan_value(self):
        return self.variable.dialplan_value(self.value)

    def __unicode__(self):
        return "%s.%s" % (self.action, self.variable)

    class Meta:
        verbose_name = _("action data")
        verbose_name_plural = _("action data")
        unique_together = (('action', 'variable'),)


class ExtensionAction(models.Model):
    extension = models.ForeignKey("Extension")
    action = models.ForeignKey("Action")
    order = models.PositiveIntegerField()

    def __unicode__(self):
        return "%s + %s (%d)" % (self.extension, self.action, self.order)

    class Meta:
        unique_together = (('extension', 'order'),)
        ordering = ['order']


class Extension(models.Model):
    """
    An extension, the equivalent of the file-based extensions in
    default_context.xml:

    <extension name="neoconf">
      <condition field="destination_number" expression="^neoconf[-]?([0-9]*)$">
        <action application="set" data="conf_code=$1"/>
        <action application="python" data="neoconf.ivr.prompt_pin"/>
      </condition>
    </extension>
    """
    # which account owns this extension?
    account = models.ForeignKey("Account", verbose_name=_(u"account"))
    auth_call = models.BooleanField(_(u"authenticate calls"), default=True)
    dest_num = models.CharField(
        _(u"destination number"), max_length=75,
        help_text=_(
            u"A perl compatible regular expression used to match against "
            "the destination number, eg: ^101$ to match 101,"
            "^(\d{10,11})$ to match all 10 or 11 digit numbers"))
    callerid_num = models.CharField(
        _(u"caller ID number"), max_length=75, blank=True, null=True,
        help_text=_(
            u"A perl compatible regular expression used to match against "
            "the caller ID number"))
    desc = models.CharField(_(u"description"), max_length=250, blank=True)

    # the actions in a malformed rootless xml snippet:
    # <action application="set" data="conf_code=$1"/>
    # <action application="python" data="neoconf.ivr.prompt_pin"/>
    # yes, this assumes only basic usage, but in fact _anything_
    # stuck in here will be mirrored into the dialplan result
    # returned from views.xml_dialplan()
    actions_xml = models.TextField(_(u"actions XML"), default='')
    is_temporary = models.BooleanField(_(u"is temporary"), default=False)

    # is this extension associated w/ a particular endpoint?
    # eg, when user creates them both at the same time
    endpoint = models.ForeignKey(
        "Endpoint", verbose_name=_(u"endpoint"), null=True)

    # the priority position of this extension, relative to other extensions.
    # think of the list of extensions as if they were in a a file
    # so the "top" extension corresponds to priority position 0,
    # the one below to 1, etc.  nothing fancy here, just a simple ordering.
    priority_position = models.IntegerField(_(u"priority position"))

    def dest_num_matches(self, destnum2test):
        groups = re.findall(self.dest_num, destnum2test)
        return groups

    def get_actions_xml_dom(self):
        """
        Get a dom object like
        <actions_xml>
        <action application="set" data="conf_code=$1"/>
        <action application="python" data="neoconf.ivr.prompt_pin"/>        
        </actions_xml>
        where everything inside <actions_xml> comes right out
        of the actions_xml field.
        """
        xml_text = "<actions_xml>%s</actions_xml>" % self.actions_xml
        dom = minidom.parseString(xml_text)
        return dom

    def get_xml_preview(self):
        """
        Get the first X chars of xml for preview purposs.
        """
        numchars = 50
        retval = "Error"

        # chop off repetitive head if found
        # <action application="speak" data="cepstral|William.. -->
        # <...="speak" data="cepstral|William.. -->
        retval = re.sub(r'action application', r'...', self.actions_xml)

        if len(retval) > numchars:
            retval = "%s.." % retval[:numchars]
        return retval

    def get_sofia_url(self, modifiers=None):
        """
        Get the dialable url for this extension, eg,
        sofia/mydomain.com/600@ip:port
        """
        single_expansion = self.get_single_expansion()
        if not single_expansion:
            raise Exception(
                _(u"There is no single expansion for this extension: %s") %
                unicode(self))
        return sofiautil.extension_url(
            single_expansion, self.account, modifiers)
                                               
    def get_single_expansion(self):
        """
        Does the destination number for this extension have
        a singl expansion?  
        ^600$ -> 600
        ^\d+$ -> None
        """
        # find what's inside the ^()$, eg, ^600$ -> 600.  600->600
        # optional ^ specified by \^?, followed by any number of
        # anything except $ specified by ([^\$]*), followed
        # by optional $ specified by \$?
        regex = "\^?([^\$]*)\$?"
        groups = re.findall(regex, self.dest_num)
        stuffinside = groups[0]

        # at this point, group will be something like "600", or if
        # self.dest_num is empty, will be an empty string
        # now, find out if its alphanum ONLY, eg, no regex
        # specifiers.  do this by "regexing it against itself".
        # things like 600 will match, whereas things like 
        # '60(2|3)0' will fail.  and things like *98 will blow up *boom*
        try:
            groups = re.findall(stuffinside, stuffinside) 
            if groups:
                # doesnt cover every case, for example..
                # 1?4085400303
                if groups[0] == stuffinside:
                    return stuffinside
        except Exception:
            # this will happen in the case of an illegal regex, such as *98  
            pass

    @models.permalink
    def get_absolute_url(self):
        return 'wikipbxweb:extension-edit', (self.pk,), {}
    
    def __unicode__(self):
        return u"%s (%s)" % (self.dest_num, self.priority_position)

    class Meta:
        verbose_name = _(u"extension")
        verbose_name_plural = _(u"extensions")
        ordering = ['priority_position']


class Endpoint(models.Model):
    """
    Each SIP endpoint that will register with the system
    should have an entry here.  Upon creating an SIP endpoint,
    the system should create an extension for that endpoint
    with actions that try to bridge, then go to voicemail.
    """
    userid = models.CharField(
        _(u"user ID"), max_length=100,
        help_text=_(
            u"The User ID the SIP endpoint logs in with. Normally "
            "this should be numeric, for example: 101. This is only a "
            "recommendation and not a hard rule, and this can be "
            "anything, for example my_sip_endpoint_101@foo.com."))
    password = models.CharField(_(u"password"), max_length=100, blank=True,
        help_text=_(u"It's recomended to use strong passwords for the "
                    "endpoint."))
    account = models.ForeignKey("Account", verbose_name=_(u"account"))
    userprofile = models.ForeignKey(
        'UserProfile', null=True, verbose_name=_(u'web user'),
        help_text=_(
            u"(Optional) Associate this endpoint with an existing User."))
    contact_addr = models.IPAddressField(
        _("contact address"), blank=True, default="0.0.0.0")
    vm_enabled = models.BooleanField(_(u"voice mail"), default=True,
        help_text=_(
            u"Enable voice mail for endpoint. When turned off this endpoint "
            "will not have a voice mail box. This means busy and no answer "
            "calls will not forward to a voice mail box, nor will the user be "
            "able to log in to a voice mail box. "))
    vm_password = models.CharField(
        _(u"voice mail password"), max_length=20, blank=True,
        help_text=_(
            u"Usually numbers only, because it'll be entered form the dial "
            "pad."))
    vm_mailto = models.EmailField(
        _(u"email voice mail message to"), blank=True,
        help_text=_(
            u"Send recorded voice mail message to specified email address."))
    vm_notify_mailto = models.EmailField(
        _(u"email voice mail notification to"), blank=True,
        help_text=_(
            u"Send notification about received voice mail to specified email "
            "address."))
    vm_remove_local_after_email = models.BooleanField(
        _(u"delete voice mail after email"), 
        default=False,
        help_text=_(
            u"Voice mail message will be removed from the local storage after "
            "sending via email."))
    toll_allow = models.CharField(
        _(u"toll allow"), max_length=100, blank=True,
        help_text=_(
            u"Specifies which types of calls this user can make. "
            "Multiple values can be specified separated with the coma. "
            "E.g.: domestic,international,local"))
    effective_caller_id_name = models.CharField(
        _(u"effective CallerID name"), max_length=50, blank=True,
        help_text=_(
            u"Caller ID name displayed on called party's phone "
            "when calling another registered endpoint."))
    effective_caller_id_number = models.CharField(
        _(u"effective CallerID number"), max_length=80, blank=True,
        help_text=_(
            u"Caller ID number displayed on called party's phone "
            "when calling another registered endpoint."))
    outbound_caller_id_name = models.CharField(
        _(u"outbound CallerID name"), max_length=50, blank=True,
        help_text=_(u"Caller ID name sent to provider on outbound calls."))
    outbound_caller_id_number = models.CharField(
        _(u"outbound CallerID number"), max_length=80, blank=True,
        help_text=_(u"Caller ID number sent to provider on outbound calls."))

    # Default value. Note that it's not stored in DB anymore.
    is_registered = False

    def get_extensions(self):
        return self.extension_set.all()

    @models.permalink
    def get_absolute_url(self):
        return 'wikipbxweb:endpoint', (self.pk,), {}
    
    def __unicode__(self):
        return self.userid

    class Meta:
        unique_together = (("userid", "account"),)
        verbose_name = _(u"endpoint")
        verbose_name_plural = _(u"endpoints")
        ordering = ['userid']
    
pre_delete.connect(listeners.pre_delete_endpoint, sender=Endpoint)


class SofiaGateway(models.Model):
    name = models.CharField(_(u"name"), max_length=100, unique=True)
    sip_profile = models.ForeignKey(
        'SipProfile', verbose_name=_(u"SIP profile"),
        help_text=_(
            u"Which Sip Profile communication with this gateway will take place"
            " on."))
    account = models.ForeignKey('Account', verbose_name=_(u"account"))
    username = models.CharField(_(u"username"), max_length=25)
    password = models.CharField(_(u"password"), max_length=25)
    proxy = models.CharField(
        _(u"proxy"), max_length=50, blank=True,
        help_text=_(u"Same as realm, if blank."))
    register = models.BooleanField(_(u"register"), default=False)
    extension = models.CharField(
        _(u"extension number"), max_length=50, blank=True, default="",
        help_text=_(u"Extension for inbound calls. Same as username, if "
                    "blank."))
    realm = models.CharField(
        _(u"realm"), max_length=50, blank=True, default="",
        help_text=_("Authentication realm. Same as gateway name, if blank."))
    from_domain = models.CharField(
        _(u"from domain"), max_length=50, blank=True, default="",
        help_text=_(
            u"Domain to use in from from field. Same as realm if blank."))
    expire_seconds = models.PositiveIntegerField(
        _(u"expire seconds"), default=3600, null=True)
    retry_seconds = models.PositiveIntegerField(
        _(u"retry seconds"), default=30, null=True,
        help_text=_(
            u"How many seconds before a retry when a failure or timeout "
            "occurs"))
    caller_id_in_from = models.BooleanField(
        _(u"caller ID in From field"), default=False,
        help_text=_(
            u"Use the callerid of an inbound call in the from field on "
            "outbound calls via this gateway."))

    # is this gateway accessible to all accounts?  temporary hack until
    # "root gateways" are implemented.
    accessible_all_accts = models.BooleanField(
        _(u"accessible for all accounts"), default=False)

    @models.permalink
    def get_absolute_url(self):
        return 'wikipbxweb:gateway-edit', (self.pk,), {}

    def __unicode__(self):
        return self.name

    def form_dict(self):
        return {
            'name': self.name, 'username': self.username,
            'password': self.password, 'proxy': self.proxy,
            'register': self.register, 'extension': self.extension,
            'realm': self.realm, 'from_domain': self.from_domain,
            'expire_seconds': self.expire_seconds,
            'retry_seconds': self.retry_seconds,
            'caller_id_in_from': self.caller_id_in_from,
            'accessible_all_accts': self.accessible_all_accts,
            'sip_profile': self.sip_profile.id}

    class Meta:
        verbose_name = _(u"Sofia gateway")
        verbose_name_plural = _(u"Sofia gateways")


class ServerLog(models.Model):
    """
    Certain failures, like when an error occurs trying to add a CDR
    record when freeswitch calls the webserver, should be logged in
    this table for display on the web GUI.
    """
    account = models.ForeignKey(
        "Account", verbose_name=_(u"account"), null=True)
    logtime = models.DateTimeField(_(u"log creation time"), auto_now_add=True)
    message = models.TextField(_(u"message"))

    @models.permalink
    def get_absolute_url(self):
        return 'wikipbxweb:log-list', (), {}

    class Meta:
        verbose_name = _(u"server log")
        verbose_name_plural = _(u"server logs")


class EmailConfig(models.Model):
    """
    When the server needs to send email, it uses the per-account email
    configuration or falls back to the per-server configuration, if one exists.
    """
    account = models.ForeignKey(
        "Account", verbose_name=_(u"account"), null=True)
    from_email = models.EmailField(
        _(u"from e-mail"), default='nobody@example.com')
    email_host = models.CharField(
        _(u"e-mail host"), max_length=100, default='example.com')
    email_port = models.PositiveIntegerField(
        _(u"e-mail port"), default=25)
    auth_user = models.CharField(
        _(u"authentication user"), max_length=100, blank=True, default='',
        help_text=_(u"Enable if your mail server requires login credentials"))
    auth_password = models.CharField(
        _(u"authentication password"), max_length=100, blank=True, default='',
        help_text=_(u"Enable if your mail server requires login credentials"))
    use_tls = models.BooleanField(
        _(u"use TLS"), default=False,
        help_text=_(u"Enable if your mail server requires Transport Layer "
                    "Security (TLS) encryption"))

    @models.permalink
    def get_absolute_url(self):
        return 'wikipbxweb:email-config', (), {}

    class Meta:
        verbose_name = _(u"e-mail config")
        verbose_name_plural = _(u"e-mail configs")


class Ivr(models.Model):
    """
    An IVR script.
    
    If it belonst to an account, it will be stored in
    ${wikipbx_root}/ivr/${account.name}. Otherwise it's a "global" ivr and will
    be in ${wikipbx_root}/ivr.
    """
    LANGUAGE_EXT_CHOICES = (("js", "JavaScript"), ("lua", "Lua"), 
        ("py", "Python"), ("xml", "IVR"), ("ivr_form", "IVR Menu"))

    name = models.CharField(
        _(u"name"), max_length=100,
        help_text=_(u"The filename, without the extension."))
    language_ext = models.CharField(
        _(u"language extension"), max_length=20,
        choices=LANGUAGE_EXT_CHOICES, default="py")
    account = models.ForeignKey(
        "Account", verbose_name=_(u"account"), null=True)

    def get_action_xml(self):
        return '<action application="%s" data="%s"/>' % (
            self.get_language_ext_display().lower(), self.get_module_path())
  
    def get_module_path(self):
        """
        Return module path.
        """
        if self.language_ext == "py":
            if self.account:        
                return "wikipbx.ivr.%s.%s" % (self.account.name, self.name)
            else:
                return "wikipbx.ivr.%s" % self.name
        elif self.language_ext == "xml":
            return self.name
        elif self.language_ext in ("js", "lua"):
            if self.account:
                return os.path.join(
                    settings.INSTALL_SRC, 'ivr', self.account.name, '%s.%s' %
                    (self.name, self.language_ext))
            else:
                return os.path.join(
                    settings.INSTALL_SRC, 'ivr', '%s.%s' % 
                    (self.name, self.language_ext))
        else:
            raise ValueError(_(u"Invalid extension: %s") %  self.language_ext)
        
    def get_script_path(self):
        script_dir = self.get_script_dir()
        script_fn = "%s.%s" % (self.name, self.language_ext)
        script_path = os.path.join(script_dir, script_fn)
        return script_path

    def get_script_dir(self):
        application_root = settings.INSTALL_SRC
        if self.account:
            ivr_root = os.path.join(application_root, "ivr")
            account_ivr_root = os.path.join(ivr_root, self.account.name)
            if not os.path.exists(account_ivr_root):
                os.makedirs(account_ivr_root)
                self.create_module_inits()
            return account_ivr_root
        else:
            ivr_root = os.path.join(application_root, "ivr")
            return ivr_root

    def create_module_inits(self):
        """
        The ivr dir and each subdir needs to have __init__.py
        scripts.
        """
        application_root = settings.INSTALL_SRC
        ivr_root = os.path.join(application_root, "ivr")
        ivr_init_path = os.path.join(ivr_root, "__init__.py")
        open(ivr_init_path,'w').write("# placeholder")
        account_ivr_root = os.path.join(ivr_root, self.account.name)        
        account_ivr_init_path = os.path.join(account_ivr_root, "__init__.py")
        open(account_ivr_init_path,'w').write("# placeholder")

    @models.permalink
    def get_absolute_url(self):
        return 'wikipbxweb:ivr-edit', (self.pk,), {}

    def __unicode__(self):
        return "%s.%s (id=%s)" % (self.name, self.language_ext, self.id)

    class Meta:
        verbose_name = _(u"IVR")
        verbose_name_plural = _(u"IVRs")
        ordering = ['name']

pre_delete.connect(listeners.pre_delete_ivr, sender=Ivr)


class IvrMenu(models.Model):
    """
    An XML IVR Menu definition.
    """
    ivr = models.OneToOneField('Ivr')
    greet_long = models.ForeignKey(
        'Soundclip', null=True, verbose_name=_(u'long greeting'), 
        related_name='greet_long',
        help_text=_(
            u"The initial recording that is played when a caller reaches "
            "this IVR."))
    greet_short = models.ForeignKey(
        'Soundclip', null=True, verbose_name=_(u'short greeting'),
        related_name='greet_short',
        help_text=_(
            u"The greeting that is re-played when the caller enters invalid "
            "information or no information at all. This is usually the same "
            "greeting as 'long greeting', but without the intro phrase."))
    invalid_sound = models.ForeignKey(
        'Soundclip', null=True, verbose_name=_(u'invalid sound'),
        related_name='invalid_sound',
        help_text=_(
            u"The greeting played when caller enters a wrong choice."))
    exit_sound = models.ForeignKey(
        'Soundclip', null=True, verbose_name=_(u'exit sound'),
        related_name='exit_sound',
        help_text=_(
            u"This is played when the caller made too many failed attempts "
            "or a timeout occurs just before it disconnects the call."))
    timeout = models.PositiveIntegerField(
        _(u"timeout"), default=10000,
        help_text=_(
            u"Time to wait for the user to start entering digits after "
            "the greeting has played. Number in milliseconds."))
    inter_digit_timeout = models.PositiveIntegerField(
        _(u"inter digit timeout"), default=2000,
        help_text=_(
            u"The maximum amount of time to wait in-between each digit "
            "the caller presses.  Number in milliseconds."))
    max_failures = models.PositiveIntegerField(
        _(u"max failures"), default=3,
        help_text=_(
            u"After how many failures call will be disconnected."))
    max_timeouts = models.PositiveIntegerField(
        _(u"max timeouts"), default=3,
        help_text=_(
            u"Number of allowed timeouts before disconnecting the call."))
    digit_len = models.PositiveIntegerField(
        _(u"digit length"), default=3,
        help_text=_(
            u"Number of digits to accept before determining the entry is "
            "complete. Usually should match extensions numbers length."))

    @models.permalink
    def get_absolute_url(self):
        return self.ivr.get_absolute_url()

    def __unicode__(self):
        return "%s" % (self.ivr.name)

    class Meta:
        ordering = ['ivr__name']


class IvrMenuDestination(models.Model):
    """
    An XML IVR menu destinations.
    """
    ivr_menu = models.ForeignKey('IvrMenu')
    action = models.ForeignKey("Action")
    order = models.PositiveIntegerField()

    def __unicode__(self):
        return "%s + %s (%d)" % (self.ivr_menu, self.action, self.order)

    class Meta:
        unique_together = (('ivr_menu', 'order'),)
        ordering = ['order']


class Soundclip(models.Model):
    """
    A sound clip, stored in /${app_root}/soundclips/${account.name}/%{name} or
    /${app_root}/soundclips/%{name}.
    """
    # TODO: support other file extensions like slin, mp3, ogg, etc
    # TODO: soundclips should be bound to users, not accounts?
    account = models.ForeignKey("Account", verbose_name=_(u"account"))
    name = models.CharField(_(u"name"), max_length=100)
    desc = models.CharField(
        _(u"description"), max_length=100, blank=True, default='')

    @property
    def path(self):
        return self.get_path()
    
    def get_path(self):
        """
        Return path to recorded file.
        """
        if self.pk:
            # Path for user soundclips
            soundclip_root = os.path.join(
                settings.INSTALL_SRC, "soundclips", self.account.name)
            if not os.path.exists(soundclip_root):
                os.makedirs(soundclip_root)
            file_name = self.pk    
        else:
            # Path for system soundclips
            soundclip_root = os.path.join(
                settings.INSTALL_ROOT, "soundclips")
            file_name = self.name    

        soundclip_fname = "%s.wav" % file_name
        soundclip_path = os.path.join(soundclip_root, soundclip_fname)
        return soundclip_path

    @models.permalink
    def get_absolute_url(self):
        # TODO: soundclip edit
        return 'wikipbxweb:soundclip-list', (), {}
    
    def __unicode__(self):
        return "%s (id=%s)" % (self.name, self.id)

    class Meta:
        unique_together = (('account', 'name'),)
        verbose_name = _(u"Sound clip")
        verbose_name_plural = _(u"Sound clips")
        ordering = ['name']

pre_delete.connect(listeners.pre_delete_soundclip, sender=Soundclip)


class CompletedCall(models.Model):
    """
    Every incoming call will be recorded here.  (WARNING:
    this table could get big and slow down the system)
    """
    account = models.ForeignKey(
        'Account', verbose_name=_(u"account"), null=True)
    uuid = models.CharField(_(u"UUID"), max_length=100)
    caller_id_number = models.CharField(_(u"caller ID number"), max_length=100)
    destination_number = models.CharField(
        _(u"Destination number"), max_length=100)
    chan_name = models.CharField(_(u"channel name"), max_length=100)
    answered_time = models.DateTimeField(_(u"answered time"))
    hangup_time = models.DateTimeField(_(u"hangup time"))
    cdr_xml = models.TextField(_(u"CDR XML"))

    @models.permalink
    def get_absolute_url(self):
        return (
            'wikipbxweb:calls-matched' if self.account_id else
            'wikipbxweb:calls-unmatched'), (), {}

    class Meta:
        verbose_name = _(u"completed call")
        verbose_name_plural = _(u"completed calls")
    

class EventSocketConfig(models.Model):
    """
    Data for event socket config.

    Sample config looks like this:
    
    <configuration name="event_socket.conf" description="Socket Client">
      <settings>
        <param name="listen-ip" value="127.0.0.1"/>
        <param name="listen-port" value="8021"/>
        <param name="password" value="ClueCon"/>
      </settings>
    </configuration>
    """
    listen_ip = models.IPAddressField(_(u"listen IP"), default='127.0.0.1')
    listen_port = models.PositiveIntegerField(_(u"listen port"), default=8021)
    password = models.CharField(
        _(u"password"), max_length=25, default=_(u'CHANGE ME'))

    def get_absolute_url(self):
        return 'wikibxweb:event-socket', (), {}

    class Meta:
        verbose_name = _(u"event socket config")
        verbose_name_plural = _(u"event socket configs")
        
