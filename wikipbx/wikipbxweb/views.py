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
import datetime
import itertools
import os
import shutil
import time
from django import http
from django.conf import settings
from django.contrib.auth import authenticate, login, logout, models as djmodels
from django.core.urlresolvers import reverse
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, render
from django.utils.translation import ugettext as _
from django.utils.decorators import method_decorator
from django.views.generic.list import ListView
from django.views.decorators.csrf import csrf_exempt
from pprint import pformat
from wikipbx import logger, fsutil, utils, extensionutil, authutil
from wikipbx import xmlconfig, cdrutil, mailutil, sofiautil, ttsutil, statics
from wikipbx.wikipbxweb import decorators, forms, models


def index(request):
    return render(request, 'index.html', {'nousers': not djmodels.User.objects.all()})

@decorators.require_login
def dashboard(request):
    return render(request, 'dashboard.html')

def memberlogin(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                return http.HttpResponseRedirect(reverse(
                    'wikipbxweb:dashboard'))
        msg = _(
            u"Authentication failed.  Please try again, make sure the" 
            " CAPS-LOCK key is off and there are no typo's.")
        return http.HttpResponseRedirect(
            reverse('wikipbxweb:index') + "?urgentmsg=%s" % msg)
    else:
        return http.HttpResponseRedirect(reverse('wikipbxweb:index'))

@decorators.require_login
def memberlogout(request):
    logout(request)
    msg = _("You have been logged out")
    return http.HttpResponseRedirect(
        reverse('wikipbxweb:index') + "?infomsg=%s" % msg)

@decorators.require_admin
def extensions(request):
    account = request.user.get_profile().account
    exts = models.Extension.objects.filter(account=account, is_temporary=False)
    blurb = _(
        u"When an incoming call comes into the PBX, extensions are matched in "
        "the order they are shown here, from top to bottom.  Once a match is "
        "found it is executed.  Re-order extensions using the green arrows.")
    return render(request, 'extensions.html', {'exts': exts, 'blurb': blurb})

@decorators.require_admin
def ext_priority(request, extension_id, action):
    """
    Action can be one of 'highest', 'lowest', 'raise' or 'lower'.
    """
    account = request.user.get_profile().account
    extension = get_object_or_404(
        models.Extension, account=account, pk=extension_id)
                                        
    msg = _("Invalid action.")
    if action in ["lowest", "highest"]:
        extensionutil.reset_priority_position(account, extension, action)
        msg = _(u"Extension priority set to %s.") % action
    elif action in ["raise", "lower"]:
        extensionutil.bump_priority_position(account, extension, action)
        msg = (
            _(u"Extension priority raised.") if action == 'raise' else
            _(u"Extension priority lowered."))
    return http.HttpResponseRedirect(
        reverse('wikipbxweb:extension-list') + "?infomsg=%s" % msg)

@decorators.require_admin
def edit_extension(request, extension_id):
    account = request.user.get_profile().account

    if extension_id:
        # Edit extension
        extension = get_object_or_404(
            models.Extension, account=account, pk=extension_id)
        # Load all Actions for this extension
        actions = models.ExtensionAction.objects.filter(extension=extension_id)
    else:
        # Add extension
        priority = extensionutil.new_ext_priority_position(account)
        extension = models.Extension(
            account=account, priority_position=priority)
        actions = models.Action.create_actions(models.ExtensionAction, 1)

    request_data = request.POST if request.method == 'POST' else None

    # Build form for Extension
    form = forms.ExtensionForm(request_data, instance=extension)

    # Build subforms for every action
    form_actions = forms.ActionsEditForm(request_data, actions, account)

    # Validate forms
    if request.method == 'POST' and \
        form.is_valid() and form_actions.is_valid():
        # Save Extension
        extension = form.save()
        # Save actions
        form_actions.save(extension)
        msg = _(u"Extension %s saved.") % extension
        return http.HttpResponseRedirect(
            reverse('wikipbxweb:extension-list') + "?infomsg=%s" % msg)

    blurb = _(
        u"Dialplan extensions can bridge to locally registered endpoints,"
        " remote endpoints, PSTN numbers via gateways, special applications"
        " such as the Echo Test, or IVR scripts.")
    return render(request, 'edit_extension.html',
        {'form': form, 'form_actions': form_actions, 'blurb':blurb})

@decorators.require_admin
def del_extension(request, extension_id):
    account = request.user.get_profile().account
    # Check if this is an extension of authorized account
    extension = get_object_or_404(
        models.Extension, account=account, pk=extension_id)
    # Remove Actions used together with this extension
    actions = models.Action.objects.filter(
        extensionaction__extension=extension).delete()
    # Remove extension
    extension.delete()
    msg = _(u"Extension %s deleted.") % extension
    return http.HttpResponseRedirect(
        reverse('wikipbxweb:extension-list') + "?infomsg=%s" % msg)

@decorators.require_admin
def add_ext_action(request, extension_id):
    account = request.user.get_profile().account

    # Check if this is an extension of authorized account
    extension = get_object_or_404(
        models.Extension, account=account, pk=extension_id)

    # Load all Actions for this Extension
    actions = models.ExtensionAction.objects.filter(extension=extension_id)
    ordered_actions = actions.order_by("-order")
    next_order = (ordered_actions[0].order + 1) if ordered_actions else 1
    # Create new Action
    actions = models.Action.create_actions(models.ExtensionAction, 1, next_order)

    request_data = request.POST if request.method == 'POST' else None

    # Build subform for every action
    form_actions = forms.ActionsEditForm(request_data, actions, account)

    # Validate forms
    if request.method == 'POST' and form_actions.is_valid():
        # Save actions
        form_actions.save(extension)
        msg = _(u"Action added.")
        return http.HttpResponseRedirect(
            reverse('wikipbxweb:extension-edit', args=[extension_id]) +
            "?infomsg=%s" % msg)

    blurb = _(u"Add new action.")
    action_name = _(u"Action")
    return render(request, 'action.html', 
        {'form_actions': form_actions, 'blurb': blurb,
        'action_name':action_name})

@decorators.require_admin
def add_ivr_action(request, ivr_id):
    account = request.user.get_profile().account

    # Check if this is an IVR of authorized account
    ivr_menu = get_object_or_404(
        models.IvrMenu, ivr__id=ivr_id, ivr__account=account)

    # Load all Actions for this IVR menu
    actions = models.IvrMenuDestination.objects.filter(ivr_menu__ivr=ivr_id)
    ordered_actions = actions.order_by("-order")
    next_order = (ordered_actions[0].order + 1) if ordered_actions else 1
    # Create new Action            
    actions = models.Action.create_actions(models.IvrMenuDestination, 1, next_order)
        
    request_data = request.POST if request.method == 'POST' else None

    # Build subform for every action
    form_actions = forms.ActionsEditForm(request_data, actions, account)

    # Validate forms
    if request.method == 'POST' and form_actions.is_valid():
        # Save actions
        form_actions.save(ivr_menu)
        msg = _(u"Action added.")
        return http.HttpResponseRedirect(
            reverse('wikipbxweb:ivr-xml-edit', args=[ivr_id]) +
            "?infomsg=%s" % msg)
                        
    blurb = _(u"Add new IVR destination.")
    action_name = _(u"IVR destination")
    return render(request, 'action.html', 
        {'form_actions': form_actions, 'blurb': blurb, 
        'action_name':action_name})

@decorators.require_admin
def del_ext_action(request, action_id):
    account = request.user.get_profile().account

    # Check if this Action exists and belongs to this account
    action = get_object_or_404(models.Action, pk=action_id)
    extension_action = get_object_or_404(models.ExtensionAction, 
        Q(extension__account=account, action=action))

    # Remove Action
    action.delete()
    msg = _(u"Action deleted.")
    return http.HttpResponseRedirect(
        reverse('wikipbxweb:extension-edit', args=[extension_action.extension.id]) +
        "?infomsg=%s" % msg)

@decorators.require_admin
def del_ivr_action(request, action_id):
    account = request.user.get_profile().account

    # Check if this Action exists and belongs to this account
    action = get_object_or_404(models.Action, pk=action_id)
    ivr_menu_destination = get_object_or_404(models.IvrMenuDestination,
        Q(ivr_menu__ivr__account=account, action=action))

    # Remove Action
    action.delete()
    msg = _(u"Action deleted.")
    return http.HttpResponseRedirect(
        reverse('wikipbxweb:ivr-xml-edit',
                args=[ivr_menu_destination.ivr_menu.ivr.id]) +
        "?infomsg=%s" % msg)

@decorators.require_admin
def ivrs(request):
    account = request.user.get_profile().account
    account_ivrs = models.Ivr.objects.filter(
        account=account).exclude(language_ext='ivr_form')
    account_ivr_menus = models.Ivr.objects.filter(
        account=account, language_ext='ivr_form')
    system_ivrs = models.Ivr.objects.filter(account__isnull=True)
    return render(request, 'ivrs.html',
        {'account_ivrs':account_ivrs,
        'account_ivr_menus':account_ivr_menus,
        'system_ivrs':system_ivrs})
        
@decorators.require_admin
def edit_ivr(request, ivr_id):
    account = request.user.get_profile().account
    ivr = get_object_or_404(models.Ivr, account=account, pk=ivr_id)

    if request.method == 'POST':
        # If its a system ivr, only root can edit.
        if ivr.account or request.user.is_superuser:
            form = forms.IvrForm(request.POST, instance=ivr)
            if form.is_valid():
                ivr = form.save()
                msg = _(u"IVR %s saved.") % ivr
                return http.HttpResponseRedirect(
                    reverse('wikipbxweb:ivr-list') + "?infomsg=%s" % msg)
        else:
            msg = _(u"Only root can edit system-wide IVRs.")
            return http.HttpResponseRedirect(
                reverse('wikipbxweb:ivr-list') + "?urgentmsg=%s" % msg)
    else:
        form = forms.IvrForm(instance=ivr)
        
    return render(request, 'edit_ivr.html', {'form': form})

@decorators.require_admin
def del_ivr(request, ivr_id):
    account = request.user.get_profile().account                
    ivr = get_object_or_404(models.Ivr, account=account, pk=ivr_id)
    # Remove Actions used together with this IVR
    actions = models.Action.objects.filter(
        ivrmenudestination__ivr_menu__ivr=ivr)
    actions.delete()
    # Remove IVR
    ivr.delete()
    msg = _(u"Ivr %s deleted.") % ivr
    return http.HttpResponseRedirect(
        reverse('wikipbxweb:ivr-list') + "?infomsg=%s" % msg)

@decorators.require_root
def del_account(request, account_id):
    account = get_object_or_404(models.Account, pk=account_id)
    profile_name = account.dialout_profile.name
    account.delete()
    try:
        fsutil.sofia_profile_restart(profile_name)
        msg = _(u"Account deleted. FreeSWITCH notified.")
    except Exception, e:
        msg = _(u"Account deleted, failed to notify FreeSWITCH: %s.") % str(e)
    return http.HttpResponseRedirect(
        reverse('wikipbxweb:account-list') + "?infomsg=%s" % msg)

@decorators.require_root
def del_sip_profile(request, profile_id):
    sip_profile = models.SipProfile.objects.get(pk=profile_id)
    gateways = sip_profile.get_gateways()
    if gateways:
        msg = _(u"There are still %s gateways associated with this SIP profile,"
                " fix this first.") % len(gateways)
        return http.HttpResponseRedirect(
            reverse('wikipbxweb:profile-list') + "?urgentmsg=%s" % msg)
    sip_profile_name = sip_profile.name
    sip_profile.delete()
    try:
        fsutil.sofia_profile_stop(sip_profile_name)
        msg = _(u"SIP Profile deleted. FreeSWITCH notified.")
    except Exception, e:
        msg = _(u"SIP Profile deleted, "
                 "failed to notify FreeSWITCH: %s.") % str(e)
    return http.HttpResponseRedirect(
        reverse('wikipbxweb:profile-list') + "?infomsg=%s" % msg)

@decorators.require_root
def event_socket(request):
    eventsockets = models.EventSocketConfig.objects.all()[:1]
    if eventsockets:
        # Get first available event socket config.
        eventsocket = eventsockets[0]
    else:
        # Otherwise create a new one.
        eventsocket = models.EventSocketConfig()
    
    if request.method == 'POST':
        form = forms.EventSocketConfigForm(request.POST, instance=eventsocket)
        if form.is_valid():
            eventsocket = form.save()
            msg = _(u"Event_socket config %s updated.") % eventsocket.id
            return http.HttpResponseRedirect(
                reverse('wikipbxweb:dashboard') + "?infomsg=%s" % msg)
    else:
        form = forms.EventSocketConfigForm(instance=eventsocket)
        
    return render(request, 'object_form.html', {'form':form})

@decorators.require_admin
def add_ivr(request):
    account = request.user.get_profile().account
    ivr = models.Ivr(account=account)
    if request.method == 'POST':
        form = forms.IvrForm(request.POST, instance=ivr)
        if form.is_valid():
            ivr = form.save()
            msg = _(u"IVR %s saved.") % ivr
            return http.HttpResponseRedirect(
                reverse('wikipbxweb:ivr-list') + "?infomsg=%s" % msg)
    else:
        form = forms.IvrForm(instance=ivr)
    
    blurb = _(u"IVR script")    
    return render(request, 'object_form.html',
        {'form':form, 'blurb':blurb})

@decorators.require_admin
def edit_ivr_xml(request, ivr_id=None):
    account = request.user.get_profile().account

    request_data = request.POST if request.method == 'POST' else None

    # Add or Edit IVR menu?
    if ivr_id:
        ivr = get_object_or_404(models.Ivr, pk=ivr_id, account=account)
        ivr_menu = get_object_or_404(models.IvrMenu, ivr=ivr)
        # Load all Actions for this IVR
        actions = models.IvrMenuDestination.objects.filter(ivr_menu__ivr=ivr_id)
    else:
        ivr = models.Ivr(account=account, language_ext='ivr_form')
        ivr_menu = models.IvrMenu(ivr=ivr)
        # Create empty action templates
        actions = models.Action.create_actions(models.IvrMenuDestination, 3)

    # IVR menu general properties forms
    form_ivr_name = forms.IvrNameForm(request_data, instance=ivr)
    form_ivr_menu = forms.IvrMenuForm(request_data, instance=ivr_menu)

    # Build form for every Action
    form_actions = forms.ActionsEditForm(request_data, actions, account)

    # Validate forms
    if request.method == 'POST' and form_ivr_name.is_valid() and \
        form_ivr_menu.is_valid() and form_actions.is_valid():
        # Save IVR
        ivr = form_ivr_name.save()
        # Save IVR Menu
        ivr_menu = form_ivr_menu.save(commit=False)
        ivr_menu.ivr = ivr
        ivr_menu.save()
        # Save actions
        form_actions.save(ivr_menu)
        msg = _(u"IVR %s saved.") % ivr
        return http.HttpResponseRedirect(
            reverse('wikipbxweb:ivr-list') + "?infomsg=%s" % msg)

    blurb = _(u"IVR menu")
    return render(request, 'edit_ivr_menu.html', 
        {'form_ivr_name':form_ivr_name, 'form_ivr_menu':form_ivr_menu, 
         'form_actions': form_actions, 'blurb':blurb}) 

@decorators.require_root
def edit_account(request, account_id):
    account = get_object_or_404(models.Account, pk=account_id)
    sip_profiles = models.SipProfile.objects.all()
    if request.method == 'POST':
        form = forms.AccountForm(sip_profiles, request.POST)        
        if form.is_valid():
            old_profile_name = account.dialout_profile.name
            dp_id = form.cleaned_data['dialout_profile']
            dialout_profile = models.SipProfile.objects.get(pk=dp_id)
            account.name = form.cleaned_data['name']
            account.enabled = form.cleaned_data['enabled']
            account.domain = form.cleaned_data['domain']            
            account.dialout_profile = dialout_profile
            account.aliased = form.cleaned_data['aliased']
            account.save()

            try:
                fsutil.sofia_profile_restart(old_profile_name)
                if old_profile_name != dialout_profile.name:
                    time.sleep(5)
                    fsutil.sofia_profile_restart(dialout_profile.name)
                msg = _(u"Account updated. FreeSWITCH notified.")
            except Exception, e:
                msg = _(u"Account updated, "
                         "failed to notify FreeSWITCH: %s") % str(e)
            return http.HttpResponseRedirect(
                reverse('wikipbxweb:account-list') + "?infomsg=%s" % msg)
    else:
        form = forms.AccountForm(sip_profiles, account.form_dict())
        
    return render(request, 'object_form.html', {'form':form})    

@decorators.require_root
def add_sip_profile(request):
    if request.method == 'POST':
        form = forms.SipProfileForm(request.POST)
        if form.is_valid():
            sip_profile = form.save()
            try:
                fsutil.sofia_profile_start(sip_profile.name)
                msg = _(u"SIP Profile added. FreeSWITCH notified.")
            except Exception, e:
                msg = _(u"SIP Profile added, "
                         "failed to notify FreeSWITCH: %s.") % str(e)
            return http.HttpResponseRedirect(
                reverse('wikipbxweb:profile-list') + "?infomsg=%s" % msg)
    else:
        form = forms.SipProfileForm()

    return render(request, 'object_form.html', 
        {'form':form, 'blurb':form.blurb})

@decorators.require_root
def edit_sip_profile(request, profile_id):
    sipprofile = get_object_or_404(models.SipProfile, pk=profile_id)
    if request.method == 'POST':
        profile_old_name = sipprofile.name
        form = forms.SipProfileForm(request.POST, instance=sipprofile)        
        if form.is_valid():
            sip_profile = form.save()
            try:
                fsutil.sofia_profile_stop(profile_old_name)
                time.sleep(5)
                fsutil.sofia_profile_start(sip_profile.name)
                msg = _(u"SIP Profile updated. FreeSWITCH notified.")
            except Exception, e:
                msg = _(u"SIP Profile updated, "
                         "failed to notify FreeSWITCH: %s.") % str(e)
            return http.HttpResponseRedirect(
                reverse('wikipbxweb:profile-list') + "?infomsg=%s" % msg)
    else:
        form = forms.SipProfileForm(instance=sipprofile)

    return render(request, 'object_form.html', 
        {'form':form, 'blurb':form.blurb})

@decorators.require_root
def add_account(request):
    sip_profiles = models.SipProfile.objects.all()
    if request.method == 'POST':
        # process form
        form = forms.AccountAndAdminForm(sip_profiles, request.POST)        
        if form.is_valid():
            try:
                transaction.enter_transaction_management()
                transaction.managed(True)

                dp_id = form.cleaned_data['dialout_profile']
                dialout_profile = models.SipProfile.objects.get(pk=dp_id)
                
                account = models.Account.objects.create(
                    name=form.cleaned_data['name'],
                    enabled=form.cleaned_data['enabled'],
                    domain=form.cleaned_data['domain'],
                    dialout_profile=dialout_profile,
                    aliased=form.cleaned_data['aliased'])
                email = form.cleaned_data['email']
                user = models.UserProfile(
                    username=email, email=email,
                    first_name=form.cleaned_data['first_name'],
                    last_name=form.cleaned_data['last_name'], is_staff=False,
                    is_active=form.cleaned_data['is_active'],
                    is_superuser=False, account=account)
                user.set_password(form.cleaned_data['password'])
                user.save()

                account.admins.add(user)
                
                # commit transaction
                transaction.commit()
                transaction.leave_transaction_management()

                try:
                    fsutil.sofia_profile_rescan(dialout_profile.name)
                    msg = _(u"Account added. FreeSWITCH notified.")
                except Exception, e:
                    msg = _(u"Account added, "
                             "failed to notify FreeSWITCH: %s.") % str(e)
                return http.HttpResponseRedirect(
                    reverse('wikipbxweb:account-list') + "?infomsg=%s" % msg)
        
            except Exception, e:
                logger.error("Error adding account: %s" % str(e))
                try:
                    transaction.rollback()
                    msg = _("Error adding account: %s.") % str(e)
                except Exception, e2:
                    transaction.leave_transaction_management()
                    logger.error(e2)
                    msg = _("Error adding account.")
                return http.HttpResponseRedirect(
                    reverse('wikipbxweb:dashboard') + "?urgentmsg=%s" % msg)
    else:
        if sip_profiles:
            form = forms.AccountAndAdminForm(sip_profiles)
        else:
            # First make sure we have at least one sip profile defined.
            msg = _(
                u"You must have at least one sip profile to add an account.")
            return http.HttpResponseRedirect(
                reverse('wikipbxweb:dashboard') + "?urgentmsg=%s" % msg)
        
    return render(request, 'object_form.html', 
        {'form':form, 'blurb':form.blurb})

@decorators.require_root_or_admin
def users(request, account_id):
    account = get_object_or_404(models.Account, pk=account_id)
    userprofs = models.UserProfile.objects.filter(account=account)
    return render(request, 'users.html', 
        {'userprofs':userprofs, 'account':account})

@decorators.require_root_or_admin
def add_user(request, account_id):
    account = get_object_or_404(models.Account, pk=account_id)

    # Preset user profile account.
    userprofile = models.UserProfile(account=account)
    
    if request.method == 'POST':
        form = forms.UserProfileForm(request.POST, instance=userprofile)
        if form.is_valid():
            userprofile = form.save()
            is_admin = form.cleaned_data['is_admin']
            if is_admin:
                account.admins.add(userprofile)

            msg = _("User %s added.") % userprofile
            return http.HttpResponseRedirect(
                reverse('wikipbxweb:user-account', args=[account.id]) +
                "?infomsg=%s" % msg)
    else:
        form = forms.UserProfileForm(instance=userprofile)

    return render(request, 'object_form.html', {'form': form})

@decorators.require_root_or_admin
def del_user(request, account_id, user_id):
    account = get_object_or_404(models.Account, pk=account_id)
    userprof = get_object_or_404(
        models.UserProfile, pk=user_id, account=account)
    userprof.delete()
    msg = _(u"User %s deleted.") % user_id
    return http.HttpResponseRedirect(
        reverse('wikipbxweb:user-account', args=[account.id]) +
        "?infomsg=%s" % msg)

@decorators.require_root_or_admin
def edit_user(request, account_id, user_id):
    account = get_object_or_404(models.Account, pk=account_id)
    userprofile = get_object_or_404(
        models.UserProfile, pk=user_id, account=account)
    if request.method == 'POST':
        form = forms.UserProfileEditForm(request.POST, instance=userprofile)
        if form.is_valid():
            userprofile = form.save()
            msg = _(u"User %s updated.") % userprofile
            return http.HttpResponseRedirect(
                reverse('wikipbxweb:user-account', args=[account.id]) +
                "?infomsg=%s" % msg)
    else:
        form = forms.UserProfileEditForm(instance=userprofile)

    return render(request, 'object_form.html', {'form': form})

@decorators.require_root
def sip_profiles(request):
    sip_profiles = models.SipProfile.objects.all()
    return render(request, 'sip_profiles.html', 
        {'sip_profiles': sip_profiles})

@decorators.require_root
def accounts(request):
    accounts = models.Account.objects.all()
    return render(request, 'accounts.html', 
        {'accounts':accounts})
    
@decorators.require_admin
def gateways(request):
    account = request.user.get_profile().account    
    gateways = models.SofiaGateway.objects.filter(account=account)
    return render(request, 'gateways.html', 
        {'gateways':gateways})    

@decorators.require_admin
def edit_gateway(request, gateway_id):
    account = request.user.get_profile().account
    gw = get_object_or_404(
        models.SofiaGateway, account=account, pk=gateway_id)

    if request.method == 'POST':
        form = forms.SofiaGatewayForm(
            models.SipProfile.objects.all(), False, request.POST)        
        if form.is_valid():
            old_profile_name = gw.sip_profile.name
            old_gw_name = gw.name

            sip_profile_id = form.cleaned_data['sip_profile']
            gw.sip_profile = models.SipProfile.objects.get(pk=sip_profile_id)
            
            ciif = form.cleaned_data['caller_id_in_from']
            gw.name = form.cleaned_data['name']
            gw.username = form.cleaned_data['username']
            gw.password = form.cleaned_data['password']
            gw.proxy = form.cleaned_data['proxy']
            gw.register = form.cleaned_data['register']
            gw.extension = form.cleaned_data['extension']
            gw.realm = form.cleaned_data['realm']
            gw.from_domain = form.cleaned_data['from_domain']
            gw.expire_seconds = form.cleaned_data['expire_seconds']
            gw.retry_seconds = form.cleaned_data['retry_seconds']
            val = form.cleaned_data['accessible_all_accts']
            gw.accessible_all_accts = val
            gw.caller_id_in_from = ciif
            gw.save()
            try:
                fsutil.sofia_profile_killgw(old_profile_name, old_gw_name)
                # Delay profile rescan to allow killgw to be executed
                time.sleep(5)
                fsutil.sofia_profile_rescan(old_profile_name)
                # If profile was changed rescan the new profile too
                if old_profile_name != gw.sip_profile.name:
                     fsutil.sofia_profile_rescan(gw.sip_profile.name)
                msg = _(u"Gateway updated. FreeSWITCH notified.")
            except Exception, e:
                msg = _(u"Gateway updated, "
                         "failed to notify FreeSWITCH: %s.") % str(e)
            return http.HttpResponseRedirect(
                reverse('wikipbxweb:gateway-list') + "?infomsg=%s" % msg)
    else:
        form = forms.SofiaGatewayForm(
            models.SipProfile.objects.all(), False, gw.form_dict())

    return render(request, 'object_form.html', 
        {'form':form, 'gateway':gw})

@decorators.require_admin
def del_gateway(request, gateway_id):
    account = request.user.get_profile().account
    gateway = get_object_or_404(
        models.SofiaGateway, account=account, pk=gateway_id)
    sip_profile_name = gateway.sip_profile.name
    gateway_name = gateway.name
    gateway.delete()
    try:
        fsutil.sofia_profile_killgw(sip_profile_name, gateway_name)
        msg = _(u"Gateway deleted. FreeSWITCH notified.")
    except Exception, e:
        msg = _(u"Gateway deleted, "
                 "failed to notify FreeSWITCH: %s.") % str(e)
    return http.HttpResponseRedirect(
        reverse('wikipbxweb:gateway-list') + "?infomsg=%s" % msg)

@decorators.require_admin
def add_gateway(request):
    account = request.user.get_profile().account
    if request.method == 'POST':
        form = forms.SofiaGatewayForm(
            models.SipProfile.objects.all(), False, request.POST)
        if form.is_valid():
            sip_profile_id = request.POST['sip_profile']                
            if sip_profile_id and sip_profile_id != "-1":
                sip_profile = models.SipProfile.objects.get(pk=sip_profile_id)
            else:
                raise Exception(
                    "Could not find Sip Profile: %s" % sip_profile_id)

            ciif = form.cleaned_data['caller_id_in_from']
            aac = form.cleaned_data['accessible_all_accts']
            gateway = models.SofiaGateway.objects.create(
                account=account, name=form.cleaned_data['name'],
                username=form.cleaned_data['username'],
                sip_profile=sip_profile,
                password=form.cleaned_data['password'],
                proxy=form.cleaned_data['proxy'],
                register=form.cleaned_data['register'],
                caller_id_in_from=ciif,
                extension=form.cleaned_data['extension'],
                realm=form.cleaned_data['realm'],
                from_domain=form.cleaned_data['from_domain'],
                expire_seconds=form.cleaned_data['expire_seconds'],
                retry_seconds=form.cleaned_data['retry_seconds'],
                accessible_all_accts=aac)
            try:
                fsutil.sofia_profile_rescan(sip_profile.name)
                msg = _(u"Gateway added. FreeSWITCH notified.")
            except Exception, e:
                msg = _(u"Gateway added, "
                         "failed to notify FreeSWITCH: %s.") % str(e)
            return http.HttpResponseRedirect(
                reverse('wikipbxweb:gateway-list') + "?infomsg=%s" % msg)
    else:
        form = forms.SofiaGatewayForm(models.SipProfile.objects.all(), False)

    return render(request, 'object_form.html',
        {'form': form,
         'blurb': _(u'SIP gateways are used for peering with another SIP '
                    'provider, such as a provider which provides outgoing '
                    'and/or origination access to the PSTN')})

@decorators.require_admin
def add_endpoint(request):
    account = request.user.get_profile().account
    endpoint = models.Endpoint(account=account)
    
    if request.method == 'POST':
        form = forms.EndpointCreateForm(request.POST, instance=endpoint)
        if form.is_valid():
            endpoint = form.save()
            msg = _(u"Endpoint %s saved.") % endpoint
            if form.cleaned_data['create_extension']:
                priority = extensionutil.new_ext_priority_position(
                    endpoint.account)
                userid = endpoint.userid
                endpoint_actions = (
                    '<action application="set" data="call_timeout=30"/>\n'
                    '<action application="set" data="continue_on_fail=true"/>\n'
                    '<action application="set" '
                    'data="hangup_after_bridge=true"/>\n'
                    '<action application="bridge" data="sofia/%s/%s%%%s"/>\n'
                    '<action application="voicemail" data="default '
                    '${domain_name} ${dialed_extension"/>') % (
                    account.dialout_profile.name, userid, account.domain)
                extension = models.Extension.objects.create(
                    account=endpoint.account, endpoint=endpoint,
                    desc=_(u"Extension for %s") % userid,
                    actions_xml= endpoint_actions, dest_num="^%s$" % userid,
                    priority_position=priority)
                msg += _(u"New extension %s created.") % extension.dest_num
            return http.HttpResponseRedirect(
                reverse('wikipbxweb:endpoint-list') + "?infomsg=%s" % msg)
    else:
        form = forms.EndpointCreateForm(
            initial={'password': utils.generate_passwd()},
            instance=endpoint)
    blurb = _(u"Define an endpoint to allow it to register on the PBX.")
    return render(request, 'object_form.html', 
        {'form':form, 'blurb': blurb})

@decorators.require_admin
def endpoints(request):
    account = request.user.get_profile().account    
    endpoints = models.Endpoint.objects.filter(account=account)

    # Which endpoints for this domain are reg'd?  Ask freeswitch.
    errorconnecting2fs = False
    for connection in fsutil.get_fs_connections():
        try:
            for endpoint in endpoints:
                # We have to check each profile, since in theory an endpoint
                # can be registered to any defined profile.
                regd_on_any_profile = False
                for sipprofile in models.SipProfile.objects.all():
                    cmd = (
                        "api sofia status profile %s user %s@%s" %
                        (sipprofile.name, endpoint.userid, account.domain)
                        ).encode('utf-8')
                    results = connection.sendRecv(cmd)
                    if not results:
                        raise Exception("Could not connect to FreeSWITCH")
                    data = results.getBody().splitlines()
                    for line in data:
                        if line.startswith("Contact:"):
                            # Found "Contact:", that means this endpoint is
                            # reg'd.
                            endpoint.is_registered = True
                            break

        except Exception, e:
            errorconnecting2fs = True
            logger.error("Failed to update endpoints' registration status")
            logger.error("Detailed error: %s" % str(e))

    extra_context = {'endpoints':endpoints}
    if errorconnecting2fs:
        extra_context['urgentmsg'] = _(
            u"Failed to get current registration status from FreeSWITCH.")
    return render(request, 'endpoints.html', extra_context)

@decorators.require_admin
def exts4endpoint(request, endpoint_id):
    account = request.user.get_profile().account
    endpoint = get_object_or_404(
        models.Endpoint, account=account, pk=endpoint_id)
    exts = endpoint.extension_set.all()
    return render(request, 'extensions.html', 
        {'exts': exts, 'endpoint':endpoint})

@decorators.require_admin
def edit_endpoint(request, endpoint_id):
    account = request.user.get_profile().account
    endpoint = get_object_or_404(
        models.Endpoint, account=account, pk=endpoint_id)

    if request.method == 'POST':
        form = forms.EndpointEditForm(request.POST, instance=endpoint)
        if form.is_valid():
            endpoint = form.save()
            msg = _("Endpoint %s saved.") % endpoint
            return http.HttpResponseRedirect(
                reverse('wikipbxweb:endpoint-list') + "?infomsg=%s" % msg)
    else:
        form = forms.EndpointEditForm(instance=endpoint)

    return render(request, 'object_form.html',
        {'form': form, 'endpoint': endpoint,
         'userprofs': models.UserProfile.objects.filter(account=account)})

@decorators.require_admin
def del_endpoint(request, endpoint_id):
    account = request.user.get_profile().account            
    endpoint = get_object_or_404(
        models.Endpoint, account=account, pk=endpoint_id)
    endpoint.delete()
    msg = _(u"Endpoint %s deleted.") % endpoint
    return http.HttpResponseRedirect(
        reverse('wikipbxweb:endpoint-list') + "?infomsg=%s" % msg)

@decorators.require_admin
def del_soundclip(request, soundclip_id):
    account = request.user.get_profile().account
    soundclip = get_object_or_404(
        models.Soundclip, account=account, pk=soundclip_id)
    soundclip.delete()
    msg = _(u"Soundclip %s deleted.") % soundclip
    return http.HttpResponseRedirect(
        reverse('wikipbxweb:soundclip-list') + "?infomsg=%s" % msg)

@decorators.require_login
def add_soundclip(request):
    if request.method == 'POST':
        # TODO: make a temporary extension with dest num: add_clip_8787
        # and store in the database
        name = request.POST['name']
        account = request.user.get_profile().account
        soundclip = models.Soundclip(account=account)
        form = forms.SoundclipForm(request.POST, instance=soundclip)
        tts_form = forms.SoundclipTTSForm(request.POST)
        if form.is_valid():
            upload_method = form.cleaned_data['upload_method']
            name = form.cleaned_data['name']
            desc = form.cleaned_data['desc']
            
            if upload_method == "dialout":
                vardict = {
                    'name': name, 'desc': desc, 'account_id': account.id}
                ivr_app = "wikipbx.ivr.soundclip_recorder" 
                action = '<action application="python" data="%s"/>' % ivr_app
                sound_clip_ext = extensionutil.get_temp_ext(
                    vardict=vardict, action=action, tempname="soundclip",
                    account=account)
                dest_ext_app = sound_clip_ext
            
                # Will go to dialout form where they can choose destination.
                return http.HttpResponseRedirect(
                    reverse('wikipbxweb:dialout', args=[dest_ext_app]))
        
            elif upload_method == "upload_wav":
                soundclip = form.save()
                soundclip_file = open(soundclip.get_path(), 'wb')
                for chunk in request.FILES['upload_wav'].chunks():
                    soundclip_file.write(chunk)
                soundclip_file.close()
                msg = _(u"Soundclip was uploaded.")
                return http.HttpResponseRedirect(
                    reverse('wikipbxweb:soundclip-list') + "?infomsg=%s" % msg)
            elif upload_method == "wav_url":
                soundclip = form.save()
                try:
                    utils.download_url(
                        request.POST['wav_url'], soundclip.get_path())
                except Exception, e:
                    msg = _("Soundclip could not be uploaded: %s.") % str(e)
                    soundclip.delete()
                    return http.HttpResponseRedirect(
                        reverse('wikipbxweb:soundclip-list') +
                        "?urgentmsg=%s" % msg)
                else:
                    msg = _(u"Soundclip was uploaded.")
                    return http.HttpResponseRedirect(
                        reverse('wikipbxweb:soundclip-list') +
                        "?infomsg=%s" % msg)
            elif upload_method == "tts":
                if tts_form.is_valid():
                    soundclip = form.save()
                    tts_file = ttsutil.make_tts_file(
                        tts_form.cleaned_data['tts_text'],
                        tts_voice=tts_form.cleaned_data['tts_voice'],
                        cache=False)
                    shutil.move(tts_file, soundclip.get_path())
                    msg = _(u"Soundclip was created.")
                    return http.HttpResponseRedirect(
                        reverse('wikipbxweb:soundclip-list') +
                        "?infomsg=%s" % msg)
    else:
        form = forms.SoundclipForm()
        tts_form = forms.SoundclipTTSForm()

    blurb = _(
        u"The system will call you and prompt you to record a soundclip, which"
        " will be stored in the library with the soundclip name that you assign"
        " to it.  This soundclip will then be available for IVR's and other"
        " PBX features.")
    return render(request, 'add_soundclip.html', 
        {'form': form, 'blurb': blurb, 'tts_form': tts_form})

@decorators.require_login
def soundclips(request):
    account = request.user.get_profile().account        
    soundclips = models.Soundclip.objects.filter(account=account)
    return render(request, 'soundclips.html',
        {'soundclips':soundclips, 'account':account})

@decorators.require_admin
def completedcalls(request):
    account = request.user.get_profile().account
    queryset = models.CompletedCall.objects.filter(
        account=account).order_by("-hangup_time")
    return list_detail.object_list(
        request, queryset, paginate_by=50, template_name="completedcalls.html",
        extra_context={'calltype': 'completed'})

#@decorators.require_root
#def unmatched_completedcalls(request, page=1):
#    queryset = models.CompletedCall.objects.filter(
#        account__isnull=True).order_by("-hangup_time")
#    return list_detail.object_list(
#        request, queryset, paginate_by=50, template_name='completedcalls.html',
#        extra_context={'calltype': 'unmatched'})

class UnmatchedCompletedCalls(ListView):
    extra_context = {'calltype': 'unmatched'}
    queryset = models.CompletedCall.objects.filter(
        account__isnull=True).order_by("-hangup_time")
    paginate_by=50
    template_name="completedcalls.html"

    def get_context_data(self, **kwargs):
        context = super(UnmatchedCompletedCalls, self).get_context_data(**kwargs)
        context.update(self.extra_context)
        return context

    @method_decorator(decorators.require_root)
    def dispatch(self, request, *args, **kwargs):
        return super(UnmatchedCompletedCalls, self).dispatch(request, *args, **kwargs)

@decorators.require_login
def outgoing2endpoint(request, endpoint_id):
    """
    Dialout to endpoint.
    """
    account = request.user.get_profile().account
    endpoint = get_object_or_404(
        models.Endpoint, account=account, pk=endpoint_id)
    
    connection = fsutil.get_fs_connection()
    try:
        # {ignore_early_media=true} is absolutely essential so that
        # ext2dialfrom does not consider the channel answered until the other
        # side picks up, and it ignores "pre-answers". This ensures playback
        # does not start until other side picks up.
        modifiers = {"ignore_early_media": "true"}
        
        # Generate the call url. This is a direct url to the locally registered
        # SIP endpoint. No extension mapping needed.
        party2dial = "%".join((endpoint.userid, endpoint.account.domain))
        sofia_url = sofiautil.sip_dialout_url(
            party2dial, endpoint.account, modifiers)

        file2play = os.path.join(
            settings.INSTALL_ROOT, "soundclips", "welcome_echo.wav")

        action = (
            '<action application="answer"/>'
            '<action application="playback" data="%s"/>'
            '<action application="echo" />'
            ) % file2play
        sound_clip_ext = extensionutil.get_temp_ext(
            vardict={}, action=action, tempname="outgoing2endpoint",
            account=endpoint.account)
        cmd = "bgapi originate %s %s XML %s" % (
            sofia_url, sound_clip_ext, endpoint.account.context)
        connection.sendRecv(cmd.encode('utf-8'))
    
    except Exception, e:
        msg = _(u"Dialout failed: %s.") % str(e)
        if settings.DEBUG:
            raise
    else:
        msg = _("Dialout succeeded.")
    return http.HttpResponseRedirect(
        reverse('wikipbxweb:endpoint-list') + "?infomsg=%s" % msg)

def add_root(request):
    if djmodels.User.objects.filter(is_superuser=True):
        msg = _(u"Already have root user.")
        return http.HttpResponseRedirect("/?urgentmsg=%s" % msg)        

    if request.method == 'POST':
        form = forms.RootUserForm(request.POST)        
        if form.is_valid():
            email = form.cleaned_data['email']
            user = djmodels.User(
                username=email, email=email,
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name'],
                is_active=True, is_staff=True, is_superuser=True)
            user.set_password(form.cleaned_data['password'])
            user.save()

            msg = _("Root %s added.") % user
            return http.HttpResponseRedirect(
                reverse('wikipbxweb:index') + "?infomsg=%s" % msg)
    else:
        form = forms.RootUserForm()

    return render(request, 'object_form.html', {'form':form})
    
@decorators.require_root_or_admin
def livecalls(request):
    account = request.user.get_profile().account
    channels = []
    # Comma as default delimiter doesn't work because of field containing
    # "XML,enum".
    delim = '|'
    for connection in fsutil.get_fs_connections():
        try:
            results = connection.sendRecv("api show channels as delim " + delim)
            if not results:
                raise Exception("Could not connect to FreeSWITCH")
            data = results.getBody().splitlines()

            if len(data) > 3:
                headers = data[0].split(delim)
                header_strings = (
                    'name', 'dest', 'cid_num', 'cid_name', 'created', 'uuid',
                    'context')
                indexes = map(headers.index, header_strings)
                assert all(x != -1 for x in indexes), \
                       "Unable to parse Freeswitch response"
                for i in range(1, len(data) - 2):
                    values = data[i].split(delim)
                    d = dict((header_strings[j], values[indexes[j]])
                        for j in range(len(header_strings)))
                    # List channels only from account context
                    if d['context'] == account.context:
                        channels.append(d)

        except Exception, e:
            msg = _(u"Could not get live calls: %s.") % str(e)
            return http.HttpResponseRedirect(
                reverse('wikipbxweb:dashboard') + "?urgentmsg=%s" % msg)

    return render(request, 'livecalls.html', 
        {'channels':channels})

@decorators.require_root_or_admin
def transfer(request, chan_uuid):
    """
    Transfer one or both legs of a call do a different extension.
    """
    account = request.user.get_profile().account    
    if request.method == 'POST':
        try:
            # Figure out where they want to transfer to.
            extension_id = request.POST.get('dialplan_extension')
            extension = get_object_or_404(
                models.Extension, account=account, pk=extension_id)
            connection = fsutil.get_fs_connection()
            connection.sendRecv(
                ("bgapi uuid_transfer %s %s" %
                (chan_uuid, extension.get_single_expansion())).encode('utf-8'))
            msg = _(u"Call transferred.")
            return http.HttpResponseRedirect(
                reverse('wikipbxweb:calls-live') + "?infomsg=%s" % msg)
        except Exception, e:
            msg = _(u"Transfer failed: %s.") % str(e)
            return http.HttpResponseRedirect(
                reverse('wikipbxweb:calls-live') + "?urgentmsg=%s" % msg)
    else:
        extensions = [
            x for x in list(models.Extension.objects.filter(
                account=account, is_temporary=False))
            if x.get_single_expansion()]
        return render(request, 'transfer.html',
            {'chan_uuid': chan_uuid, 'extensions': extensions})

@decorators.require_root_or_admin
def broadcast2channel(request, chan_uuid):
    """
    Broadcast a soundclip to both legs of channel.
    """
    account = request.user.get_profile().account

    if not request.REQUEST.has_key('action'):
        # show form that asks them to pick soundclip
        soundclips = models.Soundclip.objects.filter(account=account)
        return render(request, 'broadcast2channel.html',
            {'soundclips': soundclips, 'account': account,
             'chan_uuid': chan_uuid})
    else:
        try:
            # play the soundclip into the channel

            if request.REQUEST['action'] == "soundclip":
                soundclip_id = request.REQUEST['soundclip_id']
                soundclip = models.Soundclip.objects.get(pk=soundclip_id)
                file2play = soundclip.get_path()
            elif request.REQUEST['action'] == "tts":
                file2play = ttsutil.make_tts_file(
                    request.REQUEST['text2speak'], tts_voice=None, cache=False)
            else:
                raise Exception(
                    "Unknown action: %s" % request.REQUEST['action'])

            connection = fsutil.get_fs_connection()
            connection.sendRecv(
                (u"bgapi uuid_broadcast %s '%s'" % (chan_uuid, file2play)
                 ).encode('utf-8'))
        except Exception, e:
            msg = _(u"Broadcast failed: %s") % str(e)
            return http.HttpResponseRedirect(
                reverse('wikipbxweb:channel-broadcast', args=[chan_uuid]) +
                "?urgentmsg=%s" % msg)
        else:
            msg = _(u"Broadcast succeeded")
            return http.HttpResponseRedirect(
                reverse(
                    'wikipbxweb:channel-broadcast',
                    args=[chan_uuid]) + "?infomsg=%s" % msg)

@decorators.require_root_or_admin
def hangup_channels(request, chan_uuid=None):
    """
    If chan_iuud is not given, hangup all.
    """
    account = request.user.get_profile().account
    
    try:
        connection = fsutil.get_fs_connection()
        connection.sendRecv(
            (u"bgapi uuid_kill %s" % chan_uuid).encode('utf-8')
            if chan_uuid else (u"bgapi hupall normal_clearing context %s" % 
                               account.context).encode('utf-8'))
    except Exception, e:
        msg = (
            _("Could not hangup call %(channel)s: %(error)s") % {
                'channel': chan_uuid, 'error': str(e)}
            ) if chan_uuid else (_("Could not hangup calls: %s") % str(e))
        url = reverse('wikipbxweb:calls-live') + "?urgentmsg=%s" % msg
    else:
        msg = (
            (_(u"Call %s hangup succeeded.") % chan_uuid) if chan_uuid else
            _(u"Calls hangup succeeded."))
        logger.error(msg)
        url = reverse('wikipbxweb:calls-live') + "?infomsg=%s" % msg
    return http.HttpResponseRedirect(url)

#@decorators.require_root
#def server_logs(request):
#    queryset = models.ServerLog.objects.all().order_by("-logtime")
#    return list_detail.object_list(
#        request, queryset, paginate_by=15, template_name="server_logs.html")

class ServerLogsView(ListView):
    queryset = models.ServerLog.objects.all().order_by("-logtime")
    paginate_by=15
    template_name="server_logs.html"

    @method_decorator(decorators.require_root)
    def dispatch(self, request, *args, **kwargs):
        return super(ServerLogsView, self).dispatch(request, *args, **kwargs)

@decorators.require_root_or_admin
def config_mailserver(request):
    account = request.user.get_profile().account
    emailconfig, _created = models.EmailConfig.objects.get_or_create(
        account=account)
    
    if request.method == 'POST':
        # Collect form data and show form.
        form = forms.EmailConfigForm(request.POST, instance=emailconfig)
        if form.is_valid():
            form.save()
            msg = _("Email server configuration successful.")
            return http.HttpResponseRedirect(
                reverse('wikipbxweb:dashboard') + "?infomsg=%s" % msg)
    else:
        form = forms.EmailConfigForm(instance=emailconfig)

    return render(request, 'object_form.html',
        {'form': form,
         'blurb': _(u'Configure Email server for this account.  At the time of'
                    ' this writing, only tested with GMail accounts with'
                    ' use_tls set to True')})

@decorators.require_root_or_admin
def test_mailserver(request):
    """
    Allow user to show test email from a web page to see if mailserver
    is correctly configured.
    """
    account = request.user.get_profile().account
    emailconfigs = models.EmailConfig.objects.filter(account=account)[:1]
    if not emailconfigs:
        msg = _(u"Sorry, no email servers configured for this account.")
        return http.HttpResponseRedirect(
            reverse('wikipbxweb:dashboard') + "?urgentmsg=%s" % msg)

    if request.method == 'POST':
        # Collect form data and show form
        form = forms.TestMailserverForm(request.POST)
        emailconfig = emailconfigs[0]
        if form.is_valid():
            mailutil.acct_send(
                recipients=[form.cleaned_data["recipient"]],
                subject=form.cleaned_data["subject"],
                msg_body=form.cleaned_data["msg_body"], account=account,
                emailconfig=emailconfig)

            msg = _(u"Test email was sent")
            return http.HttpResponseRedirect(
                reverse('wikipbxweb:dashboard') + "?infomsg=%s" % msg)
    else:
        form = forms.TestMailserverForm()

    return render(request, 'test_mailserver.html', {'form': form})

@decorators.require_root_or_admin
def dialout(request, dest_ext_app):
    account = request.user.get_profile().account
    
    if request.method == 'POST':
        # Did user specify anything?
        something2dial = False        
        checked_dp_exts = request.POST.getlist('checked_dialplan_extensions') 
        logger.debug("Checked_dialplan_extensions: %s." % checked_dp_exts)
        if checked_dp_exts:
            something2dial = True
        
        dlist = []
        # Dialout calls don't require dialplan authorization
        modifiers = {"web_dialout": "true"}
        
        # Dial the extensions that were checked (checkboxes).
        for checked_dp_ext in checked_dp_exts:
            # Get the dialable url for this extension, eg,
            # sofia/mydomain.com/600@ip:port.
            extension = models.Extension.objects.get(
                account=account, pk=checked_dp_ext)
            party2dial = extension.get_sofia_url(modifiers)

            concurrent_fname = "concurrent_dpext_%s" % extension.id
            concurrent = int(request.POST[concurrent_fname])
            for i in xrange(0, concurrent):
                dlist.append((party2dial, dest_ext_app))

        # Dial the additional extensions and SIP urls. These are the ones in
        # the free textfield(s).
        for i in xrange(1, 1000):
            num2check = "number_%s" % i
            if request.POST.has_key(num2check):
                something2dial = True
                number2dial = request.POST[num2check]
                if not number2dial:
                    continue
                # Is it a sip url or an extension?
                if number2dial.find("@") != -1:
                    # SIP URL.
                    party2dial = sofiautil.sip_dialout_url(
                        number2dial, account, modifiers)
                else:
                    # Extension.
                    party2dial = sofiautil.extension_url(
                        number2dial, account, modifiers)
                    
                # Dial concurrent?
                concurrent_fname = "concurrent_number_%s" % i
                concurrent = int(request.POST[concurrent_fname])
                for i in xrange(0, concurrent):
                    dlist.append((party2dial, dest_ext_app))
            else:
                break

        if not something2dial:
            msg = _(u"Nothing to dial. Ignored request.")
            url = reverse('wikipbxweb:dashboard') + "?urgentmsg=%s" % msg
        else:
            try:
                connections = itertools.cycle(fsutil.get_fs_connections())
                for connection, params in itertools.izip(connections, dlist):
                    cmd = "bgapi originate %s %s XML %s" % (
                        params + (account.context,))
                    connection.sendRecv(cmd.encode('utf-8'))
            except Exception, e:
                msg = _(u"Dialout failed: %s.") % str(e)
                url = reverse('wikipbxweb:dashboard') + "?urgentmsg=%s" % msg
            else:
                msg = _(u"Dialout succeeded.")
                url = reverse(
                    'wikipbxweb:dialout', args=[dest_ext_app]
                    ) + "?infomsg=%s" % msg
        return http.HttpResponseRedirect(url)

    # Find all endpoints for this account.
    endpoints = models.Endpoint.objects.filter(account=account)
    
    # Find all single-expansion extensions for this account.
    extensions = [
        x for x in models.Extension.objects.filter(
            account=account, is_temporary=False)
        if x.get_single_expansion()]

    return render(request, 'dialout.html',
        {'endpoints': endpoints, 'extensions': extensions,
         'dest_ext_app': dest_ext_app})

@decorators.require_root_or_admin
def click2call(request):
    account = request.user.get_profile().account
    userprof = request.user.get_profile()
    
    if request.method == 'POST':
        form = forms.Click2CallForm(request.POST)
        form.fields['gateway'].choices = account.get_gateway_choices()
            
        if form.is_valid():
            gateway_id = form.cleaned_data['gateway']
            # Allow only gateways which belongs to account
            try:
                gwname = models.SofiaGateway.objects.get(
                    account=account, pk=gateway_id).name
            except:
                msg = _(u"Gateway not found.")
                return http.HttpResponseRedirect(
                    reverse('wikipbxweb:click-to-call') +
                    "?urgentmsg=%s" % msg)
            caller = form.cleaned_data['caller']
            called_party = form.cleaned_data['called_party']
            dialout_params = "{ignore_early_media=true}"
            arg1 = "%ssofia/gateway/%s/%s" % (dialout_params, gwname, caller)
            arg2 = "&bridge(sofia/gateway/%s/%s)" % (gwname, called_party)
            try:
                for connection in fsutil.get_fs_connections():
                    cmd = "bgapi originate %s %s" % (arg1, arg2)
                    connection.sendRecv(cmd.encode('utf-8'))
            except Exception, e:
                msg = _(u"Dialout failed: %s.") % str(e)
                url = reverse('wikipbxweb:dashboard') + "?urgentmsg=%s" % msg
            else:
                msg = _(u"Dialout succeeded.")
                url = reverse('wikipbxweb:dashboard') + "?infomsg=%s" % msg
            return http.HttpResponseRedirect(url)
    else:
        form = forms.Click2CallForm()
        form.fields['gateway'].choices = account.get_gateway_choices()

    return render(request, 'object_form.html', {'form':form})

def add_cdr(request):
    """
    This is called by the freeswitch xml_cdr_curl module
    for an example xml file, see
    http://wiki.freeswitch.org/wiki/Mod_xml_cdr
    """
    try:
        if not request.POST:
            raise Exception("Not a POST request")
        if not request.POST.has_key('cdr'):
            raise Exception("Parameter 'cdr' not found")
        cdr = request.POST['cdr']
        cp = cdrutil.process(cdr)
        if cp:
            logger.debug("CDR Added. Account: %s." % cp.account)
        else:
            logger.debug("Ingoring CDR.")
    except Exception, e:
        msg = _("Fatal error adding cdr xml: %s") % e
        logger.error(str(e))
        try:
            now = datetime.datetime.now()
            models.ServerLog.objects.create(logtime=now, message=msg)
        except Exception, e:
            logger.error("Error adding server log entry: %s" % str(e))
        raise e
    return http.HttpResponse("OK")

@csrf_exempt    
def xml_dialplan(request):
    """
    This is called by freeswitch to get either configuration,
    dialplan, or directory settings.
    See
    http://wiki.freeswitch.org/wiki/Mod_xml_curl
    
    configuration example
    =====================

    {'key_value': ['conference.conf'], 'key_name': ['name'],
    'section': ['configuration'], 'tag_name': ['configuration'],
    'profile_name': ['default'], 'conf_name': ['250']}>

    """
    retval_template = (
        '<?xml version="1.0"?>\n<document type="freeswitch/xml">\n'
        '<section name="configuration" description'
        '="Various Configuration">\n%s\n</section>\n</document>')
    try:
        # Security: only serve config to localhost for now and try to add
        # suppport for user/password authentication that freeswitch already
        # supports. This should be stored in the settings.py config, along
        # with some other config that is currently stored in the database..
        # like the listening port, but which makes more sense to store in a
        # file.
        if not request.POST:
            # FS should always send a POST, so its probably a browser.
            if not authutil.is_root(request):
                msg = "You must be logged in as superuser"
                return http.HttpResponseRedirect("/?urgentmsg=%s" % msg)
            return render(
                request, 'xml_dialplan.html',
                dictionary={'blurb': _('Use this form to view the raw XML '
                                         'returned to FreeSWITCH when '
                                         'requested')})

        if request.POST['section'] == "configuration":
            # when freeswitch contacts wikipbx to pull its
            # configuration, it should pass its event socket
            # port so wikipbx knows how to "call it back".
            # maybe it already does!  but for now, let the
            # user define freeswitch instances in the gui.
            # in any operation that involves connecting to
            # freeswitch, a freeswitch instances will need
            # to be explicitly chosen.   or better yet, a global
            # binding that can be easily changed from web gui.  
            logger.debug("got post: %s" % pformat(dict(request.POST)))

            # does it need to be wrapped in the retval_template?
            needsRetValTemplate = True

            # does it need <?xml version="1.0"?> header stripped off?
            needsXmlHeaderStripped = True

            if request.POST['key_value'] == "event_socket.conf":
                needsRetValTemplate = False
                needsXmlHeaderStripped = False
                raw_xml = xmlconfig.event_socket_config()
                logger.info("raw_xml: %s" % raw_xml)
            elif request.POST['key_value'] == "sofia.conf":
                needsRetValTemplate = False
                needsXmlHeaderStripped = False
                raw_xml = xmlconfig.sofia_config(request)
                logger.info("raw_xml: %s" % raw_xml)
            elif request.POST['key_value'] == "xml_cdr.conf":
                needsRetValTemplate = False
                needsXmlHeaderStripped = False
                raw_xml = xmlconfig.xml_cdr_config()
                logger.info("raw_xml: %s" % raw_xml)
            elif request.POST['key_value'] == "ivr.conf":
                needsRetValTemplate = False
                needsXmlHeaderStripped = False
                raw_xml = xmlconfig.ivr_config(request)
                logger.info("raw_xml: %s" % raw_xml)
            else:
                return http.HttpResponse(statics.not_found)                

            # strip xml header if needed
            xml_snippet = str(
                utils.xml_snippet_no_header(raw_xml) if needsXmlHeaderStripped
                else raw_xml)

            # wrap in retval_template if needed
            retval = (
                (retval_template % xml_snippet) if needsRetValTemplate
                else xml_snippet)
            
            return http.HttpResponse(retval, mimetype="text/plain")
        elif request.POST['section'] == "dialplan":
            logger.debug("Dialplan request: %s" % pformat(dict(request.POST)))
            try:
                raw_xml = xmlconfig.dialplan_entry(request)
                logger.info("raw_xml: %s" % raw_xml)
                return http.HttpResponse(raw_xml, mimetype="text/plain")
                
            except Exception, e:
                logger.error("Error generating dialplan: %s" % e)
                return http.HttpResponse(statics.not_found)
        elif request.POST['section'] == "directory":
            logger.debug("Directory request: %s" % pformat(dict(request.POST)))
            try:
                raw_xml = xmlconfig.directory(request)
                if raw_xml:
                    logger.info("raw_xml: %s" % raw_xml)
                    return http.HttpResponse(raw_xml, mimetype="text/plain")
                else:
                    logger.error("Returing not found response")
                    return http.HttpResponse(statics.not_found)
            except Exception, e:
                logger.error("Error generating directory: %s" % e)
                return http.HttpResponse(statics.not_found)
    except Exception, e:
        logger.error("Error generating config: %s" % e)
        return http.HttpResponse(statics.not_found)

