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

from django.conf import settings
from django.core.urlresolvers import reverse
from django.template import Context, loader
from wikipbx import dialplanbuilder, logger
from wikipbx.wikipbxweb import models


class AccountDomainError(Exception):
    "Multiple accounts for domain name"
    

def xml_cdr_config():
    """
    Generate xml_cdr config xml by rendering template
    (freeswitchxml/xml_cdr.conf.xml) with data in database.
    """
    t = loader.get_template('xml_cdr.conf.xml')

    url = ''.join((settings.FREESWITCH_URL_PORT, reverse('wikipbxweb:cdr-add')))
    
    c = Context(
        {"url": url, "log_dir": settings.CDR_LOG_DIR,
         "err_log_dir": settings.CDR_ERR_LOG_DIR})
    return t.render(c)

def event_socket_config():
    """
    Generate event socket config. Freeswitch uses this config to determine
    which ip/port to listen on for incoming event socket connections. Also
    determines username/password it will accept for authenticating users that
    try to connect.
    """
    t = loader.get_template('event_socket.conf.xml')

    esconfig = models.EventSocketConfig.objects.all()[0]

    c = Context(
        {"listen_ip": esconfig.listen_ip, "listen_port": esconfig.listen_port,
         "password": esconfig.password})
    return t.render(c)

def sofia_config(request):
    """
    Generate xml config for sofia (sip stack) configuration.
    """
    t = loader.get_template('sofia.conf.xml')
    # Load requested profile only
    if request.POST.has_key('profile'):
        sipprofiles = models.SipProfile.objects.filter(
            name=request.POST['profile'])
    else:
        sipprofiles = models.SipProfile.objects.all()
    accounts = models.Account.objects.filter(enabled=True)
    c = Context({"sipprofiles": sipprofiles, "accounts":accounts})
    return t.render(c)

def ivr_config(request):
    """
    Generate xml config for IVR configuration.
    """
    t = loader.get_template('ivr.conf.xml')
    ivr_menu_xml = ''

    # Find account
    account = find_account_dialplan_request(request)
#    if request.POST.has_key('Caller-Context'):
#        account_id = models.Account.context_account(
#            request.POST['Caller-Context'])
#    else:
#        account_id = None

    # Load XML IVR scripts for found account
    ivrs = models.Ivr.objects.filter(
        account=account, language_ext='xml')
    for ivr in ivrs:
        script_path = ivr.get_script_path()
        ivr_code = open(script_path, 'r').read()
        ivr_menu_xml += ivr_code

    # Load IRV menus
    ivr_menus = []
    ivrs = models.Ivr.objects.filter(
        account=account, language_ext='ivr_form')
    for ivr in ivrs:
        ivr_menu = models.IvrMenu.objects.get(ivr=ivr)
        # Load IvrMenu actions
        actions = models.Action.objects.filter(
            ivrmenudestination__ivr_menu=ivr_menu
            ).order_by("ivrmenudestination__order")
        if actions:
            ivr_menu.dest = dialplanbuilder.build_action_xml(actions, account)
        ivr_menus.append(ivr_menu)

    c = Context(
        {"ivr_menu_xml": ivr_menu_xml, "ivr_menus": ivr_menus}, 
        autoescape=False)
    return t.render(c)

def dialplan_entry(request):
    """
    Generate dialplan entry.

    Find all extensions that have a matching destination number.
    """
    if request.POST.has_key('Caller-Destination-Number'):
        # works in fs rev 7511
        dest_num = request.POST['Caller-Destination-Number'] 
    else:
        raise Exception("No destination_number given")

    # Get SIP profile
    sip_profile = find_spiprofile_dialplan_request(request)

    # Find account
    account = find_account_dialplan_request(request)

    # Get caller ID
    caller_id = request.POST.get('Caller-Caller-ID-Number', None)

    # Get extension
    extension, groups = dialplanbuilder.find_extension(
        account, dest_num, caller_id)
    if not extension:
        raise Exception('Extension %s not found' % dest_num)

    # Do we need to authorize this call?
    # 1. Call may come in a context of an Account or in a context of a SIP 
    # Profile. If it's in the context of the Account it means it was 
    # previously authenticated or it's some transfer to the Account context.
    # 2. Non authenticated calls will be in the context of the SIP Profile. 
    # In this case, depending from the Extension settings, 
    # we issue a challenge or transfer a call to the Extension context 
    # (in case of the public Extension).
    if request.POST['Caller-Context'] == account.context:
        call_context = extension.account.context
        template_name = 'dialplan.xml'
    else:
        call_context = sip_profile.context
        if check_call_needs_auth(extension, request):
            template_name = 'dialplan_auth_challenge.xml'
        else:
            template_name = 'dialplan_public_extension.xml'

    t = loader.get_template(template_name)

    logger.info("SIP Profile: %s, Account: %s, Extension: %s, "
        "Caller-Context: %s, Extension.auth_call: %s, Template: %s" % 
        (sip_profile, account, extension,
        request.POST['Caller-Context'], extension.auth_call, template_name))
    
    # Get the actions xml snippet input by the user in the gui.
    actions_xml = extension.actions_xml

    # substitute placeholders, eg, $1 -> 18005551212
    # TODO: only do substitution within each "data" attribute, not over
    #       entire xml snippet
    actions_xml = dialplanbuilder.group_substitutions(actions_xml, groups)

    # render template
    c = Context({
        "extension": extension, 
        "processed_actions_xml": actions_xml,
        "dialed_extension": dest_num,
        "call_context": call_context,
        },)
    return t.render(c)

def find_spiprofile_dialplan_request(request):
    """
    Find out what SIP profile is used for this call
    """
    if not request.POST.has_key('variable_sofia_profile_name'):
        raise Exception("POST request did not contain header: variable_sofia_profile_name")
        
    profile_name = request.POST['variable_sofia_profile_name']

    sip_profiles = models.SipProfile.objects.filter(name=profile_name)
    if not sip_profiles:
        raise Exception("No SipProfile found with name: %s" % profile_name)

    return sip_profiles[0]

def find_account_dialplan_request(request):
    """
    Given a freeswitch request for a dialplan, find out which account should
    be used.

    The examined variables are (in order of checks):
    * variable_sip_req_params
    * variable_domain_name
    * variable_sip_req_host
    """
    domain_names = []
    
    params = request.POST.get('variable_sip_req_params', None)
    if params:
        params = dict(pair.split('=', 1) for pair in params.split(';'))
        domain_names.append(params.get('domain', None))

    for variable in ('variable_domain_name', 'variable_sip_req_host'):
        domain_names.append(request.POST.get(variable, None))

    for domain in domain_names:
        if domain:
            accounts = models.Account.objects.filter(
                domain=domain, enabled=True)
            num_accounts = len(accounts)
            if num_accounts == 1:
                return accounts[0]
            elif num_accounts > 1:
                msg = (
                    "Multiple accounts found with domains: %s." %
                    str(domain_names))
                raise AccountDomainError(msg)
    else:
        raise AccountDomainError(
            "No accounts found for domains: %s." % domain_names)

def check_call_needs_auth(extension, request):
    """
    in the context of generating dialplan xml for freeswitch,
    decide if we need to first authorize the caller before
    generating the actual extension.  if the extension in
    the db has the auth_call flag set, then we check the
    request to see if it is already authd.  If not, we return
    special dialplan xml that first challenges and then
    redirects back into the dialplan back to the extension.
    """
    call_needs_auth = True

    # don't require auth for temporary extensions.  without this
    # the Test button on the endpoints page is broken
    if extension.is_temporary:
        return False
    
    # don't authorize calls initiated via 'dialout' function from 
    # web admin center        
    if request.POST.has_key('variable_web_dialout'):
        val = request.POST['variable_web_dialout']
        if val and val.lower() == "true":
            return False
    
    if extension.auth_call:
        # extension has auth_call flag, unless already authd need 2 challenge
        # 'variable_sip_authorized': ['true']
        if request.POST.has_key('variable_sip_authorized'):
            val = request.POST['variable_sip_authorized']
            if val and val.lower() == "true":
                call_needs_auth = False
        else:
            # call not auth'd already, need to challenge
            call_needs_auth = True            
    else:
        # the extension doesn't have the auth_call flag, no need to challenge
        call_needs_auth = False
    return call_needs_auth

def directory(request):
    """
    Handle all directory requests
    """
    if request.POST.has_key('domain'):
        # When freeswitch is trying to authenticate an endpoint, it passes the
        # domain parameter. So when we see that we assume that it wants a
        # particular user's information such as its password. 
        logger.info("directory_user")
        return directory_user(request)
    else:
        # When freeswitch sees a <domains> tag in a profile definition (as used
        # for aliasing a domain to a sip profile and telling freeswitch to load
        # all gateways contained in a directory), then it will call wikipbx
        # with a request that does NOT have the domain parameter. 
        logger.info("directory_profile_parse")
        return directory_profile_parse(request)
    
def directory_profile_parse(request):
    """
    freeswitch is parsing a sip profile and saw a <domains><domain> tag and
    wants information on a particular domain.  Params will look like:

    key_name: ['name']
    key_value: ['yourcompany.com']
    """
    
    t = loader.get_template('directory_user.conf.xml')

    key_name = request.POST["key_name"]
    if key_name != "name":
        raise Exception("key_name != name")

    domain = request.POST["key_value"]
    accounts = models.Account.objects.filter(domain=domain, enabled=True)
    if not accounts:
        raise Exception("No account found with domain name: %s" % domain)
    account = accounts[0]
    
    c = Context({"account": account})

    return t.render(c)

def directory_user(request):
    """
    Generate XML config for a "directory user". When a sip endpoint tries to
    register, freeswitch will make an http request with some metadata about the
    user trying to register. Then we lookup in our user database and try to
    find that user, and return xml.

    Example request fs rev 7511:

    'ip': ['192.168.1.70']
    'key_value': ['192.168.1.101']
    'sip_auth_realm': ['192.168.1.101']
    'key_name': ['name']
    'section': ['directory']
    'hostname': ['spider']
    'sip_auth_method': ['REGISTER']
    'sip_user_agent': ['Linksys/SPA2002-3.1.9(d)']
    'sip_auth_qop': ['auth']
    'sip_auth_username': ['100']
    'tag_name': ['domain']
    'sip_auth_nonce': ['237c9962-3ad8-4e79-807e-f63a4396a999']
    'user': ['100']
    'key': ['id']
    'sip_profile': ['192.168.1.101']
    'action': ['sip_auth']
    'domain': ['192.168.1.101']
    'sip_auth_nc': ['00000002']
    'sip_auth_cnonce': ['8a511ce']
    'sip_auth_response': ['978dc8d62712762f50357f5c61b04113']
    'sip_auth_uri': ['sip:192.168.1.101:5072']
    
    WikiPBX returns:

    <domain name="192.168.0.58">
        <user id="2760">
            <params>
                <param name="password" value="foo" />
            </params>
        </user>
    </domain>
    
    """
    t = loader.get_template('directory_user.conf.xml')
    domain = request.POST['domain']

    if not request.POST.has_key('user'):
        logger.info(
            "FreeSWITCH is requesting entire directory for domain: %s but this "
            "request is being ignored as this type of directory request is not "
            "yet supported by WikiPBX. Not known to cause bugs." % domain)
        return None
                    
    user = request.POST['user']

    if domain:
        accounts = models.Account.objects.filter(domain=domain, enabled=True)
    else:
        raise Exception("No domain, cannot lookup account")
        
    if not accounts:
        # TODO: make this error msg available in front-end gui
        raise Exception("No account found for domain: %s" % domain)
    else:
        account = accounts[0]

    endpoints = models.Endpoint.objects.filter(account=account, userid=user)
    if not endpoints:
        # TODO: make this error msg available in front-end gui
        raise Exception(
            "No endpoint found with userid: %s in account: %s" %
            (user, account))
    else:
        endpoint = endpoints[0]

    # make sure domain that the endpoint 'came in on' matches what
    # we have in the database (or the sip_ext_ip) if no domain is set
    if domain != endpoint.account.domain:
        # TODO: make this error msg available in front-end gui
        raise Exception(
            "SIP endpoint trying to register with: %s, but that does not match "
            "the domain in the db: %s " % (domain, endpoint.account.domain))

    logger.info("endpoint: %s" % endpoint)
    c = Context({"account": account, "endpoint": endpoint})
    return t.render(c)
    
