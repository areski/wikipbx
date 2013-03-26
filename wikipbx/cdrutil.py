#!/usr/bin/env python

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

"""
Extract information from an XML CDR record the mod_xml_cdr passes to wikipbx after a call finishes.
"""

import os
os.environ['DJANGO_SETTINGS_MODULE']='wikipbx.settings'

from wikipbx.wikipbxweb.models import *
from wikipbx import logger
from wikipbx.xmlutil import getText, firstElementTextByTagName
from django.conf import settings

from xml.dom import minidom
import datetime

def process(cdr_xml_str):
    """
    take an xml string, parse it, and use the information
    to create a Cdr object and return it

    <cdr>
      <variables>
        <local_media_ip>192.168.1.201</local_media_ip>
        <sip_call_id>c477994b-9f62-122a-43a0-000f1fc8e441</sip_call_id>
        <remote_media_ip>67.65.105.29</remote_media_ip>
        <hangup_cause>NORMAL_CLEARING</hangup_cause>
        <endpoint_disposition>ANSWER</endpoint_disposition>
        <switch_r_sdp>v%3D0%20%..........etc</switch_r_sdp>
        <local_media_port>13780</local_media_port>
        <remote_media_port>13780</remote_media_port>
        <ignore_early_media>true</ignore_early_media>
      </variables>
      <app_log>
        <application app_name="conference" app_data="221"></application>
      </app_log>
      <callflow dialplan="">
        <extension name="221" number="221">
          <application app_name="conference" app_data="221"></application>
        </extension>
        <caller_profile>
          <username></username>
          <dialplan></dialplan>
          <caller_id_name>FreeSWITCH</caller_id_name>
          <ani></ani>
          <aniii></aniii>
          <caller_id_number>0000000000</caller_id_number>
          <network_addr></network_addr>
          <rdnis></rdnis>
          <destination_number>mydomain.com/foo@bar.com</destination_number>
          <uuid>ed18eda4-24bf-11dc-913a-37ac3cdbbaa7</uuid>
          <source>src/switch_ivr_originate.c</source>
          <context>default</context>
          <chan_name>sofia/mydomain.com/foo@bar.com</chan_name>
        </caller_profile>
        <times>
          <created_time>1182956764946190</created_time>
          <answered_time>1182956765107959</answered_time>
          <hangup_time>1182956785394251</hangup_time>
          <transfer_time>0</transfer_time>
        </times>
      </callflow>
    </cdr>
    
    """

    cleaned = cdr_xml_str.encode('ascii', 'replace')
    logger.debug(cleaned)
    
    dom = minidom.parseString(cleaned)

    # first try to use the account_id (which is set in the dialplan.xml
    # template).  if that fails, fallback to "domain_name", which
    # is set in the "web dialout string" and possibly by freeswitch
    # in some cases.
    # After that look for dialplan context
    account_id = get_account_id(dom)
    domain_name = get_domain_name(dom)
    context = get_context(dom)
    
    # Get Account Id from the context string
    context_account_id = Account.context_account(context)
    
    sq = {}
    account=None

    if account_id:
        sq = dict(pk=account_id)
    elif domain_name:
        sq = dict(domain=domain_name)
    elif context_account_id:
        sq = dict(pk=context_account_id)
    else:
        msg = ("WARN: Cannot associate this CDR with an account.  "
               "Did not find either a valid account_id, "
               "domain_name or context channel variable")
        logger.warn(msg)
        now = datetime.datetime.now()
        ServerLog.objects.create(logtime=now, message=msg)
    if sq:
        try:
            account = Account.objects.get(**sq)        
        except Account.DoesNotExist:    
            msg = ("WARN: No account found. account_id=%s, "
                "domain_name=%s, context=%s" % 
                (account_id, domain_name, context))
            logger.warn(msg)
            now = datetime.datetime.now()
            ServerLog.objects.create(logtime=now, message=msg)

    dest_num = get_destination_number_field(dom)
    caller_id_number = get_callerid_number_field(dom)

    answered_time = get_answered_time(dom)
    hangup_time = get_hangup_time(dom)    
    uuid = get_uuid(dom)

    if not settings.CDR_SAVE_XML:
        cdr_xml_str = "Saving raw CDR XML disabled in settings.py"
    
    completed_call = CompletedCall(account=account,
                                   uuid=uuid,
                                   destination_number=dest_num,
                                   caller_id_number=caller_id_number,
                                   chan_name=get_chan_name(dom),
                                   cdr_xml=cdr_xml_str,
                                   answered_time=answered_time,
                                   hangup_time=hangup_time)
    completed_call.save()
    return completed_call


def get_destination_number_field(dom):
    """
    <destination_number>mydomain.com/foo@bar.com</destination_number>    
    """
    element_text = firstElementTextByTagName(dom, "destination_number")
    return element_text


def get_callerid_number_field(dom):
    """
    <caller_id_number>0000000000</caller_id_number>
    """
    element_text = firstElementTextByTagName(dom, "caller_id_number")    
    return element_text


def get_time_field(dom, field_name):
    """
    <answered_time>1182956765107959</answered_time>
    """
    element_text = firstElementTextByTagName(dom, field_name)
    return msepoch2datetime(int(element_text))


def get_uuid(dom):
    """
    <uuid>ed18eda4-24bf-11dc-913a-37ac3cdbbaa7</uuid>
    """
    return firstElementTextByTagName(dom, "uuid")

    
def get_chan_name(dom):
    """
    <chan_name>sofia/mydomain.com/foo@bar.com</chan_name>
    """
    return firstElementTextByTagName(dom, "chan_name")    

    
def get_domain_name(dom):
    """
    <domain_name>pbx.foo.com</domain_name>
    """
    return firstElementTextByTagName(dom, "domain_name")    

    
def get_account_id(dom):
    """
    <account_id>1</account_id>
    """
    return firstElementTextByTagName(dom, "account_id")    


def get_answered_time(dom):
    """
    <answered_time>1182956765107959</answered_time>
    """
    return get_time_field(dom, "answered_time")

def get_hangup_time(dom):
    """
    <hangup_time>1182956785394251</hangup_time>
    """
    return get_time_field(dom, "hangup_time")

def get_context(dom):
    """
    <context>pbxfoo</context>
    """
    return firstElementTextByTagName(dom, "context")    

def msepoch2datetime(microseconds_since_epoch):
    
    # now convert it into a datetime object from its current
    # form, which I have determined is the number of microseconds
    # from the epoch.
    ms_epoch = microseconds_since_epoch
    seconds_since_epoch = microseconds_since_epoch / (1000 * 1000)

    # using UTC (aka GMT) .. though no idea what timezone fs is using 
    result = datetime.datetime.utcfromtimestamp(seconds_since_epoch)

    return result





if __name__=="__main__":

    cdr_xml_str = """
    <cdr>
      <variables>
        <local_media_ip>192.168.1.201</local_media_ip>
        <sip_call_id>c477994b-9f62-122a-43a0-000f1fc8e441</sip_call_id>
        <remote_media_ip>67.65.105.29</remote_media_ip>
        <hangup_cause>NORMAL_CLEARING</hangup_cause>
        <endpoint_disposition>ANSWER</endpoint_disposition>
        <switch_r_sdp>v%3D0%20%..........etc</switch_r_sdp>
        <local_media_port>13780</local_media_port>
        <remote_media_port>13780</remote_media_port>
        <ignore_early_media>true</ignore_early_media>
      </variables>
      <app_log>
        <application app_name="conference" app_data="221"></application>
      </app_log>
      <callflow dialplan="">
        <extension name="221" number="221">
          <application app_name="conference" app_data="221"></application>
        </extension>
        <caller_profile>
          <username></username>
          <dialplan></dialplan>
          <caller_id_name>FreeSWITCH</caller_id_name>
          <ani></ani>
          <aniii></aniii>
          <caller_id_number>0000000000</caller_id_number>
          <network_addr></network_addr>
          <rdnis></rdnis>
          <destination_number>mydomain.com/foo@bar.com</destination_number>
          <uuid>ed18eda4-24bf-11dc-913a-37ac3cdbbaa7</uuid>
          <source>src/switch_ivr_originate.c</source>
          <context>default</context>
          <chan_name>sofia/mydomain.com/foo@bar.com</chan_name>
        </caller_profile>
        <times>
          <created_time>1182956764946190</created_time>
          <answered_time>1182956765107959</answered_time>
          <hangup_time>1182956785394251</hangup_time>
          <transfer_time>0</transfer_time>
        </times>
      </callflow>
    </cdr>
    """
    dom = minidom.parseString(cdr_xml_str)
    entry_time=get_entry_time(dom)
    print "Entry time: %s" % entry_time
    exit_time=get_exit_time(dom)
    print "Exit time: %s" % exit_time    
    conf_id = get_conf_id(dom)
    print "Conf id: %s" % conf_id        
    confcall = ConfCall.objects.get(pk=conf_id)
    print "confcall: %s" % confcall
    chan_name = get_chan_name(dom)
    print "chan_name: %s" % chan_name    
    sip_uri = phonenumutil.strip_sofia(chan_name)
    print "sip_uri: %s" % sip_uri    
    name = dbutil.name_from_number(sip_uri)
    print "name: %s" % name            
    uuid = get_uuid(dom)
    print "uuid: %s" % uuid
    direction = get_direction(dom)
    print "direction: %s" % direction

    # the whole shebang .. check db to see if it worked
    cp = cdrxml2confpres(cdr_xml_str)
    print "Conf presence: %s" % cp




# need to figure out how to distinguish between incoming
# and outgoing calls

# EXAMPLE INCOMING .. PSTN -> STANAPHONE -> ASTERISK -> FS

"""
<?xml version="1.0"?>
<cdr>
  <variables>
    <sip_via_rport>5060</sip_via_rport>
    <sip_req_uri>wikipbx%4069.60.109.39%3A5080</sip_req_uri>
    <local_media_ip>69.60.109.39</local_media_ip>
    <sip_from_port>5060</sip_from_port>
    <remote_media_ip>69.60.109.39</remote_media_ip>
    <sip_contact_uri>4085400303%4069.60.109.39%3A5060</sip_contact_uri>
    <sip_from_user_stripped>4085400303</sip_from_user_stripped>
    <sip_via_host>69.60.109.39</sip_via_host>
    <switch_r_sdp>v%3D0%20%20o%3Droot%2019339%2019339%20IN%20IP4%2069.60.109.39%20%20s%3Dsession%20%20c%3DIN%20IP4%2069.60.109.39%20%20t%3D0%200%20%20m%3Daudio%2018452%20RTP/AVP%200%208%20110%203%2097%2010%2018%20111%204%20101%20%20a%3Drtpmap%3A0%20PCMU/8000%20%20a%3Drtpmap%3A8%20PCMA/8000%20%20a%3Drtpmap%3A110%20speex/8000%20%20a%3Drtpmap%3A3%20GSM/8000%20%20a%3Drtpmap%3A97%20iLBC/8000%20%20a%3Drtpmap%3A10%20L16/8000%20%20a%3Drtpmap%3A18%20G729/8000%20%20a%3Dfmtp%3A18%20annexb%3Dno%20%20a%3Drtpmap%3A111%20G726-32/8000%20%20a%3Drtpmap%3A4%20G723/8000%20%20a%3Drtpmap%3A101%20telephone-event/8000%20%20a%3Dfmtp%3A101%200-16%20%20a%3DsilenceSupp%3Aoff%20-%20-%20-%20-%20%20</switch_r_sdp>
    <sip_to_host>69.60.109.39</sip_to_host>
    <sip_to_user>wikipbx</sip_to_user>
    <max_forwards>70</max_forwards>
    <sip_from_uri>4085400303%4069.60.109.39%3A5060</sip_from_uri>
    <local_media_port>18452</local_media_port>
    <sip_via_port>5060</sip_via_port>
    <remote_media_port>18452</remote_media_port>
    <sip_req_host>69.60.109.39</sip_req_host>
    <sip_req_user>wikipbx</sip_req_user>
    <sip_to_port>5080</sip_to_port>
    <sip_call_id>69d0bcba15f4dd5924d5441935c92d9b%4069.60.109.39</sip_call_id>
    <hangup_cause>UNALLOCATED</hangup_cause>
    <sip_contact_host>69.60.109.39</sip_contact_host>
    <sip_contact_user>4085400303</sip_contact_user>
    <endpoint_disposition>ANSWER</endpoint_disposition>
    <sip_req_port>5080</sip_req_port>
    <sip_contact_port>5060</sip_contact_port>
    <sip_from_host>69.60.109.39</sip_from_host>
    <sip_to_uri>wikipbx%4069.60.109.39%3A5080</sip_to_uri>
    <sip_from_user>4085400303</sip_from_user>
  </variables>
  <app_log>
    <application app_name="set" app_data="conf_code="></application>
    <application app_name="python" app_data="wikipbx.ivr.prompt_pin"></application>
    <application app_name="conference" app_data="154"></application>
  </app_log>
  <callflow dialplan="enum,XML">
    <extension name="wikipbx" number="wikipbx">
      <application app_name="set" app_data="conf_code="></application>
      <application app_name="python" app_data="wikipbx.ivr.prompt_pin"></application>
    </extension>
    <caller_profile>
      <username>4085400303</username>
      <dialplan>enum,XML</dialplan>
      <caller_id_name>4085400303</caller_id_name>
      <ani></ani>
      <aniii></aniii>
      <caller_id_number>4085400303</caller_id_number>
      <network_addr>69.60.109.39</network_addr>
      <rdnis></rdnis>
      <destination_number>wikipbx</destination_number>
      <uuid>e760c6c6-26ad-11dc-ab66-857a738b9477</uuid>
      <source>mod_sofia</source>
      <context>default</context>
      <chan_name>sofia/mydomain.com/4085400303@69.60.109.39:5060</chan_name>
    </caller_profile>
    <times>
      <created_time>1183168926735180</created_time>
      <answered_time>1183168927763921</answered_time>
      <hangup_time>1183168996495910</hangup_time>
      <transfer_time>0</transfer_time>
    </times>
  </callflow>
</cdr>

"""

# EXAMPLE OUTGOING
"""
<cdr>
  <variables>
    <local_media_ip>69.60.109.39</local_media_ip>
    <sip_call_id>ab25c39f-a143-122a-cfa2-000c76e6682d</sip_call_id>
    <remote_media_ip>69.60.109.39</remote_media_ip>
    <hangup_cause>NORMAL_CLEARING</hangup_cause>
    <endpoint_disposition>ANSWER</endpoint_disposition>
    <switch_r_sdp>v%3D0%20%20o%3Droot%2019339%2019339%20IN%20IP4%2069.60.109.39%20%20s%3Dsession%20%20c%3DIN%20IP4%2069.60.109.39%20%20t%3D0%200%20%20m%3Daudio%2010690%20RTP/AVP%200%20101%20%20a%3Drtpmap%3A0%20PCMU/8000%20%20a%3Drtpmap%3A101%20telephone-event/8000%20%20a%3Dfmtp%3A101%200-16%20%20a%3DsilenceSupp%3Aoff%20-%20-%20-%20-%20%20</switch_r_sdp>
    <local_media_port>10690</local_media_port>
    <remote_media_port>10690</remote_media_port>
    <ignore_early_media>true</ignore_early_media>
  </variables>
  <app_log>
    <application app_name="conference" app_data="153"></application>
  </app_log>
  <callflow dialplan="">
    <extension name="153" number="153">
      <application app_name="conference" app_data="153"></application>
    </extension>
    <caller_profile>
      <username></username>
      <dialplan></dialplan>
      <caller_id_name>FreeSWITCH</caller_id_name>
      <ani></ani>
      <aniii></aniii>
      <caller_id_number>0000000000</caller_id_number>
      <network_addr></network_addr>
      <rdnis></rdnis>
      <destination_number>mydomain.com/600@telzap.com</destination_number>
      <uuid>d3c08744-26a0-11dc-ab66-857a738b9477</uuid>
      <source>src/switch_ivr_originate.c</source>
      <context>default</context>
      <chan_name>sofia/mydomain.com/600@telzap.com</chan_name>
    </caller_profile>
    <times>
      <created_time>1183163310350585</created_time>
      <answered_time>1183163310413510</answered_time>
      <hangup_time>1183163335375352</hangup_time>
      <transfer_time>0</transfer_time>
    </times>
  </callflow>
</cdr>
"""
