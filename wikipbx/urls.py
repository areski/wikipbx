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
import os
from django.conf import settings
from django.conf.urls.defaults import *
from django.contrib import admin

urlpatterns = patterns(
    '',
    url('',
        include( 'wikipbx.wikipbxweb.urls', namespace='wikipbxweb')))

# Contacts
if 'wikipbx.contacts' in settings.INSTALLED_APPS:
    urlpatterns += patterns(
        '',
        url(r'^contacts/',
            include('wikipbx.contacts.urls', namespace='contacts')),
        )

# Enable static serving only for debug mode. Use your web server as front-end
# in production.
if settings.DEBUG:
    urlpatterns += patterns(
        'django.views.static',
        url(r'^(fav.ico)$', 'serve',
            {'document_root': os.path.join(settings.INSTALL_SRC,
                                           'wikipbxweb', 'static', 'icons')}),
        url(r'^site_media/(.*)$', 'serve',
            {'document_root': os.path.join(settings.INSTALL_SRC,
                                           'wikipbxweb', 'static')}),
        url(r'^soundclips_media/(.*)$', 'serve',
            {'document_root': os.path.join(settings.INSTALL_SRC, 'soundclips')}))


if getattr(settings, 'ENABLE_DB_ADMIN', False):
    admin.autodiscover()

    urlpatterns += patterns(
        '',
        url('^admin/', include(admin.site.urls)),
    )


