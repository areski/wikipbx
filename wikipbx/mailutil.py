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

import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'wikipbx.settings'

import datetime
import random
import smtplib
import sys
import time
from email.MIMEText import MIMEText
from email.MIMEImage import MIMEImage
from email.MIMEMultipart import MIMEMultipart
from wikipbx.wikipbxweb import models


class HtmlMail:
    """
    Allows fine control so that image url's and text are passed
    in as parameters
    """
    def __init__(self, msg_body, server_host, server_port,
                 encoding="utf-8"):
        self.server_port = server_port
        self.server_host = server_host
        self.msg_body = msg_body        
        self.encoding = encoding
        self.img_c = 0

    def set_log(self, log):
        self.log = log

    def get_msg(self):
        msg_body = "<p>"
        msg_body += self.msg_body
        msg_body += "</p>"

        msg = MIMEMultipart("related")

        tmsg = MIMEText(msg_body, "html", self.encoding)
        msg.attach(tmsg)
            
        return msg


class EmailConfigurationError(Exception):
    pass


def acct_send(account, recipients, subject, msg_body, emailconfig=None):
    """
    Gets information from account and calls underlying send
    """
    if not emailconfig:
        emailconfigs = models.EmailConfig.objects.filter(account=account)[:1]
        if emailconfigs:
            emailconfig = emailconfigs[0]
        else:
            raise EmailConfigurationError
        
    send(
        recipients=recipients, subject=subject, msg_body=msg_body,
        server_host=account.ext_sip_ip, server_port=account.server.http_port,
        from_email=emailconfig.from_email, email_host=emailconfig.email_host,
        email_port=emailconfig.email_port, auth_user=emailconfig.auth_user,
        auth_password=emailconfig.auth_password, use_tls=emailconfig.use_tls)


def send(recipients, subject, msg_body, server_host, server_port, from_email,
         email_host, email_port, auth_user, auth_password, use_tls):
    """
    Warning: if multiple recips are specified, they will
    all be able to see eachother's email!!
    @param top_body - the html text above pictures
    @param bottom_body - the html text below pictures
    @param server_host - server host for voicemail page linkback purposes
    @param server_port - server port for voicemail page linkback purposes     
    """
    hm = HtmlMail(
        msg_body=msg_body, server_host=server_host, server_port=server_port)
    msg = hm.get_msg()

    msg["Subject"] = subject
    msg["From"] = from_email
    msg['To'] = ', '.join(recipients)

    random_bits = str(random.getrandbits(64))

    msg['Message-ID'] = "<%d.%s@%s>" % (time.time(), random_bits, "test")

    server = smtplib.SMTP(email_host, int(email_port))

    if use_tls:
        server.ehlo(email_host)
        server.starttls()

    server.ehlo(email_host)
    if auth_user:
        server.login(auth_user, auth_password)

    server.sendmail(from_email, recipients, msg.as_string())

    try:
        server.close() # with .quit(), at least smtp.gmail.com complains
    except:
        raise    
    
