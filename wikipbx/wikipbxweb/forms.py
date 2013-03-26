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
import re
from django import forms
from django.conf import settings
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _
from wikipbx import statics
from wikipbx.wikipbxweb import fields, models, widgets
from xml.dom import minidom

__all__ = (
    'EmailConfigForm', 'TestMailserverForm', 'ExtensionForm',
    'SoundclipForm', 'SoundclipTTSForm', 'IvrForm', 'UserProfileForm',
    'UserProfileEditForm', 'RootUserForm', 'AccountAndAdminForm',
    'AccountForm', 'EndpointForm', 'EventSocketConfigForm',
    'SofiaGatewayForm', 'SipProfileForm', 'Click2CallForm',
    'ActionForm', 'ActionSingleForm', 'IvrNameForm', 'IvrMenuForm',)


def model_field(model, fieldname, **kwargs):
    return model._meta.get_field(fieldname).formfield(**kwargs)


class Click2CallForm(forms.Form):
    caller = forms.CharField(
        max_length=100, required=True, label=_(u"Calling party"),
        help_text=_(u"Your phone number."))
    called_party = forms.CharField(
        max_length=100, required=True, label=_(u"Called party"),
        help_text=_(u"Destination number."))
    gateway = forms.ChoiceField(
        label=_(u"Gateway"),
        help_text=_(u"Which gateway these two calls will be routed through"))


class EmailConfigForm(forms.ModelForm):
    class Meta:
        fields = (
            'from_email', 'email_host', 'email_port', 'auth_user',
            'auth_password', 'use_tls')
        
    
class TestMailserverForm(forms.Form):
    recipient = forms.CharField(max_length=75, label=_(u"Recipient"))
    subject = forms.CharField(label=_(u"Subject"), max_length=75)
    msg_body = forms.CharField(
        max_length=500, label=_(u"Message body"),
        widget=forms.Textarea({'rows': '20', 'cols': '70'}))


class ExtensionForm(forms.ModelForm):
    EXTENSION_TEMPLATE_CHOICES = (
        ('echo', _(u'Echo Test')),
        ('sip_url', _(u'Remote Endpoint')),
        ('endpoint', _(u'Local Endpoint')),
        ('endpoint_vm', _(u'Local Endpoint With Fallback To Voicemail')),
        ('gateway', _(u'Gateway Dialout')),
        ('conference', _(u'Conference Room')),
        ('playback', _(u'Playback Audio')),
        ('speak', _(u'Speak Text')),
        ('mod_voicemail_play', _(u'Mod_Voicemail Playback')),
        ('mod_voicemail_record', _(u'Mod_Voicemail Record')),
        ('transfer', _(u'Transfer To Another Extension')),
        ('park', _(u'Park Call')),
        ('lua_ivr', _(u'Lua IVR')),
        ('python_ivr', _(u'Python IVR')),
        ('javascript_ivr', _(u'Javascript IVR')))

    auth_call = model_field(
        models.Extension, 'auth_call', form_class=forms.ChoiceField,
        choices=((True, _(u'Authenticated')), (False, _(u'Public'))),
        widget=widgets.AuthCallWidget())

    def clean_dest_num(self):
        value = self.cleaned_data['dest_num']
        try:
            re.compile(value)
        except Exception:
            raise forms.ValidationError(_(u"Invalid regex"))
        else:
            return value

    def clean_endpoint(self):
        # This is needed to prevent django from resetting endpoint if the
        # field is disabled in web interface and browser doesn't submit it.
        if hasattr(self, 'instance'):
            return self.instance.endpoint

    def clean_actions_xml(self):
        actions_xml = self.cleaned_data['actions_xml']
        # does xml parse?
        xml_str = "<fakeroot>\n%s\n</fakeroot>" % actions_xml
        try:
            minidom.parseString(str(xml_str))
        except Exception:
            raise forms.ValidationError(_(u"Malformed XML"))
        return actions_xml
        
    class Meta:
        model = models.Extension
        fields = 'dest_num', 'callerid_num', 'desc', 'auth_call'


class ActionForm(forms.ModelForm):
    order = forms.IntegerField(widget=forms.HiddenInput)

    def __init__(self, action_obj, *args, **kwargs):
        super(ActionForm, self).__init__(*args, **kwargs)

        self.asf = []
        self.action_obj = action_obj

        # Load templates depending from action objcet type
        if isinstance(action_obj, models.IvrMenuDestination):
            templates = models.ActionTemplate.objects.filter(
                name__startswith='IVR destination')
        else:
            templates = models.ActionTemplate.objects.exclude(
                name__startswith='IVR destination')
        self.fields['template'].queryset = templates

    class Meta:
        model = models.Action


class ActionSingleForm(forms.Form):
    def __init__(self, account, template, action, *args, **kwargs):
        super(ActionSingleForm, self).__init__(*args, **kwargs)

        # load extensions
        extensions = models.Extension.objects.filter(account=account, 
            is_temporary=False)
        # load endpoints
        endpoints = models.Endpoint.objects.filter(account=account)
        # load gateways
        gateways = account.get_gateway_choices()
        # load audio files
        audiofiles = models.Soundclip.objects.filter(account=account)
        # load user and system ivr files
        ivrs = models.Ivr.objects.filter(Q(account=account)|
                                         Q(account__isnull=True))
        # load user IVR menus
        ivr_menus = models.IvrMenu.objects.filter(ivr__account=account)
        # Available voicetypes
        voicetypes = settings.TTS_VOICE_CHOICES

        self.template = template

        templ_vars = models.ActionVariable.objects.filter(template=template.id)
        # for every field in template
        for tv in templ_vars:
            if tv.variable_type == statics.AV_TYPE_SELECTION:
                self.fields[tv.id] = forms.ChoiceField(label=tv.name)
                if tv.kind == statics.AV_KIND_AUDIO_FILE:
                    self.fields[tv.id].choices = [
                        (item.id, item) for item in audiofiles]
                    SYS_AUDIO_FILES = ['beep', 'welcome_echo']
                    for sa in SYS_AUDIO_FILES:
                        self.fields[tv.id].choices.append((sa, sa))
                elif tv.kind == statics.AV_KIND_EXTENSION:
                    self.fields[tv.id].choices = [
                        (item.id, item) for item in extensions]
                elif tv.kind == statics.AV_KIND_GATEWAY:
                    self.fields[tv.id].choices = gateways
                elif tv.kind == statics.AV_KIND_IVR_MENU:
                    self.fields[tv.id].choices = [
			(item.id, item) for item in ivr_menus]
                elif tv.kind == statics.AV_KIND_IVR_SCRIPT:
                    self.fields[tv.id].choices = [
			(item.id, item) for item in ivrs]
                elif tv.kind == statics.AV_KIND_LOCAL_ENDPOINT:
                    self.fields[tv.id].choices = [
			(item.id, item) for item in endpoints]
                elif tv.kind == statics.AV_KIND_VOICE_TYPE:
                    self.fields[tv.id].choices = voicetypes
            elif tv.variable_type == statics.AV_TYPE_PROMPT:
                self.fields[tv.id] = forms.CharField(
                    label=tv.name, max_length=255)
            elif tv.variable_type == statics.AV_TYPE_TEXT:
                ta_msg_body = forms.Textarea({'rows': '20', 'cols': '70'})
                self.fields[tv.id] = forms.CharField(
		    label=tv.name, max_length=500, widget=ta_msg_body)
            # Init with values from DB
            try:
                ad = models.ActionData.objects.get(action=action, variable=tv)
                self.fields[tv.id].initial = ad.value
            except models.ActionData.DoesNotExist:
                self.fields[tv.id].initial = tv.default


class ActionsEditForm:
    def __init__(self, request_data, actions, account):
        """
        Create forms for Actions and subforms for data
        """
        self.form_actions = []

        if not actions:
            templates = models.ActionTemplate.objects.all()
            if not templates:
                raise Exception(
                    "No Action Templates found. You must run: "
                    "'./manage.py loaddata extension_actions.json' "
                    "to install default templates")
                return

        # Build form for every Action
        for action_obj in actions:
            af = ActionForm(
                action_obj, request_data,
                initial={'template': action_obj.action.template.id,
                         'order': action_obj.order},
                prefix=action_obj.order)
            # Build all possible templates forms for every Action
            for template in af.fields['template'].queryset:
                asf = ActionSingleForm(
                    account, template, action_obj.action, request_data,
                    prefix=action_obj.order)
                af.asf.append(asf)
            self.form_actions.append(af)

    def __getitem__(self, i):
        """Allow to iterate through form_actions"""
        return self.form_actions[i]

    def is_valid(self):
        """
        Validate forms
        """
        # Process actions forms
        for af in self.form_actions:
            if not af.is_valid():
                break
            else:
                # Action template selected
                # Find subform data for selected action
                for asf in af.asf:
                    if asf.template == af.cleaned_data['template']:
                        break
                else:
                    # No data found for this action. Process next Action
                    continue
                if not asf.is_valid():
                    break
        else:
            return True
        return False

    def save(self, parent_object, commit=True):
        """
        Save Actions forms
        """
        for af in self.form_actions:
            # Save Action
            action = af.save()

            # Save parent action object
            af.action_obj.action = action
            if isinstance(parent_object, models.IvrMenu):
                af.action_obj.ivr_menu = parent_object
            else:
                af.action_obj.extension = parent_object
            af.action_obj.order = af.cleaned_data['order']
            af.action_obj.save()

            # Find subform data for selected Action
            for asf in af.asf:
                if asf.template == af.cleaned_data['template']:
                    # Found subform with required template
                    break
            else:
                # No data found for this action. Process next Action
                continue

            # Process action variables and save their values
            for (key, val) in asf.cleaned_data.items():
                av = models.ActionVariable.objects.get(id=key)
                # Check if action data exists for this variable
                try:
                    # Yes. Update them with the new value
                    ad = models.ActionData.objects.get(
                        action=action, variable=av)
                    ad.value = val
                except models.ActionData.DoesNotExist:
                    # No. Create new one
                    ad = models.ActionData(
                        action=action, variable=av, value=val)
                # Save variable
                ad.save()
        return


class SoundclipForm(forms.ModelForm):
    upload_method = forms.ChoiceField(
        choices=(("dialout", _(u"Dialout")), ("upload_wav", _(u"WAV upload")),
                 ("wav_url", _(u"WAV URL")), ("tts", _(u"Text to speech"))),
        initial="dialout",
        label=_(u"Upload method"),
        widget=forms.RadioSelect(attrs={'onclick': 'choose_upload_method()'}))

    def clean_name(self):
        value = self.cleaned_data['name']
        if self.instance.pk is None and (
            models.Soundclip.objects.filter(
                name=value, account=self.instance.account).exists()):
            raise forms.ValidationError(_(u'This value is already occupied.'))
        return value
            
    class Meta:
        model = models.Soundclip
        fields = ['upload_method', 'name', 'desc']


class SoundclipTTSForm(forms.Form):
    tts_text = forms.CharField(
        max_length=2000, label=_(u'Text to speak'),required=True)
    tts_voice = forms.ChoiceField(
        choices=settings.TTS_VOICE_CHOICES,
        initial=settings.TTS_DEFAULT_VOICE,
        label=_(u'Voice'))


class IvrForm(forms.ModelForm):
    ivr_code = forms.CharField(
        max_length=50000, required=True, label=_("IVR code"),
        widget=forms.Textarea({'rows': '20', 'cols': '70'}))

    def __init__(self, *args, **kwargs):
        super(IvrForm, self).__init__(*args, **kwargs)
        if self.instance.pk:
            script_path = self.instance.get_script_path()
            initial_ivr_code = open(script_path, 'r').read()
            self.fields['ivr_code'].initial = initial_ivr_code

    def save(self, commit=True):
        result = super(IvrForm, self).save(commit=commit)

        script_path = result.get_script_path()
        open(script_path, 'w').write(self.cleaned_data['ivr_code'])

        return result

    class Meta:
        model = models.Ivr
        exclude = ['account']


class IvrNameForm(forms.ModelForm):
    name = model_field(models.Ivr, 'name', help_text=_('IVR name.'))
                    
    class Meta:
        model = models.Ivr
        fields = ['name']


class IvrMenuForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(IvrMenuForm, self).__init__(*args, **kwargs)

        soundclips = models.Soundclip.objects.filter(
            account=self.instance.ivr.account)
        self.fields['greet_long'].queryset = soundclips
        self.fields['greet_short'].queryset = soundclips
        self.fields['invalid_sound'].queryset = soundclips
        self.fields['exit_sound'].queryset = soundclips

    class Meta:
        model = models.IvrMenu
        exclude = ['ivr']


class BaseUserProfileForm(forms.ModelForm):
    class Meta:
        model = models.UserProfile
        

class UserProfileForm(forms.ModelForm):
    password = model_field(
        models.UserProfile, 'password', help_text=_('Type password twice.'),
        form_class=fields.RepeatedPasswordField)
    is_admin = forms.BooleanField(required=False, label=_(u'Is admin'))

    def clean_email(self):
        email = self.cleaned_data['email']

        self.instance.username = email

        existing_profiles = models.UserProfile.objects.filter(
                Q(username=email) | Q(email=email))
        if self.instance.pk:
            existing_profiles = existing_profiles.exclude(pk=self.instance.pk)
            
        if existing_profiles.count():
            raise forms.ValidationError(_(u"This email is already occupied"))
        else:
            return email
    
    def clean_password(self):
        self.instance.set_password(self.cleaned_data['password'])
        return self.instance.password
    
    class Meta(BaseUserProfileForm.Meta):
        fields = (
            'email', 'password', 'first_name', 'last_name', 'is_admin',
            'is_active')


class UserProfileEditForm(BaseUserProfileForm):
    class Meta(BaseUserProfileForm.Meta):
        fields = ['email', 'first_name', 'last_name', 'is_active']


class RootUserForm(forms.Form):
    blurb = _(
        u"WikiPBX has a single root user which acts as the superuser, "
        "operating outside of all accounts (tenants), and has unlimited "
        "security access.  Once these values have been entered they cannot "
        "be changed via the GUI, and the only way to modify them will be to "
        "go direct to the database.  Ditto goes for lost/forgotten root "
        "passwords.")
    email = forms.EmailField(max_length=100, label=_(u'Email'))
    password = forms.CharField(
        label=_('Password'), max_length=100, widget=forms.PasswordInput())
    first_name = forms.CharField(max_length=100, label=_('First name'))
    last_name = forms.CharField(max_length=100, label=_('Last name'))


class SipProfileForm(forms.ModelForm):
    blurb = _(
        u"FreeSWITCH can listen on multiple ports (e.g. 5060, 5061) and IP "
        "addresses.  Each one of these listening points requires its own SIP "
        "profile. Most installations can get by with a single profile that "
        "listens on port 5060 of the internet-facing IP address. "
        "Other typical scenario is to have two profiles. "
        "One for 'internal' calls and another for 'external' calls. "
        "In this case internal profile requires calls to be authenticated. "
        "External profile allows non-authenticated calls handled in "
        "public context."
        )
    ext_rtp_ip = model_field(models.SipProfile, 'ext_rtp_ip',
        form_class=fields.FreeswitchAddressField)
    ext_sip_ip = model_field(models.SipProfile, 'ext_sip_ip',
        form_class=fields.FreeswitchAddressField)
    rtp_ip = model_field(models.SipProfile, 'rtp_ip',
        form_class=fields.FreeswitchAddressField)
    sip_ip = model_field(models.SipProfile, 'sip_ip',
        form_class=fields.FreeswitchAddressField)
        
    class Meta:
        model = models.SipProfile


class AccountAndAdminForm(forms.Form):
    """
    Form that adds an account and and admin at the same time.
    """
    blurb = _(
        u"An account is essentially a Tenant.  WikiPBX is designed in such a "
        "way to minimize data sharing between accounts, so for example each "
        "account has its own set of users, endpoints, gateways, call detail "
        "records,  and dialplan that is not shared with other accounts.  When "
        "an account is created you must specify an initial  account admin, "
        "which can later be modified or deleted.")
    name = forms.CharField(
        max_length=50, label=_(u"Account name"),
        help_text=_(u"Name of account, eg, yourcompany or yourcompany.com"))
    enabled = forms.BooleanField(initial=True, required=False)
    domain = forms.CharField(
        max_length=100, label=_(u'Domain'), required=False,
        help_text=_(u"The domain associated with this account, eg. "
                    "sip.yourcompany.com. Endpoints belonging to this account "
                    "should be configured to register to this domain."))
    dialout_profile = forms.ChoiceField(
        label=_("SIP profile for dialout"),
        help_text=_(u"When web dialout is used for this account, which SIP "
                    "profile should it use?"))
    aliased = forms.BooleanField(
        initial=True, required=False,
        label=_(u"Alias this domain to Dialout SIP profile?"),
        help_text=_(
            u"When checked, this account's domain will become an alias for "
            "the dialout SIP profile."))
    email = forms.EmailField(label=_(u"Admin email"))
    password = forms.CharField(
        max_length=100, label=_("Admin password"), widget=forms.PasswordInput)
    first_name = forms.CharField(max_length=100, label=_(u"Admin first name"))
    last_name = forms.CharField(max_length=100, label=_(u"Admin last name"))
    is_active = forms.BooleanField(initial=True, label=_(u"Active"))

    def __init__(self, sip_profiles, *args, **kwargs):
        # the current sip_profile is selected based on the
        # dialout_profile key in the form dictionary (see form_dict()
        # method in Account model)

        super(AccountAndAdminForm, self).__init__(*args, **kwargs)
        ddp_choices = []
        for sip_profile in sip_profiles:
            ddp_choices.append((sip_profile.id,
                                sip_profile.name))
        self.fields['dialout_profile'].choices = ddp_choices

class AccountForm(forms.Form):
    name = forms.CharField(
        max_length=50, label=_(u"Account name"),
        help_text=_(u"Name of account, eg, yourcompany or yourcompany.com"))
    enabled = forms.BooleanField(initial=True, required=False)
    domain = forms.CharField(
        max_length=100, label=_(u'Domain'), required=False,
        help_text=_(u"The domain associated with this account, eg. "
                    "sip.yourcompany.com. Endpoints belonging to this account "
                    "should be configured to register to this domain."))
    dialout_profile = forms.ChoiceField(
        label=_(u"Dialout SIP Profile"),
        help_text=_(u"When WikiPBX generates dial strings for this domain, "
                    "which SIP profile should it use?"))
    aliased = forms.BooleanField(initial=True, required=False,
        label=_(u"Alias this domain to Dialout SIP profile?"),
        help_text=(u"When checked, this account's domain will become an "
                   "alias for the dialout sip profile."))

    def __init__(self, sip_profiles, *args, **kwargs):

        # the current sip_profile is selected based on the
        # dialout_profile key in the form dictionary (see form_dict()
        # method in Account model)

        super(AccountForm, self).__init__(*args, **kwargs)
        ddp_choices = []
        for sip_profile in sip_profiles:
            ddp_choices.append((sip_profile.id,
                                sip_profile.name))
        self.fields['dialout_profile'].choices = ddp_choices
        
        
class EndpointEditForm(forms.ModelForm):
    # Display the endpoint domain from the account settings.
    # Let the user now how to configure his endpoints.
    domain = forms.CharField(
        widget=forms.TextInput(attrs={'readonly':'readonly'}),
        required=False, label=_(u'Domain'),
        help_text=_(
            u"The domain associated with this account. "
            "The endpoint should be configured to register to this domain."))

    def __init__(self, *args, **kwargs):
        super(EndpointEditForm, self).__init__(*args, **kwargs)

        available_profiles = models.UserProfile.objects.filter(
            account=self.instance.account)
        self.fields['userprofile'].required = False
        self.fields['userprofile'].queryset = available_profiles
        self.fields['userprofile'].choices = [('', '')] + [
            (profile.id, profile) for profile in available_profiles]
        
        self.fields['domain'].initial = self.instance.account.domain    
        
    class Meta:
        model = models.Endpoint
        fields = (
            'userid', 'password', 'domain', 'userprofile', 'vm_enabled',
            'vm_password', 'vm_notify_mailto', 'vm_mailto', 
            'vm_remove_local_after_email', 'toll_allow',
            'effective_caller_id_name', 'effective_caller_id_number',
            'outbound_caller_id_name', 'outbound_caller_id_number')


class EndpointCreateForm(EndpointEditForm):
    create_extension = forms.BooleanField(
        required=False, initial=False, label=_(u'Create extension'),
        help_text=_('Create a dialplan entry for this number'))
        

class EventSocketConfigForm(forms.ModelForm):
    class Meta:
        model = models.EventSocketConfig


class SofiaGatewayForm(forms.Form):
    name = forms.CharField(
        max_length=100, required=True, label=_(u"Gateway name"))
    sip_profile = forms.ChoiceField(
        label=_(u"SIP profile"),
        help_text=_(
            u"Which SIP Profile communication with this gateway will take "
            "place on."))
    username = forms.CharField(
        max_length=25, label=_(u'Username'),
        help_text=_(u"Username for gateway login authentication."))
    password = forms.CharField(
        max_length=25, label=_(u"Password"),
        help_text=_(u"Password for gateway login authentication."),
        widget=forms.PasswordInput())
    proxy = forms.CharField(
        max_length=50, label=_(u"Proxy"),
        help_text=_(u"Proxy host: *optional* same as realm, if blank."))
    register = forms.BooleanField(
        initial=False, required=False, label=_(u"Register"),
        help_text=_(u"Register with the gateway?"))
    extension = forms.CharField(
        max_length=50, required=False, label=_(u'Extension'),
        help_text=_(
            u"Extension for inbound calls: *optional* same as username, if "
            "blank."))
    realm = forms.CharField(
        max_length=50, required=False, label=_(u'Realm'),
        help_text=_(u"Auth realm: *optional* same as gateway name, if blank."))
    from_domain = forms.CharField(
        max_length=50, required=False, label=_(u"From domain"),
        help_text=_(
            u"Domain to use in From field: *optional* same as realm, if "
            "blank."))
    expire_seconds = forms.IntegerField(
        initial=60, label=_(u"Expire seconds"),
        help_text=_(u"Expire in seconds: *optional* 3600, if blank."))
    retry_seconds = forms.IntegerField(
        initial=30,
        help_text=_(u"How many seconds before a retry when a failure or "
                    "timeout occurs"))
    caller_id_in_from = forms.BooleanField(
        initial=False, required=False, label=_(u'Caller ID in From'),
        help_text=_(
            u"Use the caller ID of an inbound call in the From field on "
            "outbound calls via this gateway."))
    accessible_all_accts = forms.BooleanField(
        initial=False, required=False, label=_(u'Accessible for all accounts'),
        help_text=_(
            u"Are other WikiPBX accounts allowed to dial out of this "
            "gateway?"))
    
    def __init__(self, sip_profiles, show_none, *args, **kwargs):
        super(SofiaGatewayForm, self).__init__(*args, **kwargs)

        # when showing an edit gateway form, the sip_profile is selected
        # based on the sip_profile key in the form dictionary (see form_dict()
        # method in SofiaGateway model)
        
        sip_profile_choices = []
        if show_none:
            sip_profile_choices.append((-1,"None"))                
        if sip_profiles:
            for sip_profile in sip_profiles:
                if not sip_profile:
                    continue
                if type(sip_profile) == type(""):
                    continue                
                sip_profile_choices.append((sip_profile.id,
                                         sip_profile.name))
        self.fields['sip_profile'].choices = sip_profile_choices
